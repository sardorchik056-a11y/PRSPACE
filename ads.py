from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router(name="ads")

BTN_ADVERTISE_TEXT = "Рекламировать"
CURRENCY = "SP"

# Подписи и минимальные суммы за задание по типам (в SP)
TASK_TYPE_LABELS = {
    "channel": "📢 Канал",
    "group": "👥 Группа",
    "post": "📝 Пост",
    "bot": "🤖 Бот",
    "reactions": "😀 Реакции",
    "advanced": "⚙️ Расширенное задание",
}

# Минимальная сумма вознаграждения за одно выполнение задания.
# Для "reactions" точная цифра не была указана — временно поставил 500 SP
# (на уровне просмотра поста), поправь при необходимости.
MIN_AMOUNTS = {
    "channel": 1000,
    "group": 1000,
    "bot": 2500,
    "post": 500,
    "reactions": 500,
    "advanced": 5000,
}

TASK_TYPE_DESCRIPTIONS = {
    "channel": "Пользователь подписывается на указанный канал.",
    "group": "Пользователь вступает в указанную группу.",
    "post": "Пользователь просматривает указанный пост.",
    "bot": "Пользователь запускает указанного бота (/start).",
    "reactions": "Пользователь ставит реакцию на указанный пост.",
    "advanced": "Вы сами описываете, что именно должен сделать пользователь.",
}


def get_user_balance(user_id: int) -> int:
    """Заглушка. Здесь будет запрос реального баланса пользователя из БД."""
    return 0


def ads_main_text(user_id: int) -> str:
    balance = get_user_balance(user_id)
    return (
        "📣 <b>Рекламировать</b>\n\n"
        "Продвигайте свои каналы, группы, ботов и посты руками других "
        "пользователей: они выполняют ваши задания, а вы платите "
        f"{CURRENCY} только за реально выполненные действия.\n\n"
        f"💰 Баланс: <b>{balance} {CURRENCY}</b>\n\n"
        "Выберите действие:"
    )


def ads_main_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📝 Создать задание", callback_data="ads:create")],
        [InlineKeyboardButton(text="📋 Мои задания", callback_data="ads:my_tasks")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="ads:stats")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def ads_create_text() -> str:
    lines = ["📝 <b>Создание задания</b>", "", "Выберите тип задания:", ""]
    for key, label in TASK_TYPE_LABELS.items():
        lines.append(f"{label} — от {MIN_AMOUNTS[key]} {CURRENCY}")
    return "\n".join(lines)


def ads_create_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=TASK_TYPE_LABELS["channel"], callback_data="ads:create:channel"),
            InlineKeyboardButton(text=TASK_TYPE_LABELS["group"], callback_data="ads:create:group"),
        ],
        [
            InlineKeyboardButton(text=TASK_TYPE_LABELS["post"], callback_data="ads:create:post"),
            InlineKeyboardButton(text=TASK_TYPE_LABELS["bot"], callback_data="ads:create:bot"),
        ],
        [
            InlineKeyboardButton(text=TASK_TYPE_LABELS["reactions"], callback_data="ads:create:reactions"),
            InlineKeyboardButton(text=TASK_TYPE_LABELS["advanced"], callback_data="ads:create:advanced"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="ads:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def ads_create_type_text(task_type: str) -> str:
    label = TASK_TYPE_LABELS.get(task_type, task_type)
    min_amount = MIN_AMOUNTS.get(task_type, 0)
    description = TASK_TYPE_DESCRIPTIONS.get(task_type, "")
    return (
        f"{label}\n\n"
        f"{description}\n\n"
        f"Минимальная сумма за выполнение: <b>{min_amount} {CURRENCY}</b>\n\n"
        "Заглушка: дальше будет ввод ссылки/данных и суммы вознаграждения."
    )


def ads_create_type_kb() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="ads:create")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == BTN_ADVERTISE_TEXT)
async def open_ads_menu(message: Message):
    await message.answer(
        ads_main_text(message.from_user.id),
        reply_markup=ads_main_kb(),
    )


@router.callback_query(F.data == "ads:create")
async def ads_create(callback: CallbackQuery):
    await callback.message.edit_text(ads_create_text(), reply_markup=ads_create_kb())
    await callback.answer()


@router.callback_query(F.data == "ads:my_tasks")
async def ads_my_tasks(callback: CallbackQuery):
    await callback.answer("Раздел «Мои задания» в разработке.", show_alert=True)


@router.callback_query(F.data == "ads:stats")
async def ads_stats(callback: CallbackQuery):
    await callback.answer("Раздел «Статистика» в разработке.", show_alert=True)


@router.callback_query(F.data == "ads:back")
async def ads_back(callback: CallbackQuery):
    await callback.message.edit_text(
        ads_main_text(callback.from_user.id),
        reply_markup=ads_main_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ads:create:"))
async def ads_create_type(callback: CallbackQuery):
    task_type = callback.data.split(":")[-1]
    await callback.message.edit_text(
        ads_create_type_text(task_type),
        reply_markup=ads_create_type_kb(),
    )
    await callback.answer()
