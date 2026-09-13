import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

import ads

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8841055640:AAE65cYHaE9XVEo2fQLwZ5kPxrR1Fncqm5Q"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(ads.router)

# --- Тексты кнопок (используем как константы, чтобы не дублировать строки) ---
BTN_TASKS = "Задания"
BTN_PROFILE = "Профиль"
BTN_STATS = "Общая статистика"
BTN_LEADERS = "Лидеры"
BTN_INFO = "Информация"
BTN_ADVERTISE = "Рекламировать"


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное reply-меню. Синий стиль (primary) + кастомные emoji."""
    keyboard = [
        [
            KeyboardButton(
                text=BTN_TASKS,
                style="primary",
                icon_custom_emoji_id="5310273663281417659",
            ),
            KeyboardButton(
                text=BTN_PROFILE,
                style="primary",
                icon_custom_emoji_id="5452085950022707790",
            ),
        ],
        [
            KeyboardButton(
                text=BTN_STATS,
                style="primary",
                icon_custom_emoji_id="5203993413346680064",
            ),
            KeyboardButton(
                text=BTN_LEADERS,
                style="primary",
                icon_custom_emoji_id="5244590801438138696",
            ),
        ],
        [
            KeyboardButton(
                text=BTN_INFO,
                style="primary",
                icon_custom_emoji_id="6100614423896918505",
            )
        ],
        [
            KeyboardButton(
                text=BTN_ADVERTISE,
                style="primary",
                icon_custom_emoji_id="5424818078833715060",
            )
        ],
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


# Обработка кнопки "Рекламировать" теперь в ads.py (router ads.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
