from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import task
import wallet

router = Router(name="ads")

BTN_ADVERTISE_TEXT = "Рекламировать"
CURRENCY = wallet.CURRENCY

TASK_TYPE_LABELS = {
    "channel": "📢 Канал",
    "group": "👥 Группа",
    "post": "📝 Пост",
    "bot": "🤖 Бот",
    "reactions": "😀 Реакции",
    "advanced": "⚙️ Расширенное задание",
}

# Минимальная сумма вознаграждения за одно выполнение (в SP).
# Для "reactions" точная цифра не была указана — временно поставил 500
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

# Для этих типов уже реализован полный сбор данных (ссылка/сумма/кол-во).
# Остальные (bot/post/reactions/advanced) пока показывают только заглушку.
CONFIGURABLE_TYPES = {"channel", "group"}

QUANTITY_OPTIONS = [5, 10, 25, 50, 125, 250]

CANCEL_TEXT = "✖️ Отменить"
CANCEL_CALLBACK = "ads:cancel"


class CreateTaskStates(StatesGroup):
    waiting_link = State()
    waiting_amount = State()
    waiting_quantity = State()
    waiting_custom_quantity = State()


def cancel_kb() -> InlineKeyboardMarkup:
    """Клавиатура с одной кнопкой отмены — используется на каждом шаге
    создания задания, где бот ждёт текстовый ввод."""
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=CANCEL_TEXT, callback_data=CANCEL_CALLBACK)]])


def ads_main_text(user_id: int) -> str:
    balance = wallet.get_balance(user_id)
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
        "Заглушка: этот тип задания пока в разработке."
    )


def ads_create_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="ads:create")]])


def parse_chat_ref(text: str) -> str | None:
    """Достаёт @username из ссылки/юзернейма. Инвайт-ссылки на приватные
    чаты (t.me/+hash или t.me/joinchat/...) пока не поддерживаются — бот
    не может их разрешить, не будучи уже добавленным в чат."""
    text = text.strip()
    if not text:
        return None
    if "t.me/" in text:
        tail = text.split("t.me/")[-1].split("?")[0].split("/")[0]
        if not tail or tail.startswith("+") or tail.lower() == "joinchat":
            return None
        return f"@{tail}"
    if text.startswith("@"):
        return text
    return f"@{text}"


def affordable_options(balance: int, amount: int) -> list[int]:
    return [q for q in QUANTITY_OPTIONS if amount * q <= balance]


def quantity_kb(balance: int, amount: int) -> InlineKeyboardMarkup:
    options = affordable_options(balance, amount)
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for qty in options:
        row.append(InlineKeyboardButton(text=str(qty), callback_data=f"ads:qty:{qty}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="ads:qty:custom")])
    rows.append([InlineKeyboardButton(text=CANCEL_TEXT, callback_data=CANCEL_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def finalize_task(user_id: int, quantity: int, state: FSMContext) -> tuple[bool, str]:
    """Создаёт задание, списывает баланс. Возвращает (успех, текст для юзера)."""
    data = await state.get_data()
    task_type = data["task_type"]
    amount = data["amount"]
    chat_id = data.get("chat_id")
    chat_title = data.get("chat_title", "")
    chat_link = data.get("chat_link")

    total_cost = amount * quantity
    if not wallet.subtract_balance(user_id, total_cost):
        balance = wallet.get_balance(user_id)
        await state.clear()
        return False, (
            f"Недостаточно баланса: нужно {total_cost} {CURRENCY}, "
            f"у вас {balance} {CURRENCY}.\n"
            "Создание задания отменено. Начните заново через «Создать задание»."
        )

    label = TASK_TYPE_LABELS[task_type]
    title = f"{label}: {chat_title}"

    task.add_task(
        type_=task_type,
        title=title,
        reward=amount,
        quantity=quantity,
        creator_id=user_id,
        chat_id=chat_id,
        link=chat_link,
    )

    await state.clear()

    text = (
        "✅ Задание создано и опубликовано в разделе «Задания»!\n\n"
        f"{title}\n"
        f"Награда: {amount} {CURRENCY} за выполнение\n"
        f"Количество: {quantity}\n"
        f"Списано: {total_cost} {CURRENCY}\n"
        f"Остаток баланса: {wallet.get_balance(user_id)} {CURRENCY}"
    )
    return True, text


@router.message(F.text == BTN_ADVERTISE_TEXT)
async def open_ads_menu(message: Message):
    await message.answer(ads_main_text(message.from_user.id), reply_markup=ads_main_kb())


@router.callback_query(F.data == "ads:create")
async def ads_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(ads_create_text(), reply_markup=ads_create_kb())
    await callback.answer()


@router.callback_query(F.data == "ads:my_tasks")
async def ads_my_tasks(callback: CallbackQuery):
    await callback.answer("Раздел «Мои задания» в разработке.", show_alert=True)


@router.callback_query(F.data == "ads:stats")
async def ads_stats(callback: CallbackQuery):
    await callback.answer("Раздел «Статистика» в разработке.", show_alert=True)


@router.callback_query(F.data == "ads:back")
async def ads_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(ads_main_text(callback.from_user.id), reply_markup=ads_main_kb())
    await callback.answer()


@router.callback_query(F.data == CANCEL_CALLBACK)
async def ads_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(ads_main_text(callback.from_user.id), reply_markup=ads_main_kb())
    await callback.answer("Отменено.")


@router.callback_query(F.data.startswith("ads:create:"))
async def ads_create_type(callback: CallbackQuery, state: FSMContext):
    task_type = callback.data.split(":")[-1]

    if task_type in CONFIGURABLE_TYPES:
        await state.set_state(CreateTaskStates.waiting_link)
        await state.update_data(task_type=task_type)
        label = TASK_TYPE_LABELS[task_type]
        await callback.message.edit_text(
            f"{label}\n\n"
            "Отправьте ссылку или юзернейм (@username или https://t.me/username).\n\n"
            "⚠️ Бот должен быть добавлен туда администратором — иначе он не "
            "сможет проверять подписки/вступления.",
            reply_markup=cancel_kb(),
        )
        await callback.answer()
        return

    # Остальные типы (bot/post/reactions/advanced) пока без сбора данных.
    await callback.message.edit_text(ads_create_type_text(task_type), reply_markup=ads_create_type_kb())
    await callback.answer()


@router.message(CreateTaskStates.waiting_link)
async def process_link(message: Message, state: FSMContext, bot: Bot):
    # Ждём ссылку только один раз: любая ошибка сразу отменяет создание
    # задания вместо повторного запроса.
    chat_ref = parse_chat_ref(message.text or "")
    if not chat_ref:
        await state.clear()
        await message.answer(
            "Это не похоже на ссылку или юзернейм канала/группы.\n"
            "Создание задания отменено. Начните заново через «Создать задание».",
            reply_markup=ads_main_kb(),
        )
        return

    try:
        chat = await bot.get_chat(chat_ref)
    except Exception:
        await state.clear()
        await message.answer(
            "Не удалось найти такой канал/группу.\n"
            "Создание задания отменено. Начните заново через «Создать задание».",
            reply_markup=ads_main_kb(),
        )
        return

    try:
        member = await bot.get_chat_member(chat.id, bot.id)
    except Exception:
        member = None

    if not member or member.status not in ("administrator", "creator"):
        await state.clear()
        await message.answer(
            "Бот не является администратором этого канала/группы.\n"
            "Добавьте бота в админы и создайте задание заново через "
            "«Создать задание».",
            reply_markup=ads_main_kb(),
        )
        return

    data = await state.get_data()
    task_type = data["task_type"]
    min_amount = MIN_AMOUNTS[task_type]

    chat_link = f"https://t.me/{chat.username}" if chat.username else None
    await state.update_data(chat_id=chat.id, chat_title=chat.title or chat_ref, chat_link=chat_link)
    await state.set_state(CreateTaskStates.waiting_amount)

    await message.answer(
        f"Отлично, бот — админ в «{chat.title or chat_ref}».\n\n"
        f"Теперь укажите сумму оплаты за одно выполнение "
        f"(минимум {min_amount} {CURRENCY}):",
        reply_markup=cancel_kb(),
    )


@router.message(CreateTaskStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    # Ждём сумму только один раз: ошибка сразу отменяет создание задания.
    data = await state.get_data()
    task_type = data["task_type"]
    min_amount = MIN_AMOUNTS[task_type]

    text = (message.text or "").strip()
    if not text.isdigit() or int(text) < min_amount:
        await state.clear()
        await message.answer(
            f"Нужно было ввести число не меньше {min_amount} {CURRENCY}.\n"
            "Создание задания отменено. Начните заново через «Создать задание».",
            reply_markup=ads_main_kb(),
        )
        return

    amount = int(text)
    balance = wallet.get_balance(message.from_user.id)
    await state.update_data(amount=amount)
    await state.set_state(CreateTaskStates.waiting_quantity)

    if not affordable_options(balance, amount):
        await message.answer(
            f"Сумма за одно выполнение: {amount} {CURRENCY}.\n"
            f"Ваш баланс: {balance} {CURRENCY}.\n\n"
            f"Баланса не хватает даже на {QUANTITY_OPTIONS[0]} выполнений. "
            "Введите количество вручную (столько, сколько позволяет баланс):",
            reply_markup=quantity_kb(balance, amount),
        )
        return

    await message.answer(
        f"Сумма за одно выполнение: {amount} {CURRENCY}.\n"
        f"Ваш баланс: {balance} {CURRENCY}.\n\n"
        "Сколько выполнений нужно?",
        reply_markup=quantity_kb(balance, amount),
    )


@router.callback_query(CreateTaskStates.waiting_quantity, F.data.startswith("ads:qty:"))
async def process_quantity_choice(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]

    if value == "custom":
        await state.set_state(CreateTaskStates.waiting_custom_quantity)
        await callback.message.edit_text(
            "Введите количество выполнений числом:",
            reply_markup=cancel_kb(),
        )
        await callback.answer()
        return

    quantity = int(value)
    ok, text = await finalize_task(callback.from_user.id, quantity, state)
    kb = ads_main_kb()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.message(CreateTaskStates.waiting_custom_quantity)
async def process_custom_quantity(message: Message, state: FSMContext):
    # Ждём число только один раз: ошибка сразу отменяет создание задания.
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await state.clear()
        await message.answer(
            "Нужно было ввести положительное целое число.\n"
            "Создание задания отменено. Начните заново через «Создать задание».",
            reply_markup=ads_main_kb(),
        )
        return

    quantity = int(text)
    ok, result_text = await finalize_task(message.from_user.id, quantity, state)
    await message.answer(result_text, reply_markup=ads_main_kb())
