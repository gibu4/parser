"""Настройки парсера.

Токен и chat_id читаются из переменных окружения (так их получают GitHub Actions
из секретов репозитория). Если переменных нет, берутся значения по умолчанию —
их удобно подставить для локального теста.
"""

import os
from pathlib import Path


def _load_env_file(path: Path = Path(__file__).with_name(".env")) -> None:
    """Локальный .env (не коммитится). Значения из окружения важнее файла."""
    try:
        content = path.read_text("utf-8")
    except FileNotFoundError:
        return
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file()

# ВАЖНО: "@aihelperformebotbot" — это username бота, а не токен.
# Настоящий токен вида "123456789:AAE...zzz" выдаёт @BotFather.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "@aihelperformebotbot")
CHAT_ID = os.getenv("CHAT_ID", "1846569504")

# Freelancehunt отдаёт заказы только по API-токену. Без него источник пропускается.
FREELANCEHUNT_TOKEN = os.getenv("FREELANCEHUNT_TOKEN", "")

# Бюджетный фильтр, руб.
MIN_BUDGET = 400
MAX_BUDGET = 30000

# Заказ проходит, если в заголовке/описании есть хотя бы одно слово
# (совпадение с начала слова, регистр не важен).
KEYWORDS = [
    "создать сайт",
    "лендинг",
    "телеграм-бот",
    "парсинг",
    "игра",
    "Unity",
    "Python",
    "сайт",
    "верстка",
    "бот",
]

# Любое из этих слов в тексте — заказ отбрасывается.
STOP_WORDS = [
    "бесплатно",
    "студент",
    "тестовое за копейки",
    "без оплаты",
    "для портфолио",
    "недорого",
    "обучение",
]
