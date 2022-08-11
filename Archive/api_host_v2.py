from fastapi import FastAPI
import aiosqlite
import asyncio
import time
import config
import base64
import json

app = FastAPI()

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

@app.post("/license/new")
async def post_activate_new(license: str, script: str, expiration: int, owner_pass: str):
    try:
        license_json = json.loads(base64.b64decode(license.encode("ascii")).decode("ascii"))
    except:
        return {"error": "Invalid license"}, 400

    if owner_pass != config.api_owner_pass:
        return "You aren't allowed to do that but good try", 403

    info_raw = asyncio.run(get_license_info(license))

    if info_raw:
        return "License already activated", 409

    if license_json["script"] != script:
        return "License script doesn't match", 409
    if license_json["expiration"] != expiration:
        return "License expiration doesn't match", 409

    action = asyncio.run(
        update_license_info(
            license, script, "abcxyz", time.time() + expiration * 60 * 60 ### hours * minutes * seconds
        )
    )

    if action:
        return f"License: {license} for script: {script} has been activated for: {expiration}", 200

@app.put("/license/activate")
async def post_activate(license:str, script:str, mac_address:str):
    try:
        license_json = json.loads(base64.b64decode(license.encode("ascii")).decode("ascii"))
    except:
        return {"error": "Invalid license"}, 400

    info_raw = asyncio.run(get_license_info(license))
    if not info_raw:
        return "License has not been activated by developer yet.", 403

    if license_json["script"] != script:
        return "License script doesn't match", 409

    if license_json["mac_address"] != "abcxyz":
        return "License used on another machine", 409

    action = asyncio.run(
        update_license_info(
            license,
            script,
            mac_address,
            info_raw["expiration"],
        )
    )

    if action is True:
        return "Worked!", 200
    else:
        return f"Something happened Ffs {action}", 500

@app.get("/license/verify")
async def get_verify_license(license: str, script: str, mac_address: str):
    try:
        license_json = json.loads(base64.b64decode(license.encode("ascii")).decode("ascii"))
    except:
        return {"error": "Invalid license"}, 400
    
    if license_json["script"] != script:
        return "License script doesn't match", 409
    if license_json["mac_address"] != mac_address:
        return "License used on another machine", 409

    info_raw = asyncio.run(get_license_info(license))

    if not info_raw:
        return "Not a valid license for the script.", 403

    if int(time.time()) > info_raw["expiration"]:
        return "Expired!", 403

    return info_raw["expiration"], 200
