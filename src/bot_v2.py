import asyncio
from distutils.command.config import config
from nextcord import Client, Interaction, SlashOption, Embed, Colour
import time
import aiohttp
import json
import base64
from Classes import Config

client = Client()


def validate_license_key(license_key: str):
	try:
		license_json = json.loads(base64.b64decode(license_key.encode("ascii")).decode("ascii"))
	except:
		return False
	if len([i for i in ["script", "limit_type", "expire_limit", "generation_time"] if i not in license_json.keys()]) > 0:
		return False
	return license_json

@client.event
async def on_ready():
	print(f"Logged in as {client.user.name} ({client.user.id})")

@client.slash_command(name="new_license_key", guild_ids=client.config.get("guild_ids"), description="Generate and register a new license key")
async def new_key(
	interaction: Interaction,
	script = SlashOption(
		description="The script to generate a license key for",
		choices=[
			"twitter_gen",
			"discord_gen",
			"twitter_tools",
			"discord_tools",
		],
		required=True
	),
	limit_type = SlashOption(
		description="The type of limit to apply to the license key",
		choices=[
			"time_limit",
			"accounts_limit",
		],
		required=True
	),
	expire_limit: float = SlashOption(
		description="The limit to apply to the license key. days(30/60) if limited by time or number of accounts(1000/5000) if limited by accounts",
		required=True
	)
):
	if str(interaction.user.id) not in client.config.get("master_keys").values():
		return await interaction.reply("You are not authorized to use this command")

	gen_time = time.time()
	data = {
		"script": script,
		"limit_type": limit_type,
		"expire_limit": (gen_time+(expire_limit*86400)) if limit_type == "time_limit" else expire_limit, ## days * 864000 = seconds
		"generation_time": gen_time
	}
	license_key = base64.b64encode(json.dumps(data).encode("ascii")).decode("ascii")

	register = await client.session.post(
		url=f"http://{client.host_addr}/license/owner/register",
		json=data,
		headers={
			"Authorization": client.config.get("master_keys")[str(interaction.user.id)],
			"license_key": license_key
		}
	)

	if register.status_code != 204:
		return await interaction.send(f"Error: {register.status_code}\n{register.text}")
	return await interaction.send(embed=Embed(
		title="New License Key",
		colour=Colour.green(),
		description=f"""
License key: {license_key}
Script: {script}
Limit type: {limit_type}
Limit: {expire_limit} {"days" if limit_type == "time_limit" else "accounts"}
Generation time: {gen_time}
"""
		)
	)

@client.slash_command(name="delete", guild_ids=client.config.get("guild_ids"), description="Force delete a license key")
async def delete_key(
	interaction: Interaction,
	license_key: str = SlashOption(
		description="The license key to delete",
		required=True
	),
	reason: str = SlashOption(
		description="The reason for deleting the license key",
		required=True
	)
):
	if str(interaction.user.id) not in client.config.get("master_keys").values():
		return await interaction.reply("You are not authorized to use this command")

	license_json = validate_license_key(license_key)
	if not license_json:
		return await interaction.reply("Invalid license key")

	delete = await client.session.delete(
		url=f"http://{client.host_addr}/license/owner/delete",
		headers={
			"Authorization": client.config.get("master_keys")[str(interaction.user.id)],
			"license_key": license_key
		},
	)

	if delete.status_code != 204:
		return await interaction.send(f"Error: {delete.status_code}\n{delete.text}")

	return await interaction.send(embed=Embed(
		title="License Key Deleted",
		colour=Colour.red(),
		description=f"""
License key: {license_key}
Reason: {reason}
"""
		)
	)

@client.slash_command(name="update", guild_ids=client.config.get("guild_ids"), description="Update a license key")
async def update_key(
	interaction: Interaction,
	license_key: str = SlashOption(
		description="The license key to update",
		required=True
	),
	expire_limit: float = SlashOption(
		description="The limit to apply to the license key. days(30/60) if limited by time or number of accounts(1000/5000) if limited by accounts",
		required=True
	)
):
	if str(interaction.user.id) not in client.config.get("master_keys").values():
		return await interaction.reply("You are not authorized to use this command")

	license_json = validate_license_key(license_key)
	if not license_json:
		return await interaction.reply("Invalid license key")

	update = await client.session.put(
		url=f"http://{client.host_addr}/license/owner/update",
		json={"expire_limit": expire_limit},
		headers={
			"Authorization": client.config.get("master_keys")[str(interaction.user.id)],
			"license_key": license_key
		}
	)

	if update.status_code != 204:
		return await interaction.send(f"Error: {update.status_code}\n{update.text}")

	return await interaction.send(embed=Embed(
		title="License Key Updated",
		colour=Colour.green(),
		description=f"""
License key: {license_key}
Limit: {expire_limit} {"days" if license_json["limit_type"] == "time_limit" else "accounts"}
"""
		)
	)

@client.slash_command(name="info", guild_ids=client.config.get("guild_ids"), description="Get information about a license key")
async def info_key(
	interaction: Interaction,
	license_key: str = SlashOption(
		description="The license key to get information about",
		required=True
	)
):
	license_json = validate_license_key(license_key)
	if not license_json:
		return await interaction.reply("Invalid license key")
	
	info_req = await client.session.get(
		url=f"http://{client.host_addr}/license/user/validate",
		headers={"license_key": license_key},
		json={"hwid": "bypass", "script": "bypass"}
	)

	return await interaction.send(embed=Embed(
		title="License Key Information",
		colour=Colour.green(),
		description=f"""
License key: {license_key}
Script: {license_json["script"]}
Limit type: {license_json["limit_type"]}
Initial Limit: {license_json["expire_limit"]} {"days" if license_json["limit_type"] == "time_limit" else "accounts"}
Limit Left: {info_req.json()[0]["expire_limit"]} {"days" if license_json["limit_type"] == "time_limit" else "accounts"}
Generation time: {license_json["generation_time"]}
"""
		)
	)

@client.slash_command(name="purge_database", guild_ids=client.config.get("guild_ids"), description="COMPLETELY Purge the database of all license keys")
async def purge_database(interaction: Interaction):
	if str(interaction.user.id) not in client.config.get("master_keys").values():
		return await interaction.reply("You are not authorized to use this command")
	
	other_user = [i for i in config.get("master_keys").keys() if i != str(interaction.user.id)][0]

	await interaction.channel.send(f"<@{other_user}> send `agree` if you wish to continue with this action. You have 5 minutes.")
	def check(m):
		m.channel.id == interaction.channel.id and m.author.id == int(other_user) and m.content.lower() == "agree"

	try:
		msg = await client.wait_for("message", check=check, timeout=60*5)
	except asyncio.TimeoutError:
		return await interaction.reply("No response from other admin. Aborting.")


	purge = await client.session.delete(
		url=f"http://{client.host_addr}/license/owner/purge",
		headers={
			"Authorization": "".join(list(config.get("master_keys").values()))
		}
	)

	if purge.status_code != 204:
		return await interaction.send(f"Error: {purge.status_code}\n{purge.text}")

	return await interaction.send(embed=Embed(
		title="Database Purged",
		colour=Colour.red(),
		description="The database has been purged"
		)
	)

async def startup():
	client.config = Config("config.json")
	client.session = aiohttp.ClientSession()
	client.host_addr = client.config.get("api_host_addr")



client.loop.create_task(startup())
client.run(client.config.get("token"))

