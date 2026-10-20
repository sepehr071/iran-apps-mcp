"""Shared async HTTP client for Cafe Bazaar (JSON API) and Myket (server-rendered HTML).

`bazaar(request, body)` POSTs a Cafe Bazaar `rest-v1/process/<Request>` call, `myket(path, params)` GETs a Myket page.
`_send` caps concurrency, retries timeouts, dropped connections, 429 and 5xx with jittered backoff and turns HTTP
failures into `ToolError` messages the model can act on. The wire format is a Chrome impersonation (curl_cffi).
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any

import httpx
from httpx_curl_cffi import AsyncCurlTransport
from mcp.server.mcpserver.exceptions import ToolError

BAZAAR_API = "https://api.cafebazaar.ir/rest-v1/process"
MYKET = "https://myket.ir"

HEADERS = {"Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8"}
PAGE_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

MAX_CONCURRENCY = 4
JITTER = (0.05, 0.25)  # seconds before each upstream call
MAX_RETRIES = 2
MAX_RETRY_WAIT = 10  # cap for Retry-After and backoff, seconds
RETRY_DELAY = 0.5

_transport: httpx.AsyncBaseTransport | None = None
_client: httpx.AsyncClient | None = None
_limit: asyncio.Semaphore | None = None
_proxy_index = 0


class ApiError(ToolError):
    """A failed upstream call. `status` is the HTTP (or Bazaar) status, or None for network errors."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def set_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Swap the transport (tests use httpx.MockTransport). Drops the current client."""
    global _transport, _client, _limit, _proxy_index
    _transport, _client, _limit, _proxy_index = transport, None, None, 0


def _proxies() -> list[str]:
    """IRAN_APPS_MCP_PROXY: one proxy URL, or a comma-separated list used one at a time."""
    return [p.strip() for p in os.environ.get("IRAN_APPS_MCP_PROXY", "").split(",") if p.strip()]


def _next_proxy(client: httpx.AsyncClient) -> None:
    """Sticky pool: move to the next proxy after a connect error; the next call rebuilds the client."""
    global _client, _limit, _proxy_index
    if len(_proxies()) < 2 or client is not _client:
        return
    _client, _limit, _proxy_index = None, None, _proxy_index + 1


def _get_client() -> tuple[httpx.AsyncClient, asyncio.Semaphore]:
    global _client, _limit
    if _client is None:
        # Both stores are reachable directly from Iran and from most abroad IPs; a proxy is only used when the user
        # opts in with IRAN_APPS_MCP_PROXY. System proxies are ignored (trust_env=False).
        proxies = _proxies()
        _client = httpx.AsyncClient(
            transport=_transport
            or AsyncCurlTransport(
                impersonate="chrome",
                default_headers=True,
                proxy=proxies[_proxy_index % len(proxies)] if proxies else None,
                max_connections=2 * MAX_CONCURRENCY,
            ),
            headers=HEADERS,
            timeout=30,
            limits=httpx.Limits(max_connections=2 * MAX_CONCURRENCY),
            follow_redirects=True,
            trust_env=False,
        )
        _limit = asyncio.Semaphore(MAX_CONCURRENCY)
    assert _limit is not None
    return _client, _limit


async def bazaar(request: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST one Cafe Bazaar request; returns the reply object (`singleReply.<request>Reply`)."""
    name = request[0].upper() + request[1:]
    payload = {
        "properties": {"language": 2, "clientID": "iran-apps-mcp", "deviceID": "iran-apps-mcp", "clientVersion": "web"},
        "singleRequest": {request: body},
    }
    for attempt in range(MAX_RETRIES + 1):
        r = await _send("POST", f"{BAZAAR_API}/{name}", json=payload)
        try:
            data = r.json()
        except ValueError as e:
            raise ApiError(f"api.cafebazaar.ir returned a non-JSON response for {name} (HTTP {r.status_code}).") from e
        props = data.get("properties") or {}
        status = props.get("statusCode", 200)
        if status < 500 or attempt == MAX_RETRIES:
            break
        await asyncio.sleep(RETRY_DELAY * 2**attempt)  # the API answers an inner 500 now and then; a retry works
    reply = (data.get("singleReply") or {}).get(request.removesuffix("Request") + "Reply")
    if status == 404 or (status == 200 and reply is None):
        raise ApiError("Not found on Cafe Bazaar. Check the package name or category.", 404)
    if status != 200 or reply is None:
        raise ApiError(
            f"Cafe Bazaar rejected the request ({name}: {status} {str(props.get('errorMessage'))[:200]}).", status
        )
    return reply


async def myket(path: str, params: dict[str, Any] | None = None) -> str:
    """GET a Myket page or fragment and return its HTML (decoded as UTF-8)."""
    r = await _send("GET", f"{MYKET}{path}", params=params, headers=PAGE_HEADERS)
    return r.content.decode("utf-8", "replace")


async def _send(method: str, url: str, **kwargs: Any) -> httpx.Response:
    host = httpx.URL(url).host
    retries = 0
    while True:
        client, limit = _get_client()
        wait = None
        try:
            async with limit:
                await asyncio.sleep(random.uniform(*JITTER))
                r = await client.request(method, url, **kwargs)
        except httpx.TimeoutException as e:
            err = ApiError(f"{host} did not answer in time. Try again in a moment.")
            err.__cause__ = e
        except httpx.TransportError as e:
            if isinstance(e, httpx.ConnectError | httpx.ProxyError):
                _next_proxy(client)
            err = ApiError(
                f"Could not reach {host} ({type(e).__name__}). Check the internet connection, or set IRAN_APPS_MCP_PROXY."
            )
            err.__cause__ = e
        else:
            if r.status_code == 429 or r.status_code >= 500:
                err = ApiError(_status_message(r, host), r.status_code)
                wait = _retry_after(r)
            elif r.status_code >= 400:
                raise ApiError(_status_message(r, host), r.status_code)
            else:
                return r
        if retries == MAX_RETRIES:
            raise err
        wait = wait if wait is not None else RETRY_DELAY * 2**retries * random.uniform(1, 1.5)
        retries += 1
        await asyncio.sleep(min(wait, MAX_RETRY_WAIT))


def _retry_after(r: httpx.Response) -> float | None:
    """Seconds from a numeric Retry-After on a 429/503, else None (HTTP-date form is ignored)."""
    v = r.headers.get("retry-after", "")
    return float(v) if r.status_code in (429, 503) and v.replace(".", "", 1).isdigit() else None


def _status_message(r: httpx.Response, host: str) -> str:
    code = r.status_code
    if code == 404:
        return f"Not found on {host} (HTTP 404). Check the package name, category or list."
    if code == 403:
        return f"{host} blocked the request (HTTP 403). Turn off VPN/proxy or set IRAN_APPS_MCP_PROXY."
    if code == 429:
        return f"{host} is rate limiting requests (HTTP 429). Wait a minute before retrying."
    if code >= 500:
        return f"{host} had a server error (HTTP {code}). Try again later."
    return f"{host} rejected the request (HTTP {code})."
