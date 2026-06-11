import asyncio
import logging
import requests
from bs4 import BeautifulSoup
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

# ================= ГОРОСКОП =================
zodiacs = {
    "aries": "♈ Овен", "taurus": "♉ Телец", "gemini": "♊ Близнецы",
    "cancer": "♋ Рак", "leo": "♌ Лев", "virgo": "♍ Дева",
    "libra": "♎ Весы", "scorpio": "♏ Скорпион", "sagittarius": "♐ Стрелец",
    "capricorn": "♑ Козерог", "aquarius": "♒ Водолей", "pisces": "♓ Рыбы"
}

def get_horoscope(sign: str):
    try:
        url = f"https://horoscopes.rambler.ru/{sign}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for selector in ["div.horoscope__text", "div.article__text", "p", "div.text"]:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(strip=True)
                if len(text) > 120:
                    return text[:1800]
    except:
        pass
    return "😔 Не удалось загрузить гороскоп. Попробуйте позже."

# ================= КАРТА ДНЯ =================
def get_card_of_the_day():
    try:
        url = "https://horoscopes.rambler.ru/taro/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        card = soup.find("h2", string=lambda t: t and "Карта Таро сегодня" in t)
        if card:
            desc = card.find_next("p")
            return f"<b>{card.get_text(strip=True)}</b>\n\n{desc.get_text(strip=True) if desc else ''}"
    except:
        pass
    return "🃏 Не удалось загрузить Карту Дня. Попробуйте позже."

# ============================================

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def get_subscribe_keyboard():
    kb = [
        [InlineKeyboardButton(text="📢 Подписаться на @darinsight_psy", url="https://t.me/darinsight_psy")],
        [InlineKeyboardButton(text="📢 Подписаться на @darinsight", url="https://t.me/darinsight")],
        [InlineKeyboardButton(text="✅ Я подписался(ась)", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

async def check_subscriptions(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= ГЛАВНОЕ МЕНЮ =================
async def main_menu(message: Message):
    kb = [
        [InlineKeyboardButton(text="🔮 Расклады Таро", callback_data="tarot_section")],
        [InlineKeyboardButton(text="🧠 Психология", callback_data="psychology_section")],
        [InlineKeyboardButton(text="ℹ️ Обо мне / Помощь", callback_data="about")]
    ]
    await message.answer("🎴 <b>Главное меню Таро и Психологии от Дарьи</b>", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= РАЗДЕЛ ТАРО =================
@dp.callback_query(F.data == "tarot_section")
async def tarot_section(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🃏 Карта Дня", callback_data="card_of_day")],
        [InlineKeyboardButton(text="🌟 Гороскоп на сегодня", callback_data="horoscope")],
        [InlineKeyboardButton(text="💳 Заказать личный расклад", callback_data="order_spread")],
        [InlineKeyboardButton(text="🎂 Таро-профиль по дате рождения", callback_data="birth_profile")],
        [InlineKeyboardButton(text="📅 Аркан месяца по дате рождения", callback_data="month_arcan")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🔮 <b>Расклады Таро</b>", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= РАЗДЕЛ ПСИХОЛОГИЯ =================
@dp.callback_query(F.data == "psychology_section")
async def psychology_section(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📋 Получить чек-лист", callback_data="checklist")],
        [InlineKeyboardButton(text="📅 Записаться на консультацию", callback_data="consultation")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🧠 <b>Психология</b>", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= КАРТА ДНЯ =================
@dp.callback_query(F.data == "card_of_day")
async def send_card_of_day(call: CallbackQuery):
    await call.message.edit_text("🃏 Загружаю Карту Дня...")
    card_text = get_card_of_the_day()
    text = f"🃏 <b>Карта Дня</b>\n\n{card_text}"
    kb = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="card_of_day")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ГОРОСКОП =================
@dp.callback_query(F.data == "horoscope")
async def horoscope_menu(call: CallbackQuery):
    kb = [[InlineKeyboardButton(text=name, callback_data=f"hor_{code}")] for code, name in zodiacs.items()]
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")])
    await call.message.edit_text("🌟 <b>Гороскоп на сегодня</b>\n\nВыберите знак зодиака:", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("hor_"))
async def send_horoscope(call: CallbackQuery):
    sign = call.data[4:]
    name = [n for c, n in zodiacs.items() if c == sign][0]
    await call.message.edit_text(f"🌟 Загружаю гороскоп для <b>{name}</b>...")
    horo = get_horoscope(sign)
    text = f"🌟 <b>Гороскоп на сегодня — {name}</b>\n\n{horo}"
    kb = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"hor_{sign}")],
        [InlineKeyboardButton(text="↩️ Другой знак", callback_data="horoscope")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ЗАКАЗАТЬ ЛИЧНЫЙ РАСКЛАД =================
@dp.callback_query(F.data == "order_spread")
async def order_spread(call: CallbackQuery):
    text = """🃏 <b>Заказать личный расклад</b>

Привет! Я занимаюсь Таро уже 5 лет и смотрю на карты не как на магию, а как на мощный инструмент работы с бессознательным.

Это глубокая психологическая работа: карты помогают вытащить на поверхность то, что ты уже знаешь внутри, но пока не можешь сформулировать сам. 

<b>Что я предлагаю:</b>
• Помогаю правильно подобрать расклад под твой запрос
• Вместе формулируем точные вопросы
• Делаю полноценный личный расклад 60 минут в аудиоформате
• Аудио остаётся у тебя навсегда

<b>Важные ограничения:</b>
❌ Не работаю с темами смерти, здоровья и беременности

Готов погрузиться в настоящий психологический разбор?"""
    kb = [
        [InlineKeyboardButton(text="Записаться", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ТАРО-ПРОФИЛЬ =================
@dp.callback_query(F.data == "birth_profile")
async def birth_profile(call: CallbackQuery):
    text = """🃏 <b>Таро-профиль по дате рождения за 5475 ₽</b>

Персональный психологический портрет на 8-10 страниц в красивом PDF.

<b>Что внутри:</b>
• Титульная страница с вашим Арканом
• Подробный психологический портрет
• Сильные стороны и таланты
• Теневые аспекты и вызовы
• Проявление в отношениях, карьере, саморазвитии
• Практические рекомендации

Пришлите дату рождения после оплаты."""
    kb = [
        [InlineKeyboardButton(text="Написать", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= АРКАН МЕСЯЦА =================
@dp.callback_query(F.data == "month_arcan")
async def month_arcan(call: CallbackQuery):
    text = """🃏 <b>Аркан Месяца по дате рождения — 399 ₽</b>

Аркан Месяца — твой персональный архетип на текущий месяц.

Это короткий, но очень точный психологический разбор главной энергии месяца.

<b>Что ты получишь в PDF:</b>
• Титульная страница с Арканом Месяца + изображением карты
• Подробный психологический портрет энергии месяца
• Ресурсы, возможности, таланты
• Главные вызовы и теневая сторона
• Как лучше проживать этот месяц
• Практические рекомендации

Объём: 3–5 страниц. Срок: до 24 часов."""
    kb = [
        [InlineKeyboardButton(text="Заказать", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ЧЕК-ЛИСТ =================
@dp.callback_query(F.data == "checklist")
async def checklist(call: CallbackQuery):
    text = """📋 <b>Получить чек-лист</b>

Здесь можно вставить свою ссылку на чек-лист.

(Отредактируй код и замени ссылку ниже на свою)"""
    kb = [
        [InlineKeyboardButton(text="Получить чек-лист", url="https://t.me/taro_darinsight")],  # ← Замени на свою ссылку
        [InlineKeyboardButton(text="↩️ Назад", callback_data="psychology_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ЗАПИСАТЬСЯ НА КОНСУЛЬТАЦИЮ =================
@dp.callback_query(F.data == "consultation")
async def consultation(call: CallbackQuery):
    text = """🪴 <b>Записаться на консультацию</b>

Привет, я Дарья — психолог, гештальт-терапевт.

С 2023 года помогаю взрослым людям обретать ясность, внутреннюю опору и направление в периоды тревоги, эмоционального хаоса и потери смысла.

<b>Мой подход:</b>
• Гештальт-терапия
• МАК-карты
• Элементы арт-терапии

<b>Форматы:</b>
• 50 минут — стандартная консультация
• 100 минут — двойная консультация

Провожу онлайн и очно в Санкт-Петербурге."""
    kb = [
        [InlineKeyboardButton(text="Записаться", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="psychology_section")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ОБО МНЕ =================
@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = """🪴 <b>Обо мне</b>

Привет! Я Дарья — гештальт-терапевт и таролог.

Я создала этот бот, чтобы вся полезная информация, услуги и возможности были собраны в одном удобном месте.

Работаю на стыке психологии и Таро как мощного психологического инструмента. Здесь нет мистики — только честная и бережная работа с собой.

Если вы здесь — значит уже сделали важный шаг к себе. Я рада быть рядом на этом пути ✨"""
    kb = [
        [InlineKeyboardButton(text="Спросить", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= НАВИГАЦИЯ =================
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await main_menu(call.message)

# ================= СТАРТ =================
@dp.message(Command("start"))
async def start(message: Message):
    if await check_subscriptions(message.from_user.id):
        await main_menu(message)
    else:
        await message.answer(
            "👋 <b>Добро пожаловать в бот Таро и Психологии от Дарьи!</b>\n\n"
            "Для доступа к контенту подпишитесь на два канала:",
            reply_markup=get_subscribe_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    if await check_subscriptions(call.from_user.id):
        await call.message.edit_text("✅ <b>Подписка подтверждена!</b>\nДобро пожаловать ❤️")
        await main_menu(call.message)
    else:
        await call.answer("❌ Вы ещё не подписаны на все каналы!", show_alert=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
