"""Kwork — проекты из HTML-страницы. Данные лежат в window.stateData (JSON в <script>),
поэтому BeautifulSoup ищет скрипт, а заказы берутся из готового JSON, а не из вёрстки.
"""

import html
import json
import re

import requests
from bs4 import BeautifulSoup

from . import Order

URL = "https://kwork.ru/projects"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
_STATE_RE = re.compile(r"window\.stateData\s*=\s*")
MAX_DESCRIPTION = 600


def _state(html_text: str) -> dict:
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script"):
        text = script.string or ""
        match = _STATE_RE.search(text)
        if match:
            data, _ = json.JSONDecoder().raw_decode(text[match.end():].lstrip())
            return data
    return {}


def _price(item: dict) -> int | None:
    for key in ("priceLimit", "possiblePriceLimit"):
        try:
            amount = int(float(item.get(key) or 0))
        except (TypeError, ValueError):
            continue
        if amount > 0:
            return amount
    return None


def fetch() -> list[Order]:
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    wants = ((_state(response.text).get("wantsListData") or {}).get("wants")) or []
    orders: list[Order] = []
    for item in wants:
        title = html.unescape(item.get("name") or "").strip()
        if not title or not item.get("id"):
            continue
        description = html.unescape(item.get("description") or "").strip()
        orders.append(
            Order(
                id=f"kwork:{item['id']}",
                source="Kwork",
                title=title,
                url=f"https://kwork.ru/projects/{item['id']}",
                description=description[:MAX_DESCRIPTION],
                budget=_price(item),
            )
        )
    return orders
