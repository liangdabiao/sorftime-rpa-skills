---
name: sorftime-product
description: Pull Amazon top-product board from sorftime.com 产品 / 选品 (/home/chooseproduct) across 14 marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill — sorftime encrypts API bodies; we drive the page's own Vue VM to load data and read decrypted rows from productboard.data. Free tier exposes ~20 unmasked ASINs per station per fetch (the rest show ASIN="--" with numeric fields only). Returns 22 fields including ASIN/title/brand/price/profit/sales/reviews/seller.
---

# sorftime-product

Fetch **Amazon top products** from **sorftime 选品** (`/home/chooseproduct`).

This page presents a "product board" — the default view shows the top ~5,213 products on US (varies by site), sortable by sales, price, BSR, etc. Free tier only fully exposes ~20 ASINs per fetch (ASIN/Name/Brand visible); the rest of the 100-row page shows masked values like `ASIN="--"` with numeric fields only (useful for aggregate stats but not for cross-reference).

## Quick start

```bash
# Single station
python scripts/fetch_products.py --station US --out data/us_products.csv

# Multi-station
python scripts/fetch_products.py --station US,JP,GB --out data/by_station.csv

# Generate report
python scripts/analyze.py --products data/by_station.csv --out-md reports/by_station.md
```

## Requirements

- **Kimi WebBridge daemon** running and extension connected
- **sorftime login** in the same browser profile
- Python 3.10+ (no third-party packages)

## What you get

Each CSV row = one product-board ASIN, with 22 fields:

| Field | Meaning |
|---|---|
| `station` / `station_name` | Amazon marketplace code + 中文 |
| `rank` | 1-20 (visible rank on the board) |
| `asin` / `parent_asin` | Child + parent ASIN |
| `name` / `brand` | Product identity |
| `price` / `single_price` | Current price + per-unit (variations) |
| `gross_profit` / `fba_fee` | FBA profit + fee |
| `page_sale_count` / `page_sale_volume` | Monthly sales units + revenue |
| `year_sale_count` | Annual sales (-9999 = unknown) |
| `score` / `comment_count` | Star rating + review count |
| `deliver` | `FBA` or `FBM` |
| `seller_nationality` | Seller country |
| `node_id` | Amazon category node |
| `update_time` / `image_url` / `asin_url` | Metadata + links |

## CLI flags

| Flag | Notes |
|---|---|
| `--station` | Required. Comma-separated site codes |
| `--out` | Required. CSV output path |
| `--page-size` | Default 100. sorftime free tier only shows ~20 unmasked regardless |

## Gotchas

1. **DOM-driven**: same encryption story as bestseller. Call `vm.onPageSizeChange(N)` to load, then read `vm._data.productboard.data`.

2. **Free-tier masking**: ASIN/Name/Brand are blanked beyond rank ~20. Other numeric fields stay visible but the row is useless for cross-reference. The script auto-filters to only emit unmasked rows.

3. **`PageSaleCount` caps at 10000**: rows showing `PageSaleCount=10000` actually mean "10000+" (the true number is masked). Treat as `>=10000` in analysis.

4. **`YearSaleCount=-9999`**: sorftime uses `-9999` as a sentinel for "unknown" or "not yet tracked". Filter these out in numeric aggregation.

5. **Page total ~5000-20000**: `vm._data.page.totalCount` shows the full board size (e.g. 5213 for US), but free tier only reveals 20 ASINs. Don't read total as your accessible sample size.

6. **VM discovery**: traverse `$children` looking for `_data` containing both `topAsinList` and `productboard`. There are ~6 levels deep — use the bundled `find_vm()` which handles this.

7. **Page init 7s**: like bestseller, the page needs time after navigate to mount Vue + fetch the encrypted board.

## Architecture note

| | product | bestseller |
|---|---|---|
| Trigger | Auto-loads on page nav | `vm.treeItemClick(node)` per category |
| Per fetch | ~20 ASINs (free tier mask) | 100 ASINs (full TOP100) |
| Use case | Broad overview of top sellers | Deep per-category drill-down |
| Best paired with | keyword/market skills | Cross-category analysis |

For category-specific TOP100, use `sorftime-bestseller`. For "show me the biggest sellers across the whole site" overview, use this skill.

## See also

- `references/api_notes.md` — full state-machine + field list
- `references/environment.md` — Windows/bash/jq/heredoc quirks
- `references/analysis_recipe.md` — multi-station report template
- `scripts/fetch_products.py` — main scraper
- `scripts/analyze.py` — multi-station report generator
