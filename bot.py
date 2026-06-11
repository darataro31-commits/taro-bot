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
    "@darinsight_psy",   # ← Замени
    "@darinsight",   # ← Замени
]

# ================= ПОЛНАЯ КОЛОДА ТАРО (78 карт) =================
tarot_deck = [
    # Старшие Арканы
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

    # Младшие Арканы - Жезлы
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

    # Кубки
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

    # Мечи
    "⚔️ **Туз Мечей** — Ясность, правда",
    "⚔️ **Двойка Мечей** — Трудный выбор",
    "⚔️ **Тройка Мечей** — Боль, предательство",
    "⚔️ **Четвёрка Мечей** — Отдых, восстановление",
    "⚔️ **Пятёрка Мечей** — Конфликт, победа любой ценой",
    "⚔️ **Шестёрка Мечей** — Переход, уход от проблем",
    "⚔️ **Семёрка Мечей** — Хитрость, стратегия",
    "⚔️ **Восьмёрка Мечей** — Чувство ловушки",
    "⚔️ **Девятка Мечей** — Страхи, тревога",
    "⚔️ **Десятка Мечей** — Дно, конец страданий",
    "⚔️ **Паж Мечей** — Любопытство, новые идеи",
    "⚔️ **Рыцарь Мечей** — Решительность, скорость",
    "⚔️ **Королева Мечей** — Честность, ясность ума",
    "⚔️ **Король Мечей** — Интеллект, авторитет",

    # Пентакли
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

# Проверка подписки (оставляем как было)
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
        [InlineKeyboardButton(text="📢 Подписаться на канал 1", url="https://t.me/darinsight_psy")],
        [InlineKeyboardButton(text="📢 Подписаться на канал 2", url="https://t.me/darinsight")],
        [InlineKeyboardButton(text="✅ Я подписался(ась)", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Главное меню
async def main_menu(message: Message):
    kb = [
        [InlineKeyboardButton(text="🔮 Расклады Таро", callback_data="tarot_menu")],
        [InlineKeyboardButton(text="🧠 Психология", callback_data="psychology_menu")],
        [InlineKeyboardButton(text="ℹ️ Обо мне / Помощь", callback_data="about")]
    ]
    await message.answer(
        "🎴 <b>Таро и Психология с Дарьей</b>\n\n"
        "Здесь ты можешь получить глубокие ответы через Таро и психологию.\n\n"
        "Что выбираешь сегодня? 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# ================= МЕНЮ РАСКЛАДОВ =================
@dp.callback_query(F.data == "tarot_menu")
async def tarot_menu(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🃏 Карта дня (1 карта)", callback_data="spread_1")],
        [InlineKeyboardButton(text="📅 Расклад на неделю", callback_data="spread_week")],
        [InlineKeyboardButton(text="💎 Заказать личный расклад", callback_data="paid_consult")],
        [InlineKeyboardButton(text="🌟 Таро-профиль по дате рождения", callback_data="paid_birth")],
        [InlineKeyboardButton(text="🔥 Аркан месяца по дате рождения", callback_data="paid_month")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🔮 <b>Расклады Таро</b>\n\nВыбери нужный формат:", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= МЕНЮ ПСИХОЛОГИИ =================
@dp.callback_query(F.data == "psychology_menu")
async def psychology_menu(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📝 Получить чек-лист", callback_data="checklist")],
        [InlineKeyboardButton(text="💎 Заказать консультацию", callback_data="paid_consult")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
    ]
    await call.message.edit_text(
        "🧠 <b>Психология</b>\n\n"
        "Я работаю с глубинной психологией, внутренним ребёнком, тревогой и самооценкой.\n\n"
        "Ты уже подписана на мой канал с полезным контентом по психологии.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# ================= ОБРАБОТЧИКИ =================
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await main_menu(call.message)

@dp.callback_query(F.data == "spread_1")
async def card_of_day(call: CallbackQuery):
    card = random.choice(tarot_deck)
    await call.message.edit_text(f"🃏 <b>Твоя Карта Дня:</b>\n\n{card}")

@dp.callback_query(F.data == "spread_week")
async def spread_week(call: CallbackQuery):
    cards = get_random_cards(3)
    text = "📅 <b>Расклад на неделю</b>\n\n"
    days = ["Понедельник", "Среда", "Пятница"]
    for day, card in zip(days, cards):
        text += f"<b>{day}:</b> {card}\n\n"
    await call.message.edit_text(text)

@dp.callback_query(F.data.startswith("paid_"))
async def paid_services(call: CallbackQuery):
    await call.message.edit_text(
        "💎 <b>Личная консультация</b>\n\n"
        "Для записи на платный расклад, Таро-профиль или консультацию — напишите мне в личку @ваш_ник\n\n"
        "Я отвечу в ближайшее время ❤️",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]])
    )

@dp.callback_query(F.data == "checklist")
async def checklist(call: CallbackQuery):
    await call.message.edit_text("📝 Чек-лист скоро будет доступен (в разработке)")

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await call.message.edit_text("ℹ️ Информация обо мне и помощь скоро будет добавлена.")

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
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
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Для доступа к раскладам и материалам подпишись на два канала:",
            reply_markup=get_subscribe_keyboard()
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот Таро и Психологии успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
