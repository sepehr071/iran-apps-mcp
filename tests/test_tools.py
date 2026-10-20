import pytest
from conftest import fixture

pytestmark = pytest.mark.anyio

DETAIL = "/rest-v1/process/AppDetailsRequest"
SEARCH = "/rest-v1/process/SearchBodyV2Request"
LIST = "/rest-v1/process/GetPageBodyRequest"


async def call(client, name, args):
    result = await client.call_tool(name, args)
    assert not result.is_error, result.content[0].text
    return result.structured_content


async def test_all_tools_are_read_only(client):
    tools = (await client.list_tools()).tools
    assert sorted(t.name for t in tools) == [
        "ap_app",
        "ap_categories",
        "ap_compare",
        "ap_search",
        "ap_similar",
        "ap_top",
    ]
    for t in tools:
        assert t.annotations.read_only_hint is True and t.annotations.destructive_hint is False, t.name
        assert t.description and t.title, t.name


async def test_search_both(client, api):
    api[SEARCH] = fixture("bazaar_search.json")
    api["/Search/Apps"] = fixture("myket_search.html")
    data = await call(client, "ap_search", {"query": "تاکسی", "limit": 3})
    assert len(data["bazaar"]) == 3 and len(data["myket"]) == 3
    b = data["bazaar"][0]
    assert b["store"] == "bazaar" and b["url"] == f"https://cafebazaar.ir/app/{b['package']}" and b["name"]
    m = data["myket"][0]
    assert m["package"] == "com.GlimGames.heytaxi" and m["name"] == "هی تاکسی" and m["tagline"] == "تفننی"
    assert not any(a["package"].startswith("v-") for a in data["myket"])  # video results are not apps
    bazaar_call = next(c for c in api.calls if c.url.path == SEARCH)
    assert bazaar_call.content and b"searchBodyV2Request" in bazaar_call.content
    myket_call = next(c for c in api.calls if c.url.path == "/Search/Apps")
    assert dict(myket_call.url.params) == {"keyword": "تاکسی", "page": "0"}


async def test_search_page_and_single_store(client, api):
    api["/Search/Apps"] = fixture("myket_search.html")
    data = await call(client, "ap_search", {"query": "x", "store": "myket", "page": 3})
    assert "bazaar" not in data and len(data["myket"]) == 4
    assert api.params()["page"] == "2"


async def test_search_one_store_failing_is_reported(client, api):
    api[SEARCH] = fixture("bazaar_search.json")  # Myket answers 404
    data = await call(client, "ap_search", {"query": "x"})
    assert data["bazaar"] and "Not found on myket.ir" in data["myket"]["error"]


async def test_app_bazaar(client, api):
    api[DETAIL] = fixture("bazaar_detail.json")
    d = await call(client, "ap_app", {"package": "ir.mci.ecareapp", "store": "bazaar"})
    assert d["name"] == "MyMCI" and d["version"] == "6.6.1" and d["version_code"] == 66105
    assert d["rating"] == 3.9 and d["rating_count"] == 295871 and d["installs"] == 54_000_000
    assert d["size_mb"] == 28.4 and d["updated"] == "2026-05-17" and d["price"] == 0
    assert d["rating_histogram"][4] == 188969 and d["url"] == "https://cafebazaar.ir/app/ir.mci.ecareapp"
    assert "<" not in d["description"]
    assert api.body()["appDetailsRequest"]["packageName"] == "ir.mci.ecareapp"


async def test_app_myket(client, api):
    api["/app/ir.mci.ecareapp"] = fixture("myket_app.html")
    d = await call(client, "ap_app", {"package": "ir.mci.ecareapp", "store": "myket"})
    assert d["name"] == "همراه من" and d["version"] == "6.6.1" and d["rating"] == 4.3 and d["rating_count"] == 325463
    assert d["installs"] == 32_000_000 and d["size_mb"] == 28.4 and d["updated"] == "2026-05-17"
    assert d["published"] == "2018-12-16" and d["price"] == 0 and d["is_game"] is False
    assert d["category_slug"] == "productivity" and d["developer"] == "همراه اول" and d["developer_id"] == "dev-54560"


async def test_app_not_found_and_bad_package(client, api):
    api[DETAIL] = fixture("bazaar_notfound.json")
    result = await client.call_tool("ap_app", {"package": "no.such.app", "store": "bazaar"})
    assert result.is_error and "Not found on Cafe Bazaar" in result.content[0].text
    result = await client.call_tool("ap_app", {"package": "no.such.app", "store": "myket"})
    assert result.is_error and "Not found on myket.ir" in result.content[0].text
    calls = len(api.calls)
    result = await client.call_tool("ap_app", {"package": "../etc/passwd"})
    assert result.is_error and "not an Android package name" in result.content[0].text and len(api.calls) == calls


async def test_compare(client, api):
    api[DETAIL] = fixture("bazaar_detail.json")
    api["/app/ir.mci.ecareapp"] = fixture("myket_app.html")
    d = await call(client, "ap_compare", {"package": "ir.mci.ecareapp"})
    assert d["bazaar"]["rating"] == 3.9 and d["myket"]["rating"] == 4.3
    assert d["diff"] == {"newer_version": "same", "rating_diff": -0.4}
    assert "description" not in d["bazaar"]


async def test_compare_newer_version_and_missing_store(client, api):
    detail = fixture("bazaar_detail.json")
    detail["singleReply"]["appDetailsReply"]["package"]["versionName"] = "6.10.0"
    api[DETAIL] = detail
    api["/app/ir.mci.ecareapp"] = fixture("myket_app.html")
    d = await call(client, "ap_compare", {"package": "ir.mci.ecareapp"})
    assert d["diff"]["newer_version"] == "bazaar"  # 6.10.0 > 6.6.1 numerically
    del api["/app/ir.mci.ecareapp"]
    d = await call(client, "ap_compare", {"package": "ir.mci.ecareapp"})
    assert d["myket"] is None and d["bazaar"]["version"] == "6.10.0" and "diff" not in d


async def test_compare_in_neither_store(client, api):
    api[DETAIL] = fixture("bazaar_notfound.json")
    result = await client.call_tool("ap_compare", {"package": "no.such.app"})
    assert result.is_error and "neither Cafe Bazaar nor Myket" in result.content[0].text


async def test_top_bazaar(client, api):
    api[LIST] = fixture("bazaar_best.json")
    d = await call(client, "ap_top", {"store": "bazaar", "category": "tools", "limit": 2, "page": 2})
    assert len(d["apps"]) == 2 and d["apps"][0]["package"] and d["page"] == 2
    assert api.body()["getPageBodyRequest"] == {"path": "list~app~automatic~APP_BEST~tools", "offset": 24}
    await call(client, "ap_top", {"store": "bazaar", "category": "action", "type": "game", "kind": "new"})
    assert api.body()["getPageBodyRequest"]["path"] == "list~app~automatic~APP_NEW~action"
    await call(client, "ap_top", {"store": "bazaar", "type": "game"})
    assert api.body()["getPageBodyRequest"]["path"] == "list~app~automatic~APP_TOP_CHARTS~home-game_trend"


async def test_top_myket(client, api):
    for path in ("/list/Category_Hot_14", "/list/Category_New_26", "/list/page", "/list/must-have-android-apps"):
        api[path] = fixture("myket_search.html")
    d = await call(client, "ap_top", {"store": "myket", "category": "productivity"})
    assert len(d["apps"]) == 4 and d["apps"][0]["store"] == "myket"
    await call(client, "ap_top", {"store": "myket", "category": "action", "type": "game", "kind": "new"})
    assert api.calls[-1].url.path == "/list/Category_New_26"
    await call(client, "ap_top", {"store": "myket", "category": "productivity", "page": 2})
    assert api.params() == {"listKey": "Category_Hot_14", "page": "1"}
    await call(client, "ap_top", {"store": "myket"})
    assert api.calls[-1].url.path == "/list/must-have-android-apps"


async def test_top_errors(client, api):
    for args, msg in [
        ({"store": "myket", "category": "tools"}, "Unknown myket app category 'tools'"),
        ({"store": "bazaar", "category": "productivity"}, "Unknown bazaar app category"),
        ({"store": "bazaar", "kind": "new"}, "needs a category"),
    ]:
        result = await client.call_tool("ap_top", args)
        assert result.is_error and msg in result.content[0].text, args
    assert not api.calls


async def test_categories(client):
    b = await call(client, "ap_categories", {"store": "bazaar"})
    assert "tools" in b["apps"] and "action" in b["games"]
    m = await call(client, "ap_categories", {"store": "myket"})
    assert m["apps"]["productivity"] == "ابزارهای کاربردی" and "action" in m["games"]


async def test_similar(client, api):
    api[DETAIL] = fixture("bazaar_detail.json")
    api["/app/ir.mci.ecareapp"] = fixture("myket_app.html")
    b = await call(client, "ap_similar", {"package": "ir.mci.ecareapp"})
    assert len(b["groups"]) == 3 and b["groups"][0]["apps"][0]["package"] == "com.intsig.camscanner"
    m = await call(client, "ap_similar", {"package": "ir.mci.ecareapp", "store": "myket"})
    assert len(m["groups"][0]["apps"]) == 3 and m["groups"][0]["apps"][0]["store"] == "myket"


async def test_bazaar_price_is_converted_from_rial(client, api):
    reply = fixture("bazaar_detail.json")
    reply["singleReply"]["appDetailsReply"]["price"] = {"price": 20000, "priceString": "2000 Tomans"}
    api[DETAIL] = reply
    d = await call(client, "ap_app", {"package": "ir.mci.ecareapp", "store": "bazaar"})
    assert d["price"] == 2000 and d["price_text"] == "2000 Tomans"


async def test_myket_price_is_converted_from_rial(client, api):
    api["/app/ir.mci.ecareapp"] = fixture("myket_app.html").replace('"price": "0"', '"price": "150000"')
    d = await call(client, "ap_app", {"package": "ir.mci.ecareapp", "store": "myket"})
    assert d["price"] == 15000
