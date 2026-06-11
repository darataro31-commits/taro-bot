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
    "@твой_канал1",
    "@твой_канал2",
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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Новый способ поиска (актуально на 2026)
        horo_block = soup.find("div", class_=lambda x: x and "horoscope__text" in str(x))
        if horo_block:
            return horo_block.get_text(strip=True)
        
        # Резервный вариант
        p_tags = soup.find_all("p")
        for p in p_tags:
            if len(p.get_text(strip=True)) > 100:
                return p.get_text(strip=True)
    except:
        pass
    return "Не удалось загрузить гороскоп. Попробуйте позже."

# ============================================

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def get_subscribe_keyboard():
    kb = [
        [InlineKeyboardButton(text="📢 Подписаться на канал 1", url="https://t.me/твой_канал1")],
        [InlineKeyboardButton(text="📢 Подписаться на канал 2", url="https://t.me/твой_канал2")],
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

async def main_menu(message: Message):
    kb = [
        [InlineKeyboardButton(text="🔮 Расклады Таро", callback_data="tarot_section")],
        [InlineKeyboardButton(text="🧠 Психология", callback_data="psychology_section")],
        [InlineKeyboardButton(text="ℹ️ Обо мне / Помощь", callback_data="about")]
    ]
    await message.answer("🎴 <b>Главное меню Таро и Психологии</b>", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= РАЗДЕЛ ТАРО =================
@dp.callback_query(F.data == "tarot_section")
async def tarot_section(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🃏 Карта Дня", callback_data="card_of_day")],
        [InlineKeyboardButton(text="🌟 Гороскоп на сегодня", callback_data="horoscope")],
        [InlineKeyboardButton(text="💳 Заказать личный расклад", callback_data="order_spread")],
        [InlineKeyboardButton(text="🎂 Таро-профиль по дате рождения", callback_data="birth_profile")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🔮 <b>Расклады Таро</b>", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ГОРОСКОП =================
@dp.callback_query(F.data == "horoscope")
async def horoscope_menu(call: CallbackQuery):
    kb = []
    for eng, rus in zodiacs.items():
        kb.append([InlineKeyboardButton(text=rus, callback_data=f"hor_{eng}")])
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")])
    
    await call.message.edit_text("🌟 <b>Гороскоп на сегодня</b>\n\nВыберите знак зодиака:", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("hor_"))
async def send_horoscope(call: CallbackQuery):
    sign = call.data[4:]
    rus_name = zodiacs[sign]
    
    await call.message.edit_text(f"🌟 Загружаю гороскоп для <b>{rus_name}</b>...")
    
    horo_text = get_horoscope(sign)
    
    text = f"🌟 <b>Гороскоп на сегодня — {rus_name}</b>\n\n{horo_text}"
    
    kb = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"hor_{sign}")],
        [InlineKeyboardButton(text="↩️ Другой знак", callback_data="horoscope")],
        [InlineKeyboardButton(text="↩️ В меню", callback_data="back_to_main")]
    ]
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= КАРТА ДНЯ =================
@dp.callback_query(F.data == "card_of_day")
async def send_card_of_day(call: CallbackQuery):
    await call.message.edit_text("🃏 Загружаю Карту Дня...")
    # (тут можно оставить функцию из предыдущего кода)
    await call.answer("🃏 Карта Дня скоро будет доступна!", show_alert=True)

# ================= ДРУГИЕ РАЗДЕЛЫ =================
@dp.callback_query(F.data.in_(["psychology_section", "order_spread", "birth_profile", "about"]))
async def coming_soon(call: CallbackQuery):
    await call.answer("⏳ Эта функция в разработке", show_alert=True)

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
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Для доступа к контенту подпишитесь на два канала:",
            reply_markup=get_subscribe_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    if await check_subscriptions(call.from_user.id):
        await call.message.edit_text("✅ <b>Подписка подтверждена!</b>")
        await main_menu(call.message)
    else:
        await call.answer("❌ Подпишитесь на все каналы!", show_alert=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
