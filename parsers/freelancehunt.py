"""Freelancehunt — официальное API v2. Работает только с токеном."""

import requests

from . import Order

API_URL = "https://api.freelancehunt.com/v2/projects"
PROJECT_URL = "https://freelancehunt.com/project/{id}.html"


def fetch() -> list[Order]:
    from config import FREELANCEHUNT_TOKEN

    if not FREELANCEHUNT_TOKEN:
        print("freelancehunt: FREELANCEHUNT_TOKEN не задан — источник пропущен")
        return []

    response = requests.get(
        API_URL,
        headers={
            "Authorization": f"Bearer {FREELANCEHUNT_TOKEN}",
            "Accept": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    orders: list[Order] = []
    for item in response.json().get("data", []):
        attributes = item.get("attributes") or {}
        title = (attributes.get("name") or "").strip()
        if not title:
            continue

        budget_info = attributes.get("budget") or {}
        amount = budget_info.get("amount")
        try:
            budget = int(float(amount)) if amount else None
        except (TypeError, ValueError):
            budget = None

        links = item.get("links") or {}
        url = (links.get("self") or {}).get("web") or PROJECT_URL.format(id=item.get("id"))

        orders.append(
            Order(
                id=f"fh:{item.get('id')}",
                source="Freelancehunt",
                title=title,
                url=url,
                description=(attributes.get("description") or "").strip(),
                budget=budget,
                # ponytail: фильтр бюджета числовой, валюту не пересчитываем —
                # показываем как есть (UAH/RUB), курс не хардкодим
                currency=(budget_info.get("currency") or "RUB").upper(),
            )
        )
    return orders
