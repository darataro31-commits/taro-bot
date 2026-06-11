import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "6303692408:AAHrB3RJbb2Anh6N9nXFCKbiD00MFAi8BKM"

CHANNELS = [
    "@darinsight_psy",
    "@darinsight",
]

# ================= ПОЛНАЯ КОЛОДА ТАРО =================
tarot_deck = [
    "🃏 **0 - Дурак** — Новый путь, спонтанность, вера, риск",
    "🔮 **I - Маг** — Мастерство, сила воли, концентрация",
    "🌙 **II - Верховная Жрица** — Интуиция, тайна, внутренний голос",
    "👑 **III - Императрица** — Изобилие, творчество, женственность",
    "⚔️ **IV - Император** — Структура, власть, стабильность",
    "🙏 **V - Иерофант** — Традиции, обучение, духовность",
    "❤️ **VI - Влюблённые** — Выбор, любовь, отношения",
    "🦁 **VII - Колесница** — Победа, движение вперёд",
    "⚖️ **VIII - Сила** — Внутренняя сила, терпение",
    "🌟 **IX - Отшельник** — Поиск истины, мудрость",
    "🎡 **X - Колесо Фортуны** — Судьба, циклы, перемены",
    "⚖️ **XI - Справедливость** — Правда, карма, баланс",
    "🧘 **XII - Повешенный** — Новый взгляд, жертва",
    "☠️ **XIII - Смерть** — Трансформация, новое начало",
    "🌊 **XIV - Умеренность** — Баланс, гармония",
    "😈 **XV - Дьявол** — Зависимость, тень",
    "🏰 **XVI - Башня** — Внезапные перемены",
    "⭐ **XVII - Звезда** — Надежда, вдохновение",
    "🌕 **XVIII - Луна** — Иллюзии, подсознание",
    "☀️ **XIX - Солнце** — Радость, успех",
    "🎺 **XX - Суд** — Пробуждение, возрождение",
    "🌍 **XXI - Мир** — Завершение, гармония",

    "🔥 **Туз Жезлов** — Новое начало, вдохновение",
    "🔥 **Двойка Жезлов** — Планирование, выбор пути",
    "🔥 **Тройка Жезлов** — Расширение, ожидание",
    "🔥 **Четвёрка Жезлов** — Праздник, стабильность дома",
    "🔥 **Пятёрка Жезлов** — Конкуренция, борьба",
    "🔥 **Шестёрка Жезлов** — Победа, признание",
    "🔥 **Семёрка Жезлов** — Защита своей позиции",
    "🔥 **Восьмёрка Жезлов** — Быстрые новости, прогресс",
    "🔥 **Девятка Жезлов** — Усталость, но стойкость",
    "🔥 **Десятка Жезлов** — Перегрузка, тяжёлая ноша",
    "🔥 **Паж Жезлов** — Энтузиазм, новые идеи",
    "🔥 **Рыцарь Жезлов** — Страсть, приключения",
    "🔥 **Королева Жезлов** — Харизма, уверенность",
    "🔥 **Король Жезлов** — Лидерство, видение",

    "💖 **Туз Кубков** — Новые эмоции, любовь",
    "💖 **Двойка Кубков** — Партнёрство, взаимная любовь",
    "💖 **Тройка Кубков** — Дружба, праздник",
    "💖 **Четвёрка Кубков** — Апатия, размышления",
    "💖 **Пятёрка Кубков** — Разочарование, грусть",
    "💖 **Шестёрка Кубков** — Ностальгия, добрые воспоминания",
    "💖 **Семёрка Кубков** — Иллюзии, выбор",
    "💖 **Восьмёрка Кубков** — Поиск смысла, уход",
    "💖 **Девятка Кубков** — Исполнение желаний",
    "💖 **Десятка Кубков** — Семейное счастье",
    "💖 **Паж Кубков** — Романтика, чувствительность",
    "💖 **Рыцарь Кубков** — Романтик, предложение",
    "💖 **Королева Кубков** — Эмпатия, интуиция",
    "💖 **Король Кубков** — Эмоциональная зрелость",

    "⚔️ **Туз Мечей** — Ясность, правда",
    "⚔️ **Двойка Мечей** — Трудный выбор",
    "⚔️ **Тройка Мечей** — Боль, предательство",
    "⚔️ **Четвёрка Мечей** — Отдых, восстановление",
    "⚔️ **Пятёрка Мечей** — Конфликт",
    "⚔️ **Шестёрка Мечей** — Переход, уход от проблем",
    "⚔️ **Семёрка Мечей** — Хитрость, стратегия",
    "⚔️ **Восьмёрка Мечей** — Чувство ловушки",
    "⚔️ **Девятка Мечей** — Страхи, тревога",
    "⚔️ **Десятка Мечей** — Дно, конец страданий",
    "⚔️ **Паж Мечей** — Любопытство, новые идеи",
    "⚔️ **Рыцарь Мечей** — Решительность, скорость",
    "⚔️ **Королева Мечей** — Честность, ясность ума",
    "⚔️ **Король Мечей** — Интеллект, авторитет",

    "💰 **Туз Пентаклей** — Новые финансовые возможности",
    "💰 **Двойка Пентаклей** — Баланс дел",
    "💰 **Тройка Пентаклей** — Мастерство, работа",
    "💰 **Четвёрка Пентаклей** — Жадность, контроль",
    "💰 **Пятёрка Пентаклей** — Финансовые трудности",
    "💰 **Шестёрка Пентаклей** — Щедрость, помощь",
    "💰 **Семёрка Пентаклей** — Ожидание результатов",
    "💰 **Восьмёрка Пентаклей** — Усердная работа",
    "💰 **Девятка Пентаклей** — Самодостаточность, успех",
    "💰 **Десятка Пентаклей** — Семейное благополучие",
    "💰 **Паж Пентаклей** — Учёба, практичность",
    "💰 **Рыцарь Пентаклей** — Надёжность, трудолюбие",
    "💰 **Королева Пентаклей** — Забота, изобилие",
    "💰 **Король Пентаклей** — Финансовый успех"
]

def get_random_cards(n: int = 3):
    return random.sample(tarot_deck, n)

# ============================================

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def check_subscriptions(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def get_subscribe_keyboard():
    kb = [
        [InlineKeyboardButton(text="📢 Подписаться на darinsight_psy", url="https://t.me/darinsight_psy")],
        [InlineKeyboardButton(text="📢 Подписаться на darinsight", url="https://t.me/darinsight")],
        [InlineKeyboardButton(text="✅ Я подписалась", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================= ГЛАВНОЕ МЕНЮ =================
async def main_menu(message: Message):
    kb = [
        [InlineKeyboardButton(text="🔮 Расклады Таро", callback_data="tarot_menu")],
        [InlineKeyboardButton(text="🧠 Психология", callback_data="psychology_menu")],
        [InlineKeyboardButton(text="ℹ️ Обо мне / Помощь", callback_data="about")]
    ]
    await message.answer(
        "🎴 <b>Таро и Психология с Дарьей</b>\n\n"
        "Выбери раздел 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# ================= МЕНЮ РАСКЛАДОВ =================
@dp.callback_query(F.data == "tarot_menu")
async def tarot_menu(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🃏 Карта дня", callback_data="spread_1")],
        [InlineKeyboardButton(text="💎 Заказать личный расклад", callback_data="paid_consult")],
        [InlineKeyboardButton(text="🌟 Таро-профиль по дате рождения", callback_data="paid_profile")],
        [InlineKeyboardButton(text="🔥 Аркан месяца по дате рождения", callback_data="paid_month")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🔮 <b>Расклады Таро</b>\n\nВыбери нужное:", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "spread_1")
async def card_of_day(call: CallbackQuery):
    card = random.choice(tarot_deck)
    kb = [[InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_menu")]]
    await call.message.edit_text(f"🃏 <b>Твоя Карта Дня</b>\n\n{card}", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ПСИХОЛОГИЯ =================
@dp.callback_query(F.data == "psychology_menu")
async def psychology_menu(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📝 Получить чек-лист", callback_data="checklist")],
        [InlineKeyboardButton(text="💎 Заказать консультацию", callback_data="paid_consult")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ]
    await call.message.edit_text(
        "🧠 <b>Психология</b>\n\n"
        "Я работаю с глубинной психологией, самооценкой, внутренним ребёнком и тревожностью.\n\n"
        "Ты уже подписана на мой канал с полезным контентом.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ПЛАТНЫЕ УСЛУГИ =================
@dp.callback_query(F.data == "paid_consult")
async def paid_consult(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💬 Записаться ко мне", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_menu")]
    ]
    await call.message.edit_text(
        "💎 <b>Личная консультация</b>\n\n"
        "• Таро + Психология (1 час)\n"
        "• Глубокий разбор ситуации\n\n"
        "💰 Цена: от 1500 ₽\n\n"
        "Нажми кнопку ниже, чтобы записаться:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data == "paid_profile")
async def paid_profile(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💬 Записаться ко мне", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_menu")]
    ]
    await call.message.edit_text(
        "🌟 <b>Таро-профиль по дате рождения</b>\n\n"
        "Подробный разбор вашей энергетики (10-15 страниц)\n\n"
        "💰 Стоимость: 999 – 1500 ₽\n\n"
        "Нажми кнопку ниже для заказа:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data == "paid_month")
async def paid_month(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="💬 Записаться ко мне", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_menu")]
    ]
    await call.message.edit_text(
        "🔥 <b>Аркан месяца по дате рождения</b>\n\n"
        "Личный Аркан + подробная расшифровка на месяц\n\n"
        "💰 Стоимость: 349 ₽\n\n"
        "Нажми кнопку ниже для заказа:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data == "checklist")
async def checklist(call: CallbackQuery):
    kb = [[InlineKeyboardButton(text="↩️ Назад", callback_data="psychology_menu")]]
    await call.message.edit_text(
        "📝 <b>Чек-лист по психологии</b>\n\n"
        "Ссылка: [ВСТАВЬ ССЫЛКУ НА ЧЕК-ЛИСТ ЗДЕСЬ]",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    kb = [[InlineKeyboardButton(text="↩️ Назад в главное меню", callback_data="back_to_main")]]
    await call.message.edit_text(
        "ℹ️ <b>Обо мне / Помощь</b>\n\n"
        "Здесь будет информация обо мне и ответы на частые вопросы.\n\n"
        "Для записи на консультацию пишите @taro_darinsight",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await call.answer()
    await main_menu(call.message)

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    await call.answer()
    if await check_subscriptions(call.from_user.id):
        await call.message.edit_text("✅ <b>Подписка подтверждена!</b>\nДобро пожаловать ❤️")
        await main_menu(call.message)
    else:
        await call.answer("❌ Вы ещё не подписаны на все каналы!", show_alert=True)

# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    if await check_subscriptions(message.from_user.id):
        await main_menu(message)
    else:
        await message.answer(
            "👋 <b>Добро пожаловать в бот Таро и Психологии!</b>\n\n"
            "Для доступа к раскладам и материалам подпишись на два канала:",
            reply_markup=get_subscribe_keyboard()
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
