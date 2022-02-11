import traceback
from nextcord.ext import commands
import aiosqlite
import time
import datetime
import json
import base64
import config

bot = commands.Bot(
    command_prefix=config.bot_prefix, owner_ids=config.bot_owner_ids
)


async def get_license_info(license_key):
    db = await aiosqlite.connect("licenses.sqlite3")
    license_details_raw = await (
        await db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
    ).fetchone()

    if not license_details_raw:
        return False

    license_details = {
        "activation_key": license_details_raw[0],
        "script": license_details_raw[1],
        "mac_address": license_details_raw[2],
        "expiration": license_details_raw[3],
    }
    return license_details


async def update_license_info(license_key, script, mac_address, expiration):
    db = await aiosqlite.connect("licenses.sqlite3")
    try:
        await db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
        await db.execute(
            "INSERT INTO licenses (license_key, script, mac_address, expiration) VALUES(?, ?, ?, ?)",
            (license_key, script, mac_address, expiration),
        )
        await db.commit()
        return True
    except Exception as e:
        return e

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id}) in {len(bot.guilds)} servers, seeing {len(bot.users)} users")

@bot.command(
    name="newkey",
    aliases=[
        "generate",
        "gen",
        "generatekey",
        "generatenew",
        "generatenewkey",
        "genkey",
        "gennew",
        "gennewkey",
    ],
)
async def newkey_(ctx, userid: int, script, expiration: int):
    data = {
        "userId": userid,
        "script": script,
        "expiration": expiration * 60 * 60,  ### hours * minutes * seconds
        "generationTime": int(time.time()),
    }

    data = base64.b64encode(json.dumps(data).encode("ascii")).decode("ascii")
    await ctx.send(data)


@bot.command(name="register", aliases=["activate", "update"])
@commands.is_owner()
async def activate_(ctx, license_key_raw, script, expiration: int):
    license_json = json.loads(base64.b64decode(license_key_raw.encode("ascii")).decode("ascii"))

    if license_json["script"] != script:
        return await ctx.reply("Failed bot check, key is not for this script.")
    if license_json["expiration"] != expiration:
        return await ctx.reply("Failed bot check, expiration does not match.")

    try:
        info_raw = await get_license_info(license_key_raw)
        if info_raw:
            seconds = info_raw["expiration"] + (expiration * 60 * 60)
        else:
            seconds = time.time() + (expiration * 60 * 60)

        action = await update_license_info(license_key_raw, script, "abcxyz", seconds)

        if action is True:
            return await ctx.reply(
                f"Activated license `{license_key_raw}` for script `{script}` for `{expiration}` hours, till `{datetime.datetime.utcfromtimestamp(seconds).strftime('%A, %d %B %Y, %H:%M:%S')}` (GMT)"
            )
        else:
            return await ctx.reply(f"Something happened Ffs {action}")
    except Exception as e:
        await ctx.send(traceback.format_exc())
        return await ctx.reply(e)


@bot.command(name="delete", aliases=["deactivate", "unregister"])
@commands.is_owner()
async def delete_(ctx, *keys):
    db = await aiosqlite.connect("licenses.sqlite3")
    for license_key in keys:
        try:
            await db.execute(
                "DELETE FROM licenses WHERE license_key = ?", (license_key,)
            )
            await db.commit()
            await ctx.send(f"Deleted {license_key}.")
        except Exception as e:
            return await ctx.reply(e)
    await ctx.reply("Done.")


@bot.command(name="deleteall", aliases=["purge"])
@commands.is_owner()
async def deleteall_(ctx):
    db = await aiosqlite.connect("licenses.sqlite3")
    cursor = await db.execute("SELECT license_key FROM licenses")
    keys = await cursor.fetchall()
    for license_key in keys:
        try:
            await db.execute(
                "DELETE FROM licenses WHERE license_key = ?", (license_key,)
            )
            await db.commit()
            await ctx.send(f"Deleted {license_key}.")
        except Exception as e:
            return await ctx.reply(e)
    await ctx.reply("Done.")


@bot.command(name="info")
@commands.is_owner()
async def info_(ctx, license_key):
    return await ctx.reply(await get_license_info(license_key))


@bot.command(name="fetchall")
@commands.is_owner()
async def fetchall_(ctx):
    db = await aiosqlite.connect("licenses.sqlite3")
    cursor = await db.execute("SELECT * FROM licenses")
    for i in await cursor.fetchall():
        license_details = {
            "license_key": i[0],
            "script": i[1],
            "mac_address": i[2],
            "expiration": datetime.datetime.utcfromtimestamp(i[3] + 19800).strftime(
                "%A, %d %B %Y, %H:%M:%S"
            ),
        }
        await ctx.send(license_details)
    await ctx.reply("Done.")


@bot.command(name="fetchfor", aliases=["fetch"])
async def fetchfor(ctx, col):
    db = await aiosqlite.connect("licenses.sqlite3")
    if col not in (
        "license",
        "license_key",
        "licenses",
        "keys",
        "script",
        "mac_address",
        "mac",
        "address",
    ):
        return await ctx.reply("Invalid request.")
    if col in ("license", "license_key", "licenses", "keys"):
        col = "expiration"
    elif col in ("mac_address", "mac", "address"):
        col = "mac_address"
    cursor = await db.execute(f"SELECT license_key, {col} FROM licenses")
    await ctx.reply(
        "\n".join(
            [
                f"{i[0]} ## {datetime.datetime.utcfromtimestamp(i[1] + 19800).strftime('%A, %d %B %Y, %H:%M:%S')}"
                for i in await cursor.fetchall()
            ]
        )
    )


@info_.error
async def info_error(ctx, error):
    error = getattr(error, "original", error)
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply("You use it like this: `!!info license_key`")


@delete_.error
async def delete_error(ctx, error):
    error = getattr(error, "original", error)
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply("You use it like this: `!!delete license_key`")


@activate_.error
async def delete_error(ctx, error):
    error = getattr(error, "original", error)
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply(
            "You use it like this: `!!activate license_key script time_in_hours`"
        )

@commands.group()
async def help(ctx):
    return await ctx.reply("register, delete and info commands i have right now lul.")


@help.command(name="register", aliases=["activate", "update"])
async def activate_help(ctx):
    return await ctx.reply(
        "You use it like this: `!!activate license_key script time_in_hours`\nActivate a license so its usable."
    )


@help.command(name="delete", aliases=["deactivate", "unregister"])
async def activate_help(ctx):
    return await ctx.reply(
        "You use it like this: `!!delete license_key`\nDeletes a license key from the db, it will no longer be usable or shit."
    )


@help.command(name="info")
async def activate_help(ctx):
    return await ctx.reply(
        "You use it like this: `!!get license_key`\nGives you all the info about a license key, the expiration is in seconds since epoch, convert using https://www.epochconverter.com/"
    )


bot.run(config.bot_token)
