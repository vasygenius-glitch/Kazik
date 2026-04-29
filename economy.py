from aiogram import Router, F, types
from aiogram.filters import Command
import secrets
from economy_utils import get_global_tax
from user_manager import get_user_data, update_user_balance, check_and_give_bonus, update_user_field, get_top_users
from escape import escape_html
import time
import secrets

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    # Инициализируем данные пользователя (при первом запуске выдается стартовый баланс)
    await get_user_data(chat_id, user_id, full_name)

    text = (
        f"👋 <b>Привет, {full_name}!</b>\n\n"
        "Я бот для экономики и мини-игр! Твой стартовый баланс составляет <b>500</b> сыроежек.\n\n"
        "Пиши <code>/help</code> чтобы увидеть список всех команд."
    )
    await message.answer(text)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📜 <b>ПОЛНЫЙ СПИСОК КОМАНД БОТА</b> 📜\n\n"

        "💰 <b>ЭКОНОМИКА И БАНК:</b>\n"
        "<code>/profile</code> — Ваш полный профиль (деньги, клан, брак, варны).\n"
        "<code>/bank deposit [сумма]</code> — Положить деньги в банк.\n"
        "<code>/bank withdraw [сумма]</code> — Снять деньги из банка.\n"
        "<code>/bonus</code> — Собрать прибыль с бизнесов, банка и получить дневной бонус.\n"
        "<code>/work</code> — Работать (легально).\n"
        "<code>/crime</code> — Рискованное ограбление.\n"
        "<code>/pay [сумма] [реплай]</code> — Перевод денег другому игроку (с учетом налога).\n\n"

        "🛒 <b>МАГАЗИН И ПРОКАЧКА:</b>\n"
        "<code>/shop</code> — Магазин бизнесов, машин и VIP-статуса.\n"
        "<code>/upgrade [название]</code> — Улучшить бизнес до 10 уровня.\n"
        "<code>/skills</code> — Меню прокачки RPG навыков (Удача, Скрытность, Бизнесмен).\n\n"

        "🛡 <b>КЛАНЫ И СЕМЬИ:</b>\n"
        "<code>/clan</code> — Меню кланов (создать, пригласить, выгнать).\n"
        "<code>Брак</code> или <code>/marry</code> [реплай] — Сделать предложение.\n"
        "<code>Развод</code> — Расторгнуть брак.\n"
        "<code>Подарок [сумма]</code> [реплай на свадьбу] — Подарить молодоженам деньги.\n\n"

        "🎰 <b>ИГРЫ:</b>\n"
        "<code>/bj [ставка]</code> — Блэкджек.\n"
        "<code>/slots [ставка]</code> — Слоты.\n"
        "<code>/roulette [ставка] [число/цвет]</code> — Рулетка.\n"
        "<code>Дуэль [ставка]</code> [реплай] — Вызвать игрока на кубиках.\n"
        "(Также доступны: /cups, /dice, /craps, /baccarat).\n\n"

        "📊 <b>ТОПЫ (Обновляются каждое воскресенье):</b>\n"
        "<code>/top</code> — Топ богачей.\n"
        "<code>/top week</code> — Топ активности (сообщений) за неделю.\n"
        "<code>/top all</code> — Топ сообщений за всё время.\n\n"

        "👮‍♂️ <b>АДМИНИСТРИРОВАНИЕ:</b>\n"
        "<code>мут [время] [причина]</code> [реплай] — Замутить.\n"
        "<code>бан [причина]</code> [реплай] — Забанить.\n"
        "<code>варн [время] [причина]</code> [реплай] — Выдать предупреждение (3 варна = бан).\n"
        "<code>повысить [1-5]</code> [реплай] — Выдать модератора.\n"
        "<code>кто админ</code> — Список администраторов.\n\n"

        "🎭 <b>РП-КОМАНДЫ (Реплаем):</b>\n"
        "<code>Обнять</code>, <code>Поцеловать</code>, <code>Ударить</code>, <code>Кусь</code>, <code>Погладить</code>.\n"
        "Для повышения репутации (кармы) пишите: <code>+</code>, <code>спасибо</code>, <code>реп</code>."
    )
    await message.answer(text)

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

    tax_percent = await get_global_tax()
    total_cost = int(amount * (1 + tax_percent / 100))
    commission = total_cost - amount

    if sender_data.get('balance', 0) < total_cost:
        await message.answer(f"Недостаточно средств. Для перевода {amount} нужно {total_cost} сыроежек (налог {tax_percent}%).")
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

    phrases = [
        f"Налоговая откусила кусок в {commission} сыроежек.",
        f"Гоблины-сборщики забрали {commission} сыроежек в казну.",
        f"Крыша требует свою долю. Удержано {commission} сыроежек.",
        f"Банкирский дом забирает свои скромные {commission} сыроежек за услуги.",
        f"Местные рэкетиры взыскали налог: {commission} сыроежек.",
        f"Комиссия в {commission} сыроежек ушла на развитие экономики сервера."
    ]
    phrase = secrets.choice(phrases) if commission > 0 else "Налог отменен! Все средства дошли без потерь."

    await message.answer(
        f"💸 <b>Успешный перевод!</b>\n\n"
        f"Отправлено: {amount} сыроежек пользователю {target_name}.\n"
        f"<i>{phrase}</i> (Налог {tax_percent}%, распределен между админами)."
    )

@router.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    success, receipt = await check_and_give_bonus(chat_id, user_id, full_name)
    if success:
        text = f"🧾 <b>Квитанция о доходах</b>\n\n"
        if receipt.get('base', 0) > 0:
            text += f"🎁 Ежедневный бонус: <b>{receipt['base']}</b>\n"
        text += f"🏢 Доход с бизнесов: <b>{receipt['business']}</b>\n"
        text += f"🚗 Доход с машин: <b>{receipt['car']}</b>\n"
        text += f"➖ Налог ({receipt['tax_percent']}%): <b>-{receipt['tax_amount']}</b>\n"
        text += f"-----------------------\n"
        text += f"💰 Итого на руки: <b>{receipt['total']}</b> сыроежек"

        await message.answer(text)
    else:
        await message.answer("❌ Вы уже собирали доход недавно. Попробуйте через час!")

@router.message(Command("work"))
async def cmd_work(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return await message.answer("Вы забанены и не можете работать.")

    last_work = data.get('last_work_time', 0)
    current_time = time.time()

    # 1 hour cooldown for work
    if current_time - last_work < 3600:
        remain = int(3600 - (current_time - last_work))
        mins, secs = divmod(remain, 60)
        return await message.answer(f"⏳ Вы устали. Отдохните еще {mins} минут и {secs} секунд.")

    rand = secrets.SystemRandom()
    earnings = rand.randint(50, 250)

    await update_user_field(chat_id, user_id, 'last_work_time', current_time)

    balance = data.get('balance', 0)
    if balance < 0 and rand.randint(1, 100) <= 30: # 30% chance for collectors if in debt
        penalty = rand.randint(50, 100)
        await update_user_balance(chat_id, user_id, -penalty)
        return await message.answer(
            f"💼 Вы честно трудились и заработали {earnings} сыроежек, но тут появились <b>КОЛЛЕКТОРЫ</b>! 🦹‍♂️\n\n"
            f"Они отобрали всю вашу зарплату и выбили еще {penalty} сыроежек сверху в счет вашего долга."
        )

    await update_user_balance(chat_id, user_id, earnings)

    jobs = [
        "убрали мусор на улице",
        "помогли бабушке перейти дорогу",
        "доставили посылку",
        "поработали на стройке",
        "помыли окна"
    ]
    job = rand.choice(jobs)

    await message.answer(f"💼 Вы <b>{job}</b> и заработали <b>{earnings}</b> сыроежек!")

@router.message(Command("crime"))
async def cmd_crime(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return await message.answer("Вы забанены и не можете совершать преступления.")

    last_crime = data.get('last_crime_time', 0)
    current_time = time.time()

    # 2 hours cooldown for crime
    if current_time - last_crime < 7200:
        remain = int(7200 - (current_time - last_crime))
        mins, secs = divmod(remain, 60)
        hours, mins = divmod(mins, 60)
        return await message.answer(f"⏳ Полиция все еще ищет вас. Залягте на дно еще {hours} ч. {mins} мин.")

    await update_user_field(chat_id, user_id, 'last_crime_time', current_time)

    rand = secrets.SystemRandom()
    stealth_level = data.get('skills', {}).get('stealth', 0)
    if rand.random() < (0.4 + stealth_level * 0.05): # 40% + 5% per level
        earnings = rand.randint(200, 800)

        balance = data.get('balance', 0)
        if balance < 0 and rand.randint(1, 100) <= 40: # 40% chance for collectors on successful crime if in debt
            penalty = rand.randint(100, 200)
            await update_user_balance(chat_id, user_id, -penalty)
            return await message.answer(
                f"🥷 Вы успешно провернули дело и украли {earnings} сыроежек...\n"
                f"Но за углом вас поджидали <b>КОЛЛЕКТОРЫ</b>! 🦹‍♂️\n"
                f"Они забрали всю добычу и выпотрошили карманы еще на {penalty} сыроежек в счет долга."
            )

        await update_user_balance(chat_id, user_id, earnings)
        crimes = ["ограбили магазин", "угнали велосипед", "украли кошелек", "взломали банкомат"]
        crime = rand.choice(crimes)
        await message.answer(f"🥷 Вы успешно <b>{crime}</b> и получили <b>{earnings}</b> сыроежек!")
    else:
        fine = rand.randint(100, 300)
        await update_user_balance(chat_id, user_id, -fine)
        await message.answer(f"🚔 Вас поймала полиция! Вы заплатили штраф в размере <b>{fine}</b> сыроежек.")


