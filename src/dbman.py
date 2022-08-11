import aiosqlite, asyncio


async def make():
    db = await aiosqlite.connect("licenses.sqlite3.example")
    await db.execute("CREATE TABLE IF NOT EXISTS licenses (license_key TEXT, limit_type TEXT, script TEXT, hwid TEXT, expire_limit INTEGER)")
    await db.commit()
    await db.close()

asyncio.run(make())