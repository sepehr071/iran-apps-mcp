"""Myket (myket.ir): server-rendered HTML. App pages carry schema.org JSON-LD plus a facts table; lists are card HTML."""

import html
import json
import re
from typing import Any

from . import http
from .util import ascii_digits, clip, jalali_to_iso, parse_count, slim

SITE = "https://myket.ir"
PAGE = 20  # cards per search or list page

# slug -> (list id, Persian name). The ids come from the `Category_Hot_<id>` list links on each category page.
APP_CATEGORIES = {
    "weather": (13, "آب\u200cوهوا"), "food-and-drink": (155, "آشپزی و رستوران"), "education": (24, "آموزشی"),
    "productivity": (14, "ابزارهای کاربردی"), "news-and-magazines": (18, "اخبار"), "finance": (20, "امور مالی"),
    "medical": (33, "پزشکی و سلامت"), "health-and-fitness": (21, "تناسب اندام"), "shopping": (15, "خرید"),
    "lifestyle": (23, "سبک زندگی"), "entertainment": (11, "سرگرمی"), "travel-and-local": (6, "سیر و سفر"),
    "social": (32, "شبکه\u200cهای اجتماعی"), "personalization": (12, "شخصی\u200cسازی"),
    "music-and-audio": (10, "صوت و موسیقی"), "video-players-and-editors": (4, "عکس و فیلم"),
    "books-and-reference": (9, "کتاب"), "business": (17, "کسب و کار"), "religion": (38, "مذهبی"),
    "sports": (19, "ورزشی"),
}  # fmt: skip
GAME_CATEGORIES = {
    "strategy": (124, "استراتژی"), "action": (26, "اکشن"), "casual": (27, "تفننی"), "racing": (29, "رانندگی"),
    "simulation": (123, "شبیه\u200cسازی"), "puzzle": (28, "فکری"), "word": (126, "کلمات و دانستنی\u200cها"),
    "kids": (182, "کودک"), "adventure": (115, "ماجراجویی"), "sports": (31, "ورزشی"),
}  # fmt: skip
# Editorial lists used when no category is given.
OVERALL = {"app": "must-have-android-apps", "game": "best-free-android-games"}

_CARD = re.compile(
    r'<a href="/app/[^"]*" class="app-detail-link" data-package-name="([^"]+)" title="([^"]*)"(.*?)</a>', re.S
)
_MARKS = " \t\n\u200e\u200f"  # right-to-left marks the store puts around names
_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def url(package: str) -> str:
    return f"{SITE}/app/{package}"


def cards(page_html: str) -> list[dict[str, Any]]:
    """App cards (`.list-app`) of a search, list or app page, in order, without duplicates."""
    seen, out = set(), []
    for pkg, title, rest in _CARD.findall(html.unescape(page_html)):
        if pkg in seen:
            continue
        seen.add(pkg)
        tag = re.search(r'<p class="app-group">(.*?)</p>', rest, re.S)
        out.append(
            slim(
                {
                    "store": "myket",
                    "package": pkg,
                    "name": title.strip(_MARKS),
                    "tagline": tag and tag.group(1).strip(),
                    "url": url(pkg),
                }
            )
        )
    return out


async def search(query: str, page: int) -> list[dict[str, Any]]:
    """/Search/Apps is the fragment the search page loads (20 apps per page, also holds video results)."""
    return cards(await http.myket("/Search/Apps", {"keyword": query, "page": page - 1}))


async def listing(key: str, page: int) -> list[dict[str, Any]]:
    """A list by key (`Category_Hot_14`, `Category_New_14`, `must-have-android-apps`); page 1 is the list page itself."""
    if page == 1:
        return cards(await http.myket(f"/list/{key}"))
    return cards(await http.myket("/list/page", {"listKey": key, "page": page - 1}))


def _ld(page: str) -> dict[str, Any]:
    for raw in _LD.findall(page):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "SoftwareApplication":
            return data
    return {}


def _size_mb(text: str | None) -> float | None:
    m = re.fullmatch(r"\s*([\d.]+)\s*(kB|KB|MB|GB)\s*", text or "")
    return round(float(m.group(1)) * {"kb": 1e-3, "mb": 1, "gb": 1e3}[m.group(2).lower()], 1) if m else None


def strip(s: str | None) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def parse_detail(page: str, package: str) -> dict[str, Any]:
    ld = _ld(page)
    if not ld:
        raise http.ApiError(f"Could not read the Myket page of {package}: no app data found.", 404)
    text = html.unescape(page)
    facts = {
        re.sub(r"<[^>]+>", "", k).strip(): v
        for k, v in re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td></tr>", text, re.S)
    }
    cat = re.search(r'href="/(apps|games)/([^"]+)"[^>]*>', facts.get("دسته\u200cبندی", ""))
    dev = re.search(r'href="/developer/([^"]+)"', facts.get("سازنده", ""))
    rating = ld.get("aggregateRating") or {}
    price = (ld.get("offers") or {}).get("price")
    return slim(
        {
            "store": "myket",
            "package": package,
            "name": (ld.get("name") or "").strip(_MARKS),
            "version": ld.get("softwareVersion") or ascii_digits(strip(facts.get("نسخه"))),
            "rating": rating.get("ratingValue") or None,
            "rating_count": rating.get("ratingCount"),
            "installs": parse_count(strip(facts.get("تعداد دانلود"))),
            "size_mb": _size_mb(ld.get("fileSize")),
            "updated": jalali_to_iso(strip(facts.get("آخرین بروزرسانی"))),
            "published": (ld.get("datePublished") or "")[:10],
            "category": strip(facts.get("دسته\u200cبندی")),
            "category_slug": cat and cat.group(2),
            "is_game": cat and cat.group(1) == "games",
            "developer": strip(facts.get("سازنده")),
            "developer_id": dev and dev.group(1),
            # JSON-LD prices are Rial (priceCurrency IRR); 1 Toman = 10 Rial
            "price": int(float(price) / 10) if price not in (None, "") else None,
            "description": clip(ld.get("description"), 1500),
            "icon": ld.get("image"),
            "url": url(package),
        }
    )


async def detail(package: str) -> dict[str, Any]:
    return parse_detail(await http.myket(f"/app/{package}"), package)


async def related(package: str) -> list[dict[str, Any]]:
    """The "برنامه\u200cهای مرتبط" (related apps) block of an app page."""
    page = html.unescape(await http.myket(f"/app/{package}"))
    i = page.find("برنامه\u200cهای مرتبط")
    apps = [c for c in cards(page[i:]) if c["package"] != package] if i >= 0 else []
    return [{"title": "برنامه\u200cهای مرتبط", "apps": apps}] if apps else []
