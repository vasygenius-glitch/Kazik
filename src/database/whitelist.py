from database.db import get_db
import json

_whitelist_cache = None

async def get_whitelist():
    global _whitelist_cache
    if _whitelist_cache is not None:
        return _whitelist_cache

    db = get_db()
    async with db.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'whitelist'") as cursor:
        row = await cursor.fetchone()

    if row:
        data = json.loads(row['setting_value'])
        # data might be list or dict based on old migration logic
        if isinstance(data, list):
            _whitelist_cache = {int(k): "Unknown Group" for k in data if str(k).strip()}
            await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'whitelist'", (json.dumps({str(k): v for k, v in _whitelist_cache.items()}),))
            await db.commit()
        else:
            _whitelist_cache = {int(k): v for k, v in data.items() if str(k).strip()}
    else:
        _whitelist_cache = {}
        await db.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES ('whitelist', '{}')")
        await db.commit()

    return _whitelist_cache

async def add_to_whitelist(chat_id: int, chat_title: str = "Unknown Group"):
    global _whitelist_cache
    whitelist = await get_whitelist()
    if chat_id not in whitelist:
        whitelist[chat_id] = chat_title
        _whitelist_cache = whitelist

        save_data = {str(k): v for k, v in whitelist.items()}
        db = get_db()
        await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'whitelist'", (json.dumps(save_data),))
        await db.commit()
        return True
    return False

async def remove_from_whitelist(chat_id: int):
    global _whitelist_cache
    whitelist = await get_whitelist()
    if chat_id in whitelist:
        del whitelist[chat_id]
        _whitelist_cache = whitelist

        save_data = {str(k): v for k, v in whitelist.items()}
        db = get_db()
        await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'whitelist'", (json.dumps(save_data),))
        await db.commit()
        return True
    return False


async def log_unauthorized_chat(chat_id: int, chat_title: str):
    db = get_db()
    async with db.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'unauthorized_logs'") as cursor:
        row = await cursor.fetchone()

    logs = json.loads(row['setting_value']) if row else {}

    str_id = str(chat_id)
    if str_id not in logs:
        logs[str_id] = chat_title
        if row:
            await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'unauthorized_logs'", (json.dumps(logs),))
        else:
            await db.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES ('unauthorized_logs', ?)", (json.dumps(logs),))
        await db.commit()
        return True
    return False
