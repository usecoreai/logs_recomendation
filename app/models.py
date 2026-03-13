from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LogEvent:
    timestamp: Optional[datetime]
    source_file: str
    http_method: Optional[str]
    endpoint: Optional[str]
    message: str
    raw_line: str


@dataclass
class OutputPaths:
    report_json: str
    client_events_csv: str
    report_html: str

