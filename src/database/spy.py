from database.db import get_db
import json

_spy_cache = None

async def get_spy_chats() -> list:
    global _spy_cache
    if _spy_cache is not None:
        return _spy_cache

    db = get_db()
    async with db.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'spy_chats'") as cursor:
        row = await cursor.fetchone()

    if row:
        _spy_cache = json.loads(row['setting_value'])
    else:
        _spy_cache = []
        await db.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES ('spy_chats', '[]')")
        await db.commit()

    return _spy_cache

async def toggle_spy(chat_id: int) -> bool:
    global _spy_cache
    chats = await get_spy_chats()

    is_enabled = False
    if chat_id in chats:
        chats.remove(chat_id)
    else:
        chats.append(chat_id)
        is_enabled = True

    _spy_cache = chats
    db = get_db()
    await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'spy_chats'", (json.dumps(chats),))
    await db.commit()
    return is_enabled
