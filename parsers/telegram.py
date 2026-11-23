"""Заказы из публичных Telegram-каналов через веб-превью t.me/s/<канал>.

Каналы задаются списком ORDER_CHANNELS в config.py — можно добавлять свои.
"""

import re

import requests
from bs4 import BeautifulSoup

from . import Order, extract_budget

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
MAX_TITLE = 120


def _clean_title(line: str) -> str:
    # «📌 Бот парсер…» -> «Бот парсер…»: убираем эмодзи/значки в начале
    return re.sub(r"^[^\w]+", "", line).strip()[:MAX_TITLE]


def _fetch_channel(channel: str) -> list[Order]:
    response = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    orders: list[Order] = []
    for message in soup.select(".tgme_widget_message"):
        post = message.get("data-post") or ""
        text_el = message.select_one(".tgme_widget_message_text")
        if not post or text_el is None:
            continue

        text = text_el.get_text("\n", strip=True)
        lines = [_clean_title(line) for line in text.splitlines()]
        lines = [line for line in lines if line]  # «📌» и прочие строки-значки не нужны
        if not lines:
            continue

        title = lines[0]
        description = " ".join(lines[1:]) if len(lines) > 1 else text
        orders.append(
            Order(
                id=f"tg:{post}",
                source=f"Telegram @{channel}",
                title=title,
                url=f"https://t.me/{post}",
                description=description,
                budget=extract_budget(text),
            )
        )
    return orders


def fetch() -> list[Order]:
    from config import ORDER_CHANNELS

    orders: list[Order] = []
    for channel in ORDER_CHANNELS:
        try:
            orders.extend(_fetch_channel(channel))
        except Exception as exc:
            print(f"telegram: @{channel}: {exc}")
    return orders
