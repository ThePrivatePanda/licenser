import asyncio
import time

import aiosqlite
from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)


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


class Activate(Resource):
    def put(self):
        try:
            parser = reqparse.RequestParser()

            parser.add_argument("license", required=True)
            parser.add_argument("script", required=True)
            parser.add_argument("expiration", type=int, required=True)
            parser.add_argument("pwd", required=True)
            args = parser.parse_args()
        except:
            return "Bad request.", 400

        license = args["license"]
        if (
            args["pwd"]
            != "very not guessable password."
        ):
            return "You aren't allowed to do that but good try", 401

        info_raw = asyncio.run(get_license_info(license))

        if info_raw:
            seconds = info_raw["expiration"] + (args["expiration"] * 60 * 60)
        else:
            seconds = time.time() + (args["expiration"] * 60 * 60)

        action = asyncio.run(
            update_license_info(
                license, args["script"], "abcxyz", time.time() + seconds
            )
        )
        if action is True:
            return "Worked!", 200
        else:
            return f"Something happened Ffs {action}", 500

    def post(self):
        try:
            parser = reqparse.RequestParser()

            parser.add_argument("license", required=True)
            parser.add_argument("script", required=True)
            parser.add_argument("mac_address", required=True)
            args = parser.parse_args()
        except:
            return "Bad request.", 400

        info_raw = asyncio.run(get_license_info(args["license"]))
        if not info_raw:
            return "License is invalid or has not been activated by developer yet.", 403

        if info_raw["mac_address"] == "abcxyz" and info_raw["script"] == args["script"]:
            action = asyncio.run(
                update_license_info(
                    info_raw["license_key"],
                    info_raw["script"],
                    args["mac_address"],
                    info_raw["expiration"],
                )
            )
            if action is True:
                return "Worked!", 200
            else:
                return f"Something happened Ffs {action}", 500
        elif info_raw["mac_address"] == args["mac_address"]:
            return "Already done!", 200
        else:
            return "License already used on another machine.", 409


class VerifyLicense(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()

            parser.add_argument("license", required=True)
            parser.add_argument("script", required=True)
            parser.add_argument("mac_address", required=True)
            args = parser.parse_args()
        except:
            return "Bad request.", 400

        info_raw = asyncio.run(get_license_info(args["license"]))
        if not info_raw:
            return "Not a valid license for the script.", 403

        if int(time.time()) > info_raw["expiration"]:
            return "Expired!", 403
        if info_raw["mac_address"] != args["mac_address"]:
            return "This license has already been used on another machine.", 409
        elif info_raw["mac_address"] == "abcxyz":
            return info_raw["expiration"], 200
        return info_raw["expiration"], 200


api.add_resource(VerifyLicense, "/verify_license")
api.add_resource(Activate, "/activate")

app.run("0.0.0.0", "50505")
