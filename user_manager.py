from db import get_db
import time

def get_user_ref(chat_id, user_id):
    db = get_db()
    return db.collection('chats').document(str(chat_id)).collection('users').document(str(user_id))

# Кэш пользователей: {(chat_id, user_id): {"data": dict, "timestamp": float}}
_user_cache = {}
CACHE_TTL = 10.0 # Время жизни кэша в секундах

def get_from_cache(chat_id, user_id):
    key = (chat_id, user_id)
    if key in _user_cache:
        cache_entry = _user_cache[key]
        if time.time() - cache_entry["timestamp"] < CACHE_TTL:
            return cache_entry["data"].copy()
    return None

def set_in_cache(chat_id, user_id, data):
    key = (chat_id, user_id)
    _user_cache[key] = {"data": data.copy(), "timestamp": time.time()}

async def get_user_data(chat_id, user_id, full_name=None):
    cached_data = get_from_cache(chat_id, user_id)
    if cached_data:
        if full_name and cached_data.get('full_name') != full_name:
            # Обновляем имя, если изменилось
            cached_data['full_name'] = full_name
            set_in_cache(chat_id, user_id, cached_data)
            # В фоне обновляем в БД
            import asyncio
            ref = get_user_ref(chat_id, user_id)
            asyncio.create_task(ref.update({'full_name': full_name}))
        return cached_data

    ref = get_user_ref(chat_id, user_id)
    doc = await ref.get()

    if doc.exists:
        data = doc.to_dict()
        if full_name and data.get('full_name') != full_name:
            await ref.update({'full_name': full_name})
            data['full_name'] = full_name
        set_in_cache(chat_id, user_id, data)
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
        set_in_cache(chat_id, user_id, default_data)
        return default_data

async def update_user_balance(chat_id, user_id, amount):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id) # Запрашиваем через кэш/бд
    new_balance = data.get('balance', 0) + amount
    await ref.update({'balance': new_balance})

    # Обновляем кэш
    data['balance'] = new_balance
    set_in_cache(chat_id, user_id, data)
    return new_balance

async def update_user_field(chat_id, user_id, field, value):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id)
    await ref.update({field: value})

    # Обновляем кэш
    data[field] = value
    set_in_cache(chat_id, user_id, data)

BUSINESSES = {
    "shawarma": 10000,
    "carwash": 60000,
    "restaurant": 300000,
    "dealership": 1500000,
    "casino": 10000000
}

async def check_and_give_bonus(chat_id, user_id, full_name=None):
    import time
    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return False, {}

    last_bonus = data.get('last_bonus_time', 0)
    current_time = time.time()

    if current_time - last_bonus >= 3600: # 1 hour for businesses
        ref = get_user_ref(chat_id, user_id)
        is_vip = data.get('is_vip', False)

        bank_deposit = data.get('bank_deposit', 0)
        bank_income = 0

        # Give base bonus AND bank income only once a day
        base_bonus = 0
        if current_time - data.get('last_daily_time', 0) >= 86400:
            base_bonus = 1000 if is_vip else 450
            if bank_deposit > 0:
                if bank_deposit <= 100000000:
                    bank_income = int(bank_deposit * 0.02)
                elif bank_deposit <= 1000000000:
                    bank_income = int(bank_deposit * 0.01)
                else:
                    bank_income = int(bank_deposit * 0.005)
                await ref.update({'bank_deposit': bank_deposit + bank_income})
            await ref.update({'last_daily_time': current_time})


        from shop import ITEMS
        from economy_utils import get_global_tax


        tax_percent = await get_global_tax()
        negotiation_level = data.get('skills', {}).get('negotiation', 0)
        tax_percent = max(0, tax_percent - negotiation_level)


        business_income = 0
        car_income = 0
        inventory = data.get('inventory', {})

        for item_id, count in inventory.items():
            item_info = ITEMS.get(item_id)
            if not item_info:
                continue
            if item_info.get('action') == 'business':
                level = min(count, 10)
                business_income += item_info.get('income', 0) * level
            elif item_info.get('action') == 'car':
                car_income += item_info.get('income', 0) * count

        gross_income = business_income + car_income
        tax_amount = int(gross_income * (tax_percent / 100.0))
        net_income = gross_income - tax_amount

        total_profit = base_bonus + net_income

        new_balance = data.get('balance', 500) + total_profit
        await ref.update({
            'balance': new_balance,
            'last_bonus_time': current_time
        })

        # Обновляем кэш
        data['balance'] = new_balance
        data['last_bonus_time'] = current_time
        if base_bonus > 0:
            data['last_daily_time'] = current_time
        if bank_deposit > 0 and base_bonus > 0:
            data['bank_deposit'] = bank_deposit + bank_income
        set_in_cache(chat_id, user_id, data)

        receipt = {
            'base': base_bonus,
            'business': business_income,
            'car': car_income,
            'gross': gross_income,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'net': net_income,
            'total': total_profit
        }

        return True, receipt
    return False, {}


async def add_item_to_inventory(chat_id, user_id, item_name):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    inv[item_name] = inv.get(item_name, 0) + 1
    await ref.update({'inventory': inv})

    # Обновляем кэш
    data['inventory'] = inv
    set_in_cache(chat_id, user_id, data)

async def remove_item_from_inventory(chat_id, user_id, item_name):
    ref = get_user_ref(chat_id, user_id)
    data = await get_user_data(chat_id, user_id)
    inv = data.get('inventory', {})
    if inv.get(item_name, 0) > 0:
        inv[item_name] -= 1
        if inv[item_name] == 0:
            del inv[item_name]
        await ref.update({'inventory': inv})

        # Обновляем кэш
        data['inventory'] = inv
        set_in_cache(chat_id, user_id, data)
        return True
    return False

async def get_top_users(chat_id, limit=10):
    db = get_db()
    users_ref = db.collection('chats').document(str(chat_id)).collection('users')
    # Fetch more than the limit to account for users that might be filtered out locally
    docs = await users_ref.order_by('balance', direction='DESCENDING').limit(limit + 20).get()

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
            if len(users) >= limit:
                break

    return users
