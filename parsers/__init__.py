"""Общая модель заказа и разбор денежных сумм — используется всеми парсерами."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Order:
    id: str
    source: str
    title: str
    url: str
    description: str = ""
    budget: int | None = None
    currency: str = "RUB"


# Сумма с валютой: "15 000 руб.", "30 000₽", "5000 р."
_MONEY_RE = re.compile(r"(\d[\d\s\u00a0]{2,})\s*(?:₽|руб\w*|р\.|rub)", re.IGNORECASE)


def extract_budget(*texts: str) -> int | None:
    """Первая сумма с валютой в тексте: «Бюджет: 15 000 руб.» -> 15000."""
    for text in texts:
        for match in _MONEY_RE.finditer(text or ""):
            value = int(re.sub(r"\D", "", match.group(1)))
            if value >= 100:  # отсекаем «5 руб.» и прочий мусор
                return value
    return None
