import httpx
import pytest
from conftest import fixture

from iran_apps_mcp import http

pytestmark = pytest.mark.anyio

DETAIL = "/rest-v1/process/AppDetailsRequest"


async def test_bazaar_inner_500_is_retried(client, api):
    replies = [{"properties": {"statusCode": 500, "errorMessage": "internal server error"}, "singleReply": None}]

    def flaky(request):
        return httpx.Response(200, json=replies.pop() if replies else fixture("bazaar_detail.json"))

    api[DETAIL] = flaky
    result = await client.call_tool("ap_app", {"package": "ir.mci.ecareapp"})
    assert not result.is_error and len(api.calls) == 2


async def test_http_5xx_is_retried_then_reported(client, api):
    api["/app/ir.mci.ecareapp"] = lambda r: httpx.Response(503, text="down")
    result = await client.call_tool("ap_app", {"package": "ir.mci.ecareapp", "store": "myket"})
    assert result.is_error and "server error (HTTP 503)" in result.content[0].text and len(api.calls) == 3


async def test_http_403_is_not_retried(client, api):
    api["/app/ir.mci.ecareapp"] = lambda r: httpx.Response(403, text="no")
    result = await client.call_tool("ap_app", {"package": "ir.mci.ecareapp", "store": "myket"})
    assert result.is_error and "blocked the request" in result.content[0].text and len(api.calls) == 1


async def test_network_error_message(client, api):
    def boom(request):
        raise httpx.ConnectError("refused")

    api[DETAIL] = boom
    result = await client.call_tool("ap_app", {"package": "ir.mci.ecareapp"})
    assert result.is_error and "IRAN_APPS_MCP_PROXY" in result.content[0].text


async def test_proxy_list(monkeypatch):
    monkeypatch.setenv("IRAN_APPS_MCP_PROXY", " http://a:1 , http://b:2 ")
    assert http._proxies() == ["http://a:1", "http://b:2"]
