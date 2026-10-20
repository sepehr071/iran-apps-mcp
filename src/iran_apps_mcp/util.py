"""Small helpers shared by both stores: Persian digits, counts like "۳۲ میلیون", Jalali dates, HTML to text."""

import html
import re

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬،", "01234567890123456789.,,")
_UNITS = {"میلیارد": 1e9, "billion": 1e9, "میلیون": 1e6, "million": 1e6, "هزار": 1e3, "thousand": 1e3}
PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")


def ascii_digits(s: str) -> str:
    return s.translate(_DIGITS)


def parse_count(text: str | None) -> int | None:
    """'۳۲ میلیون' -> 32000000, '54,000,000' -> 54000000, '۴.۹ میلیون' -> 4900000; None if no number."""
    if not text:
        return None
    s = ascii_digits(text).replace(",", "")
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    unit = next((v for k, v in _UNITS.items() if k in s.lower()), 1)
    return round(float(m.group()) * unit)


def jalali_to_iso(text: str) -> str | None:
    """'1405/03/27' (Persian or ASCII digits) -> '2026-06-17'; None if it is not a Jalali date."""
    m = re.fullmatch(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})\s*", ascii_digits(text))
    if not m:
        return None
    jy, jm, jd = (int(x) for x in m.groups())
    jy += 1595
    days = (
        -355668
        + 365 * jy
        + (jy // 33) * 8
        + ((jy % 33) + 3) // 4
        + jd
        + ((jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186)
    )
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    months = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and gd > months[gm]:
        gd -= months[gm]
        gm += 1
    return f"{gy:04d}-{gm + 1:02d}-{gd:02d}"


def text_of(fragment: str) -> str:
    """HTML fragment -> plain text: block tags become newlines, entities are decoded."""
    s = re.sub(r"<(?:br|/p|/li|/h\d)[^>]*>", "\n", fragment, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", s)).strip()


def clip(s: str | None, n: int) -> str | None:
    if not s:
        return None
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def slim(d: dict) -> dict:
    """Drop None and empty-string values."""
    return {k: v for k, v in d.items() if v is not None and v != ""}
