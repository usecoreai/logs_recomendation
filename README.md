# Client Log Analyzer

CLI-проект для анализа активности по сервисным логам.
Скрипт находит события по телефону клиента или по имени дизайнера, считает метрики и формирует понятный отчёт.

## Что делает проект

- читает все `*.log` файлы из указанной папки (рекурсивно);
- **по клиенту** (`analyze`): находит строки по телефону (поддерживаются разные форматы номера), строит аналитику и отчёт для дизайнера/менеджера;
- **по дизайнеру** (`analyze-designer`): находит строки по полю `user` или пути `/prod/...`, строит аналитику по активности дизайнера (заявки, клиенты, ошибки);
- сохраняет:
  - `report.json` (структурированные метрики),
  - `client_events.csv` / `designer_events.csv` (все найденные события),
  - `report.html` (человеко-читаемый отчёт с графиками).

## Структура проекта

```text
Logs_analysis/
  logs_recomendation/
    client.py      # CLI (Typer)
    parser.py      # чтение и парсинг логов
    analyzer.py    # расчет аналитики клиента
    report.py      # генерация json/csv/html
    utils.py       # вспомогательные функции и SVG-графики
    models.py      # dataclass-модели
  all.log
  api_methods.log
  pyproject.toml
  Dockerfile
  README.md
```

## Требования

- Python 3.10+
- `pip`

## Установка и запуск локально

```bash
cd logs_recomendation
python3 -m pip install -e .
```

Проверить CLI:

```bash
client --help
```

Запуск анализа по клиенту:

```bash
client analyze \
  --logs-dir . \
  --client-phone 9160993434 \
  --output ./output
```

Запуск анализа по дизайнеру:

```bash
client analyze-designer \
  --logs-dir . \
  --designer-name "user@mrdoors.ru" \
  --output ./output
```

## Параметры CLI

**Команда `analyze` (по клиенту):**

- `--logs-dir` — папка с логами (`*.log`), например `.` или `./logs`
- `--client-phone` — телефон клиента (например `9160993434`, `+7 916 099 34 34`)
- `--output` — папка для результатов

**Команда `analyze-designer` (по дизайнеру):**

- `--logs-dir` — папка с логами (`*.log`)
- `--designer-name` — имя/email дизайнера (как в логах, например `user@mrdoors.ru`)
- `--output` — папка для результатов

Папка `--output` создаётся автоматически, если её нет.

## Docker

Сборка образа:

```bash
cd logs_recomendation
docker build -t logs-recomendation .
```

Запуск анализа по клиенту (логи и вывод монтируются отдельно, не перезаписывайте `/app`):

```bash
docker run --rm \
  -v "$(pwd)/logging/prod:/logs" \
  -v "$(pwd)/output:/output" \
  logs-recomendation analyze \
  --logs-dir /logs \
  --client-phone 9160993434 \
  --output /output
```

Запуск анализа по дизайнеру:

```bash
docker run --rm \
  -v "$(pwd)/logging/prod:/logs" \
  -v "$(pwd)/output:/output" \
  logs-recomendation analyze-designer \
  --logs-dir /logs \
  --designer-name "user@mrdoors.ru" \
  --output /output
```

## Результаты

После `analyze` в директории `--output` будут:

- `report.json`
- `client_events.csv`
- `report.html`

После `analyze-designer` в директории `--output` будут:

- `report.json`
- `designer_events.csv`
- `report.html`

