from typing import Literal
from fastapi import FastAPI, Header
import aiosqlite
import asyncio
import time
import base64
import json
from Classes import New, Activate, Validate, Update, Config

config = Config("config.json")


app = FastAPI()

async def get_license_info(license_key: str):
    db = await aiosqlite.connect("licenses.sqlite3")
    license_details_raw = await (
        await db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
    ).fetchone()

    if not license_details_raw:
        return False

    license_details = {
        "limit_type": license_details_raw[1],
        "script": license_details_raw[2],
        "hwid": license_details_raw[3],
        "expire_limit": license_details_raw[4],
    }
    return license_details


async def update_license_info(license_key: str, limit_type: Literal["time_limit", "accounts_limit"], script: Literal["twitter_gen", "discord_gen", "twitter_tools", "discord_tools"], hwid: str, expire_limit: int):
    db = await aiosqlite.connect("licenses.sqlite3")
    try:
        await db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
        await db.execute(
            "INSERT INTO licenses (license_key, limit_type, script, hwid, expire_limit) VALUES(?, ?, ?, ?)",
            (license_key, limit_type, script, hwid, expire_limit),
        )
        await db.commit()
        return True
    except Exception as e:
        return e

async def delete(license_key: str):
    db = await aiosqlite.connect("licenses.sqlite3")
    try:
        await db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
        await db.commit()
        return True
    except Exception as e:
        return e

async def purge_db():
    db = await aiosqlite.connect("licenses.sqlite3")
    try:
        await db.execute("DELETE FROM licenses;")
        await db.commit()
        return True
    except Exception as e:
        return e

def validate_license_key(license_key: str):
    try:
        license_json = json.loads(base64.b64decode(license_key.encode("ascii")).decode("ascii"))
    except:
        return False
    return license_json

@app.put("/license/owner/register")
async def put_register(data: New, authorization: str = Header(default=None), license_key: str = Header(default=None)):
    if authorization not in config.get("master_keys").values():
        return 401, "Unauthorized"

    license_json = validate_license_key(license_key)
    if not license_json:
        return 400

    if license_json["script"] != data.script or license_key["limit_type"] != data.limit_type or license_key["expire_limit"] != data.expire_limit:
        return 400, "Key does not match passed data"

    action = asyncio.run(
        update_license_info(
            license_key=license_key,
            limit_type=data.limit_type,
            script=data.script,
            hwid="abcxyz",
            limit=data.expire_limit,
        )
    )

    return 204 if action else 500, f"Unhandled error: {action}"


@app.post("/license/user/activate")
async def post_activate(data: Activate, license_key: str = Header(default=None)):
    license_json = validate_license_key()
    if not license_json:
        return 400

    info_raw = asyncio.run(get_license_info(license_key))
    if not info_raw:
        return 403, "Not a valid license key."

    if info_raw["hwid"] != "abcxyz":
        return 409, "This license key has already been used on another machine."

    if not(info_raw["script"] == data.script == license_json["script"]):
        return 403, "Invalid for this script."

    if info_raw["limit_type"] == "time_limit":
        expire_limit = int(time.time())

    action = asyncio.run(
        update_license_info(
            license_key=license_key,
            limit_type=info_raw["limit_type"],
            script=info_raw["script"],
            hwid=data.hwid,
            limit=expire_limit,
        )
    )

    return 204 if action else 500, f"Unhandled error: {action}"

@app.get("/license/user/validate")
async def get_verify_license(data: Validate, license_key: str = Header(default=None)):
    license_json = validate_license_key(license_key)
    if not license_json:
        return 400

    info_raw = asyncio.run(get_license_info(license_key))
    if not info_raw:
        return 403, "Not a valid license key for this script."

    if info_raw["hwid"] != data.hwid:
        return 409, "License key used on another machine."

    if not(info_raw["script"] == data.script == license_json["script"]):
        return 403, "Invalid for this script."

    if info_raw["limit_type"] == "time_limit":
        return 403, "License key has expired." if time.time() > info_raw["expire_limit"] else 200, info_raw["expire_limit"]

    elif info_raw["limit_type"] == "accounts_limit":
        return 403, "License key accounts allowance is finished." if info_raw["expire_limit"] <= 0 else 200, info_raw["expire_limit"]


@app.post("/license/owner/update")
async def post_update(data: Update, authorization: str = Header(default=None), license_key: str = Header(default=None)):
    if authorization not in config.get("master_keys").values():
        return 401, "Unauthorized"

    license_json = validate_license_key(license_key)
    if not license_json:
        return 400

    info_raw = asyncio.run(get_license_info(license_key))
    if not info_raw:
        return 400, {"Error": "License key not found"}

    if not(info_raw["script"] == data.script == license_json["script"]):
        return 400, {"Error": "Script does not match"}

    action = asyncio.run(
        update_license_info(
            license_key,
            info_raw["limit_type"],
            info_raw["script"],
            info_raw["hwid"],
            data.expire_limit
        )
    )
    return 204 if action else 500, f"Unhandled error: {action}"


@app.delete("/license/owner/delete")
async def delete_license(authorization: str = Header(default=None), license_key: str = Header(default=None)):
    if authorization not in config.get("master_keys").values():
        return 401, "Unauthorized"

    action = asyncio.run(delete(license_key))
    return 204 if action else 500, f"Unhandled error: {action}"

@app.delete("/license/owner/purge")
async def purge(authorization_1: str = Header(default=None), authorization_2: str = Header(default=None)):
    if authorization_1 not in config.get("master_keys").values() or authorization_2 not in config.get("master_keys").values():
        return 401, "Unauthorized"
    
    action = asyncio.run(purge())
    return 204 if action else 500, f"Unhandled error: {action}"
