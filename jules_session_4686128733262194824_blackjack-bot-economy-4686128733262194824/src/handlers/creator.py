from aiogram import Router, types
from aiogram.filters import Command

from database.db import get_db
from database.user_manager import get_user_data, update_user_balance, get_user_ref
from bot.config import CREATOR_USERNAME
from utils.escape import escape_html

router = Router()

def is_creator(message: types.Message):
    return message.from_user.username == CREATOR_USERNAME

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    chat_id = message.chat.id
    db = get_db()

    users_ref = db.collection('chats').document(str(chat_id)).collection('users')

    try:
        docs = users_ref.stream()

        users_list = []
        async for doc in docs:
            data = doc.to_dict()
            if not data.get('hide_in_top', False):
                users_list.append({
                    'name': data.get('full_name', 'Unknown'),
                    'balance': data.get('balance', 0)
                })

        users_list.sort(key=lambda x: x['balance'], reverse=True)
        top_10 = users_list[:10]

        if not top_10:
            await message.answer("Топ пуст.")
            return

        text = "🏆 ТОП-10 ИГРОКОВ ЧАТА 🏆\n\n"
        for i, u in enumerate(top_10, 1):
            text += f"{i}. {u['name']} — {u['balance']} сыроежек\n"

        await message.answer(text)
    except Exception as e:
        print(f"Ошибка при получении топа: {e}")
        await message.answer("Топ временно недоступен.")

@router.message(Command("give"))
async def cmd_give(message: types.Message):
    if not is_creator(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите сумму.")
        return

    try:
        amount = int(args[1])
        chat_id = message.chat.id
        target_id = message.reply_to_message.from_user.id
        target_name = escape_html(message.reply_to_message.from_user.full_name)

        await get_user_data(chat_id, target_id, target_name)
        await update_user_balance(chat_id, target_id, amount)
        await message.answer(f"Выдано {amount} сыроежек пользователю {target_name}.")
    except ValueError:
        pass

@router.message(Command("take"))
async def cmd_take(message: types.Message):
    if not is_creator(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите сумму.")
        return

    try:
        amount = int(args[1])
        chat_id = message.chat.id
        target_id = message.reply_to_message.from_user.id
        target_name = escape_html(message.reply_to_message.from_user.full_name)

        await get_user_data(chat_id, target_id, target_name)
        await update_user_balance(chat_id, target_id, -amount)
        await message.answer(f"Забрано {amount} сыроежек у пользователя {target_name}.")
    except ValueError:
        pass

@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not is_creator(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя.")
        return

    chat_id = message.chat.id
    target_id = message.reply_to_message.from_user.id
    target_name = escape_html(message.reply_to_message.from_user.full_name)
    await get_user_data(chat_id, target_id, target_name)
    ref = get_user_ref(chat_id, target_id)
    await ref.update({'is_banned': True})
    await message.answer(f"Пользователь забанен в боте.")

@router.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not is_creator(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя.")
        return

    chat_id = message.chat.id
    target_id = message.reply_to_message.from_user.id
    target_name = escape_html(message.reply_to_message.from_user.full_name)
    await get_user_data(chat_id, target_id, target_name)
    ref = get_user_ref(chat_id, target_id)
    await ref.update({'is_banned': False})
    await message.answer(f"Пользователь разбанен в боте.")

@router.message(Command("hide"))
async def cmd_hide(message: types.Message):
    if not is_creator(message):
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = escape_html(message.from_user.full_name)
    await get_user_data(chat_id, user_id, user_name)
    ref = get_user_ref(chat_id, user_id)
    await ref.update({'hide_in_top': True})
    await message.answer("Вы скрыты из топа.")

@router.message(Command("show"))
async def cmd_show(message: types.Message):
    if not is_creator(message):
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = escape_html(message.from_user.full_name)
    await get_user_data(chat_id, user_id, user_name)
    ref = get_user_ref(chat_id, user_id)
    await ref.update({'hide_in_top': False})
    await message.answer("Вы теперь отображаетесь в топе.")
