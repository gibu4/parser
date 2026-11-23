"""Быстрая проверка: python test_leads.py"""

import pathlib

import main
from parsers import Lead


def lead(**kwargs) -> Lead:
    base = dict(
        id="node/1",
        name="Кафе <Ромашка> & Ко",
        category="кафе",
        phone="+7 999 123-45-67",
        address="ул. Ленина, 1",
        map_url="https://www.openstreetmap.org/node/1",
        search_url="https://yandex.ru/maps/?text=test",
    )
    base.update(kwargs)
    return Lead(**base)


text = main.format_digest([lead(), lead(id="node/2", name="Бар", phone="", address="")])
assert "&lt;Ромашка&gt; &amp; Ко" in text  # HTML экранирован
assert "<Ромашка>" not in text
assert "1 новых" in text or "2 новых" in text
assert "https://www.openstreetmap.org/node/1" in text
assert "+7 999 123-45-67" in text

seen_file = pathlib.Path(main.BASE_DIR) / ".seen_test.json"
main.SEEN_FILE = seen_file
assert main.load_seen() == []
main.save_seen(["node/1", "node/2"])
assert main.load_seen() == ["node/1", "node/2"]
seen_file.unlink()

print("OK")
