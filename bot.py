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
        [InlineKeyboardButton(text="📢 Подписаться на канал 1", url="https://t.me/darinsight_psy")],
        [InlineKeyboardButton(text="📢 Подписаться на канал 2", url="https://t.me/darinsight")],
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
    await message.answer("🎴 <b>Главное меню</b>\n\nВыберите раздел:", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= РАЗДЕЛ "РАСКЛАДЫ ТАРО" =================
@dp.callback_query(F.data == "tarot_section")
async def tarot_section(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🃏 Карта Дня", callback_data="card_of_day")],
        [InlineKeyboardButton(text="🌟 Гороскоп на сегодня", callback_data="daily_horoscope")],
        [InlineKeyboardButton(text="💳 Заказать личный расклад", callback_data="order_spread")],
        [InlineKeyboardButton(text="🎂 Таро-профиль по дате рождения", callback_data="birth_profile")],
        [InlineKeyboardButton(text="📅 Аркан месяца по дате рождения", callback_data="month_arcan")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🔮 <b>Расклады Таро</b>\n\nЧто хотите посмотреть?", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= РАЗДЕЛ "ПСИХОЛОГИЯ" =================
@dp.callback_query(F.data == "psychology_section")
async def psychology_section(call: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📋 Получить чек-лист", callback_data="checklist")],
        [InlineKeyboardButton(text="📅 Записаться на консультацию", callback_data="consultation")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ]
    await call.message.edit_text("🧠 <b>Психология</b>\n\nЧто вас интересует?", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= КАРТА ДНЯ =================
@dp.callback_query(F.data == "card_of_day")
async def send_card_of_day(call: CallbackQuery):
    await call.message.edit_text("🃏 Загружаю Карту Дня...")
    card_text = get_card_of_the_day()
    text = f"🃏 <b>Карта Дня</b>\n\n{card_text}"
    kb = [[InlineKeyboardButton(text="🔄 Обновить", callback_data="card_of_day")],
          [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ЗАГЛУШКИ =================
@dp.callback_query(F.data.in_(["daily_horoscope", "order_spread", "birth_profile", "month_arcan", "checklist", "consultation", "about"]))
async def coming_soon(call: CallbackQuery):
    await call.answer("⏳ Эта функция скоро будет доступна!", show_alert=True)

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
            "👋 <b>Добро пожаловать в бот Таро и Психологии!</b>\n\n"
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
