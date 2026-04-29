import time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from db import get_db
from escape import escape_html
from user_manager import get_user_data, update_user_balance, update_user_field
from shop import ITEMS

router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    chat_id = message.chat.id
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = escape_html(message.reply_to_message.from_user.full_name)
    else:
        target_id = message.from_user.id
        target_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, target_id, target_name)

    vip_status = "💎 VIP" if data.get('is_vip') else "Обычный"
    balance = data.get('balance', 0)
    rep = data.get('reputation', 0)
    clan = escape_html(data.get('clan', 'Нет'))
    warns = len(data.get('warns', []))

    partner_id = data.get('partner')
    partner_text = "Нет"
    if partner_id:
        p_data = await get_user_data(chat_id, partner_id)
        partner_text = escape_html(p_data.get('full_name', f"ID: {partner_id}"))

    inventory = data.get('inventory', {})
    cars = sum(v for k, v in inventory.items() if ITEMS.get(k, {}).get('action') == 'car')
    biz = sum(v for k, v in inventory.items() if ITEMS.get(k, {}).get('action') == 'business')

    # Банковский счет
    bank_deposit = data.get('bank_deposit', 0)

    # Статистика сообщений
    db = get_db()
    stats_doc = await db.collection('chats').document(str(chat_id)).collection('stats').document(str(target_id)).get()
    msg_count = stats_doc.to_dict().get('all_time', 0) if stats_doc.exists else 0

    text = (
        f"👤 <b>Профиль: {target_name}</b>\n"
        f"Статус: {vip_status}\n"
        f"Репутация: {rep} 📈\n"
        f"Предупреждения: {warns}/3 ⚠️\n\n"

        f"💰 Баланс: {balance} сыр.\n"
        f"🏦 В банке: {bank_deposit} сыр.\n\n"

        f"🛡 Клан: {clan}\n"
        f"💍 Брак: {partner_text}\n\n"

        f"🚗 Машин: {cars}\n"
        f"🏢 Бизнесов: {biz}\n\n"

        f"💬 Сообщений в чате: {msg_count}"
    )

    await message.answer(text)

@router.message(Command("bank"))
async def cmd_bank(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    args = message.text.split()
    if len(args) < 2:
        return await message.answer(
            "🏦 <b>Банк Сыроежек</b>\n\n"
            "Вы можете положить деньги под плавающий процент. Минимальный вклад: 10.000.000\n"
            "Процент начисляется при ежедневном бонусе (/bonus).\n\n"
            "Команды:\n"
            "<code>/bank deposit [сумма]</code>\n"
            "<code>/bank withdraw [сумма]</code>"
        )

    action = args[1].lower()
    if len(args) < 3:
        return await message.answer("Укажите сумму.")

    try:
        amount = int(args[2])
        if amount <= 0: return
    except:
        return

    data = await get_user_data(chat_id, user_id)
    current_deposit = data.get('bank_deposit', 0)

    if action == "deposit":
        if amount < 10000000 and current_deposit == 0:
            return await message.answer("Минимальный первоначальный вклад: 10.000.000 сыроежек.")
        if data.get('balance', 0) < amount:
            return await message.answer("Недостаточно средств на балансе.")

        await update_user_balance(chat_id, user_id, -amount)
        await update_user_field(chat_id, user_id, 'bank_deposit', current_deposit + amount)
        await message.answer(f"✅ Вы успешно положили {amount} сыроежек в банк. Всего вкладов: {current_deposit + amount}.")

    elif action == "withdraw":
        if current_deposit < amount:
            return await message.answer(f"У вас в банке только {current_deposit} сыроежек.")

        await update_user_field(chat_id, user_id, 'bank_deposit', current_deposit - amount)
        await update_user_balance(chat_id, user_id, amount)
        await message.answer(f"💸 Вы успешно сняли {amount} сыроежек со счета.")
