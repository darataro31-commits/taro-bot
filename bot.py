import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "6303692408:AAHrB3RJbb2Anh6N9nXFCKbiD00MFAi8BKM"

CHANNELS = [
    "@darinsight_psy",   # Замени на username первого канала
    "@darinsight",   # Замени на username второго канала
]

# ============================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
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

async def main_menu(message: Message):
    kb = [
        [InlineKeyboardButton(text="🔮 Посмотреть расклад", callback_data="tarot")],
        [InlineKeyboardButton(text="🧠 Получить консультацию", callback_data="consult")],
        [InlineKeyboardButton(text="📘 Скачать бесплатный гайд", callback_data="guide")],
        [InlineKeyboardButton(text="❤️ О боте", callback_data="about")]
    ]
    await message.answer("🎴 <b>Главное меню бота Таро и Психологии</b>", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message(Command("start"))
async def start(message: Message):
    if await check_subscriptions(message.from_user.id):
        await main_menu(message)
    else:
        await message.answer(
            "👋 <b>Добро пожаловать в бот Таро и Психологии!</b>\n\n"
            "Чтобы получить доступ к функционалу — подпишись на два моих канала:",
            reply_markup=get_subscribe_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    if await check_subscriptions(call.from_user.id):
        await call.message.edit_text("✅ <b>Подписка подтверждена!</b>\nДобро пожаловать ❤️")
        await main_menu(call.message)
    else:
        await call.answer("❌ Вы ещё не подписаны на все каналы!", show_alert=True)

# Заглушки
@dp.callback_query(F.data == "tarot")
async def tarot(call: CallbackQuery):
    await call.message.answer("🔮 Функция раскладов пока в разработке...")

@dp.callback_query(F.data == "guide")
async def guide(call: CallbackQuery):
    await call.message.answer("📘 Ссылка на бесплатный гайд (скоро добавим)")

@dp.callback_query()
async def other(call: CallbackQuery):
    await call.answer("Эта функция скоро будет доступна!")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
