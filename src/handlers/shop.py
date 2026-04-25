from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.user_manager import get_user_data, update_user_balance, add_item_to_inventory, remove_item_from_inventory
from utils.escape import escape_html

router = Router()

ITEMS = {
    "unwarn": {"name": "Снять варн", "price": 2500, "action": "-варн"},
    "mute": {"name": "Мут 5 минут", "price": 10000, "action": "Мут 5 минут"}
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

    if balance < item['price']:
        await callback.answer(f"Недостаточно сыроежек! Нужно {item['price']}.", show_alert=True)
        return

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
async def cmd_unwarn(message: types.Message):
    await use_item(message, "unwarn")

@router.message(Command("mute"))
async def cmd_mute(message: types.Message):
    await use_item(message, "mute")

async def use_item(message: types.Message, item_id: str):
    if not message.reply_to_message:
        await message.answer(f"Ответьте на сообщение человека, чтобы применить {ITEMS[item_id]['name']}.")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if await remove_item_from_inventory(chat_id, user_id, item_id):
        action_text = ITEMS[item_id]['action']
        await message.bot.send_message(
            chat_id=chat_id,
            text=action_text,
            reply_to_message_id=message.reply_to_message.message_id
        )
    else:
        await message.answer(f"У вас нет предмета '{ITEMS[item_id]['name']}'. Купите его в /shop")
