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
                    'balance': data.get('balance', 0),
                    'is_vip': data.get('is_vip', False)
                })

        users_list.sort(key=lambda x: x['balance'], reverse=True)
        top_10 = users_list[:10]

        if not top_10:
            await message.answer("Топ пуст.")
            return

        text = "🏆 ТОП-10 ИГРОКОВ ЧАТА 🏆\n\n"
        for i, u in enumerate(top_10, 1):
            vip_icon = " 👑" if u['is_vip'] else ""
            text += f"{i}. {u['name']}{vip_icon} — {u['balance']} сыроежек\n"

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

@router.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
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
    await ref.update({'is_vip': True})
    await message.answer(f"Пользователь {target_name} получил статус 👑 VIP!")

@router.message(Command("delvip"))
async def cmd_delvip(message: types.Message):
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
    await ref.update({'is_vip': False})
    await message.answer(f"Пользователь {target_name} лишен статуса VIP.")

from database.whitelist import add_to_whitelist, remove_from_whitelist, get_whitelist

@router.message(Command("allow"))
async def cmd_allow(message: types.Message):
    if not is_creator(message):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ID группы. Пример: <code>/allow -100123456789</code>")
        return

    try:
        chat_id = int(args[1])
        success = await add_to_whitelist(chat_id)
        if success:
            await message.answer(f"✅ Группа <code>{chat_id}</code> добавлена в белый список.")
        else:
            await message.answer(f"Группа <code>{chat_id}</code> уже в белом списке.")
    except ValueError:
        await message.answer("ID группы должен быть числом.")

@router.message(Command("disallow"))
async def cmd_disallow(message: types.Message):
    if not is_creator(message):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ID группы. Пример: <code>/disallow -100123456789</code>")
        return

    try:
        chat_id = int(args[1])
        success = await remove_from_whitelist(chat_id)
        if success:
            await message.answer(f"❌ Группа <code>{chat_id}</code> удалена из белого списка.")
        else:
            await message.answer(f"Группы <code>{chat_id}</code> нет в белом списке.")
    except ValueError:
        await message.answer("ID группы должен быть числом.")

@router.message(Command("whitelist"))
async def cmd_whitelist(message: types.Message):
    if not is_creator(message):
        return

    whitelist = await get_whitelist()
    if not whitelist:
        await message.answer("Белый список пуст.")
        return

    text = "📝 <b>Разрешенные группы:</b>\n\n"
    for chat_id in whitelist:
        text += f"<code>{chat_id}</code>\n"

    await message.answer(text)

from database.chances import set_game_chance, get_game_chance

@router.message(Command("setchance"))
async def cmd_setchance(message: types.Message):
    if not is_creator(message):
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Использование: <code>/setchance <игра> <процент></code>\n"
            "Доступные игры: <code>slots</code>, <code>cups</code>, <code>roulette</code>\n"
            "Процент: 0-100 (установите -1 для честного рандома).\n"
            "Пример: <code>/setchance slots 50</code>"
        )
        return

    game_name = args[1].lower()
    valid_games = ['slots', 'cups', 'roulette']

    if game_name not in valid_games:
        await message.answer(f"Неизвестная игра. Доступные: {', '.join(valid_games)}")
        return

    try:
        percentage = int(args[2])
        if percentage < -1 or percentage > 100:
            await message.answer("Процент должен быть от -1 до 100.")
            return

        await set_game_chance(game_name, percentage)
        if percentage == -1:
            await message.answer(f"Для игры <b>{game_name}</b> установлен честный рандом.")
        else:
            await message.answer(f"Для игры <b>{game_name}</b> установлен принудительный шанс победы: <b>{percentage}%</b>")
    except ValueError:
        await message.answer("Процент должен быть числом.")

@router.message(Command("info"))
async def cmd_info(message: types.Message):
    if not is_creator(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя.")
        return

    chat_id = message.chat.id
    target_id = message.reply_to_message.from_user.id
    target_name = escape_html(message.reply_to_message.from_user.full_name)

    data = await get_user_data(chat_id, target_id, target_name)

    balance = data.get('balance', 0)
    is_vip = data.get('is_vip', False)
    is_banned = data.get('is_banned', False)
    inventory = data.get('inventory', {})

    inv_text = ", ".join([f"{k}: {v}" for k, v in inventory.items()]) if inventory else "Пусто"
    vip_text = "Да 👑" if is_vip else "Нет"
    ban_text = "Да 🚫" if is_banned else "Нет"

    text = (
        f"📊 <b>Информация о пользователе {target_name}</b>\n\n"
        f"ID: <code>{target_id}</code>\n"
        f"Баланс: {balance} сыроежек\n"
        f"VIP статус: {vip_text}\n"
        f"Бан: {ban_text}\n"
        f"Инвентарь: {inv_text}"
    )

    await message.answer(text)
