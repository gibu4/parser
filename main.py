"""Собирает заказы с Freelance.ru и публичных Telegram-каналов, фильтрует и шлёт в Telegram."""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
from pathlib import Path

import requests

from config import CHAT_ID, KEYWORDS, MAX_BUDGET, MIN_BUDGET, STOP_WORDS, TELEGRAM_BOT_TOKEN
from parsers import Order, freelance_ru, telegram

log = logging.getLogger("parser")

BASE_DIR = Path(__file__).resolve().parent
SEEN_FILE = BASE_DIR / "seen_ids.json"
SEEN_LIMIT = 2000
PARSERS = (freelance_ru, telegram)
CURRENCY_SIGNS = {"RUB": "₽", "UAH": "₴", "USD": "$", "EUR": "€"}
# Настоящий токен BotFather: "123456789:AAE...". Username сюда не подходит.
TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")


def _word_re(word: str) -> re.Pattern[str]:
    # Совпадение с начала слова: «бот» не должен ловить «работа», «сайт» — «посайти».
    return re.compile(r"(?<![а-яёa-z])" + re.escape(word), re.IGNORECASE)


_KEYWORD_RES = [_word_re(word) for word in KEYWORDS]
_STOP_RES = [_word_re(word) for word in STOP_WORDS]


def matches(order: Order) -> bool:
    """Ключевое слово есть, стоп-слов нет, бюджет в диапазоне (неизвестный — пропускаем)."""
    text = f"{order.title}\n{order.description}"
    if not any(pattern.search(text) for pattern in _KEYWORD_RES):
        return False
    if any(pattern.search(text) for pattern in _STOP_RES):
        return False
    if order.budget is not None and not MIN_BUDGET <= order.budget <= MAX_BUDGET:
        return False
    return True


def format_message(order: Order) -> str:
    if order.budget is None:
        budget = "не указан"
    else:
        sign = CURRENCY_SIGNS.get(order.currency, order.currency)
        budget = f"{order.budget:,}".replace(",", " ") + f" {sign}"

    description = re.sub(r"\s+", " ", order.description).strip()
    if len(description) > 400:
        description = description[:400].rsplit(" ", 1)[0] + "…"

    parts = [
        f"<b>🆕 {html.escape(order.source)}</b>",
        f"<b>{html.escape(order.title)}</b>",
        f"💰 Бюджет: {budget}",
    ]
    if description:
        parts.append(html.escape(description))
    parts.append(f'🔗 <a href="{html.escape(order.url, quote=True)}">Открыть заказ</a>')
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
    sent = 0

    for module in PARSERS:
        try:
            orders = module.fetch()
        except Exception as exc:
            log.warning("%s: %s", module.__name__, exc)
            continue

        log.info("%s: получено %d заказов", module.__name__, len(orders))
        for order in orders:
            if order.id in seen_set or not matches(order):
                continue

            if dry_run:
                budget = order.budget if order.budget is not None else "не указан"
                print(f"[{order.source}] {order.title} — {budget} — {order.url}")
                seen_set.add(order.id)
                sent += 1
                continue

            try:
                send(format_message(order))
            except Exception:
                # не помечаем как отправленное, чтобы повторить на следующем запуске
                log.exception("Telegram: не удалось отправить %s", order.id)
                continue

            seen.append(order.id)
            seen_set.add(order.id)
            sent += 1
            log.info("Отправлено: %s — %s", order.source, order.title)

    if not dry_run:
        save_seen(seen)
    log.info("Новых заказов: %d", sent)
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Парсер фриланс-заказов")
    parser.add_argument(
        "--dry-run", action="store_true", help="показать найденное, ничего не отправляя"
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
