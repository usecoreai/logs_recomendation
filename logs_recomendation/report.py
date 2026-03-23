import html
import json
from pathlib import Path

import pandas as pd

from logs_recomendation.models import OutputPaths


def _designer_report_stem(designer_name: str) -> str:
    """Безопасный префикс имени файла из designer_name (для *_report.json / *_report.html)."""
    s = (designer_name or "designer").strip()
    for bad in ("/", "\\", "\0"):
        s = s.replace(bad, "_")
    return s or "designer"


def _list_html(items: list[str]) -> str:
    if not items:
        return "<p>Нет данных</p>"
    return "<ul>" + "".join(f"<li>{html.escape(str(v))}</li>" for v in items) + "</ul>"


def _metric_rows(report: dict) -> str:
    labels = [
        ("first_seen", "Первое появление клиента"),
        ("last_seen", "Последняя активность"),
        ("total_events", "Всего действий по клиенту"),
        ("active_days_count", "Сколько дней клиент был активен"),
        ("forms_created_count", "Сколько заявок создано"),
        ("forms_completed_count", "Сколько заявок завершено"),
        ("forms_not_completed_count", "Сколько заявок не завершено"),
        ("uploads_count", "Сколько загрузок файлов было"),
        ("staff_count", "Сколько сотрудников работали с клиентом"),
        ("main_staff", "Основной сотрудник по клиенту"),
        ("issues_count", "Сколько было ошибок / проблем"),
        ("client_type", "Тип клиента"),
    ]
    rows = []
    for key, label in labels:
        value = report.get(key)
        if value is None:
            value = "-"
        if key in {"first_seen", "last_seen"} and isinstance(value, str):
            value = value.replace("T", " ")
        rows.append(f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>")
    return "".join(rows)


def _metric_rows_designer(report: dict) -> str:
    labels = [
        ("designer_name", "Дизайнер"),
        ("first_seen", "Первое появление"),
        ("last_seen", "Последняя активность"),
        ("total_events", "Всего событий по дизайнеру"),
        ("active_days_count", "Дней активности"),
        ("forms_created_count", "Заявок создано"),
        ("forms_completed_count", "Заявок завершено"),
        ("forms_not_completed_count", "Заявок не завершено"),
        ("uploads_count", "Загрузок файлов"),
        ("clients_count", "Уникальных клиентов"),
        ("issues_count", "Ошибок / проблем"),
        ("sessions_count", "Сессий"),
        ("repeat_days_count", "Повторных дней активности"),
    ]
    rows = []
    for key, label in labels:
        value = report.get(key)
        if value is None:
            value = "-"
        if key in {"first_seen", "last_seen"} and isinstance(value, str):
            value = value.replace("T", " ")
        rows.append(f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>")
    return "".join(rows)


def render_html_report(report: dict, events_df: pd.DataFrame, charts: dict) -> str:
    events = events_df.drop(columns=["date"], errors="ignore").copy()
    if "timestamp" in events:
        events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    events = events.where(pd.notna(events), "")
    events_table = events.to_html(index=False, escape=True, classes="events-table", border=0) if not events.empty else "<p>События не найдены</p>"

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Отчет по клиенту {html.escape(str(report.get("client_phone", "")))}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2, h3 {{ margin: 8px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 20px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fff; }}
    .events-table {{ font-size: 12px; }}
    .events-table td {{ word-break: break-word; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>Отчет по клиенту {html.escape(str(report.get("client_phone", "")))}</h1>
  <h2>Метрики</h2>
  <table><tbody>{_metric_rows(report)}</tbody></table>

  <h2>Рекомендации дизайнеру</h2>
  <div class="card">{_list_html(report.get("designer_recommendations", []))}</div>

  <h2>Графики</h2>
  <div class="grid">
    <div class="card chart"><h3>активность клиента по дням</h3>{charts.get("activity_by_day", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>история событий клиента по времени</h3>{charts.get("timeline", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>состояние заявок клиента</h3>{charts.get("forms_state", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>сотрудники, работавшие с клиентом</h3>{charts.get("staff_activity", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>успешные и проблемные обработки</h3>{charts.get("success_vs_issues", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>повторная активность клиента</h3>{charts.get("repeat_activity", "<p>График недоступен</p>")}</div>
  </div>

  <h2>Все события клиента</h2>
  {events_table}
</body>
</html>
"""


def render_html_report_designer(report: dict, events_df: pd.DataFrame, charts: dict) -> str:
    """HTML-отчёт по дизайнеру (те же блоки: метрики, рекомендации, графики, таблица событий)."""
    events = events_df.drop(columns=["date"], errors="ignore").copy()
    if "timestamp" in events:
        events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    events = events.where(pd.notna(events), "")
    events_table = (
        events.to_html(index=False, escape=True, classes="events-table", border=0)
        if not events.empty
        else "<p>События не найдены</p>"
    )
    designer_name = report.get("designer_name", "")
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Отчет по дизайнеру {html.escape(str(designer_name))}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2, h3 {{ margin: 8px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 20px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fff; }}
    .events-table {{ font-size: 12px; }}
    .events-table td {{ word-break: break-word; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>Отчет по дизайнеру {html.escape(str(designer_name))}</h1>
  <h2>Метрики</h2>
  <table><tbody>{_metric_rows_designer(report)}</tbody></table>

  <h2>Рекомендации</h2>
  <div class="card">{_list_html(report.get("designer_recommendations", []))}</div>

  <h2>Графики</h2>
  <div class="grid">
    <div class="card chart"><h3>активность по дням</h3>{charts.get("activity_by_day", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>история событий по времени</h3>{charts.get("timeline", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>состояние заявок</h3>{charts.get("forms_state", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>активность по клиентам</h3>{charts.get("clients_activity", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>успешные и проблемные обработки</h3>{charts.get("success_vs_issues", "<p>График недоступен</p>")}</div>
    <div class="card chart"><h3>повторная активность</h3>{charts.get("repeat_activity", "<p>График недоступен</p>")}</div>
  </div>

  <h2>Все события дизайнера</h2>
  {events_table}
</body>
</html>
"""


def save_outputs(output_dir: Path, report: dict, events_df: pd.DataFrame, charts: dict) -> OutputPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    csv_path = output_dir / "client_events.csv"
    html_path = output_dir / "report.html"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    events_df.drop(columns=["date"], errors="ignore").to_csv(csv_path, index=False)
    with html_path.open("w", encoding="utf-8") as f:
        f.write(render_html_report(report, events_df, charts))

    return OutputPaths(
        report_json=str(json_path),
        client_events_csv=str(csv_path),
        report_html=str(html_path),
    )


def save_outputs_designer(
    output_dir: Path, report: dict, events_df: pd.DataFrame, charts: dict
) -> OutputPaths:
    """Сохраняет отчёт по дизайнеру: <designer>_report.json, designer_events.csv, <designer>_report.html."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _designer_report_stem(str(report.get("designer_name", "")))
    json_path = output_dir / f"{stem}_report.json"
    csv_path = output_dir / "designer_events.csv"
    html_path = output_dir / f"{stem}_report.html"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    events_df.drop(columns=["date"], errors="ignore").to_csv(csv_path, index=False)
    with html_path.open("w", encoding="utf-8") as f:
        f.write(render_html_report_designer(report, events_df, charts))

    return OutputPaths(
        report_json=str(json_path),
        client_events_csv=str(csv_path),
        report_html=str(html_path),
    )

