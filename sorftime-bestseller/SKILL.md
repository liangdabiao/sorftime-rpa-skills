---
name: sorftime-bestseller
description: Pull Amazon Best Sellers TOP100 from sorftime.com 畅销榜 (/home/bestseller) across 14 marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill — sorftime encrypts API request/response bodies with an obfuscated AES routine, so we drive the page's own Vue + jQuery zTree to load decrypted data and read it out of the Vue VM. Returns 23 fields per ASIN including sales/price/profit/seller/brand/reviews/rating.
---

# sorftime-bestseller

Fetch **Amazon Best Sellers** (TOP 100 per category) from **sorftime 畅销榜** (`/home/bestseller`).

sorftime encrypts API bodies, so this is a **DOM-driven skill**: instead of calling `api.sorftime.com` directly, we drive the page's own Vue VM (`vm.treeItemClick(node)`) to trigger the encrypted fetch and read the decrypted result from `vm._data.bestsellerData`. Categories are site-specific (e.g. JP has 19 categories with Japanese names; US has 27 with English names).

## Quick start

```bash
# Single station, single category
python scripts/fetch_bestseller.py --station US --categories baby-products \
    --out data/us_baby.csv

# Single station, all top-level categories
python scripts/fetch_bestseller.py --station US \
    --out data/us_bestseller.csv

# Multi-station, all categories (full crawl)
python scripts/fetch_bestseller.py --station US,JP,GB \
    --out data/by_station.csv

# Generate report
python scripts/analyze.py --bestseller data/by_station.csv \
    --out-md reports/by_station.md
```

## Requirements

- **Kimi WebBridge daemon** running and extension connected: `~/.kimi-webbridge status`
- **sorftime login** in the same browser profile (free tier works — best seller list is fully visible)
- Python 3.10+ (no third-party packages)

## What you get

Each CSV row = one Best Seller ASIN, with 23 fields:

| Field | Meaning |
|---|---|
| `station` / `station_name` | Amazon marketplace code + 中文 |
| `category_slug` / `category_name` | sorftime category (e.g. `baby-products` / `Baby(宝贝)`) |
| `rank` | 1-100 rank within category |
| `asin` / `name` / `brand` | Product identity + title |
| `price` / `single_price` | Current price + per-unit price (if variation) |
| `sale_count` / `sale_estimate` | Monthly sales units + revenue |
| `gross_profit` / `fba_fee` | FBA profit estimate + fee |
| `deliver` | `FBA` or `FBM` |
| `score` / `comment_count` | Star rating + review count |
| `seller` / `seller_nationality` | Seller name + country |
| `sale_time` / `sale_time_day` | First sale date + days since |
| `node_id` / `asin_url` / `image_url` | Category node + ASIN/image links |

## CLI flags

| Flag | Notes |
|---|---|
| `--station` | Required. Comma-separated: `US,JP,GB,DE,FR,IT,ES,CA,IN,MX,AE,AU,BR,SA` |
| `--out` | Required. CSV output path |
| `--categories` | Optional. Comma-separated category slugs (default: all top-level) |
| `--max-categories` | Optional. Cap per station for debugging |

## Gotchas

1. **DOM-driven, not API-first**: sorftime encrypts request/response bodies (`{v:3, k:"<base64-ts>", d:"<AES-blob>"}`) with an obfuscated routine. Calling `fetch()` or `XMLHttpRequest` from page context → CORS block + 401. We bypass by calling `vm.treeItemClick(node)` which fires the page's own encrypted fetch and writes decrypted rows to `vm._data.bestsellerData`.

2. **Site switching via localStorage, not URL**: sorftime's `?i=N` URL param is decorative. Real site switching is `localStorage.setItem("site", "N")` + reload. Site IDs are NOT zero-padded: `1`=US, `7`=JP, `14`=SA. See `common.SITE_TO_CODE`.

3. **14 sites, not 10**: sorftime covers more markets than sellersprite — adds AE/AU/BR/SA. Site IDs are also reordered vs sellersprite (JP=7 here vs JP=6 there).

4. **Categories differ per site**: every site has a different set of top-level categories in its native language. JP has 19 (Japanese names), US has 27 (English), DE has ~25 (German). Always enumerate with `get_categories()` after site switch.

5. **Page init takes 4-7s**: zTree (`#bestseller110`) initializes asynchronously after Vue mounts. The script waits up to 20s for it; if your network is slow, raise the wait.

6. **Trust click requirement**: Vue's `@click` on zTree nodes requires a trusted click event. Synthetic `dispatchEvent` and WebBridge's `click` action both fail silently. The fix is calling `vm.treeItemClick(node)` directly — it's the same function Vue would call.

7. **Free tier is fully open for Best Seller**: unlike other sorftime modules, the Best Seller TOP100 is shown to all logged-in users without paywall masking. Per-category = exactly 100 rows (sometimes 98-99 if a product is temporarily delisted).

8. **Category tree is lazy**: only top-level nodes are loaded initially. Sub-categories load on expand. We only fetch top-level (the leaf-Best-Sellers are per top-category, not per sub-category).

9. **"selectNodeId" stays empty until first selection**: after page load, `vm._data.selectNodeId === 0` (numeric). After `treeItemClick(node)`, it becomes the node's slug (`"baby-products"`). Use this to detect when data is ready.

## Architecture note

| | bestseller (DOM-driven) | sellersprite-products (API-first) |
|---|---|---|
| Trigger | `vm.treeItemClick(node)` | `POST /v3/api/product-research` |
| Auth | Reuse page's encrypted session | Cookie via `credentials: "include"` |
| Response | Read from Vue VM | JSON response body |
| Page reload | Per station (site switch) | Per session |

## See also

- `references/api_notes.md` — full state-machine + JS source breakdown
- `references/environment.md` — Windows/bash/jq/heredoc quirks
- `references/analysis_recipe.md` — multi-station report template structure
- `scripts/fetch_bestseller.py` — main scraper
- `scripts/analyze.py` — multi-station comparison report generator
