import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8841055640:AAE65cYHaE9XVEo2fQLwZ5kPxrR1Fncqm5Q"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Тексты кнопок (используем как константы, чтобы не дублировать строки) ---
BTN_TASKS = "Задания"
BTN_PROFILE = "Профиль"
BTN_STATS = "Общая статистика"
BTN_LEADERS = "Лидеры"
BTN_INFO = "Информация"
BTN_ADVERTISE = "Рекламировать"


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное reply-меню.

    Примечание: Telegram Bot API не поддерживает цветовую стилизацию
    (primary/secondary и т.п.) для ReplyKeyboardMarkup — цвет кнопки
    определяется темой клиента, а не ботом. Здесь просто текстовые кнопки.
    """
    keyboard = [
        [KeyboardButton(text=BTN_TASKS), KeyboardButton(text=BTN_PROFILE)],
        [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_LEADERS)],
        [KeyboardButton(text=BTN_INFO)],
        [KeyboardButton(text=BTN_ADVERTISE)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать! Выберите раздел в меню ниже:",
        reply_markup=main_menu_kb(),
    )


@dp.message(F.text == BTN_TASKS)
async def handle_tasks(message: Message):
    await message.answer("Раздел «Задания» в разработке (заглушка).")


@dp.message(F.text == BTN_PROFILE)
async def handle_profile(message: Message):
    await message.answer("Раздел «Профиль» в разработке (заглушка).")


@dp.message(F.text == BTN_STATS)
async def handle_stats(message: Message):
    await message.answer("Раздел «Общая статистика» в разработке (заглушка).")


@dp.message(F.text == BTN_LEADERS)
async def handle_leaders(message: Message):
    await message.answer("Раздел «Лидеры» в разработке (заглушка).")


@dp.message(F.text == BTN_INFO)
async def handle_info(message: Message):
    await message.answer("Раздел «Информация» в разработке (заглушка).")


@dp.message(F.text == BTN_ADVERTISE)
async def handle_advertise(message: Message):
    await message.answer("Раздел «Рекламировать» в разработке (заглушка).")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
