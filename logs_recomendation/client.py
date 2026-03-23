from pathlib import Path

import typer

from logs_recomendation.analyzer import analyze_client, analyze_designer
from logs_recomendation.parser import read_client_events, read_designer_events
from logs_recomendation.report import save_outputs, save_outputs_designer
from logs_recomendation.utils import normalize_phone

app = typer.Typer(help="Аналитика клиента по логам")


@app.callback()
def main():
    """CLI entrypoint."""


@app.command("analyze")
def analyze(
    logs_dir: Path = typer.Option(..., help="Папка с .log файлами"),
    client_phone: str = typer.Option(..., help="Телефон клиента"),
    output: Path = typer.Option(..., help="Папка для report.json/client_events.csv/report.html"),
):
    """Проанализировать активность клиента и сохранить отчет."""
    phone10 = normalize_phone(client_phone)
    events_df = read_client_events(logs_dir, phone10)
    report, charts = analyze_client(events_df, phone10)
    paths = save_outputs(output, report, events_df, charts)

    typer.echo(f"Done. Events: {len(events_df)}")
    typer.echo(f"CSV: {paths.client_events_csv}")
    typer.echo(f"Report: {paths.report_json}")
    typer.echo(f"HTML: {paths.report_html}")


@app.command("analyze-designer")
def analyze_designer_cmd(
    logs_dir: Path = typer.Option(..., help="Папка с .log файлами"),
    designer_name: str = typer.Option(..., help="Имя/email дизайнера (как в логах, напр. user@mrdoors.ru)"),
    output: Path = typer.Option(..., help="Папка для report.json/designer_events.csv/report.html"),
):
    """Собрать отчёт по активности дизайнера по логам (по полю user или пути /prod/...)."""
    events_df = read_designer_events(logs_dir, designer_name)
    report, charts = analyze_designer(events_df, designer_name.strip())
    paths = save_outputs_designer(output, report, events_df, charts)

    typer.echo(f"Done. Events: {len(events_df)}")
    typer.echo(f"CSV: {paths.client_events_csv}")
    typer.echo(f"Report: {paths.report_json}")
    typer.echo(f"HTML: {paths.report_html}")


if __name__ == "__main__":
    app()

