from database.db import get_db
import json

async def get_game_chance(game_name: str) -> int:
    db = get_db()
    async with db.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'chances'") as cursor:
        row = await cursor.fetchone()

    if row:
        data = json.loads(row['setting_value'])
        return data.get(game_name, -1) # -1 означает честный рандом
    return -1

async def set_game_chance(game_name: str, percentage: int):
    db = get_db()
    async with db.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'chances'") as cursor:
        row = await cursor.fetchone()

    data = json.loads(row['setting_value']) if row else {}
    data[game_name] = percentage

    if row:
        await db.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'chances'", (json.dumps(data),))
    else:
        await db.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES ('chances', ?)", (json.dumps(data),))
    await db.commit()
