import aiosqlite, asyncio


async def make():
    db = await aiosqlite.connect("licenses.sqlite3")
    await db.execute("CREATE TABLE IF NOT EXISTS licenses (license_key TEXT UNIQUE PRIMARY KEY, limit_type TEXT, script TEXT, hwid TEXT, expire_limit BIGINT)")
    await db.commit()
    await db.close()

asyncio.run(make())