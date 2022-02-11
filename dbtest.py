import aiosqlite
import asyncio


async def make():
    db = await aiosqlite.connect("licenses.sqlite3.example")
    await db.execute(
        "CREATE TABLE IF NOT EXISTS licenses (license_key text UNIQUE PRIMARY KEY, script str, mac_address str, expiration int)"
    )
    await db.commit()
    await db.close()


async def put():
    db = await aiosqlite.connect("licenses.sqlite3.example")
    await db.execute(
        "INSERT INTO licenses (license_key, script, mac_address, expiration) VALUES(?, ?, ?, ?)",
        ("a", "a", "a", "1"),
    )
    await db.commit()


async def main():
    db = await aiosqlite.connect("licenses.sqlite3.example")
    license_details = await (
        await db.execute("SELECT * FROM licenses WHERE license_key = ?", ("b",))
    ).fetchone()
    print(license_details)
    await db.close()


asyncio.run(make())
