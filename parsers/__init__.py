"""Модель лида — бизнеса без сайта."""

from dataclasses import dataclass


@dataclass
class Lead:
    id: str
    name: str
    category: str
    phone: str
    address: str
    map_url: str
    search_url: str
