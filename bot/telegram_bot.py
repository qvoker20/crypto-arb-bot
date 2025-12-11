import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import TELEGRAM_BOT_TOKEN
from bot.db import (
    verify_user,
    get_user_by_telegram_id,
    get_db
)

# ============================
#   ЛОГ
# ============================
def log(msg: str):
    print(f"[TG] {datetime.now().isoformat()}  {msg}")


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# ============================
#   МЕНЮ
# ============================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профіль", callback_data="me")],
        [InlineKeyboardButton(text="📊 Статус арбітражу", callback_data="status")],
    ])


# ============================
#   /start
# ============================
@dp.message(Command("start"))
async def start(message: types.Message):
    tg_id = message.chat.id
    log(f"/start → {tg_id}")

    user = get_user_by_telegram_id(tg_id)

    if user:
        # вже авторизований
        await message.answer("Ви авторизовані ✔", reply_markup=main_menu())
        return

    # якщо не авторизований
    await message.answer(
        "Ваш Telegram не привʼязано.\n"
        "Введіть логін і пароль у форматі:\n`login password`",
        parse_mode="Markdown"
    )


# ============================
#   ОБРОБКА "login password"
# ============================
@dp.message(F.text.regexp(r"^\w+\s+\w+$"))
async def handle_login(message: types.Message):
    tg_id = message.chat.id
    log(f"Авторизація '{message.text}' від {tg_id}")

    username, password = message.text.split()
    user = verify_user(username, password)

    if not user:
        await message.answer("❌ Логін або пароль неправильні.")
        return

    # Прив'язуємо Telegram ID
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET telegram_id = ? WHERE username = ?",
        (str(tg_id), username)
    )
    conn.commit()
    conn.close()

    await message.answer("✅ Telegram привʼязано!", reply_markup=main_menu())
    log(f"TG ID {tg_id} привʼязано до користувача {username}")


# ============================
#   КНОПКА: ПРОФІЛЬ
# ============================
@dp.callback_query(F.data == "me")
async def show_profile(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    log(f"Кнопка Профіль → {tg_id}")

    user = get_user_by_telegram_id(tg_id)

    if not user:
        await callback.message.answer("❌ Ви не авторизовані. Натисніть /start.")
        return

    text = (
        f"👤 *Ваш профіль*\n\n"
        f"ID: `{user['id']}`\n"
        f"ПІП: {user['full_name']}\n"
        f"Логін: `{user['username']}`\n"
        f"Статус: {'Адмін' if user['is_admin'] else 'Користувач'}"
    )

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


# ============================
#   КНОПКА: СТАТУС
# ============================
@dp.callback_query(F.data == "status")
async def show_status(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    log(f"Кнопка Статус → {tg_id}")

    await callback.message.answer("📡 Арбітражний моніторинг працює стабільно.")
    await callback.answer()


# ============================
#   ВІДПРАВКА СИГНАЛІВ (monitor викликає це)
# ============================
async def send_signal(user_id: int, text: str):
    log(f"Сигнал → {user_id}: {text[:40]}...")
    try:
        await bot.send_message(user_id, text, parse_mode="Markdown")
    except Exception as e:
        log(f"[ERROR] send_signal: {e}")


# ============================
#   ЗАПУСК БОТА
# ============================
async def run_telegram():
    log("Telegram бот запущено.")
    await dp.start_polling(bot)
