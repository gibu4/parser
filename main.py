"""Ищет местный бизнес без сайта в OpenStreetMap и присылает список в Telegram."""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
from pathlib import Path

import requests

from config import AREA_NAME, CHAT_ID, MAX_LEADS, TELEGRAM_BOT_TOKEN
from parsers import Lead, osm

log = logging.getLogger("leads")

BASE_DIR = Path(__file__).resolve().parent
SEEN_FILE = BASE_DIR / "seen_ids.json"
SEEN_LIMIT = 5000
# Настоящий токен BotFather: "123456789:AAE...". Username сюда не подходит.
TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")


def format_digest(leads: list[Lead]) -> str:
    parts = [f"🏪 <b>Клиенты без сайта</b> — {html.escape(AREA_NAME)}, {len(leads)} новых"]
    for number, lead in enumerate(leads, 1):
        lines = [f"<b>{number}. {html.escape(lead.name)}</b> — {html.escape(lead.category)}"]
        details = []
        if lead.phone:
            icon = "🔗" if lead.phone.startswith("http") else "📞"
            details.append(f"{icon} {html.escape(lead.phone)}")
        if lead.address:
            details.append(f"📍 {html.escape(lead.address)}")
        if details:
            lines.append(" · ".join(details))
        links = [f'<a href="{html.escape(lead.map_url, quote=True)}">Карта</a>']
        if lead.search_url:
            links.append(f'<a href="{html.escape(lead.search_url, quote=True)}">Яндекс</a>')
        lines.append(" · ".join(links))
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def send(text: str) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()


def load_seen() -> list[str]:
    try:
        data = json.loads(SEEN_FILE.read_text("utf-8"))
        return [str(item) for item in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_seen(seen: list[str]) -> None:
    SEEN_FILE.write_text(
        json.dumps(seen[-SEEN_LIMIT:], ensure_ascii=False, indent=2), "utf-8"
    )


def run(dry_run: bool = False) -> int:
    seen = load_seen()
    seen_set = set(seen)
    leads = osm.fetch()
    log.info("найдено лидов без сайта: %d", len(leads))

    fresh = [lead for lead in leads if lead.id not in seen_set][:MAX_LEADS]
    if not fresh:
        log.info("новых лидов нет")
        return 0

    message = format_digest(fresh)
    if dry_run:
        print(re.sub(r"<[^>]+>", "", message))
        return len(fresh)

    send(message)
    save_seen(seen + [lead.id for lead in fresh])
    log.info("отправлено лидов: %d", len(fresh))
    return len(fresh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Поиск бизнеса без сайта")
    parser.add_argument(
        "--dry-run", action="store_true", help="показать список, ничего не отправляя"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.dry_run and not TOKEN_RE.match(TELEGRAM_BOT_TOKEN):
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN не похож на токен. "
            "@aihelperformebotbot — это username бота; токен выдаёт @BotFather "
            "(вида 123456789:AAE...). Задайте его в переменной окружения или секрете GitHub."
        )

    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
