"""FL.ru — заказы из RSS-ленты."""

import feedparser
import requests
from bs4 import BeautifulSoup

from . import Order, extract_budget

RSS_URL = "https://www.fl.ru/rss/all.xml"
# Скачиваем сами: urllib внутри feedparser не берёт certifi и падает на SSL.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}


def _text(value: str) -> str:
    """В RSS описания приходят с HTML-тегами и entities."""
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def fetch() -> list[Order]:
    response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"RSS недоступен: {feed.bozo_exception}")

    orders: list[Order] = []
    for entry in feed.entries:
        url = entry.get("link", "")
        title = _text(entry.get("title", ""))
        if not url or not title:
            continue
        description = _text(entry.get("summary", ""))
        orders.append(
            Order(
                id=f"fl:{entry.get('id') or url}",
                source="FL.ru",
                title=title,
                url=url,
                description=description,
                budget=extract_budget(title, description),
            )
        )
    return orders
