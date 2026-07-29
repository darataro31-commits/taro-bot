import asyncio
import logging
import os
from datetime import datetime

import aiosqlite
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

CHANNELS = ["@darinsight_psy", "@darinsight"]
DB_PATH = "bot_data.db"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_schedule_text = State()
    waiting_schedule_time = State()


# ================= БАЗА ДАННЫХ =================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT,
                last_activity TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                button TEXT,
                clicked_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_id INTEGER,
                user_id INTEGER,
                message_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                send_at TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str = None, first_name: str = None):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_activity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_activity=excluded.last_activity
        """, (user_id, username, first_name, now, now))
        await db.commit()


async def log_click(user_id: int, button: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO clicks (user_id, button, clicked_at) VALUES (?, ?, ?)",
            (user_id, button, now)
        )
        await db.commit()


# ================= ПОДПИСКА =================
async def check_subscriptions(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True


def get_subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 @darinsight_psy", url="https://t.me/darinsight_psy")],
        [InlineKeyboardButton(text="📢 @darinsight", url="https://t.me/darinsight")],
        [InlineKeyboardButton(text="✅ Я подписался(ась)", callback_data="check_sub")]
    ])


# ================= КАРТА ДНЯ И ГОРОСКОП =================
def get_card_of_the_day():
    try:
        r = requests.get("https://horoscopes.rambler.ru/taro/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        card = soup.find("h2", string=lambda t: t and "Карта Таро сегодня" in t)
        if card:
            desc = card.find_next("p")
            return f"<b>{card.get_text(strip=True)}</b>\n\n{desc.get_text(strip=True) if desc else ''}"
    except Exception:
        pass
    return "🃏 Не удалось загрузить Карту Дня. Попробуйте позже."


zodiacs = {
    "aries": "♈ Овен", "taurus": "♉ Телец", "gemini": "♊ Близнецы",
    "cancer": "♋ Рак", "leo": "♌ Лев", "virgo": "♍ Дева",
    "libra": "♎ Весы", "scorpio": "♏ Скорпион", "sagittarius": "♐ Стрелец",
    "capricorn": "♑ Козерог", "aquarius": "♒ Водолей", "pisces": "♓ Рыбы"
}


def get_horoscope(sign: str):
    try:
        r = requests.get(f"https://horoscopes.rambler.ru/{sign}/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in ["div.horoscope__text", "div.article__text", "p"]:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if len(text) > 120:
                    return text[:1800]
    except Exception:
        pass
    return "😔 Не удалось загрузить гороскоп. Попробуйте позже."


# ================= ГЛАВНОЕ МЕНЮ =================
async def main_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Расклады Таро", callback_data="tarot_section")],
        [InlineKeyboardButton(text="🧠 Психология", callback_data="psychology_section")],
        [InlineKeyboardButton(text="ℹ️ Обо мне / Помощь", callback_data="about")]
    ])
    if message.from_user.id == ADMIN_ID:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")])
    await message.answer("🎴 <b>Главное меню Таро и Психологии от Дарьи</b>", reply_markup=kb)


# ================= АДМИН-ПАНЕЛЬ =================
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⏰ Отложенная рассылка", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="🗑 Удалить рассылку", callback_data="admin_delete_broadcast")],
        [InlineKeyboardButton(text="↩️ В меню", callback_data="back_to_main")]
    ])


@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.edit_text("🛠 <b>Админ-панель</b>", reply_markup=admin_kb())


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total = (await c.fetchone())[0]
        async with db.execute(
            "SELECT user_id, username, first_name FROM users WHERE joined_at LIKE ? ORDER BY joined_at DESC LIMIT 20",
            (f"{today}%",)
        ) as c:
            new_users = await c.fetchall()
        async with db.execute(
            "SELECT user_id, username, first_name FROM users WHERE last_activity LIKE ? ORDER BY last_activity DESC LIMIT 20",
            (f"{today}%",)
        ) as c:
            active_users = await c.fetchall()
        async with db.execute("""
            SELECT u.user_id, u.username, u.first_name, COUNT(*)
            FROM clicks c JOIN users u ON c.user_id = u.user_id
            WHERE c.button = 'card_of_day' AND c.clicked_at LIKE ?
            GROUP BY u.user_id ORDER BY COUNT(*) DESC LIMIT 20
        """, (f"{today}%",)) as c:
            card_clicks = await c.fetchall()
        async with db.execute("""
            SELECT u.user_id, u.username, u.first_name, COUNT(*)
            FROM clicks c JOIN users u ON c.user_id = u.user_id
            WHERE c.button = 'horoscope' AND c.clicked_at LIKE ?
            GROUP BY u.user_id ORDER BY COUNT(*) DESC LIMIT 20
        """, (f"{today}%",)) as c:
            horo_clicks = await c.fetchall()

    def fmt_users(rows):
        if not rows:
            return "нет"
        return "\n".join([
            f"• <code>{r[0]}</code> @{r[1] or '—'} ({r[2] or '—'})" for r in rows
        ])

    def fmt_clicks(rows):
        if not rows:
            return "нет"
        return "\n".join([
            f"• <code>{r[0]}</code> @{r[1] or '—'} — {r[3]} раз" for r in rows
        ])

    text = f"""📊 <b>Статистика</b>

👥 Всего пользователей: <b>{total}</b>

🆕 <b>Новые сегодня:</b>
{fmt_users(new_users)}

📅 <b>Активные сегодня:</b>
{fmt_users(active_users)}

🃏 <b>Карта Дня сегодня:</b>
{fmt_clicks(card_clicks)}

🌟 <b>Гороскоп сегодня:</b>
{fmt_clicks(horo_clicks)}"""
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_panel")]
    ]))


# ---------- РАССЫЛКА (с сохранением message_id) ----------
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await call.message.edit_text(
        "📢 Пришлите текст рассылки (можно с HTML).\n\nОтмена: /cancel",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]
        ])
    )


@dp.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.html_text or message.text
    await state.clear()

    # создаём запись о рассылке
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO broadcasts (text, created_at) VALUES (?, ?)",
            (text[:200], datetime.now().isoformat())
        )
        broadcast_id = cursor.lastrowid
        await db.commit()

        async with db.execute("SELECT user_id FROM users") as cur:
            users = await cur.fetchall()

    ok, fail = 0, 0
    async with aiosqlite.connect(DB_PATH) as db:
        for (uid,) in users:
            try:
                msg = await bot.send_message(uid, text)
                await db.execute(
                    "INSERT INTO broadcast_messages (broadcast_id, user_id, message_id) VALUES (?, ?, ?)",
                    (broadcast_id, uid, msg.message_id)
                )
                ok += 1
                await asyncio.sleep(0.05)
            except Exception:
                fail += 1
        await db.commit()

    await message.answer(
        f"✅ Рассылка завершена\nУспешно: {ok}\nОшибок: {fail}\nID рассылки: <code>{broadcast_id}</code>",
        reply_markup=admin_kb()
    )


# ---------- УДАЛЕНИЕ КОНКРЕТНОЙ РАССЫЛКИ ----------
@dp.callback_query(F.data == "admin_delete_broadcast")
async def admin_delete_broadcast(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, text, created_at FROM broadcasts ORDER BY id DESC LIMIT 10"
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        return await call.message.edit_text(
            "Нет сохранённых рассылок.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_panel")]
            ])
        )

    buttons = []
    for bid, text, created in rows:
        short = (text[:40] + "…") if len(text) > 40 else text
        date = created[:16].replace("T", " ")
        buttons.append([InlineKeyboardButton(
            text=f"#{bid} | {date} | {short}",
            callback_data=f"del_bc_{bid}"
        )])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_panel")])

    await call.message.edit_text(
        "🗑 <b>Выберите рассылку для удаления у всех пользователей:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(F.data.startswith("del_bc_"))
async def delete_selected_broadcast(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    broadcast_id = int(call.data.replace("del_bc_", ""))
    await call.message.edit_text(f"🗑 Удаляю рассылку #{broadcast_id}...")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, message_id FROM broadcast_messages WHERE broadcast_id = ?",
            (broadcast_id,)
        ) as cur:
            msgs = await cur.fetchall()

    deleted = 0
    for uid, mid in msgs:
        try:
            await bot.delete_message(uid, mid)
            deleted += 1
            await asyncio.sleep(0.03)
        except Exception:
            pass

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM broadcast_messages WHERE broadcast_id = ?", (broadcast_id,))
        await db.execute("DELETE FROM broadcasts WHERE id = ?", (broadcast_id,))
        await db.commit()

    await call.message.edit_text(
        f"✅ Рассылка #{broadcast_id} удалена\nУдалено сообщений: <b>{deleted}</b>",
        reply_markup=admin_kb()
    )


# ---------- ОТЛОЖЕННАЯ РАССЫЛКА ----------
@dp.callback_query(F.data == "admin_schedule")
async def admin_schedule(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_schedule_text)
    await call.message.edit_text(
        "⏰ Пришлите текст отложенной рассылки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]
        ])
    )


@dp.message(AdminStates.waiting_schedule_text)
async def schedule_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(text=message.html_text or message.text)
    await state.set_state(AdminStates.waiting_schedule_time)
    await message.answer(
        "Введите время в формате:\n<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\nПример: <code>30.07.2026 10:00</code>"
    )


@dp.message(AdminStates.waiting_schedule_time)
async def schedule_time(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        send_at = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        if send_at < datetime.now():
            return await message.answer("Время уже прошло. Введите будущее время.")
        data = await state.get_data()
        text = data["text"]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO scheduled (text, send_at, status) VALUES (?, ?, 'pending')",
                (text, send_at.isoformat())
            )
            await db.commit()
        scheduler.add_job(
            do_scheduled_broadcast, "date", run_date=send_at, args=[text],
            id=f"sched_{send_at.timestamp()}"
        )
        await state.clear()
        await message.answer(
            f"✅ Рассылка запланирована на {send_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=admin_kb()
        )
    except ValueError:
        await message.answer("Неверный формат. Пример: 30.07.2026 10:00")


async def do_scheduled_broadcast(text: str):
    # создаём broadcast и сохраняем message_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO broadcasts (text, created_at) VALUES (?, ?)",
            (text[:200], datetime.now().isoformat())
        )
        broadcast_id = cursor.lastrowid
        await db.commit()

        async with db.execute("SELECT user_id FROM users") as cur:
            users = await cur.fetchall()

        for (uid,) in users:
            try:
                msg = await bot.send_message(uid, text)
                await db.execute(
                    "INSERT INTO broadcast_messages (broadcast_id, user_id, message_id) VALUES (?, ?, ?)",
                    (broadcast_id, uid, msg.message_id)
                )
                await asyncio.sleep(0.05)
            except Exception:
                pass
        await db.execute("UPDATE scheduled SET status='done' WHERE text=? AND status='pending'", (text,))
        await db.commit()


# ================= РАЗДЕЛЫ =================
@dp.callback_query(F.data == "tarot_section")
async def tarot_section(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Карта Дня", callback_data="card_of_day")],
        [InlineKeyboardButton(text="🌟 Гороскоп на сегодня", callback_data="horoscope")],
        [InlineKeyboardButton(text="💳 Заказать личный расклад", callback_data="order_spread")],
        [InlineKeyboardButton(text="🎂 Таро-профиль по дате рождения", callback_data="birth_profile")],
        [InlineKeyboardButton(text="📅 Аркан месяца по дате рождения", callback_data="month_arcan")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ])
    await call.message.edit_text("🔮 <b>Расклады Таро</b>", reply_markup=kb)


@dp.callback_query(F.data == "psychology_section")
async def psychology_section(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Получить мини-гайд", callback_data="checklist")],
        [InlineKeyboardButton(text="📅 Записаться на консультацию", callback_data="consultation")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ])
    await call.message.edit_text("🧠 <b>Психология</b>", reply_markup=kb)


@dp.callback_query(F.data == "card_of_day")
async def send_card_of_day(call: CallbackQuery):
    await log_click(call.from_user.id, "card_of_day")
    await call.message.edit_text("🃏 Загружаю Карту Дня...")
    text = f"🃏 <b>Карта Дня</b>\n\n{get_card_of_the_day()}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="card_of_day")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "horoscope")
async def horoscope_menu(call: CallbackQuery):
    await log_click(call.from_user.id, "horoscope")
    kb = [[InlineKeyboardButton(text=name, callback_data=f"hor_{code}")] for code, name in zodiacs.items()]
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")])
    await call.message.edit_text(
        "🌟 <b>Гороскоп на сегодня</b>\nВыберите знак:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@dp.callback_query(F.data.startswith("hor_"))
async def send_horoscope(call: CallbackQuery):
    sign = call.data[4:]
    name = zodiacs.get(sign, sign)
    await call.message.edit_text(f"🌟 Загружаю гороскоп для <b>{name}</b>...")
    text = f"🌟 <b>Гороскоп — {name}</b>\n\n{get_horoscope(sign)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"hor_{sign}")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="horoscope")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


# ================= ПОЛНЫЕ ТЕКСТЫ УСЛУГ =================
@dp.callback_query(F.data == "order_spread")
async def order_spread(call: CallbackQuery):
    text = """🃏 <b>Заказать личный расклад</b>

Привет! Я занимаюсь Таро уже 5 лет и смотрю на карты не как на магию, а как на мощный инструмент работы с бессознательным.

Это глубокая психологическая работа: карты помогают вытащить на поверхность то, что ты уже знаешь внутри, но пока не можешь сформулировать сам. Я не провожу ритуалы, не работаю с «энергетикой» и не даю «предсказаний судьбы». Только честный разбор ситуации через архетипы и психологию.

<b>Что я предлагаю:</b>
• Помогаю правильно подобрать расклад именно под твой запрос
• Вместе формулируем точные и глубокие вопросы
• Делаю полноценный личный расклад длительностью 60 минут в аудиоформате
• Аудио остаётся у тебя — можно переслушивать и ловить новые инсайты

<b>Важные ограничения:</b>
❌ Не работаю с темами смерти, здоровья и беременности

<b>Как это происходит:</b>
1. Ты пишешь свой запрос
2. Мы вместе уточняем ситуацию и подбираем подходящий расклад
3. Оплачиваешь
4. Я делаю расклад и присылаю тебе подробное аудио (60 минут)

Готов погрузиться в настоящий психологический разбор через Таро?"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "birth_profile")
async def birth_profile(call: CallbackQuery):
    text = """🃏 <b>Таро-профиль по дате рождения за 5475 ₽</b>

Персональный психологический портрет на 8–10 страниц в красивом PDF.

Я рассчитываю ваш основной Аркан (и дополнительные карты) по дате рождения и даю глубокий разбор через призму психологии и архетипов Таро. Без магии, ритуалов и «предсказаний» — только работа с бессознательным.

<b>Что внутри PDF:</b>
• Титульная страница с вашим Арканом
• Методика расчёта
• Подробный психологический портрет (2–3 страницы)
• Сильные стороны, таланты, ресурс
• Теневые аспекты и внутренние вызовы
• Как Аркан проявляется в отношениях, карьере, саморазвитии
• Практические рекомендации
• Вопросы для саморефлексии и дальнейшей работы

Пришлите дату рождения после оплаты — и я подготовлю ваш персональный профиль."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "month_arcan")
async def month_arcan(call: CallbackQuery):
    text = """🃏 <b>Аркан Месяца по дате рождения — 399 ₽</b>

Аркан Месяца — твой персональный архетип на текущий месяц.

Это короткий, но очень точный и полезный психологический разбор твоей главной энергии месяца по дате рождения.

Я рассчитываю Аркан Месяца (личный архетип, который наиболее сильно проявляется у тебя именно сейчас) и даю глубокий, но практичный разбор с психологической точки зрения.

<b>Что ты получишь в PDF:</b>
• Титульная страница с твоим Арканом Месяца + красивым изображением карты
• Подробный психологический портрет энергии этого месяца
• Что этот Аркан даёт тебе (ресурсы, возможности, таланты)
• Главные вызовы и теневая сторона
• Как лучше всего проживать этот месяц (отношения, работа, саморазвитие)
• Практические рекомендации и вопросы для размышления

Объём: 3–5 страниц — удобно читать за один раз и возвращаться к нему в течение месяца.
Срок подготовки: в течение 24 часов после оплаты и получения даты рождения."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Заказать", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="tarot_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "checklist")
async def checklist(call: CallbackQuery):
    text = """📋 <b>Получить мини-гайд</b>

Бесплатный мини-гайд «Тревога под контролем» 📘🕊

"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить мини-гайд", url="https://t.me/darinsight_psy/43")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="psychology_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "consultation")
async def consultation(call: CallbackQuery):
    text = """🪴 <b>Записаться на консультацию</b>

Привет, я Дарья — психолог, гештальт-терапевт.

С 2023 года я помогаю взрослым людям обретать ясность, внутреннюю опору и направление в периоды тревоги, эмоционального хаоса и потери смысла. Сама прошла через подобный опыт, поэтому хорошо понимаю, каково это — когда внутри шумит, а снаружи нужно держаться. Продолжаю личную терапию, считая это важной частью профессиональной этики.

<b>Мой подход</b>
Работаю интегративно, подбирая инструменты под конкретного человека и запрос:
• Гештальт-терапия
• МАК-карты
• Элементы арт-терапии

Также предлагаю отдельную услугу — психологические расклады Таро как способ глубже увидеть ситуацию и услышать своё бессознательное (на терапевтических сессиях карты не использую).

<b>Форматы работы</b>
• Долгосрочная терапия по психотерапевтическому контракту (глубокая проработка)
• Краткосрочная поддержка — 1–5 сессий (решение конкретного запроса)

<b>Длительность сессий:</b>
• Стандартная консультация — 50 минут (онлайн по видеосвязи)
• Двойная консультация — 100 минут (для более глубокого погружения)

Провожу сессии онлайн и очно в Санкт-Петербурге.

<b>Важные уточнения</b>
Я не работаю со следующими запросами:
• ПТСР
• Расстройства пищевого поведения (РПП)
• Подростки и дети

Регулярно прохожу супервизии, дополнительное обучение и участвую в профессиональных конференциях."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="psychology_section")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = """🪴 <b>Обо мне</b>

Привет! Я Дарья — гештальт-терапевт и таролог.

Я создала этот бот, чтобы вся полезная информация, услуги и возможности были собраны в одном удобном месте.

Я работаю на стыке психологии и Таро, но никогда не ухожу в мистику и гадания. Для меня Таро — это мощный психологический инструмент, который помогает мягко подсветить те части нас, которые мы привыкли прятать или не замечать. А гештальт-терапия даёт возможность честно и бережно с этим работать, решать внутренние задачи и двигаться дальше.

Каждый из нас иногда нуждается в безопасном пространстве, где можно наконец посмотреть на то, что раньше было сложно увидеть. Моя главная задача — создать такое пространство: комфортное, мягкое и честное.

Я очень люблю свою работу и подхожу к ней с большой заботой. Здесь нет резких «пробиваний» и травматичных разборок — только уважение к вашему темпу, поддержка и постепенное движение к изменениям.

В этом боте вы можете:
• Записаться на психологическую консультацию
• Заказать личный расклад Таро
• Получить Таро-профиль по дате рождения
• Получить Аркан Месяца
• И просто найти полезные материалы

Если вы здесь — значит, уже сделали важный шаг к себе. Я рада быть рядом на этом пути ✨"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Спросить", url="https://t.me/taro_darinsight")],
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await main_menu(call.message)


@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    if await check_subscriptions(call.from_user.id):
        await call.message.edit_text("✅ <b>Подписка подтверждена!</b>\nДобро пожаловать ❤️")
        await main_menu(call.message)
    else:
        await call.answer("❌ Вы ещё не подписаны на все каналы!", show_alert=True)


@dp.message(Command("start"))
async def start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if await check_subscriptions(message.from_user.id):
        await main_menu(message)
    else:
        await message.answer(
            "👋 <b>Добро пожаловать в бот Таро и Психологии от Дарьи!</b>\n\n"
            "Для доступа к контенту подпишитесь на два канала:",
            reply_markup=get_subscribe_keyboard()
        )


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено")


@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 <b>Админ-панель</b>", reply_markup=admin_kb())


async def on_startup():
    await init_db()
    scheduler.start()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT text, send_at FROM scheduled WHERE status='pending'") as cur:
            rows = await cur.fetchall()
    for text, send_at in rows:
        dt = datetime.fromisoformat(send_at)
        if dt > datetime.now():
            scheduler.add_job(do_scheduled_broadcast, "date", run_date=dt, args=[text])


async def main():
    logging.basicConfig(level=logging.INFO)
    await on_startup()
    print("🤖 Бот с админ-панелью запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
