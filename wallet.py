"""
Временное хранилище баланса пользователей в памяти.

Это заглушка вместо реальной БД: при перезапуске бота все балансы
обнуляются (точнее, сбрасываются к STARTING_BALANCE). Вынесено в отдельный
модуль, чтобы избежать циклического импорта между ads.py и task.py —
оба обращаются сюда за начислением/списанием SP.
"""

CURRENCY = "SP"

# Демо-баланс для новых пользователей, чтобы можно было тестировать
# создание заданий с разным количеством выполнений. Заменить на 0
# (или на реальный баланс из БД), когда появится персистентное хранилище.
STARTING_BALANCE = 50_000

_balances: dict[int, int] = {}


def get_balance(user_id: int) -> int:
    return _balances.setdefault(user_id, STARTING_BALANCE)


def add_balance(user_id: int, amount: int) -> int:
    _balances[user_id] = get_balance(user_id) + amount
    return _balances[user_id]


def subtract_balance(user_id: int, amount: int) -> bool:
    """Списывает amount, если хватает баланса. Возвращает True/False."""
    balance = get_balance(user_id)
    if balance < amount:
        return False
    _balances[user_id] = balance - amount
    return True
