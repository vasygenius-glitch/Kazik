from aiogram import Router, F, types
from aiogram.filters import Command
from database.user_manager import get_user_data, update_user_balance
from utils.escape import escape_html

router = Router()

@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    balance = data.get('balance', 0)
    is_vip = data.get('is_vip', False)

    vip_icon = " 👑 VIP" if is_vip else ""
    await message.answer(f"💰 Ваш баланс: <b>{balance}</b> сыроежек.{vip_icon}")

@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    chat_id = message.chat.id
    sender_id = message.from_user.id
    sender_name = escape_html(message.from_user.full_name)

    sender_data = await get_user_data(chat_id, sender_id, sender_name)
    if sender_data.get('is_banned', False):
        await message.answer("Вы забанены и не можете переводить деньги.")
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение человека, которому хотите перевести сыроежки.")
        return

    target_user = message.reply_to_message.from_user
    target_name = escape_html(target_user.full_name)
    if target_user.is_bot:
        await message.answer("Нельзя переводить деньги ботам.")
        return

    if target_user.id == message.from_user.id:
        await message.answer("Нельзя перевести деньги самому себе.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите сумму: <code>/pay 100</code>")
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            await message.answer("Сумма должна быть положительной.")
            return
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Сумма должна быть положительным числом.")
        return

    total_cost = int(amount * 1.1)
    commission = total_cost - amount

    if sender_data.get('balance', 0) < total_cost:
        await message.answer(f"Недостаточно средств. Для перевода {amount} нужно {total_cost} сыроежек (комиссия 10%).")
        return

    try:
        admins = await message.chat.get_administrators()
        human_admins = [admin.user.id for admin in admins if not admin.user.is_bot]
    except Exception as e:
        human_admins = []

    if not human_admins:
        human_admins = [sender_id]

    commission_per_admin = commission // len(human_admins)

    await update_user_balance(chat_id, sender_id, -total_cost)

    await get_user_data(chat_id, target_user.id, target_name)
    await update_user_balance(chat_id, target_user.id, amount)

    for admin_id in human_admins:
        await get_user_data(chat_id, admin_id)
        await update_user_balance(chat_id, admin_id, commission_per_admin)

    await message.answer(
        f"💸 Успешный перевод!\n"
        f"Отправлено: {amount} сыроежек пользователю {target_name}.\n"
        f"Комиссия: {commission} сыроежек (распределена между {len(human_admins)} администраторами)."
    )
