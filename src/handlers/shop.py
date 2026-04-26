from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.user_manager import get_user_data, update_user_balance, add_item_to_inventory, remove_item_from_inventory, get_user_ref
from utils.escape import escape_html

router = Router()

ITEMS = {
    "lada": {"name": "🚗 Lada Priora", "price": 250000, "action": "none"},
    "bmw": {"name": "🚕 BMW M5", "price": 1500000, "action": "none"},
    "bugatti": {"name": "🏎 Bugatti Chiron", "price": 10000000, "action": "none"},
    "vip": {"name": "💎 Статус VIP", "price": 5000000, "action": "vip"},
    "shawarma": {"name": "🏪 Ларёк с шаурмой", "price": 100000, "action": "business", "income": 10000},
    "carwash": {"name": "🚿 Автомойка", "price": 500000, "action": "business", "income": 60000},
    "restaurant": {"name": "🍽 Ресторан", "price": 2000000, "action": "business", "income": 300000},
    "dealership": {"name": "🚙 Автосалон", "price": 10000000, "action": "business", "income": 1500000},
    "casino": {"name": "🎰 Казино", "price": 50000000, "action": "business", "income": 10000000},
    "mute": {"name": "Мут 5 минут", "price": 15000, "action": "мут 5 минут"},
    "unwarn": {"name": "Снять варн", "price": 10000, "action": "снять варн"}
}

def get_shop_keyboard():
    builder = InlineKeyboardBuilder()
    for item_id, item_info in ITEMS.items():
        builder.button(text=f"{item_info['name']} - {item_info['price']} сыр.", callback_data=f"buy_{item_id}")
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    data = await get_user_data(chat_id, user_id, escape_html(message.from_user.full_name))
    if data.get('is_banned', False):
        await message.answer("Вы забанены и не можете пользоваться магазином.")
        return

    balance = data.get('balance', 0)
    inventory = data.get('inventory', {})

    inv_text = "\n".join([f"- {ITEMS.get(k, {}).get('name', k)}: {v} шт." for k, v in inventory.items() if v > 0])
    if not inv_text:
        inv_text = "Пусто"

    text = (
        f"🛒 <b>МАГАЗИН</b>\n"
        f"Ваш баланс: {balance} сыроежек\n\n"
        f"<b>Ваш инвентарь:</b>\n{inv_text}\n\n"
        f"Выберите товар для покупки:"
    )

    await message.answer(text, reply_markup=get_shop_keyboard())

@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    item_id = callback.data.replace("buy_", "")
    if item_id not in ITEMS:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    item = ITEMS[item_id]
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    data = await get_user_data(chat_id, user_id)
    balance = data.get('balance', 0)


    if item.get('action') == "business" or item.get('action') == "none":
        inventory = data.get('inventory', {})
        if inventory.get(item_id, 0) >= 2:
            await callback.answer(f"У вас уже есть максимальное количество (2 шт.) этого предмета!", show_alert=True)
            return

    if balance < item['price']:

        await callback.answer(f"Недостаточно сыроежек! Нужно {item['price']}.", show_alert=True)
        return

    if item_id == "vip":
        if data.get('is_vip', False):
            await callback.answer("У вас уже есть VIP статус!", show_alert=True)
            return

        await update_user_balance(chat_id, user_id, -item['price'])
        ref = get_user_ref(chat_id, user_id)
        await ref.update({'is_vip': True})
        await callback.answer("Вы успешно купили 👑 VIP Статус!", show_alert=True)
    else:
        await update_user_balance(chat_id, user_id, -item['price'])
        await add_item_to_inventory(chat_id, user_id, item_id)
        await callback.answer(f"Вы успешно купили: {item['name']}!", show_alert=True)

    data = await get_user_data(chat_id, user_id)
    new_balance = data.get('balance', 0)
    inventory = data.get('inventory', {})

    inv_text = "\n".join([f"- {ITEMS.get(k, {}).get('name', k)}: {v} шт." for k, v in inventory.items() if v > 0])
    if not inv_text:
        inv_text = "Пусто"

    text = (
        f"🛒 <b>МАГАЗИН</b>\n"
        f"Ваш баланс: {new_balance} сыроежек\n\n"
        f"<b>Ваш инвентарь:</b>\n{inv_text}\n\n"
        f"Выберите товар для покупки:"
    )

    await callback.message.edit_text(text, reply_markup=get_shop_keyboard())

@router.message(Command("unwarn"))
async def cmd_unwarn(message: types.Message, bot: Bot):
    await use_item(message, "unwarn", bot)

@router.message(Command("mute"))
async def cmd_mute(message: types.Message, bot: Bot):
    await use_item(message, "mute", bot)

async def use_item(message: types.Message, item_id: str, bot: Bot = None):
    if not message.reply_to_message:
        await message.answer(f"Ответьте на сообщение человека, чтобы применить {ITEMS[item_id]['name']}.")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if await remove_item_from_inventory(chat_id, user_id, item_id):
        from bot.config import CREATOR_ID

        target_name = escape_html(message.reply_to_message.from_user.full_name)
        target_id = message.reply_to_message.from_user.id
        sender_name = escape_html(message.from_user.full_name)
        action_name = ITEMS[item_id]['action']

        if CREATOR_ID and CREATOR_ID != 0 and bot:
            try:
                await bot.send_message(
                    chat_id=CREATOR_ID,
                    text=(
                        f"🚨 <b>Использование предмета из магазина!</b>\n\n"
                        f"Игрок: <b>{sender_name}</b> (<code>{user_id}</code>)\n"
                        f"Применил: <b>{action_name}</b>\n"
                        f"На игрока: <b>{target_name}</b> (<code>{target_id}</code>)\n"
                        f"Чат ID: <code>{chat_id}</code>\n"
                        f"Ссылка на сообщение: {message.reply_to_message.get_url() if message.reply_to_message.get_url() else 'Нет'}"
                    )
                )
            except Exception as e:
                print(f"Не удалось отправить лог создателю: {e}")

        await message.answer("✅ Запрос на применение предмета отправлен администратору бота.")
    else:
        await message.answer(f"У вас нет предмета '{ITEMS[item_id]['name']}'. Купите его в /shop")
