from db import get_db
import time

def get_user_ref(chat_id, user_id):
    db = get_db()
    return db.collection('chats').document(str(chat_id)).collection('users').document(str(user_id))

async def get_user_data(chat_id, user_id, full_name=None):
    ref = get_user_ref(chat_id, user_id)
    doc = await ref.get()

    if doc.exists:
        data = doc.to_dict()
        if full_name and data.get('full_name') != full_name:
            await ref.update({'full_name': full_name})
            data['full_name'] = full_name
        return data
    else:
        # Default data if not exists
        default_name = full_name if full_name else "User"
        default_data = {
            'balance': 500,
            'last_bonus_time': 0,
            'last_work_time': 0,
            'last_crime_time': 0,
            'inventory': {},
            'is_banned': False,
            'hide_in_top': False,
            'full_name': default_name,
            'is_vip': False
        }
        await ref.set(default_data)
        return default_data

async def update_user_balance(chat_id, user_id, amount):
    ref = get_user_ref(chat_id, user_id)
    doc = await ref.get()
    if doc.exists:
        data = doc.to_dict()
        new_balance = data.get('balance', 0) + amount
        await ref.update({'balance': new_balance})
        return new_balance
    return None

async def update_user_field(chat_id, user_id, field, value):
    ref = get_user_ref(chat_id, user_id)
    doc = await ref.get()
    if doc.exists:
        await ref.update({field: value})

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
        ref = get_user_ref(chat_id, user_id)
        is_vip = data.get('is_vip', False)
        base_bonus = 1000 if is_vip else 450

        # Calculate business income
        business_income = 0
        inventory = data.get('inventory', {})
        for item, count in inventory.items():
            if item in BUSINESSES:
                business_income += BUSINESSES[item] * count

        total_bonus = base_bonus + business_income

        new_balance = data.get('balance', 500) + total_bonus
        await ref.update({
            'balance': new_balance,
            'last_bonus_time': current_time
        })
        return True, total_bonus
    return False, 0

async def add_item_to_inventory(chat_id, user_id, item_name):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    inv[item_name] = inv.get(item_name, 0) + 1
    await ref.update({'inventory': inv})

async def remove_item_from_inventory(chat_id, user_id, item_name):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    if inv.get(item_name, 0) > 0:
        inv[item_name] -= 1
        if inv[item_name] == 0:
            del inv[item_name]
        await ref.update({'inventory': inv})
        return True
    return False

async def get_top_users(chat_id, limit=10):
    db = get_db()
    users_ref = db.collection('chats').document(str(chat_id)).collection('users')
    docs = await users_ref.get()

    users = []
    for doc in docs:
        data = doc.to_dict()
        if not data.get('hide_in_top', False) and not data.get('is_banned', False):
            users.append({
                'user_id': doc.id,
                'full_name': data.get('full_name', 'Unknown'),
                'balance': data.get('balance', 0),
                'is_vip': data.get('is_vip', False)
            })

    users.sort(key=lambda x: x['balance'], reverse=True)
    return users[:limit]
