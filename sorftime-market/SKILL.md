---
name: sorftime-market
description: Pull Amazon market-trend data from sorftime 选市场 (/home/choosemarketblock) across 14 marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill — drives sideMarket.initData(nodeId) to trigger the encrypted databoard POST, then reads marketTrendChartData (20 trend items per fetch with title/price/sale/search indices). Limited surface compared to product/bestseller: the full market dashboard has multi-tab statistical panels that require additional UI interaction beyond free tier; only marketTrendChartData is reliably readable.
---

# sorftime-market

Fetch **Amazon market-trend indicators** from **sorftime 选市场** (`/home/choosemarketblock`).

This page is the most complex of sorftime's six 选品 modules — it's a multi-tab dashboard showing aggregated category stats: trend chart, brand matrix, price distribution, seller nationality breakdown, etc. Each category node triggers an encrypted POST to `api.sorftime.com/api/marketboard/databoard?site=NN` that populates multiple Vue state slices.

**Free-tier reality**: only `marketTrendChartData` populates reliably after `initData(nodeId)`. The other slices (`statisticalData.offlineData`, `marketBoard.items`, `brandData`, etc.) need additional UI clicks (sub-tabs, filter buttons) to populate. This skill focuses on the trend chart; deeper dashboard scraping is out of scope.

## Quick start

```bash
# Single station with default category list
python scripts/fetch_markets.py --station US \
    --out data/us_markets.csv

# Multi-station with custom categories
python scripts/fetch_markets.py --station US,JP,GB \
    --categories baby-products,beauty,home-kitchen \
    --out data/by_station_markets.csv

# Generate report
python scripts/analyze.py --markets data/by_station_markets.csv \
    --out-md reports/markets_by_station.md
```

## Requirements

- **Kimi WebBridge daemon** running and extension connected
- **sorftime login** in the same browser profile
- Python 3.10+ (no third-party packages)

## What you get

Each CSV row = one trend chart item (top 20 per category trigger), with:

| Field | Meaning |
|---|---|
| `station` / `station_name` | Amazon marketplace code + 中文 |
| `category_nodeId` / `category_name` / `category_slug` | The triggered category |
| `trend_rank` | 1-20 within this category trigger |
| `title` | Item title (or `"--"` if masked) |
| `item_nodeId` | Item's category node |
| `price_show` | Price index/avg |
| `sale_show` | Sales index (sort key) |
| `search_show` | Search volume index |
| `pricsale_show` | Price×sales composite |

## CLI flags

| Flag | Notes |
|---|---|
| `--station` | Required. Comma-separated site codes |
| `--out` | Required. CSV output path |
| `--categories` | Optional. Comma-separated slugs/names/nodeIds. Falls back to first 5 auto-discovered |
| `--sleep-per-node` | Default 4.0s. Wait between trigger and read |

## Gotchas

1. **DOM-driven**: encryption on POST body prevents direct API calls. Drive `vm.initData(nodeId)` and read decrypted state from Vue.

2. **Only `marketTrendChartData` reliably populates**: The dashboard has 4+ tabs (统计 / 榜单 / 品牌 / 卖家) each with their own encrypted fetch triggered by sub-tab clicks. Without clicking those, the slices remain empty. This skill documents and accepts this limit.

3. **No zTree**: unlike bestseller, 选市场 uses a search box + custom Vue tree (`categoryListData` on the sideMarket VM). Auto-discovery reads `categoryListData` to enumerate nodes.

4. **Page has 4 sub-modes**: 多维度选市场 (default) / 消费需求选市场 / 自营新品选市场 / 低价商城选市场. Each mode has its own VM and data shape. This skill targets only 多维度选市场.

5. **Per-station category set**: each site has its own category list (US ~27, JP ~19, etc.). Auto-discovery handles this; don't hardcode.

6. **localStorage site switching**: same as bestseller — set `localStorage["site"]` then reload. URL `?i=` param does NOT work.

7. **14 sites (not 10)**: US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA. Same mapping as bestseller/product.

8. **Page init 7s**: Vue mount + axios + jQuery bootstrap is slow; `ensure_market_page` sleeps 7s after navigate.

9. **Category slug discovery is best-effort**: auto-discovery reads `categoryListData` from VM; if your requested slug doesn't match, script falls back to first 5 discovered nodes (to avoid producing an empty CSV).

## Architecture note

| | market | bestseller | product |
|---|---|---|---|
| Trigger | `vm.initData(nodeId)` | `vm.treeItemClick(node)` | auto on page load |
| Per fetch | 20 trend items | 100 ASINs (full TOP100) | ~20 unmasked ASINs |
| Use case | Category-level trend overview | Per-category ASIN drill-down | Whole-site top board |
| Surface | Partial (free-tier limit) | Full | Partial (ASIN-mask) |

For per-ASIN analysis use `sorftime-bestseller` or `sorftime-product`. Use `sorftime-market` for category-level price/sale/search indices.

## See also

- `references/api_notes.md` — VM state structure + known data slices
- `references/environment.md` — Windows/bash/jq/heredoc quirks
- `references/analysis_recipe.md` — multi-station report template
- `scripts/fetch_markets.py` — main scraper
- `scripts/analyze.py` — multi-station report generator
