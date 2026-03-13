import re

import pandas as pd

from app.utils import (
    build_designer_recommendations,
    classify_client_type,
    svg_bar_chart,
    svg_timeline_chart,
)

STATUS_FORM_ID_RE = re.compile(r"/form/status/([A-Za-z0-9_-]+)")
REQUEST_ID_RE = re.compile(r"\[REQUEST\s*#(\d+)\]")
RETRIEVAL_FAIL_RE = re.compile(r"Retrieved data:\s*0/\d+", re.IGNORECASE)
USERNAME_RE = re.compile(r"username=([^\s,]+)")
STAFF_PATH_RE = re.compile(r"/prod/([^/\s]+)/")


def _collect_staff_counts(df: pd.DataFrame) -> dict:
    staff_counts = {}
    for _, row in df.iterrows():
        msg = str(row.get("message", ""))
        raw = str(row.get("raw_line", ""))
        hits = []
        m = USERNAME_RE.search(msg)
        if m:
            hits.append(m.group(1))
        m = STAFF_PATH_RE.search(raw)
        if m:
            hits.append(m.group(1))
        for staff in hits:
            staff_counts[staff] = staff_counts.get(staff, 0) + 1
    return staff_counts


def analyze_client(df: pd.DataFrame, client_phone: str) -> tuple[dict, dict]:
    events_per_day = (
        df[df["date"].notna()].groupby("date").size().sort_index().astype(int).to_dict()
        if not df.empty and df["date"].notna().any()
        else {}
    )

    form_ids = set()
    accepted_request_ids = set()
    completed_request_ids = set()
    for msg in df["message"].dropna().astype(str):
        form_ids.update(STATUS_FORM_ID_RE.findall(msg))
        rid_match = REQUEST_ID_RE.search(msg)
        if rid_match:
            rid = rid_match.group(1)
            form_ids.add(rid)
            low = msg.lower()
            if "accepted form/presentator" in low:
                accepted_request_ids.add(rid)
            if "pipeline completed" in low:
                completed_request_ids.add(rid)

    messages = df["message"].fillna("").astype(str)
    lower = messages.str.lower()
    retrieval_failures = int(messages.str.contains(RETRIEVAL_FAIL_RE).sum())
    timeouts_count = int(
        (
            lower.str.contains("timeout")
            & ~lower.str.contains("default timeout")
            & ~lower.str.contains("with timeout")
        ).sum()
    )
    uploads_count = int(lower.str.contains(r"/records/upload|post /records/upload|\bupload\b").sum())

    staff_counts = _collect_staff_counts(df)
    staff_count = len(staff_counts)
    main_staff = max(staff_counts.items(), key=lambda x: x[1])[0] if staff_counts else "-"

    valid_ts = df["timestamp"].dropna().sort_values()
    first_seen = valid_ts.min().isoformat() if len(valid_ts) else None
    last_seen = valid_ts.max().isoformat() if len(valid_ts) else None
    sessions_count = int((valid_ts.diff().dropna().dt.total_seconds() > 1800).sum() + 1) if len(valid_ts) >= 2 else int(len(valid_ts) == 1)

    forms_created_count = len(accepted_request_ids) if accepted_request_ids else len(form_ids)
    pipeline_completed_count = int(lower.str.contains("pipeline completed").sum())
    forms_completed_count = len(completed_request_ids) if completed_request_ids else pipeline_completed_count
    forms_completed_count = min(forms_completed_count, forms_created_count) if forms_created_count else forms_completed_count
    forms_not_completed_count = max(forms_created_count - forms_completed_count, 0)

    issues_count = int(lower.str.contains(r"error|exception|traceback|failed|timeout", regex=True).sum()) + retrieval_failures
    client_type = classify_client_type(len(events_per_day), len(df), issues_count + timeouts_count)
    repeat_days_count = max(len(events_per_day) - 1, 0)

    report = {
        "client_phone": client_phone,
        "first_seen": first_seen,
        "last_seen": last_seen,
        "total_events": int(len(df)),
        "active_days_count": int(len(events_per_day)),
        "forms_created_count": int(forms_created_count),
        "forms_completed_count": int(forms_completed_count),
        "forms_not_completed_count": int(forms_not_completed_count),
        "uploads_count": int(uploads_count),
        "staff_count": int(staff_count),
        "main_staff": main_staff,
        "issues_count": int(issues_count),
        "client_type": client_type,
        "events_per_day": events_per_day,
        "sessions_count": int(sessions_count),
        "repeat_days_count": int(repeat_days_count),
        "designer_recommendations": [],
    }
    report["designer_recommendations"] = build_designer_recommendations(report)

    charts = {
        "timeline": svg_timeline_chart("timeline событий", list(valid_ts)),
        "activity_by_day": svg_bar_chart("активность по дням", events_per_day),
        "forms_state": svg_bar_chart(
            "состояние заявок клиента",
            {"создано": forms_created_count, "завершено": forms_completed_count, "не завершено": forms_not_completed_count},
        ),
        "staff_activity": svg_bar_chart("сотрудники, работавшие с клиентом", staff_counts),
        "success_vs_issues": svg_bar_chart("успешные и проблемные обработки", {"успешные": forms_completed_count, "проблемные": issues_count}),
        "repeat_activity": svg_bar_chart(
            "повторная активность клиента",
            {"первичный день": 1 if len(events_per_day) > 0 else 0, "повторные дни": repeat_days_count},
        ),
    }
    return report, charts

