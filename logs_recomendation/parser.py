import json
import re
from pathlib import Path

import pandas as pd

from logs_recomendation.utils import build_phone_regex, normalize_phone

TS_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<rest>.*)$")
MSG_RE = re.compile(r"^\[[^\]]+\]\s+\[[^\]]+\]\s+\[(?P<level>[^\]]+)\]\s*(?P<message>.*)$")
HTTP_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(\S+)")


def parse_line(line: str) -> dict:
    ts_match = TS_RE.match(line)
    timestamp = None
    message = line.strip()
    if ts_match:
        timestamp = pd.to_datetime(ts_match.group("ts"), errors="coerce")
        rest = ts_match.group("rest")
        msg_match = MSG_RE.match(rest)
        message = msg_match.group("message").strip() if msg_match else rest.strip()

    method, endpoint = None, None
    http_match = HTTP_RE.search(message)
    if http_match:
        method = http_match.group(1)
        endpoint = http_match.group(2)

    return {
        "timestamp": timestamp,
        "message": message,
        "http_method": method,
        "endpoint": endpoint,
    }


def parse_json_log_line(line: str) -> dict | None:
    """Парсит строку лога в формате JSON (api.log). Возвращает dict с timestamp, message, http_method, endpoint или None."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    ts = data.get("timestamp")
    timestamp = pd.to_datetime(ts, errors="coerce") if ts else None
    message = data.get("message", "")
    method = data.get("method")
    path = data.get("path")
    endpoint = f"{method} {path}" if method and path else (path or "")
    return {
        "timestamp": timestamp,
        "message": str(message),
        "http_method": method,
        "endpoint": path or "",
    }


def read_client_events(logs_dir: Path, client_phone: str) -> pd.DataFrame:
    phone_re = build_phone_regex(normalize_phone(client_phone))
    log_files = sorted(logs_dir.rglob("*.log"))
    if not log_files:
        raise FileNotFoundError(f"No .log files found in {logs_dir}")

    events = []
    for log_file in log_files:
        try:
            with log_file.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if phone_re.search(line):
                        parsed = parse_line(line)
                        parsed["source_file"] = log_file.name
                        parsed["raw_line"] = line.rstrip("\n")
                        events.append(parsed)
        except OSError as exc:
            print(f"Warning: failed to read {log_file}: {exc}")

    df = pd.DataFrame(events, columns=["timestamp", "source_file", "http_method", "endpoint", "message", "raw_line"])
    if df.empty:
        df["date"] = pd.Series(dtype="object")
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp", na_position="last").reset_index(drop=True)
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    return df


def _line_matches_designer(line: str, designer_name: str) -> bool:
    """Проверяет, относится ли строка лога к данному дизайнеру (user или путь /prod/...)."""
    if not designer_name or not line:
        return False
    designer_clean = designer_name.strip().lower()
    line_lower = line.lower()
    if designer_clean in line_lower:
        return True
    if line.strip().startswith("{"):
        try:
            data = json.loads(line)
            user = (data.get("user") or "").strip().lower()
            return user == designer_clean or designer_clean in user
        except json.JSONDecodeError:
            pass
    return False


def read_designer_events(logs_dir: Path, designer_name: str) -> pd.DataFrame:
    """Собирает все события логов, относящиеся к дизайнеру (по полю user или пути /prod/...)."""
    designer_key = designer_name.strip()
    if not designer_key:
        raise ValueError("designer_name must be non-empty")
    log_files = sorted(logs_dir.rglob("*.log"))
    if not log_files:
        raise FileNotFoundError(f"No .log files found in {logs_dir}")

    events = []
    for log_file in log_files:
        try:
            with log_file.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not _line_matches_designer(line, designer_key):
                        continue
                    raw = line.rstrip("\n")
                    parsed = parse_json_log_line(line)
                    if parsed is None:
                        parsed = parse_line(line)
                    parsed["source_file"] = log_file.name
                    parsed["raw_line"] = raw
                    events.append(parsed)
        except OSError as exc:
            print(f"Warning: failed to read {log_file}: {exc}")

    df = pd.DataFrame(
        events,
        columns=["timestamp", "source_file", "http_method", "endpoint", "message", "raw_line"],
    )
    if df.empty:
        df["date"] = pd.Series(dtype="object")
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp", na_position="last").reset_index(drop=True)
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    return df

