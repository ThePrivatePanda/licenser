from nextcord import Client, Interaction, SlashOption, Embed, Colour
import time
import aiohttp
import json
import base64
from Classes import Config

client = Client()


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
	...

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
	...

@client.slash_command(name="info", guild_ids=client.config.get("guild_ids"), description="Get information about a license key")
async def info_key(
	interaction: Interaction,
	license_key: str = SlashOption(
		description="The license key to get information about",
		required=True
	)
):
	...

@client.slash_command(name="purge_database", guild_ids=client.config.get("guild_ids"), description="COMPLETELY Purge the database of all license keys")
async def purge_database(interaction: Interaction):
	...


async def startup():
	client.config = Config("config.json")
	client.session = aiohttp.ClientSession()
	client.host_addr = client.config.get("api_host_addr")



client.loop.create_task(startup())
client.run(client.config.get("token"))

