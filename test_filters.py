"""Быстрая проверка фильтров: python test_filters.py"""

from main import matches
from parsers import Order, extract_budget


def order(**kwargs) -> Order:
    base = dict(id="x", source="test", title="", url="https://example.com")
    base.update(kwargs)
    return Order(**base)


assert extract_budget("Бюджет: 15 000 руб.") == 15000
assert extract_budget("до 30 000 ₽") == 30000
assert extract_budget("без бюджета") is None

assert matches(order(title="Создать сайт на Python", budget=5000))
assert not matches(order(title="Работа в офисе", budget=5000))  # «бот» не ловит «работа»
assert not matches(order(title="Сайт за 50 000 руб.", budget=50000))  # дороже лимита
assert not matches(order(title="Лендинг для портфолио", budget=5000))  # стоп-слово
assert matches(order(title="Нужен телеграм-бот"))  # бюджет не указан — пропускаем

print("OK")
