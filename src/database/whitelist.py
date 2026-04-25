from database.db import get_db

async def get_whitelist():
    db = get_db()
    ref = db.collection('bot_settings').document('whitelist')
    doc = await ref.get()
    if doc.exists:
        return doc.to_dict().get('allowed_chats', [])
    return []

async def add_to_whitelist(chat_id: int):
    db = get_db()
    ref = db.collection('bot_settings').document('whitelist')
    whitelist = await get_whitelist()
    if chat_id not in whitelist:
        whitelist.append(chat_id)
        await ref.set({'allowed_chats': whitelist}, merge=True)
        return True
    return False

async def remove_from_whitelist(chat_id: int):
    db = get_db()
    ref = db.collection('bot_settings').document('whitelist')
    whitelist = await get_whitelist()
    if chat_id in whitelist:
        whitelist.remove(chat_id)
        await ref.set({'allowed_chats': whitelist}, merge=True)
        return True
    return False

async def log_unauthorized_chat(chat_id: int, chat_title: str):
    db = get_db()
    ref = db.collection('bot_settings').document('unauthorized_logs')
    doc = await ref.get()
    logs = doc.to_dict().get('logs', {}) if doc.exists else {}

    str_id = str(chat_id)
    if str_id not in logs:
        logs[str_id] = chat_title
        await ref.set({'logs': logs}, merge=True)
        return True
    return False
