import asyncio
import json
from nextcord import Client, Interaction, SlashOption, Embed, Colour, Message, Intents
import time
import aiohttp
from Classes import Config

client = Client(intents=Intents.all())
client.config = Config("config.json")


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
		description="The limit to apply to the license key. days/accounts",
		required=True
	)
):
	await interaction.response.defer()

	if str(interaction.user.id) not in client.config.get("master_keys").keys():
		return await interaction.send("You are not authorized to use this command.", ephemeral=True)

	data = {
		"script": script,
		"limit_type": limit_type,
		"expire_limit": expire_limit*86400 if limit_type == "time_limit" else expire_limit, ## days * 864000 = seconds
	}

	try:
		register = await client.session.put(
			url=f"http://{client.host_addr}/license/owner/register",
			json=data,
			headers={
				"Authorization": client.config.get("master_keys")[str(interaction.user.id)],
			}
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while PUT `/owner/register`.\n{e}", ephemeral=True)

	if register.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif register.status_code == 401:
		return await interaction.followup.send("You are not authorized to do this action.", ephemeral=True)
	elif register.status_code == 500:
		return await interaction.followup.send(f"Backend Error: {register.json()['error']}", ephemeral=True)
	elif register.status_code == 201:
		license_key = register.json()["license_key"]
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

	return await interaction.followup.send(embed=Embed(
		title="New License Key",
		colour=Colour.green(),
		description=f"""
License key: `{license_key}`
Script: {script}
Limit type: {limit_type}
Limit: {expire_limit} {"days" if limit_type == "time_limit" else "accounts"}
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
	if str(interaction.user.id) not in client.config.get("master_keys").keys():
		return await interaction.send("You are not authorized to use this command", ephemeral=True)

	try:
		delete = await client.session.delete(
			url=f"http://{client.host_addr}/license/owner/delete",
			headers={
				"Authorization": client.config.get("master_keys")[str(interaction.user.id)],
				"license-key": license_key
			},
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while DELETE `/owner/delete`.\n{e}", ephemeral=True)

	if delete.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif delete.status_code == 401:
		return await interaction.followup.send("You are not authorized to do this action.", ephemeral=True)
	elif delete.status_code == 404:
		return await interaction.followup.send("The DB does not know any such license key.", ephemeral=True)
	elif delete.status_code == 500:
		return await interaction.followup.send(f"Backend Error: {delete.json()['error']}", ephemeral=True)
	elif delete.status_code == 204:
		pass
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

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
		description="The limit to add to the license key. days/accounts",
		required=True
	)
):
	await interaction.response.defer(ephemeral=True)
	if str(interaction.user.id) not in client.config.get("master_keys").keys():
		return await interaction.followup.send("You are not authorized to use this command", ephemeral=True)

	try:
		update = await client.session.post(
			url=f"http://{client.host_addr}/license/owner/update",
			headers={
				"authorization": client.config.get("master_keys")[str(interaction.user.id)],
				"license-key": license_key
			},
			json={
				"expire_limit": expire_limit
			}
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while POST `/owner/update`.\n{e}", ephemeral=True)

	if update.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif update.status_code == 401:
		return await interaction.followup.send("You are not authorized to do this action.", ephemeral=True)
	elif update.status_code == 404:
		return await interaction.followup.send("The DB does not know any such license key.", ephemeral=True)
	elif update.status_code == 500:
		return await interaction.followup.send(f"Backend Error: {update.json()['error']}", ephemeral=True)
	elif update.status_code == 204:
		pass
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

	return await interaction.followup.send(embed=Embed(
		title="License Key Updated",
		colour=Colour.green(),
		description=f"""
License key: {license_key}
Limit Added: {expire_limit}
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
	await interaction.response.defer(ephemeral=True)

	try:
		info_req = await client.session.get(
			url=f"http://{client.host_addr}/license/user/info",
			headers={"license-key": license_key},
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while GET `/user/info`.\n{e}", ephemeral=True)


	if info_req.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif info_req.status_code == 404:
		return await interaction.followup.send("The DB does not know any such license key.", ephemeral=True)
	elif info_req.status_code == 200:
		pass
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

	info_json = info_req.json()
	if info_json["limit_type"] == "time_limit":
		limit_left = info_json["expire_limit"]/86400
		llt = "days"
	else:
		limit_left = info_json["expire_limit"]
		llt = "accounts"

	return await interaction.followup.send(embed=Embed(
		title="License Key Information",
		colour=Colour.green(),
		description=f"""
License key: `{license_key}`
Script: {info_json["script"]}
Limit type: {info_json["limit_type"]}
Limit Left: {limit_left} {llt}
"""
		),
		ephemeral=True
	)

@client.slash_command(name="fetchall", guild_ids=client.config.get("guild_ids"), description="Fetch EVERYTHING from the DB")
async def fetchall(
	interaction: Interaction,
):
	await interaction.response.defer(ephemeral=True, with_message="Fetching...")
	if str(interaction.user.id) not in client.config.get("master_keys").keys():
		return await interaction.send("You are not authorized to use this command", ephemeral=True)
	try:
		info_req = await client.session.get(
			url=f"http://{client.host_addr}/license/owner/all",
			headers={
				"Authorization": client.config.get("master_keys")[str(interaction.user.id)]
			}
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while GET `/owner/all`.\n{e}", ephemeral=True)


	if info_req.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif info_req.status_code == 401:
		return await interaction.followup.send("You are not authorized to do this action", ephemeral=True)
	elif info_req.status_code == 410:
		return await interaction.followup.send("The DB is empty", ephemeral=True)
	elif info_req.status_code == 200:
		pass
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

	return await interaction.send(f"```json\n{json.loads(info_req.json(), indent=4)}```", ephemeral=True)

@client.slash_command(name="purge_database", guild_ids=client.config.get("guild_ids"), description="COMPLETELY Purge the database of all license keys")
async def purge_database(interaction: Interaction):
	await interaction.response.defer()

	if str(interaction.user.id) not in client.config.get("master_keys").keys():
		return await interaction.send("You are not authorized to use this command")

	other_user = [i for i in client.config.get("master_keys").keys() if i != str(interaction.user.id)][0]

	await interaction.channel.send(f"<@{other_user}> send `agree` if you wish to continue with this action. You have 5 minutes.")
	def check(m: Message):
		m.channel.id == interaction.channel.id and m.author.id == int(other_user) and m.content.lower() == "agree"

	try:
		msg = await client.wait_for("message", check=check, timeout=60*5)
	except asyncio.TimeoutError:
		return await interaction.send("No response from other admin. Aborting.")

	try:
		purge = await client.session.delete(
			url=f"http://{client.host_addr}/license/owner/purge",
			headers={
				"Authorization": "".join(list(client.config.get("master_keys").values()))
			}
		)
	except Exception as e:
		return await interaction.followup.send(f"The API did not not respond Error while DELETE `/owner/purge`.\n{e}", ephemeral=True)

	if purge.status_code == 400:
		return await interaction.followup.send("There is some missing data, perhaps you forgot to fill out a field.", ephemeral=True)
	elif purge.status_code == 401:
		return await interaction.followup.send("You are not authorized to do this action", ephemeral=True)
	elif purge.status_code == 500:
		return await interaction.followup.send(f"Internal Server Error: {e}", ephemeral=True)
	elif purge.status_code == 204:
		pass
	else:
		return await interaction.followup.send("You should not have reached here, please contact the developer to resolve.", ephemeral=True)

	return await interaction.followup.send(embed=Embed(
		title="Database Purged",
		colour=Colour.red(),
		description="The database has been purged."
		)
	)

async def startup():
	client.session = aiohttp.ClientSession()
	client.host_addr = client.config.get("api_host_addr")


client.loop.create_task(startup())
client.run(client.config.get("token"))
