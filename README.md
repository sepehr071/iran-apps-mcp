<!-- mcp-name: io.github.sepehr071/iran-apps-mcp -->

<div align="center">

# iran-apps-mcp: Cafe Bazaar and Myket MCP server for AI agents

**Let your AI agent look up apps on the Iranian Android stores.**<br>
An unofficial, read-only MCP server for [Cafe Bazaar](https://cafebazaar.ir) (کافه&zwnj;بازار) and [Myket](https://myket.ir) (مایکت):<br>
search apps and games, compare one package across both stores, and list top or new apps, from Claude, Cursor or Copilot.

[![PyPI](https://img.shields.io/pypi/v/iran-apps-mcp?color=2563eb)](https://pypi.org/project/iran-apps-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/iran-apps-mcp)](https://pypi.org/project/iran-apps-mcp/)
[![CI](https://github.com/sepehr071/iran-apps-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehr071/iran-apps-mcp/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sepehr071%2Firan--apps--mcp-7c3aed)](https://registry.modelcontextprotocol.io/?q=iran-apps-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](https://github.com/sepehr071/iran-apps-mcp/blob/main/LICENSE)
[![mcpfarsi](https://mcpfarsi.ir/badge/iran-apps.svg)](https://mcpfarsi.ir/servers/iran-apps/)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_iran--apps--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=iran-apps&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22iran-apps-mcp%22%5D%7D)

[For AI agents](#for-ai-agents) · [Quick start](#quick-start) · [What it can do](#what-it-can-do) · [Tools](#tools) · [FAQ](#faq) · [فارسی](#فارسی)

</div>

---

## For AI agents

- **What:** unofficial MCP server (model context protocol) for the two big Iranian Android app stores, Cafe Bazaar (cafebazaar.ir) and Myket (myket.ir). Queries work in Persian and English.
- **Install:** `uvx iran-apps-mcp` or `claude mcp add iran-apps -- uvx iran-apps-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none, no API key or account. Optional `IRAN_APPS_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored.
- **Access:** read-only, metadata only. It cannot log in, post reviews or download anything, so no confirmation is needed before calling any tool. Every result carries the store page URL.
- **Tools:** 6, all prefixed `ap_`. Typical sequence: `ap_search` (get the package name) -> `ap_compare` or `ap_app` -> `ap_similar`. For lists, call `ap_categories` first and pass a slug to `ap_top`.
- **Use when:** the user asks about an Android app's version, rating, installs, size or update date on the Iranian stores; whether Myket lags Bazaar; top or new apps in a category; alternatives to an app.
- **Do not use when:** the user wants to install or download an app (no download or APK links), or needs Google Play data.
- **Output:** compact JSON. An app is identified by its Android package name (same in both stores). Ratings are 1-5 per store, `installs` is an approximate count, dates are `YYYY-MM-DD` (Gregorian), prices in **Toman** (0 = free).
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/iran-apps-mcp/blob/main/server.json) and the [iran-mcp catalog](https://github.com/sepehr071/iran-mcp).

## Why

Cafe Bazaar and Myket are where most Iranian Android users get their apps, and neither offers a public API. Checking
"is the Myket version of this app behind Bazaar, and how do users rate it in each store?" means opening both sites and
reading two different pages. With `iran-apps-mcp` an agent answers it in one call and returns a short summary.

> **You:** Is Telegram up to date on Myket compared with Cafe Bazaar?
>
> **Agent:** *calls* `ap_search(query="telegram")` -> `ap_compare(package="org.telegram.messenger")`
>
> It reads both versions, says which store has the newer one, and shows the rating difference.

## What it can do

- **Search** apps and games in Cafe Bazaar, Myket or both, by Persian or English name
- **Read one app**: version, rating and rating count, installs, size, update date, developer, price and description
- **Compare** the same package in both stores side by side, with which store is newer and the rating difference
- **List top or new apps** per category (apps and games), or the store-wide trending or editorial list
- **List categories** of each store (slugs differ between the stores)
- **Find similar apps** the store itself shows as related
- **Read-only by design**: no login, no reviews, no downloads

Example prompts:

- "Search Cafe Bazaar and Myket for Snapp and show the ratings."
- "Compare the Digikala app on both stores: version, rating, installs."
- "What are the best new games on Myket this week?"
- "Top apps in the finance category on Cafe Bazaar."
- "Which apps do users also install along with Divar?"
- <span dir="rtl">اپلیکیشن بله را در کافه&zwnj;بازار و مایکت جستجو کن و نسخه و امتیازش را مقایسه کن.</span>
- <span dir="rtl">بهترین بازی&zwnj;های جدید مایکت کدام&zwnj;اند؟</span>
- <span dir="rtl">برنامه&zwnj;های مشابه اسنپ در کافه&zwnj;بازار را نشان بده.</span>

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). No API key or account.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add iran-apps -- uvx iran-apps-mcp
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "iran-apps": { "command": "uvx", "args": ["iran-apps-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add the Claude Desktop block above to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project).
</details>

<details>
<summary><b>VS Code (Copilot agent mode)</b></summary>

Click **Install in VS Code** above, or add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "iran-apps": { "type": "stdio", "command": "uvx", "args": ["iran-apps-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add iran-apps -- uvx iran-apps-mcp
```

Or in `~/.codex/config.toml`:

```toml
[mcp_servers.iran-apps]
command = "uvx"
args = ["iran-apps-mcp"]
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "iran-apps": { "command": "uvx", "args": ["iran-apps-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Windsurf</b></summary>

Add the Claude Desktop block to `~/.codeium/windsurf/mcp_config.json`.
</details>

<details>
<summary><b>Anything else</b></summary>

It is a standard stdio MCP server: run `uvx iran-apps-mcp`, or `pip install iran-apps-mcp` and run `iran-apps-mcp`.
</details>

## Tools

An app is identified by its Android package name (for example `com.whatsapp`). Get it from `ap_search`.

| Tool | What it does |
|---|---|
| `ap_search` | Search Cafe Bazaar and/or Myket for apps and games by name; returns package names, ratings and store URLs |
| `ap_app` | Get one app's metadata from one store: version, rating and rating count, installs, size, update date, developer, price, description |
| `ap_compare` | Compare one package across Cafe Bazaar and Myket: version, rating, rating count, installs, size, update date, price |
| `ap_top` | List the top ('best') or newest ('new') apps or games of a store, per category or store-wide |
| `ap_categories` | List the category slugs of a store for apps and games, to pass as `ap_top` category |
| `ap_similar` | List apps the store shows as related to one app: Bazaar gives three groups (related, others also installed, similar), Myket one |

All 6 tools are annotated `readOnlyHint: true`.

## How it works

```text
  AI agent  (Claude, Cursor, Copilot, ...)
      │
      │  MCP over stdio
      ▼
  iran-apps-mcp  (runs on your machine)
      │
      │  HTTPS
      ├──────▶  api.cafebazaar.ir   JSON API of the Bazaar web app
      └──────▶  myket.ir            page HTML (schema.org JSON-LD, facts table)
```

`iran-apps-mcp` runs locally and has no hosted server in between and no API key. Cafe Bazaar is read through the JSON
requests its own web app uses; Myket has no JSON API, so its data is parsed from page HTML. Requests go out through a
Chrome-impersonating client, at most 4 at a time with a little jitter, and a failed request is retried up to twice.
It only reads.

## Good to know

- **Prices are in Toman**, 0 means free. Both stores quote Rial internally; the server divides by 10.
- **`installs` is approximate.** Bazaar returns a range, Myket a text such as "32 million", so compare magnitudes, not exact numbers.
- **Ratings are per store** (1-5) and collected separately by each. A rating is omitted when the store has none.
- **Paging:** Bazaar returns 24 apps per page, Myket 20. Myket lists stop after about 4 pages.
- **Categories differ** between the stores; use `ap_categories` to get valid slugs for `ap_top`. Bazaar's game category list was found by probing and may be incomplete.
- **Names:** Bazaar names are often English, Myket's Persian. An app can be missing from one store (`ap_compare` gives null there); Google Play-only apps are in neither.
- **Myket depends on page HTML,** so a site redesign can break it. Bazaar uses its web app's JSON API, which is undocumented and can change.
- **Network:** both stores answered directly from Iran and through a foreign proxy exit when tested. If your network needs a proxy, set `IRAN_APPS_MCP_PROXY`.
- **What it does not do:** no download or APK links, no login, no reviews or comments, no purchases, no Google Play data. Developer descriptions and taglines are untrusted text.

## FAQ

<details>
<summary><b>Is there a Cafe Bazaar or Myket API MCP server?</b></summary>

Neither store documents a public API. `iran-apps-mcp` is an unofficial MCP server with 6 read-only tools that reads
Cafe Bazaar through its web app's API and Myket from its pages, and returns compact JSON for AI agents.
</details>

<details>
<summary><b>How do I use it with Claude, Cursor or Copilot?</b></summary>

Add the server with `claude mcp add iran-apps -- uvx iran-apps-mcp`, or use the matching config in
[Quick start](#quick-start), then ask in plain language, in Persian or English.
</details>

<details>
<summary><b>Can it download an APK or give me a download link?</b></summary>

No. It returns metadata and the store page URL only.
</details>

<details>
<summary><b>How do I compare an app's version between Bazaar and Myket?</b></summary>

Find the package name with `ap_search`, then call `ap_compare`. It shows both versions, which store is newer and the
rating difference.
</details>

<details>
<summary><b>Are prices in Rial or Toman?</b></summary>

Toman. Both stores quote Rial internally and the server converts. 0 means free.
</details>

<details>
<summary><b>Why is `installs` not an exact number?</b></summary>

The stores do not publish exact counts: Bazaar returns a range and Myket a rounded text. The server gives an approximate integer.
</details>

<details>
<summary><b>Does it work for apps that are only on Google Play?</b></summary>

No. It only sees what is listed on Cafe Bazaar and Myket.
</details>

<details>
<summary><b>Do I need a proxy?</b></summary>

Usually not. Both stores answered directly and through a foreign exit when tested. If your network blocks them, set
`IRAN_APPS_MCP_PROXY` to an HTTP proxy. System proxy variables are ignored on purpose.
</details>

<details>
<summary><b>How do I debug what the agent sees?</b></summary>

```bash
npx @modelcontextprotocol/inspector uvx iran-apps-mcp
```
</details>

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `IRAN_APPS_MCP_PROXY` | unset | Optional HTTP proxy URL for cafebazaar.ir and myket.ir; system proxy settings are ignored. A comma-separated list is tried in turn |

<a id="فارسی"></a>

## فارسی: سرور MCP کافه&zwnj;بازار و مایکت

<div dir="rtl">

**iran-apps-mcp** یک سرور MCP غیررسمی و فقط&zwnj;خواندنی برای دو فروشگاه برنامهٔ اندروید ایران، کافه&zwnj;بازار و مایکت، است. این سرور به دستیار هوش مصنوعی شما (Claude، Cursor، Copilot و ...) اجازه می&zwnj;دهد برنامه و بازی را در هر دو فروشگاه جستجو کند.

**چه کارهایی می&zwnj;کند**

- **جستجوی برنامه و بازی** در کافه&zwnj;بازار، مایکت یا هر دو، با نام فارسی یا انگلیسی.
- **اطلاعات یک برنامه**: نسخه، امتیاز و تعداد امتیاز، تعداد نصب، حجم، تاریخ به&zwnj;روزرسانی، توسعه&zwnj;دهنده، قیمت و توضیحات.
- **مقایسهٔ یک بسته در دو فروشگاه**، مثلاً اینکه نسخهٔ مایکت عقب است یا نه.
- **برترین و جدیدترین برنامه&zwnj;ها و بازی&zwnj;ها** به تفکیک دسته.
- **برنامه&zwnj;های مشابه** که خود فروشگاه نشان می&zwnj;دهد.

**نکته&zwnj;ها**

- فقط خواندنی است: وارد حساب نمی&zwnj;شود، نظر ثبت نمی&zwnj;کند و لینک دانلود یا APK نمی&zwnj;دهد.
- قیمت&zwnj;ها به تومان، امتیازها از ۱ تا ۵ برای هر فروشگاه جدا، و تعداد نصب تقریبی است. تاریخ&zwnj;ها میلادی هستند.
- کلید API لازم نیست و روی سیستم خود شما اجرا می&zwnj;شود. برای پراکسی از متغیر `IRAN_APPS_MCP_PROXY` استفاده کنید.

**نصب** (اول [uv](https://docs.astral.sh/uv/getting-started/installation/) را نصب کنید). در Claude Code:

</div>

```bash
claude mcp add iran-apps -- uvx iran-apps-mcp
```

<div dir="rtl">

در Claude Desktop، Cursor و بقیه برنامه&zwnj;ها همان تنظیم بخش [Quick start](#quick-start) را بگذارید.

**نمونه پرسش&zwnj;ها**

- «اپلیکیشن بله را در کافه&zwnj;بازار و مایکت مقایسه کن.»
- «بهترین بازی&zwnj;های جدید مایکت کدام&zwnj;اند؟»
- «برنامه&zwnj;های مشابه اسنپ را نشان بده.»

</div>

## Development

```bash
git clone https://github.com/sepehr071/iran-apps-mcp && cd iran-apps-mcp
uv sync
uv run ruff check . && uv run ruff format --check .
uv run python -m pytest -q          # offline unit tests on recorded fixtures
uv run python -m pytest -m live -q  # calls the real stores
uv build
```

Each tool is a typed async function in `src/iran_apps_mcp/tools.py` with a docstring that tells the agent when to use
it. Issues and PRs are welcome.

Releases: bump the version in `pyproject.toml` and `server.json`, then push a `v*` tag. GitHub Actions publishes to PyPI.

## Related servers

- [iran-mcp](https://github.com/sepehr071/iran-mcp): catalog of all Iranian-service MCP servers
- [iran-downloads-mcp](https://github.com/sepehr071/iran-downloads-mcp) for Iranian download sites
- [digikala-mcp](https://github.com/sepehr071/digikala-mcp) for Digikala product search and prices
- [torob-mcp](https://github.com/sepehr071/torob-mcp) for price comparison on Torob
- [divar-mcp](https://github.com/sepehr071/divar-mcp) for Divar classified ads
- Listed on [mcpfarsi.ir](https://mcpfarsi.ir/servers/iran-apps/), the Persian MCP marketplace

## Disclaimer

Unofficial and not affiliated with or endorsed by Cafe Bazaar or Myket. It is read-only and uses the web endpoints and
pages of the two stores, which can change without notice. App data is informational.

## Author

<a href="https://www.linkedin.com/in/sepehr-radmard"><img src="https://raw.githubusercontent.com/sepehr071/iran-mcp/main/assets/author-banner.png" alt="Sepehr Radmard: open-source MCP servers for the Iranian web. LinkedIn: linkedin.com/in/sepehr-radmard" width="100%"></a>

Built and maintained by **Sepehr Radmard** (سپهر رادمرد). Connect on [LinkedIn](https://www.linkedin.com/in/sepehr-radmard) or follow [@sepehr071 on GitHub](https://github.com/sepehr071) for more MCP servers for Iranian websites, all listed in [iran-mcp](https://github.com/sepehr071/iran-mcp). If this saves you time, a star on the repo helps other people find it.

## License

[MIT](https://github.com/sepehr071/iran-apps-mcp/blob/main/LICENSE)
