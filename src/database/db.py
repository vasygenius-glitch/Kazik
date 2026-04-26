import aiosqlite
import os

db_pool = None

async def init_db(db_path="database.db"):
    global db_pool
    # Initialize the database asynchronously
    db_pool = await aiosqlite.connect(db_path)

    # Enable dict rows for easier access (like Firestore's to_dict())
    db_pool.row_factory = aiosqlite.Row

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            full_name TEXT,
            balance INTEGER DEFAULT 500,
            last_bonus_time REAL DEFAULT 0,
            last_work_time REAL DEFAULT 0,
            last_crime_time REAL DEFAULT 0,
            inventory TEXT DEFAULT '{}',
            is_banned BOOLEAN DEFAULT 0,
            hide_in_top BOOLEAN DEFAULT 0,
            is_vip BOOLEAN DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)

    await db_pool.commit()
    print(f"✅ База данных SQLite ({db_path}) успешно инициализирована.")
    return db_pool

def get_db():
    global db_pool
    if db_pool is None:
        raise Exception("Database not initialized. Call init_db first.")
    return db_pool

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
