"""
Бот для создание и управления токенами.
"""

import sqlite3
import secrets
from datetime import datetime, timedelta
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import BotToken, AdminId

bot = Bot(token=BotToken)
dp = Dispatcher(bot)

DB_FILE = "../Server/tokens.db"


def init_db():
    """
    Initializes the SQLite database and creates the 'tokens' table if it doesn't exist.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                expiration TIMESTAMP NOT NULL,
                ip_address TEXT
            )
        """
        )
        conn.commit()


def create_token(expiration_seconds: int, ip_address: str = None):
    """
    Creates a new token with an expiration time in seconds and stores it in the database.
    """
    token = secrets.token_urlsafe(32)
    expiration = datetime.utcnow() + timedelta(seconds=expiration_seconds)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tokens (token, expiration, ip_address)
            VALUES (?, ?, ?)
        """,
            (token, expiration, ip_address),
        )
        conn.commit()

    return {"token": token, "expiration": expiration.isoformat()}


def clean_expired_tokens():
    """
    Cleans up expired tokens from the database.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tokens WHERE expiration <= ?", (datetime.utcnow(),))
        conn.commit()


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    """
    Starts the bot and presents the admin with options to manage tokens.
    """
    if message.from_user.id != AdminId:
        await message.reply("Вы не администратор!")
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton("Список токенов", callback_data="list_tokens")
    button2 = InlineKeyboardButton(
        "Очистить просроченные токены", callback_data="clean_tokens"
    )
    button3 = InlineKeyboardButton(
        "Создать новый токен", callback_data="generate_token"
    )
    keyboard.add(button1, button2, button3)

    await message.reply(
        "Добро пожаловать в бот для управления токенами! Выберите действие:",
        reply_markup=keyboard,
    )


@dp.message_handler(commands=["gen"])
async def generate_command(message: types.Message):
    """
    Prompts the admin to input the expiration time for generating a new token.
    """
    if message.from_user.id != AdminId:
        await message.reply("Вы не администратор!")
        return
    await message.reply(
        "Введите время жизни токена в секундах (например, 3600 для 1 часа):"
    )


@dp.message_handler(commands=["list_tokens"])
async def list_tokens_command(message: types.Message):
    """
    Lists all tokens stored in the database.
    """
    if message.from_user.id != AdminId:
        await message.reply("Вы не администратор!")
        return
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token, expiration, ip_address FROM tokens")
            rows = cursor.fetchall()

        if not rows:
            await message.reply("Нет активных токенов.")
            return

        tokens_info = "\n".join(
            [f"🔑 {row[0]}\n⏰ Действителен до: {row[1]}" for row in rows]
        )
        await message.reply(f"📜 Список токенов:\n{tokens_info}")
    except sqlite3.DatabaseError as e:
        await message.reply(f"Ошибка при доступе к базе данных: {e}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@dp.message_handler(commands=["clean_tokens"])
async def clean_tokens_command(message: types.Message):
    """
    Cleans expired tokens from the database.
    """
    if message.from_user.id != AdminId:
        await message.reply("Вы не администратор!")
        return
    try:
        clean_expired_tokens()
        await message.reply("✅ Удалены все просроченные токены.")
    except sqlite3.DatabaseError as e:
        await message.reply(f"Ошибка при очистке токенов: {e}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@dp.callback_query_handler(lambda c: c.data == "list_tokens")
async def list_tokens_callback(callback_query: types.CallbackQuery):
    """
    Handles the callback for listing tokens via inline keyboard.
    """
    if callback_query.from_user.id != AdminId:
        await bot.answer_callback_query(callback_query.id, text="Вы не администратор!")
        return
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token, expiration, ip_address FROM tokens")
            rows = cursor.fetchall()

        if not rows:
            await bot.answer_callback_query(
                callback_query.id, text="Нет активных ключей."
            )
            return

        tokens_info = "\n".join(
            [f"🔑 {row[0]}\n⏰ Действителен до: {row[1]}" for row in rows]
        )
        await bot.send_message(
            callback_query.from_user.id, f"📜 Список ключей:\n{tokens_info}"
        )
        await bot.answer_callback_query(callback_query.id)
    except sqlite3.DatabaseError as e:
        await bot.answer_callback_query(callback_query.id, text=f"Ошибка: {e}")
    except Exception as e:
        await bot.answer_callback_query(callback_query.id, text=f"Ошибка: {e}")


@dp.callback_query_handler(lambda c: c.data == "clean_tokens")
async def clean_tokens_callback(callback_query: types.CallbackQuery):
    """
    Handles the callback for cleaning expired tokens via inline keyboard.
    """
    if callback_query.from_user.id != AdminId:
        await bot.answer_callback_query(callback_query.id, text="Вы не администратор!")
        return
    try:
        clean_expired_tokens()
        await bot.send_message(
            callback_query.from_user.id, "✅ Удалены все просроченные токены."
        )
        await bot.answer_callback_query(callback_query.id)
    except sqlite3.DatabaseError as e:
        await bot.answer_callback_query(callback_query.id, text=f"Ошибка при очистке токенов: {e}")
    except Exception as e:
        await bot.answer_callback_query(callback_query.id, text=f"Ошибка: {e}")


@dp.callback_query_handler(lambda c: c.data == "generate_token")
async def generate_token_callback(callback_query: types.CallbackQuery):
    """
    Handles the callback for generating a new token with specified expiration time.
    """
    if callback_query.from_user.id != AdminId:
        await bot.answer_callback_query(callback_query.id, text="Вы не администратор!")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton("1 час", callback_data="gen_3600")
    button2 = InlineKeyboardButton("24 часа", callback_data="gen_86400")
    button3 = InlineKeyboardButton("48 часов", callback_data="gen_172800")
    keyboard.add(button1, button2, button3)

    await bot.send_message(
        callback_query.from_user.id,
        "Выберите продолжительность жизни токена:",
        reply_markup=keyboard,
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data.startswith("gen_"))
async def generate_token_with_expiration(callback_query: types.CallbackQuery):
    """
    Handles the callback for generating a token with a specific expiration time.
    """
    if callback_query.from_user.id != AdminId:
        await bot.answer_callback_query(callback_query.id, text="Вы не администратор!")
        return

    expiration_seconds = int(callback_query.data.split("_")[1])
    token_data = create_token(expiration_seconds)

    await bot.send_message(
        callback_query.from_user.id,
        f"✅ Ключ создан:\n"
        f"🔑 Токен: `{token_data['token']}`\n"
        f"⏰ Действителен до: {token_data['expiration']}",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler()
async def handle_message(message: types.Message):
    """
    Handles general messages for creating a token if the message is a valid number.
    """
    if message.from_user.id != AdminId:
        return

    if message.text.isdigit():
        expiration_seconds = int(message.text)
        token_data = create_token(expiration_seconds)

        await message.reply(
            f"✅ Ключ создан:\n"
            f"🔑 Токен: `{token_data['token']}`\n"
            f"⏰ Действителен до: {token_data['expiration']}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await message.reply(
            "Пожалуйста, введите число для времени жизни токена в секундах."
        )


async def auto_clean():
    """
    Periodically cleans expired tokens from the database every 5 minutes.
    """
    while True:
        clean_expired_tokens()
        await asyncio.sleep(300)


def main():
    """
    Initializes the database, starts the auto-clean task, and begins polling for bot updates.
    """
    init_db()
    loop = asyncio.get_event_loop()
    loop.create_task(auto_clean())
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
