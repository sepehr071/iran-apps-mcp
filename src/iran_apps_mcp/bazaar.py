"""Cafe Bazaar (cafebazaar.ir): the JSON behind its web app, `api.cafebazaar.ir/rest-v1/process/<Request>`."""

from datetime import datetime, timezone
from typing import Any

from . import http
from .util import clip, parse_count, slim, text_of

SITE = "https://cafebazaar.ir"
PAGE = 24  # rows per page of search and list replies

APP_CATEGORIES = [
    "books-reference", "education", "entertainment", "finance", "food-drink", "health-fitness", "kids-apps",
    "lifestyle", "maps-navigation", "medical", "music-audio", "personalization", "photography", "religious",
    "shopping", "social", "sports", "tools", "travel-local", "weather",
]  # fmt: skip
GAME_CATEGORIES = [
    "action", "arcade", "casual", "kids-games", "puzzle", "racing", "simulation", "sports-game", "strategy", "word-trivia",
]  # fmt: skip


def url(package: str) -> str:
    return f"{SITE}/app/{package}"


def card(info: dict[str, Any]) -> dict[str, Any]:
    """A list/search row's `simpleAppItem.info` as a compact card."""
    pay = info.get("paymentInfo") or {}
    return slim(
        {
            "store": "bazaar",
            "package": info["packageName"],
            "name": info.get("name"),
            "category": info.get("category"),
            "rating": info.get("rate") or None,
            "installs": parse_count(
                f"{info.get('installCountVerbose', '')} {info.get('installCountVerboseLabel', '')}"
            ),
            "price": pay.get("priceString") if pay.get("price") else None,
            "url": url(info["packageName"]),
        }
    )


def cards(reply: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """(cards, has_more) from a reply that holds `pageBody.rows`; ads are dropped."""
    rows = (reply.get("pageBody") or {}).get("rows") or []
    items = [r["simpleAppItem"] for r in rows if "simpleAppItem" in r]
    return [card(i["info"]) for i in items if not i.get("isAd")], bool(reply.get("hasMore"))


async def search(query: str, page: int) -> tuple[list[dict[str, Any]], bool]:
    reply = await http.bazaar(
        "searchBodyV2Request",
        {"query": query, "entities": "", "language": "fa", "offset": (page - 1) * PAGE, "scope": "app"},
    )
    return cards(reply)


async def listing(path: str, page: int) -> tuple[list[dict[str, Any]], bool]:
    """A vitrin list such as `list~app~automatic~APP_BEST~tools`."""
    reply = await http.bazaar("getPageBodyRequest", {"path": path, "offset": (page - 1) * PAGE})
    return cards(reply)


def list_path(kind: str, category: str) -> str:
    """Path of the "best" or "new" list of a category."""
    return f"list~app~automatic~{'APP_BEST' if kind == 'best' else 'APP_NEW'}~{category}"


def _iso(epoch: str | None) -> str | None:
    return datetime.fromtimestamp(int(epoch), timezone.utc).strftime("%Y-%m-%d") if epoch and epoch.isdigit() else None


async def detail(package: str) -> dict[str, Any]:
    a = await http.bazaar("appDetailsRequest", {"packageName": package, "referrer": ""})
    return parse_detail(a)


def parse_detail(a: dict[str, Any]) -> dict[str, Any]:
    pkg, stats, price = a.get("package") or {}, a.get("stats") or {}, a.get("price") or {}
    size = pkg.get("packageSize")
    return slim(
        {
            "store": "bazaar",
            "package": a["packageName"],
            "name": a.get("name"),
            "version": pkg.get("versionName"),
            "version_code": pkg.get("versionCode"),
            "rating": stats.get("rate") or None,
            "rating_count": stats.get("reviewCount"),
            "rating_histogram": [stats.get(f"rate{i}Count") for i in range(1, 6)] if stats.get("reviewCount") else None,
            "installs": parse_count(stats.get("installCountRange")),
            "size_mb": round(int(size) / 1e6, 1) if size and size.isdigit() else None,
            "updated": _iso(pkg.get("lastUpdatedTimeFromEpoch")),
            "category": a.get("categoryName"),
            "category_slug": a.get("categorySlug"),
            "is_game": a.get("isGame"),
            "developer": a.get("authorName"),
            "price": int(price.get("price") or 0) // 10,  # Bazaar sends Rial (20000 = "2000 Tomans")
            "price_text": price.get("priceString"),
            "in_app_purchase": a.get("hasInAppPurchase"),
            "homepage": a.get("homepage"),
            "summary": a.get("shortDescription"),
            "description": clip(text_of(a.get("description") or ""), 1500),
            "changelog": clip(text_of(pkg.get("changeLog") or ""), 600),
            "permissions": len(pkg.get("permissions") or []),
            "icon": a.get("icon"),
            "url": url(a["packageName"]),
        }
    )


async def related(package: str) -> list[dict[str, Any]]:
    """Related-app groups of an app: [{title, apps}]."""
    a = await http.bazaar("appDetailsRequest", {"packageName": package, "referrer": ""})
    groups = []
    for row in (a.get("relatedPage") or {}).get("commonRows") or []:
        apps = [
            slim(
                {
                    "store": "bazaar",
                    "package": i["packageName"],
                    "name": i.get("name"),
                    "rating": i.get("rate") or None,
                    "developer": i.get("authorName"),
                    "url": url(i["packageName"]),
                }
            )
            for i in (row.get("appList") or {}).get("appList") or []
        ]
        if apps:
            groups.append({"title": row.get("title") or "", "apps": apps})
    return groups
