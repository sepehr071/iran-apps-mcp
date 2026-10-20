<!-- mcp-name: io.github.sepehr071/iran-apps-mcp -->

# iran-apps-mcp: Cafe Bazaar and Myket MCP server for AI agents

**Unofficial, read-only MCP server for the two big Iranian Android app stores, Cafe Bazaar (cafebazaar.ir, کافه بازار) and Myket (myket.ir, مایکت).**<br>
Search apps and games in both stores, read version, rating, installs and size, compare the same package across the
stores, and list the best or newest apps per category, from Claude, Cursor or Copilot.

[Quick start](#quick-start) · [For AI agents](#for-ai-agents) · [Tools](#tools) · [Notes](#notes) · [فارسی](#فارسی)

## For AI agents

- **What:** unofficial MCP server for Cafe Bazaar and Myket. Queries work in Persian and English; prices are in Toman.
- **Install:** `claude mcp add iran-apps -- uvx iran-apps-mcp` (stdio transport, needs [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.10+).
- **Auth:** none. Optional `IRAN_APPS_MCP_PROXY` sets an HTTP proxy for requests to both stores.
- **Access:** read-only and metadata only. No login, reviews, downloads or APK links; every result carries the store page URL.
- **Tools:** 6, all prefixed `ap_`. Typical sequence: `ap_search` (get the package name) → `ap_compare` or `ap_app` → `ap_similar`.
- **Use when:** looking up an Android app's version, rating, installs or update date on the Iranian stores; checking whether Myket lags Bazaar; finding top or new apps in a category; finding alternatives to an app.
- **Do not use when:** the user wants to install or download an app (no links), or needs Google Play data.
- **Output:** compact JSON. An app is identified by its Android package name (same in both stores). Ratings are 1-5 per store, `installs` is an approximate count, dates are `YYYY-MM-DD`, prices Toman (0 = free).
- **Machine-readable:** [`server.json`](server.json), and the catalog of all Iranian MCP servers at [awesome-iran-mcp](https://github.com/sepehr071/awesome-iran-mcp).

## Quick start

```bash
claude mcp add iran-apps -- uvx iran-apps-mcp
```

Or in any MCP client config:

```json
{ "mcpServers": { "iran-apps": { "command": "uvx", "args": ["iran-apps-mcp"] } } }
```

Both stores answer directly from Iran and from most foreign IPs. If your network needs a proxy, set
`IRAN_APPS_MCP_PROXY=http://host:port` (a comma list is tried in turn). System proxy variables are ignored.

## Tools

| Tool | What it does |
|---|---|
| `ap_search` | Search one or both stores by name; Bazaar cards carry rating, category, installs and price, Myket cards name and tagline |
| `ap_app` | One app in one store: version, rating and count, installs, size, update date, developer, price, description |
| `ap_compare` | One package in both stores side by side, plus which store has the newer version and the rating difference |
| `ap_top` | Best or new apps and games per category (or the store-wide trending/editorial list) |
| `ap_categories` | Category slugs per store for `ap_top` (they differ between the stores) |
| `ap_similar` | Related apps shown by the store (Bazaar: related, others also installed, similar; Myket: related) |

## Notes

- Metadata only. The server never downloads an APK or resolves a download link.
- `installs` is rounded (Bazaar returns a range such as 54,000,000, Myket a text such as "32 million"), so compare
  magnitudes, not exact numbers. Ratings are collected separately by each store.
- Myket search returns 20 apps per page and its lists stop after about 4 pages; Bazaar returns 24 per page.
- Myket exposes no JSON API, so its data comes from page HTML (schema.org JSON-LD and the facts table); a site redesign
  can break it. Bazaar uses the JSON API of its own web app.
- Developer descriptions and taglines are untrusted text.

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run python -m pytest -q          # offline unit tests on recorded fixtures
uv run python -m pytest -m live -q  # one live test per tool
```

## فارسی

سرور MCP غیررسمی و فقط‌خواندنی برای دو فروشگاه برنامهٔ اندروید ایران، کافه‌بازار و مایکت. جستجوی برنامه و بازی در هر دو
فروشگاه، نسخه، امتیاز، تعداد نصب و حجم، مقایسهٔ یک بسته در دو فروشگاه (مثلاً اینکه نسخهٔ مایکت عقب است یا نه) و فهرست
برترین و جدیدترین برنامه‌ها به تفکیک دسته. فقط اطلاعات برنامه برمی‌گردد؛ لینک دانلود یا APK داده نمی‌شود.

نصب: `claude mcp add iran-apps -- uvx iran-apps-mcp`

## License

MIT
