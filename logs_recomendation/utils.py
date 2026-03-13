import html
import re


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("client-phone must have 10 digits (or 11 with 7/8 prefix)")
    return digits


def build_phone_regex(phone10: str) -> re.Pattern:
    body = r"[\s\-]*".join(list(phone10))
    pattern = rf"(?<!\d)(?:(?:\+?7|8)[\s\-]*)?{body}(?!\d)"
    return re.compile(pattern)


def classify_client_type(active_days_count: int, total_events: int, issues_count: int) -> str:
    if issues_count >= 3:
        return "проблемный"
    if active_days_count >= 5:
        return "постоянный"
    if active_days_count >= 2 or total_events >= 30:
        return "активный"
    return "разовый"


def build_designer_recommendations(report: dict) -> list[str]:
    tips = []
    if report.get("forms_created_count", 0) > 0:
        tips.append("Клиент оставлял заявку: стоит быстро связаться и уточнить текущий запрос.")
    if report.get("forms_completed_count", 0) == 0 and report.get("forms_created_count", 0) > 0:
        tips.append("По логам пайплайн не завершен: проверьте, дошел ли клиент до получения итогового результата.")
    if report.get("issues_count", 0) > 0:
        tips.append("В логах были ошибки: при общении лучше подтвердить статус клиента вручную.")
    if report.get("active_days_count", 0) >= 2:
        tips.append("Клиент активен в разные дни: предложите следующий конкретный шаг и зафиксируйте договоренность.")
    if report.get("sessions_count", 0) >= 2:
        tips.append("Есть несколько сессий активности: клиент возвращается к вопросу и нуждается в сопровождении.")
    if report.get("main_staff", "-") != "-":
        tips.append(f"Основной сотрудник по клиенту: {report.get('main_staff')}. Лучше вести коммуникацию через него.")
    if not tips:
        tips.append("По логам активность минимальная: начните с короткого уточняющего контакта.")
    return tips


def svg_wrap(title: str, body: str, width: int = 760, height: int = 240) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />'
        f'<text x="12" y="20" font-size="13" fill="#374151">{html.escape(title)}</text>'
        f"{body}</svg>"
    )


def svg_no_data(title: str) -> str:
    return svg_wrap(title, '<text x="12" y="52" font-size="12" fill="#9ca3af">no data</text>')


def svg_bar_chart(title: str, data: dict) -> str:
    if not data:
        return svg_no_data(title)
    width, height = 760, 240
    left, top, right, bottom = 40, 32, 20, 36
    chart_w, chart_h = width - left - right, height - top - bottom
    items = list(data.items())
    max_v = max(float(v) for _, v in items) or 1.0
    slot = chart_w / max(len(items), 1)
    bar_w = max(8, slot * 0.65)
    parts = [f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#d1d5db"/>']
    for i, (k, v) in enumerate(items):
        x = left + i * slot + (slot - bar_w) / 2
        h = chart_h * (float(v) / max_v)
        y = top + chart_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="#60a5fa"/>')
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{height-bottom+14}" font-size="10" text-anchor="middle" fill="#6b7280">{html.escape(str(k)[:12])}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{max(y-4, 24):.1f}" font-size="10" text-anchor="middle" fill="#374151">{html.escape(str(v))}</text>'
        )
    return svg_wrap(title, "".join(parts), width=width, height=height)


def svg_timeline_chart(title: str, timestamps: list) -> str:
    if not timestamps:
        return svg_no_data(title)
    ts = sorted([t for t in timestamps if t is not None])
    if not ts:
        return svg_no_data(title)
    width, height = 760, 180
    left, right, y = 30, 20, 100
    total = max((ts[-1] - ts[0]).total_seconds(), 1.0)
    w = width - left - right
    parts = [f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" stroke="#d1d5db"/>']
    for t in ts:
        x = left + ((t - ts[0]).total_seconds() / total) * w
        parts.append(f'<circle cx="{x:.2f}" cy="{y}" r="3" fill="#2563eb"/>')
    parts.append(f'<text x="{left}" y="{y+20}" font-size="10" fill="#6b7280">{html.escape(str(ts[0]))}</text>')
    parts.append(f'<text x="{width-right}" y="{y+20}" font-size="10" text-anchor="end" fill="#6b7280">{html.escape(str(ts[-1]))}</text>')
    return svg_wrap(title, "".join(parts), width=width, height=height)

