from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router(name="tasks")

BTN_TASKS_TEXT = "Задания"
CURRENCY = "SP"

# Временное хранилище заданий в памяти (пока нет БД).
# Каждое задание создаётся рекламодателем в разделе "Рекламировать" (ads.py)
# и должно появляться в этом списке. Пока список пуст — реальное создание
# заданий там ещё не реализовано (заглушка).
# Структура записи: {"id": int, "type": str, "title": str, "reward": int}
TASKS: list[dict] = []


def get_active_tasks() -> list[dict]:
    """Заглушка. В будущем — выборка активных заданий из БД."""
    return TASKS


def tasks_list_text(tasks: list[dict]) -> str:
    if not tasks:
        return (
            "📄 <b>Задания</b>\n\n"
            "Сейчас нет доступных заданий.\n"
            "Новые задания появляются здесь, как только рекламодатели "
            "создают их в разделе «Рекламировать». Загляните позже!"
        )
    return (
        "📄 <b>Задания</b>\n\n"
        "Выберите задание, чтобы посмотреть подробности и выполнить его. "
        f"За каждое выполненное задание вы получаете {CURRENCY}, "
        "указанные рекламодателем."
    )


def tasks_list_kb(tasks: list[dict]) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{task['title']} — {task['reward']} {CURRENCY}",
                callback_data=f"task:open:{task['id']}",
            )
        ]
        for task in tasks
    ]
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="task:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def task_details_text(task: dict) -> str:
    return (
        f"📄 <b>{task['title']}</b>\n\n"
        f"Награда: <b>{task['reward']} {CURRENCY}</b>\n\n"
        "Заглушка: здесь будет описание задания и проверка его выполнения."
    )


def task_details_kb(task: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="✅ Я выполнил", callback_data=f"task:complete:{task['id']}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="task:refresh")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def find_task(task_id: str) -> dict | None:
    return next((t for t in TASKS if str(t["id"]) == task_id), None)


@router.message(F.text == BTN_TASKS_TEXT)
async def open_tasks_menu(message: Message):
    tasks = get_active_tasks()
    await message.answer(tasks_list_text(tasks), reply_markup=tasks_list_kb(tasks))


@router.callback_query(F.data == "task:refresh")
async def refresh_tasks(callback: CallbackQuery):
    tasks = get_active_tasks()
    await callback.message.edit_text(tasks_list_text(tasks), reply_markup=tasks_list_kb(tasks))
    await callback.answer()


@router.callback_query(F.data.startswith("task:open:"))
async def open_task(callback: CallbackQuery):
    task_id = callback.data.split(":")[-1]
    task = find_task(task_id)
    if not task:
        await callback.answer("Задание больше недоступно.", show_alert=True)
        return
    await callback.message.edit_text(task_details_text(task), reply_markup=task_details_kb(task))
    await callback.answer()


@router.callback_query(F.data.startswith("task:complete:"))
async def complete_task(callback: CallbackQuery):
    task_id = callback.data.split(":")[-1]
    task = find_task(task_id)
    if not task:
        await callback.answer("Задание больше недоступно.", show_alert=True)
        return
    # Заглушка: здесь будет реальная проверка выполнения (подписка/просмотр/
    # реакция и т.д.) и начисление task["reward"] SP на баланс пользователя
    # через БД (см. get_user_balance в ads.py — потребуется set/add-функция).
    await callback.answer(
        f"Заглушка: после проверки вы получите {task['reward']} {CURRENCY}.",
        show_alert=True,
    )
