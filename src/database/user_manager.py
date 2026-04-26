from database.db import get_db
import time
import json

async def get_user_data(chat_id, user_id, full_name=None):
    db = get_db()
    async with db.execute("SELECT * FROM users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)) as cursor:
        row = await cursor.fetchone()

    if row:
        data = dict(row)
        data['inventory'] = json.loads(data['inventory'])
        data['is_banned'] = bool(data['is_banned'])
        data['hide_in_top'] = bool(data['hide_in_top'])
        data['is_vip'] = bool(data['is_vip'])

        if full_name and data.get('full_name') != full_name:
            await db.execute("UPDATE users SET full_name = ? WHERE chat_id = ? AND user_id = ?", (full_name, chat_id, user_id))
            await db.commit()
            data['full_name'] = full_name
        return data
    else:
        default_name = full_name if full_name else "User"
        default_data = {
            'balance': 500,
            'last_bonus_time': 0.0,
            'last_work_time': 0.0,
            'last_crime_time': 0.0,
            'inventory': {},
            'is_banned': False,
            'hide_in_top': False,
            'full_name': default_name,
            'is_vip': False
        }
        await db.execute("""
            INSERT INTO users (chat_id, user_id, full_name, balance, last_bonus_time, last_work_time, last_crime_time, inventory, is_banned, hide_in_top, is_vip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, user_id, default_name, default_data['balance'], default_data['last_bonus_time'], default_data['last_work_time'], default_data['last_crime_time'], json.dumps(default_data['inventory']), default_data['is_banned'], default_data['hide_in_top'], default_data['is_vip']))
        await db.commit()
        return default_data

async def update_user_balance(chat_id, user_id, amount):
    db = get_db()
    data = await get_user_data(chat_id, user_id)
    new_balance = data.get('balance', 0) + amount
    await db.execute("UPDATE users SET balance = ? WHERE chat_id = ? AND user_id = ?", (new_balance, chat_id, user_id))
    await db.commit()
    return new_balance

async def update_user_field(chat_id, user_id, field, value):
    db = get_db()
    # Simple check to prevent sql injection on field name
    allowed_fields = ['balance', 'last_bonus_time', 'last_work_time', 'last_crime_time', 'is_banned', 'hide_in_top', 'is_vip', 'full_name']
    if field in allowed_fields:
        await db.execute(f"UPDATE users SET {field} = ? WHERE chat_id = ? AND user_id = ?", (value, chat_id, user_id))
        await db.commit()


BUSINESSES = {
    "shawarma": 10000,
    "carwash": 60000,
    "restaurant": 300000,
    "dealership": 1500000,
    "casino": 10000000
}

async def check_and_give_bonus(chat_id, user_id, full_name=None):
    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return False, 0

    last_bonus = data.get('last_bonus_time', 0)
    current_time = time.time()

    if current_time - last_bonus >= 86400:
        is_vip = data.get('is_vip', False)
        base_bonus = 1000 if is_vip else 450

        # Calculate business income
        business_income = 0
        inventory = data.get('inventory', {})
        for item, count in inventory.items():
            if item in BUSINESSES:
                business_income += BUSINESSES[item] * count

        total_bonus = base_bonus + business_income

        db = get_db()
        new_balance = data.get('balance', 500) + total_bonus
        await db.execute("UPDATE users SET balance = ?, last_bonus_time = ? WHERE chat_id = ? AND user_id = ?", (new_balance, current_time, chat_id, user_id))
        await db.commit()
        return True, total_bonus
    return False, 0

async def add_item_to_inventory(chat_id, user_id, item_name):
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    inv[item_name] = inv.get(item_name, 0) + 1

    db = get_db()
    await db.execute("UPDATE users SET inventory = ? WHERE chat_id = ? AND user_id = ?", (json.dumps(inv), chat_id, user_id))
    await db.commit()

async def remove_item_from_inventory(chat_id, user_id, item_name):
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    if inv.get(item_name, 0) > 0:
        inv[item_name] -= 1
        if inv[item_name] == 0:
            del inv[item_name]

        db = get_db()
        await db.execute("UPDATE users SET inventory = ? WHERE chat_id = ? AND user_id = ?", (json.dumps(inv), chat_id, user_id))
        await db.commit()
        return True
    return False

async def get_top_users(chat_id, limit=10):
    db = get_db()
    async with db.execute("SELECT user_id, full_name, balance, is_vip FROM users WHERE chat_id = ? AND is_banned = 0 AND hide_in_top = 0 ORDER BY balance DESC LIMIT ?", (chat_id, limit)) as cursor:
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]
