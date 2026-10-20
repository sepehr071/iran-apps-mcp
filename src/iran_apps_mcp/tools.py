"""The ap_* tools: search, app details, cross-store comparison, top/new lists, categories, related apps."""

import asyncio
import re
from typing import Annotated, Any, Literal

from pydantic import Field

from . import bazaar, myket
from .http import ApiError
from .registry import tool
from .util import PACKAGE, slim

Store = Literal["bazaar", "myket"]
StoreOrBoth = Literal["both", "bazaar", "myket"]
AppType = Literal["app", "game"]

PackageArg = Annotated[
    str,
    Field(
        description="Android package name, the id in store URLs, e.g. 'ir.mci.ecareapp' or 'com.whatsapp'.",
        min_length=3,
        max_length=200,
    ),
]


def _package(package: str) -> str:
    package = package.strip()
    if not PACKAGE.match(package):
        raise ApiError(f"'{package}' is not an Android package name (like 'com.whatsapp'). Find it with ap_search.")
    return package


async def _both(*coros):
    """Run store calls concurrently; a failing store becomes {'error': message} unless every store failed."""
    results = await asyncio.gather(*coros, return_exceptions=True)
    if all(isinstance(r, Exception) for r in results):
        raise results[0]
    return [{"error": str(r)} if isinstance(r, Exception) else r for r in results]


@tool("Search apps")
async def ap_search(
    query: Annotated[
        str,
        Field(description="Search text, Persian or English, e.g. 'تاکسی' or 'snapp'.", min_length=1, max_length=100),
    ],
    store: Annotated[
        StoreOrBoth, Field(description="'bazaar' (Cafe Bazaar), 'myket' or 'both' (default, results side by side).")
    ] = "both",
    page: Annotated[int, Field(description="1-based result page (Bazaar 24 per page, Myket 20).", ge=1, le=10)] = 1,
    limit: Annotated[int, Field(description="Max apps returned per store.", ge=1, le=24)] = 10,
) -> dict[str, Any]:
    """Search Cafe Bazaar and/or Myket for apps and games by name; returns package names, ratings and store URLs.

    Use first to find a package name, then ap_app for details or ap_compare for both stores. Bazaar cards carry
    rating, category, approximate installs and a price when paid; Myket cards only name and tagline (ap_app has the rest).
    """

    async def bz():
        return (await bazaar.search(query.strip(), page))[0][:limit]

    async def mk():
        return (await myket.search(query.strip(), page))[:limit]

    stores = ["bazaar", "myket"] if store == "both" else [store]
    results = await _both(*[bz() if s == "bazaar" else mk() for s in stores])
    return {"query": query.strip(), "page": page, **dict(zip(stores, results, strict=True))}


@tool("App details")
async def ap_app(
    package: PackageArg,
    store: Annotated[Store, Field(description="'bazaar' (Cafe Bazaar) or 'myket'.")] = "bazaar",
) -> dict[str, Any]:
    """Get one app's metadata from one store: version, rating and rating count, installs, size, update date, developer, price, description.

    Bazaar also gives version_code, a 1-5 star histogram, changelog and permission count; Myket also the first publish
    date and developer_id. installs is approximate (a rounded range). Prices are Toman, 0 = free. Metadata only: no
    APK download. To see both stores at once use ap_compare.
    """
    package = _package(package)
    return await (bazaar.detail(package) if store == "bazaar" else myket.detail(package))


_COMPARE = (
    "name",
    "version",
    "version_code",
    "rating",
    "rating_count",
    "installs",
    "size_mb",
    "updated",
    "price",
    "url",
)


def _ver(v: str | None) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


@tool("Compare stores")
async def ap_compare(package: PackageArg) -> dict[str, Any]:
    """Compare one package across Cafe Bazaar and Myket: version, rating, rating count, installs, size, update date, price.

    Returns each store's figures (null when the app is not listed there) and a diff: which store has the newer
    version, the rating difference (bazaar minus myket). Use for "is the app up to date on Myket?" or "which store
    rates it higher". Ratings are not shared between stores.
    """
    package = _package(package)
    results = await asyncio.gather(bazaar.detail(package), myket.detail(package), return_exceptions=True)
    out: dict[str, Any] = {"package": package}
    for name, r in zip(("bazaar", "myket"), results, strict=True):
        if isinstance(r, ApiError) and r.status == 404:
            out[name] = None
        elif isinstance(r, Exception):
            raise r
        else:
            out[name] = slim({k: r.get(k) for k in _COMPARE})
    b, m = out["bazaar"], out["myket"]
    if b is None and m is None:
        raise ApiError(
            f"{package} is listed on neither Cafe Bazaar nor Myket. Check the package name with ap_search.", 404
        )
    if b and m:
        vb, vm = _ver(b.get("version")), _ver(m.get("version"))
        out["diff"] = slim(
            {
                "newer_version": "same"
                if vb == vm
                else "unknown"
                if not (vb and vm)
                else "bazaar"
                if vb > vm
                else "myket",
                "rating_diff": round(b["rating"] - m["rating"], 2) if b.get("rating") and m.get("rating") else None,
            }
        )
    return out


def _category(store: str, category: str | None, type_: str) -> str | None:
    """Validate a category slug for a store; returns it unchanged (None = store-wide list)."""
    if category is None:
        return None
    category = category.strip().lower()
    if store == "bazaar":
        valid = bazaar.GAME_CATEGORIES if type_ == "game" else bazaar.APP_CATEGORIES
    else:
        valid = list(myket.GAME_CATEGORIES if type_ == "game" else myket.APP_CATEGORIES)
    if category not in valid:
        raise ApiError(f"Unknown {store} {type_} category '{category}'. Valid: {', '.join(valid)} (see ap_categories).")
    return category


@tool("Top and new apps")
async def ap_top(
    store: Annotated[Store, Field(description="'bazaar' or 'myket'.")],
    kind: Annotated[
        Literal["best", "new"], Field(description="'best' = top ranked, 'new' = newest in the category.")
    ] = "best",
    category: Annotated[
        str | None,
        Field(
            description="Category slug from ap_categories, e.g. 'tools' (Bazaar) or 'productivity' (Myket). Omit for the store-wide list (best only)."
        ),
    ] = None,
    type: Annotated[
        AppType,
        Field(
            description="'app' or 'game': which category list the slug belongs to, and which store-wide list when no category."
        ),
    ] = "app",
    page: Annotated[
        int,
        Field(description="1-based page (Bazaar 24 per page, Myket 20, Myket stops after about 4 pages).", ge=1, le=10),
    ] = 1,
    limit: Annotated[int, Field(description="Max apps returned.", ge=1, le=24)] = 20,
) -> dict[str, Any]:
    """List the top ('best') or newest ('new') apps or games of a store, per category or store-wide.

    Store-wide 'best' is Bazaar's trending list or Myket's editorial must-have list (no ranking guarantee). 'new' needs a
    category. Get slugs from ap_categories (they differ per store). Then ap_app or ap_compare on a package.
    """
    category = _category(store, category, type)
    if kind == "new" and category is None:
        raise ApiError("kind='new' needs a category (see ap_categories).")
    if store == "bazaar":
        path = (
            f"list~app~automatic~APP_TOP_CHARTS~home-{type}_trend"
            if category is None
            else bazaar.list_path(kind, category)
        )
        apps = (await bazaar.listing(path, page))[0]
    else:
        if category is None:
            key = myket.OVERALL[type]
        else:
            key = f"Category_{'Hot' if kind == 'best' else 'New'}_{(myket.GAME_CATEGORIES if type == 'game' else myket.APP_CATEGORIES)[category][0]}"
        apps = await myket.listing(key, page)
    return {"store": store, "kind": kind, "type": type, "category": category, "page": page, "apps": apps[:limit]}


@tool("Categories")
async def ap_categories(
    store: Annotated[Store, Field(description="'bazaar' or 'myket'.")],
) -> dict[str, Any]:
    """List the category slugs of a store for apps and games, to pass as ap_top category.

    Slugs differ between the stores (Bazaar 'tools' = Myket 'productivity'). Myket names are Persian. The Bazaar game
    list is the set that was verified to return results, not necessarily every game category.
    """
    if store == "bazaar":
        return {"store": store, "apps": bazaar.APP_CATEGORIES, "games": bazaar.GAME_CATEGORIES}
    return {
        "store": store,
        "apps": {k: v[1] for k, v in myket.APP_CATEGORIES.items()},
        "games": {k: v[1] for k, v in myket.GAME_CATEGORIES.items()},
    }


@tool("Related apps")
async def ap_similar(
    package: PackageArg,
    store: Annotated[Store, Field(description="'bazaar' or 'myket'.")] = "bazaar",
) -> dict[str, Any]:
    """List apps the store shows as related to one app: Bazaar gives three groups (related, others also installed, similar), Myket one.

    Use to find alternatives or competitors of an app; then ap_compare or ap_app on a result.
    """
    package = _package(package)
    groups = await (bazaar.related(package) if store == "bazaar" else myket.related(package))
    return {"store": store, "package": package, "groups": groups}
