"""Freelance.ru — бесплатная лента заданий (HTML)."""

import re

import requests
from bs4 import BeautifulSoup

from . import Order, extract_budget

URL = "https://freelance.ru/projects/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
_TASK_ID = re.compile(r"/task/view/(\d+)")


def fetch() -> list[Order]:
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    orders: list[Order] = []
    for card in soup.select("article.task-card"):
        link = card.select_one("a.task-card__title-link")
        if link is None or not link.get("href"):
            continue

        url = link["href"]
        if url.startswith("/"):
            url = "https://freelance.ru" + url
        match = _TASK_ID.search(url)
        if not match:
            continue

        title = link.get_text(" ", strip=True)
        if not title:
            continue

        description = card.select_one(".task-card__desc")
        budget = card.select_one(".task-card__budget")
        orders.append(
            Order(
                id=f"fr:{match.group(1)}",
                source="Freelance.ru",
                title=title,
                url=url,
                description=description.get_text(" ", strip=True) if description else "",
                budget=extract_budget(budget.get_text(" ", strip=True)) if budget else None,
            )
        )
    return orders
