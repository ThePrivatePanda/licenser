from typing import Literal
from fastapi import FastAPI, Header, Response, status
import aiosqlite
import time
from Classes import New, Activate, Validate, Update, Config
import asyncio

config = Config("config.json")
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.db = await aiosqlite.connect("licenses.sqlite3")

@app.on_event("shutdown")
async def shutdown_event():
    await app.db.close()

async def get_all_licenses():
    licenses = await(await app.db.execute("SELECT * FROM licenses")).fetchall()
    return licenses if len(license) > 0 else [["basic", "None", "None", "None", "None"]]

async def get_license_info(license_key: str):
    license_details_raw = await (await app.db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key, ))).fetchone()

    if not license_details_raw:
        return None

    license_details = {
        "limit_type": license_details_raw[1],
        "script": license_details_raw[2],
        "hwid": license_details_raw[3],
        "expire_limit": license_details_raw[4],
    }
    return license_details


async def update_license_info(license_key: str, limit_type: Literal["time_limit", "accounts_limit"], script: Literal["twitter_gen", "discord_gen", "twitter_tools", "discord_tools"], hwid: str, expire_limit: int):
    ## here, expire limit should either be epoch time when it gets invalidated or the amount of more accounts the user can create
    ## It can be total time of validation incase of a new registration
    try:
        await app.db.execute("INSERT OR REPLACE INTO licenses (license_key, limit_type, script, hwid, expire_limit) VALUES(?, ?, ?, ?, ?)", (license_key, limit_type, script, hwid, expire_limit))
        await app.db.commit()
        return True
    except Exception as e:
        return e

async def delete(license_key: str):
    try:
        await app.db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key, ))
        await app.db.commit()
        return True
    except Exception as e:
        return e

async def purge_db():
    try:
        await app.db.execute("DELETE FROM licenses;")
        await app.db.commit()
        return True
    except Exception as e:
        return e

@app.put("/license/owner/register")
async def put_register(response: Response, data: New = None, authorization: str = Header(default=None), license_key: str = Header(default=None)):
    ## Here, in data, expire_limit should be seconds in which it gets invalidated or the amount of more accounts the user can create
    if None in [data, authorization, license_key]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    if authorization not in config.get("master_keys").values():
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Unauthorized"}

    action = await update_license_info(
        license_key=license_key,
        limit_type=data.limit_type,
        script=data.script,
        hwid="abcxyz",
        expire_limit=data.expire_limit,
        )
    if action is True:
        response.status_code = status.HTTP_201_CREATED
        return
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": action}


@app.post("/license/user/activate")
async def post_activate(response: Response, data: Activate = None, license_key: str = Header(default=None)):
    if None in [data, license_key]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    info_raw = await (get_license_info(license_key))
    if not info_raw:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "License not found"}

    if info_raw["hwid"] != "abcxyz":
        response.status_code = status.HTTP_409_CONFLICT
        return {"error": "HWID does not match"}

    if info_raw["limit_type"] == "time_limit":
        expire_limit = int(time.time()) + info_raw["expire_limit"]
    else:
        expire_limit = info_raw["expire_limit"]

    action = await (
        update_license_info(
            license_key=license_key,
            limit_type=info_raw["limit_type"],
            script=info_raw["script"],
            hwid=data.hwid,
            limit=expire_limit,
        )
    )

    if action is True:
        response.status_code = status.HTTP_202_ACCEPTED
        return
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": action}

@app.get("/license/user/validate")
async def get_verify_license(response: Response, data: Validate=None, license_key: str = Header(default=None)):
    if None in [data, license_key]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    info_raw = await get_license_info(license_key)
    if not info_raw:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "License not found"}

    if info_raw["limit_type"] == "time_limit":
        expire_limit = int(time.time()) + info_raw["expire_limit"]
    else:
        expire_limit = info_raw["expire_limit"]

    if info_raw["hwid"] == "abcxyz":
        action = await update_license_info(
            license_key=license_key,
            limit_type=info_raw["limit_type"],
            script=info_raw["script"],
            hwid=data.hwid,
            expire_limit=expire_limit,
        )

        if action is True:
            response.status_code = status.HTTP_202_ACCEPTED
            return
        else:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": action}
    elif info_raw["hwid"] == data.hwid:
        pass
    else:
        response.status_code = status.HTTP_409_CONFLICT
        return {"error": "HWID does not match"}

    if info_raw["limit_type"] == "time_limit":
        expired = time.time() > expire_limit
        if expired:
            response.status_code = status.HTTP_402_PAYMENT_REQUIRED
            return {"error": "License expired"}
        else:
            response.status_code = status.HTTP_201_OK

    elif info_raw["limit_type"] == "accounts_limit":
        if info_raw["expire_limit"] > 0:
            response.status_code = status.HTTP_201_OK
        else:
            response.status_code = status.HTTP_402_PAYMENT_REQUIRED
            return {"error": "License expired"}


@app.get("/license/user/info")
async def get_owner_info(response: Response, license_key: str = Header(default=None)):
    if not license_key:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    info_raw = await get_license_info(license_key)
    if not info_raw:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "License not found"}

    response.status_code = status.HTTP_200_OK
    return {"limit_type": info_raw["limit_type"], "expire_limit": info_raw["expire_limit"]}

@app.get("/license/owner/all")
async def get_owner_info(response: Response, authorization: str = Header(default=None)):
    if not authorization:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    if authorization not in config.get("master_keys").values():
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Unauthorized"}

    info_raw = await get_all_licenses()

    if len(info_raw) == 1 and info_raw[0][0] == "basic":
        response.status_code = status.HTTP_410_GONE
        return {"error": "Empty DB"}

    response.status_code = status.HTTP_200_OK
    return {"licenses": [{
        "license_key": i[0], 
        "limit_type": i[1],
        "script": i[2],
        "hwid": i[3],
        "expire_limit": i[4]
    }
    for i in info_raw]}

@app.post("/license/owner/update")
async def post_update(response: Response, data: Update=None, authorization: str = Header(default=None), license_key: str = Header(default=None)):
    if None in [data, authorization, license_key]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    if authorization not in config.get("master_keys").values():
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Unauthorized"}

    info_raw = await (get_license_info(license_key))
    if not info_raw:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "License not found"}

    expire_limit = data.expire_limit
    if info_raw["limit_type"] == "time_limit":
        expire_limit = int(time.time()+data.expire_limit)

    action = await (
        update_license_info(
            license_key,
            info_raw["limit_type"],
            info_raw["script"],
            info_raw["hwid"],
            expire_limit
        )
    )
    if not action:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": action}

    response.status_code = status.HTTP_204_NO_CONTENT
    return {"success": True}


@app.delete("/license/owner/delete")
async def delete_license(response: Response, authorization: str = Header(default=None), license_key: str = Header(default=None)):
    if None in [authorization, license_key]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    if authorization not in config.get("master_keys").values():
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Unauthorized"}

    action = await delete(license_key)
    if not action:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": action}

    response.status_code = status.HTTP_204_NO_CONTENT
    return {"success": True}

@app.delete("/license/owner/purge")
async def purge(response: Response, authorization: str = Header(default=None)):
    if not authorization:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing data"}

    if authorization != "".join(list(config.get("master_keys").values())):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Unauthorized"}
    
    action = await (purge())
    if not action:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": action}
    else:
        response.status_code = status.HTTP_204_NO_CONTENT
        return {"success": True}
