from iran_apps_mcp.util import jalali_to_iso, parse_count, text_of


def test_parse_count():
    assert parse_count("۳۲ میلیون") == 32_000_000
    assert parse_count("54,000,000") == 54_000_000
    assert parse_count("۴.۹ میلیون") == 4_900_000
    assert parse_count("۴٫۹ میلیون") == 4_900_000
    assert parse_count("۱۰۰ هزار") == 100_000
    assert parse_count("") is None and parse_count("نامشخص") is None


def test_jalali_to_iso():
    assert jalali_to_iso("۱۴۰۵/۰۳/۲۷") == "2026-06-17"
    assert jalali_to_iso("1405/01/01") == "2026-03-21"
    assert jalali_to_iso("1404/12/29") == "2026-03-20"
    assert jalali_to_iso("not a date") is None


def test_text_of():
    assert text_of("<p>a &amp; b</p><p>c<br>d</p>") == "a & b\nc\nd"
