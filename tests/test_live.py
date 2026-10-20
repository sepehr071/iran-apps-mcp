import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.live]

PKG = "ir.mci.ecareapp"  # MyMCI: Iranian, listed on both stores


async def call(client, name, args):
    result = await client.call_tool(name, args)
    assert not result.is_error, result.content[0].text
    return result.structured_content


async def test_ap_search(client):
    data = await call(client, "ap_search", {"query": "تاکسی", "limit": 5})
    assert len(data["bazaar"]) == 5 and len(data["myket"]) == 5
    assert all(a["package"] and a["url"].startswith("https://") for a in data["bazaar"] + data["myket"])
    assert any(a["rating"] for a in data["bazaar"])
    page2 = await call(client, "ap_search", {"query": "تاکسی", "limit": 5, "page": 2})
    assert {a["package"] for a in page2["bazaar"]}.isdisjoint({a["package"] for a in data["bazaar"]})


async def test_ap_app_bazaar(client):
    d = await call(client, "ap_app", {"package": PKG, "store": "bazaar"})
    assert d["version"] and d["version_code"] > 0 and 0 < d["rating"] <= 5 and d["rating_count"] > 1000
    assert d["installs"] >= 1_000_000 and d["size_mb"] > 1 and d["updated"].startswith("20") and d["developer"]


async def test_ap_app_myket(client):
    d = await call(client, "ap_app", {"package": PKG, "store": "myket"})
    assert d["version"] and 0 < d["rating"] <= 5 and d["rating_count"] > 1000 and d["installs"] >= 1_000_000
    assert d["updated"].startswith("20") and d["category_slug"] and d["developer_id"]


async def test_ap_app_game_on_myket(client):
    d = await call(client, "ap_app", {"package": "com.supercell.clashofclans", "store": "myket"})
    assert d["is_game"] is True and d["name"]


async def test_ap_compare(client):
    d = await call(client, "ap_compare", {"package": PKG})
    assert d["bazaar"]["version"] and d["myket"]["version"] and d["diff"]["newer_version"]
    assert d["bazaar"]["rating"] != d["myket"]["rating"] or d["bazaar"]["rating_count"] != d["myket"]["rating_count"]
    only = await call(client, "ap_compare", {"package": "com.supercell.clashofclans"})
    assert only["myket"] is not None  # Bazaar may or may not list it


async def test_ap_top(client):
    b = await call(client, "ap_top", {"store": "bazaar", "category": "tools", "limit": 10})
    assert len(b["apps"]) == 10 and all(a["category"] == "tools" for a in b["apps"])
    new = await call(client, "ap_top", {"store": "bazaar", "category": "puzzle", "type": "game", "kind": "new"})
    assert new["apps"]
    m = await call(client, "ap_top", {"store": "myket", "category": "productivity"})
    assert len(m["apps"]) >= 15
    m2 = await call(client, "ap_top", {"store": "myket", "category": "productivity", "page": 2})
    assert m2["apps"] and {a["package"] for a in m2["apps"]}.isdisjoint({a["package"] for a in m["apps"]})
    g = await call(client, "ap_top", {"store": "myket", "category": "action", "type": "game", "kind": "new"})
    assert g["apps"]
    overall = await call(client, "ap_top", {"store": "bazaar"})
    assert overall["apps"]
    overall = await call(client, "ap_top", {"store": "myket", "type": "game"})
    assert overall["apps"]


async def test_ap_categories(client):
    # every verified Bazaar category slug still answers with apps
    b = await call(client, "ap_categories", {"store": "bazaar"})
    for slug in b["apps"][:3]:
        assert (await call(client, "ap_top", {"store": "bazaar", "category": slug, "limit": 1}))["apps"], slug
    m = await call(client, "ap_categories", {"store": "myket"})
    assert len(m["apps"]) == 20 and len(m["games"]) == 10


async def test_ap_similar(client):
    b = await call(client, "ap_similar", {"package": PKG, "store": "bazaar"})
    assert len(b["groups"]) >= 2 and b["groups"][0]["apps"]
    m = await call(client, "ap_similar", {"package": PKG, "store": "myket"})
    assert m["groups"][0]["apps"] and all(a["package"] != PKG for a in m["groups"][0]["apps"])
