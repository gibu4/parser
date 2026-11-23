"""Бизнес без сайта из OpenStreetMap через Overpass API.

Ищем точки в радиусе RADIUS_KM вокруг CENTER, у которых не заполнены теги
website / contact:website / url. Данные бесплатные (ODbL), ключи не нужны.
"""

from __future__ import annotations

import math
import time
import urllib.parse

import requests

from config import CENTER, LEAD_FILTERS, MAX_RESULTS, RADIUS_KM
from . import Lead

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
HEADERS = {"User-Agent": "lead-finder/1.0 (personal use)"}
TIMEOUT = 90

# OSM открыт напрямую; локальный SOCKS-прокси из переменных окружения его ломает,
# поэтому для этих запросов прокси не используем (в Actions прокси нет).
_SESSION = requests.Session()
_SESSION.trust_env = False

CATEGORY_RU = {
    "cafe": "кафе",
    "restaurant": "ресторан",
    "fast_food": "фастфуд",
    "bar": "бар",
    "pub": "паб",
    "dentist": "стоматология",
    "car_wash": "автомойка",
    "veterinary": "ветклиника",
    "beauty": "салон красоты",
    "hairdresser": "парикмахерская",
    "florist": "цветочный",
    "optician": "оптика",
    "travel_agency": "турагентство",
    "car_repair": "автосервис",
    "laundry": "прачечная",
    "dry_cleaning": "химчистка",
    "lawyer": "юрист",
    "estate_agent": "риэлтор",
    "insurance": "страховщик",
    "accountant": "бухгалтер",
    "employment_agency": "кадровое агентство",
    "company": "компания",
    "it": "IT-компания",
    "fitness_centre": "фитнес",
}


def _bbox() -> tuple[float, float, float, float]:
    """Прямоугольник вокруг CENTER радиусом RADIUS_KM: (юг, запад, север, восток)."""
    lat, lon = CENTER
    dlat = RADIUS_KM / 111.32
    dlon = RADIUS_KM / (111.32 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def _query() -> str:
    south, west, north, east = _bbox()
    area = f"({south:.5f},{west:.5f},{north:.5f},{east:.5f})"
    clauses = [
        f'nwr["{key}"="{value}"]["name"][!"website"][!"contact:website"][!"url"]{area};'
        for key, values in LEAD_FILTERS.items()
        for value in values.split("|")
    ]
    return (
        "[out:json][timeout:120];\n(\n  "
        + "\n  ".join(clauses)
        + f"\n);\nout tags center {MAX_RESULTS};"
    )


def _overpass(query: str) -> dict:
    """Публичный Overpass бывает перегружен (502) — пробуем ещё раз с паузой."""
    last_error: Exception | None = None
    for attempt in range(2):
        for url in OVERPASS_URLS:
            try:
                response = _SESSION.post(
                    url, data={"data": query}, headers=HEADERS, timeout=TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"overpass: {url} недоступен ({exc}), пробую дальше")
                last_error = exc
        if attempt == 0:
            time.sleep(15)
    raise RuntimeError(f"Overpass недоступен: {last_error}")


def _contact(tags: dict) -> str:
    for key in ("phone", "contact:phone", "contact:telegram", "contact:vk", "contact:instagram"):
        value = (tags.get(key) or "").strip()
        if value:
            return value
    return ""


def fetch() -> list[Lead]:
    data = _overpass(_query())

    leads: list[Lead] = []
    for element in data.get("elements", []):
        tags = element.get("tags") or {}
        name = (tags.get("name") or "").strip()
        contact = _contact(tags)
        if not name or not contact:
            continue

        kind = (
            tags.get("amenity")
            or tags.get("shop")
            or tags.get("office")
            or tags.get("leisure")
            or ""
        )
        address = " ".join(
            part for part in (tags.get("addr:street"), tags.get("addr:housenumber")) if part
        )
        leads.append(
            Lead(
                id=f"{element['type']}/{element['id']}",
                name=name,
                category=CATEGORY_RU.get(kind, kind),
                phone=contact,
                address=address,
                map_url=f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
                search_url="https://yandex.ru/maps/?text="
                + urllib.parse.quote(f"{name} {address}".strip()),
            )
        )
    return leads
