# Client Log Analyzer

CLI-проект для анализа клиентской активности по сервисным логам.
Скрипт находит события клиента по телефону, считает метрики и формирует понятный отчет для дизайнера/менеджера.

## Что делает проект

- читает все `*.log` файлы из указанной папки (рекурсивно);
- находит строки, связанные с клиентом по телефону (поддерживаются разные форматы номера);
- строит аналитику по активности клиента;
- сохраняет:
  - `report.json` (структурированные метрики),
  - `client_events.csv` (все найденные события),
  - `report.html` (человеко-читаемый отчет с графиками).

## Структура проекта

```text
Logs_analysis/
  app/
    client.py      # CLI (Typer)
    parser.py      # чтение и парсинг логов
    analyzer.py    # расчет аналитики клиента
    report.py      # генерация json/csv/html
    utils.py       # вспомогательные функции и SVG-графики
    models.py      # dataclass-модели
  all.log
  api_methods.log
  pyproject.toml
  requirements.txt
  Dockerfile
  README.md
```

## Требования

- Python 3.10+
- `pip`

## Установка и запуск локально

```bash
cd Logs_analysis
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

Проверить CLI:

```bash
client --help
```

Запуск анализа:

```bash
client analyze \
  --logs-dir . \
  --client-phone 9160993434 \
  --output ./output
```

## Параметры CLI

- `--logs-dir` — папка с логами (`*.log`), например `.` или `./logs`
- `--client-phone` — телефон клиента (например `9160993434`, `+7 916 099 34 34`)
- `--output` — папка для результатов

Важно: папка `--output` создается автоматически, если ее нет.

## Docker (минимальный)

Сборка образа:

```bash
cd Logs_analysis
docker build -t client-log-analyzer .
```

Запуск контейнера:

```bash
docker run --rm \
  -v "$(pwd):/app" \
  client-log-analyzer analyze \
  --logs-dir /app \
  --client-phone 9160993434 \
  --output /app/output
```

## Результаты

После запуска в директории `--output` будут:

- `report.json`
- `client_events.csv`
- `report.html`

