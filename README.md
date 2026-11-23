# Парсер фриланс-заказов → Telegram

Ищет заказы на FL.ru, Kwork и Freelancehunt, фильтрует по бюджету и ключевым словам
и отправляет новые подходящие заказы в Telegram. Запускается на GitHub Actions
каждые 30 минут.

## Что внутри

```
parser/
├── main.py                     # сбор, фильтры, отправка, защита от дублей
├── config.py                   # токены (os.getenv + .env), слова, бюджет
├── .env                        # локальные токены, в git не попадает
├── requirements.txt
├── test_filters.py             # проверка фильтров: python test_filters.py
├── parsers/
│   ├── __init__.py             # модель Order + разбор сумм
│   ├── fl.py                   # FL.ru — RSS (feedparser)
│   ├── kwork.py                # Kwork — HTML (BeautifulSoup)
│   └── freelancehunt.py        # Freelancehunt — API v2 (нужен токен)
├── seen_ids.json               # создаётся автоматически: ID уже отправленных заказов
└── .github/workflows/parser.yml
```

## Локальный запуск

```bash
cd parser
pip install -r requirements.txt
python test_filters.py          # проверка фильтров, ничего не отправляет

# сухой прогон: показывает подходящие заказы, в Telegram не пишет
python main.py --dry-run

# реальная отправка (токен и chat_id уже в .env)
python main.py
```

`config.py` читает `TELEGRAM_BOT_TOKEN`, `CHAT_ID`, `FREELANCEHUNT_TOKEN` через
`os.getenv`, а перед этим подхватывает локальный `parser/.env` (он в `.gitignore`
и на GitHub не уедет). Значения из окружения имеют приоритет над `.env`, поэтому
в Actions работают секреты. Если ни `.env`, ни переменных нет — остаются значения
по умолчанию из `config.py`, где вместо токена стоит username бота: при реальной
отправке программа остановится с подсказкой.

Токен уже проверен через `getMe` (бот `@aihelperformebotbot`, id `9287774253`),
тестовое сообщение в чат `1846569504` доставлено.

## Загрузка на GitHub

Репозиторий = эта папка. Файл `.github/workflows/parser.yml` должен оказаться
в корне репозитория, иначе GitHub не увидит workflow.

1. Создайте пустой репозиторий на github.com (без README).
2. Загрузите содержимое папки `parser` в корень репозитория:

   ```bash
   cd parser
   git init
   git add .
   git commit -m "freelance parser"
   git branch -M main
   git remote add origin https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПО.git
   git push -u origin main
   ```

   Либо через веб-интерфейс: Add file → Upload files → перетащите содержимое
   папки (не саму папку), затем отдельно проверьте, что `.github/workflows/parser.yml`
   загрузился.

3. Добавьте секреты: Settings → Secrets and variables → Actions → New repository secret.

   | Имя | Значение |
   |-----|----------|
   | `TELEGRAM_BOT_TOKEN` | токен от [@BotFather](https://t.me/BotFather), вида `123456789:AAE...` |
   | `CHAT_ID` | ваш ID в Telegram, например `1846569504` |
   | `FREELANCEHUNT_TOKEN` | необязательно: API-токен с https://freelancehunt.com/my/api |

   В workflow секреты передаются в `os.getenv`, в коде токены не хранятся.

4. Как получить токен: в Telegram напишите @BotFather → `/newbot` → имя и username →
   он выдаст строку `123456789:AAE...`. Напишите своему боту `/start`, иначе Telegram
   не даст боту отправить вам сообщение.

5. Как узнать `CHAT_ID`: напишите @userinfobot, он пришлёт ваш ID. Либо после
   сообщения боту откройте `https://api.telegram.org/bot<ТОКЕН>/getUpdates`
   и найдите `"chat":{"id":...}`.

6. Проверка: вкладка Actions → Freelance parser → Run workflow. Через минуту
   должен прийти первый заказ (если найдутся подходящие).

## Как это работает

- **FL.ru**: `https://www.fl.ru/rss/all.xml`, бюджет вытаскивается из описания.
- **Kwork**: разбор `https://kwork.ru/projects` через BeautifulSoup; если Kwork
  отдал капчу/403 — источник пропускается, остальные работают (Kwork может
  блокировать запросы с серверных IP).
- **Freelancehunt**: `https://api.freelancehunt.com/v2/projects` с Bearer-токеном.
  Без `FREELANCEHUNT_TOKEN` источник тихо пропускается. Бюджеты там в UAH —
  фильтр по сумме числовой, валюта в сообщении показывается как есть.
- **Фильтр**: в заголовке/описании есть ключевое слово, нет стоп-слова, бюджет
  400–30 000 (заказы без указанного бюджета пропускаются в Telegram с пометкой
  «не указан»). Ключевые слова ищутся с начала слова: `бот` не сработает на `работа`.
- **Дубли**: ID отправленных заказов пишутся в `seen_ids.json`, файл кэшируется
  между запусками через `actions/cache`. Хранится последние 2000 ID. Если кэш
  пропадёт (GitHub чистит кэши, не использованные 7 дней), уже отправленные
  заказы могут прийти повторно — это безвредно.

## Ограничения

- GitHub Actions не гарантирует запуск ровно каждые 30 минут: при нагрузке
  schedule сдвигается на 5–15 минут.
- Секреты не доступны в PR из форков — это не нужно для schedule.
- Если захотите подкрутить слова/бюджет — правьте `config.py`.
