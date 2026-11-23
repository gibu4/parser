"""Настройки поиска клиентов без сайта.

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

# Точка поиска (широта, долгота) и радиус в километрах.
# Поставьте координаты своего района — взять можно из Яндекс.Карт (правый клик →
# «Что здесь?»). 3 км — это примерно 20–30 минут пешком в каждую сторону.
CENTER = (55.7558, 37.6173)  # центр Москвы
RADIUS_KM = 3
AREA_NAME = "центр Москвы"  # подпись в сообщении

# Категории бизнеса: ключ OSM -> допустимые значения через |.
LEAD_FILTERS = {
    "amenity": "cafe|restaurant|fast_food|bar|pub|dentist|car_wash|veterinary",
    "shop": "beauty|hairdresser|florist|optician|travel_agency|car_repair|laundry|dry_cleaning",
    "office": "lawyer|estate_agent|insurance|accountant|employment_agency|company|it",
    "leisure": "fitness_centre",
}

# Сколько новых лидов присылать за один запуск (одним сообщением).
MAX_LEADS = 10

# Максимум точек, которые запрашиваем у Overpass за раз.
MAX_RESULTS = 300
