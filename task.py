import itertools

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import wallet

router = Router(name="tasks")

BTN_TASKS_TEXT = "Задания"
CURRENCY = wallet.CURRENCY

# Хранилище заданий в памяти (пока нет БД).
# Задания создаются рекламодателем в ads.py через add_task().
# Структура записи:
# {
#   "id": int, "type": str, "title": str, "reward": int,
#   "quantity": int, "remaining": int, "creator_id": int,
#   "chat_id": int | None, "completed_by": set[int],
# }
TASKS: list[dict] = []

_id_counter = itertools.count(1)

# Типы заданий, для которых уже реализована реальная проверка выполнения
# (проверка подписки/членства через бота-админа в чате).
VERIFIABLE_TYPES = {"channel", "group"}


def add_task(*, type_: str, title: str, reward: int, quantity: int, creator_id: int, chat_id: int | None = None, link: str | None = None) -> dict:
    new_task = {
        "id": next(_id_counter),
        "type": type_,
        "title": title,
        "reward": reward,
        "quantity": quantity,
        "remaining": quantity,
        "creator_id": creator_id,
        "chat_id": chat_id,
        "link": link,
        "completed_by": set(),
    }
    TASKS.append(new_task)
    return new_task


def remove_task(task_id: int) -> None:
    TASKS[:] = [t for t in TASKS if t["id"] != task_id]


def find_task(task_id: str) -> dict | None:
    return next((t for t in TASKS if str(t["id"]) == task_id), None)


def get_active_tasks() -> list[dict]:
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
                text=f"{t['title']} — {t['reward']} {CURRENCY}",
                callback_data=f"task:open:{t['id']}",
            )
        ]
        for t in tasks
    ]
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="task:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def task_details_text(t: dict) -> str:
    left = t["quantity"] - t["remaining"]
    link_line = f"\nСсылка: {t['link']}\n" if t.get("link") else "\n"
    return (
        f"📄 <b>{t['title']}</b>\n\n"
        f"Награда: <b>{t['reward']} {CURRENCY}</b>\n"
        f"Выполнено: {left}/{t['quantity']}"
        f"{link_line}\n"
        "Нажмите «Я выполнил», когда подпишетесь/вступите — бот проверит "
        "это автоматически."
    )


def task_details_kb(t: dict) -> InlineKeyboardMarkup:
    keyboard = []
    if t.get("link"):
        join_label = "🔗 Подписаться" if t["type"] == "channel" else "🔗 Вступить"
        keyboard.append([InlineKeyboardButton(text=join_label, url=t["link"])])
    keyboard.append([InlineKeyboardButton(text="✅ Я выполнил", callback_data=f"task:complete:{t['id']}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="task:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
    t = find_task(task_id)
    if not t:
        await callback.answer("Задание больше недоступно.", show_alert=True)
        return
    await callback.message.edit_text(task_details_text(t), reply_markup=task_details_kb(t))
    await callback.answer()


@router.callback_query(F.data.startswith("task:complete:"))
async def complete_task(callback: CallbackQuery, bot: Bot):
    task_id = callback.data.split(":")[-1]
    t = find_task(task_id)
    if not t:
        await callback.answer("Задание больше недоступно.", show_alert=True)
        return

    user_id = callback.from_user.id

    if user_id in t["completed_by"]:
        await callback.answer("Вы уже выполнили это задание.", show_alert=True)
        return

    if t["type"] in VERIFIABLE_TYPES and t.get("chat_id") is not None:
        try:
            member = await bot.get_chat_member(t["chat_id"], user_id)
        except Exception:
            await callback.answer(
                "Не удалось проверить выполнение. Попробуйте ещё раз чуть позже.",
                show_alert=True,
            )
            return

        if member.status not in ("member", "administrator", "creator"):
            action = "подпишитесь на канал" if t["type"] == "channel" else "вступите в группу"
            await callback.answer(f"Сначала {action}, затем нажмите «Я выполнил».", show_alert=True)
            return
    else:
        # Для bot/post/reactions/advanced проверка выполнения ещё не
        # реализована — заглушка, засчитываем сразу.
        pass

    wallet.add_balance(user_id, t["reward"])
    t["completed_by"].add(user_id)
    t["remaining"] -= 1

    await callback.answer(f"✅ Задание выполнено! Вам начислено {t['reward']} {CURRENCY}.", show_alert=True)

    if t["remaining"] <= 0:
        remove_task(t["id"])
        try:
            await bot.send_message(
                t["creator_id"],
                f"🎉 Ваше задание «{t['title']}» выполнено полностью: "
                f"{t['quantity']}/{t['quantity']} пользователей.",
            )
        except Exception:
            pass

    tasks = get_active_tasks()
    await callback.message.edit_text(tasks_list_text(tasks), reply_markup=tasks_list_kb(tasks))
