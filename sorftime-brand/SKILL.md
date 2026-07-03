---
name: sorftime-brand
description: Probe sorftime 选品牌 (/home/choosebrand) page state across 14 Amazon marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill — the brand page reuses the same side-Keyword VM as the keyword page but with brand-specific column schema (Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket). Filter-gated page — requires manual category dialog interaction to populate data. Skill reads populated rows when available and emits state summary CSV documenting which stations need further UI interaction.
---

# sorftime-brand

Probe **Amazon brand board** from **sorftime 选品牌** (`/home/choosebrand`).

This page shares the same Vue infrastructure as the keyword page (same `side-Keyword` master VM) but exposes brand-level metrics. Same filter-gated limitation applies.

## Quick start

```bash
python scripts/fetch_brands.py --station US --out data/us_brand_state.csv
python scripts/fetch_brands.py --station US,JP,GB --out data/brand_state.csv
python scripts/analyze.py --brands data/brand_state.csv \
    --out-md reports/brand_state.md
```

## Requirements

- **Kimi WebBridge daemon** running and extension connected
- **sorftime login** in the same browser profile
- Python 3.10+ (no third-party packages)

## What you get

A CSV with one row per station, summarizing the side-Keyword VM state:

| Field | Meaning |
|---|---|
| `station` / `station_name` | Amazon marketplace code + 中文 |
| `vm_found` | Whether side-Keyword VM was located |
| `loading` | Page's loading flag |
| `table_data_len` | Rows in `table.node.data` |
| `table_total_count` | `page.totalCount` |
| `column_count` | Number of columns (always 11) |
| `column_props` | Comma-separated column prop names |
| `column_labels` | Comma-separated column display labels |
| `screen_select` | Selected categories string |
| `screen_nodeData_keys` | Comma-separated selected node IDs |
| `sample_row_json` | First row JSON if populated |

## CLI flags

| Flag | Notes |
|---|---|
| `--station` | Required. Comma-separated site codes |
| `--out` | Required. CSV output path |
| `--sleep` | Page init sleep (default 8.0s) |

## Gotchas

1. **Filter-gated page**: brand page requires explicit category dialog interaction. Same limitation as keyword page.

2. **Reuses side-Keyword VM**: despite the name "side-Keyword", this VM is shared across keyword/brand/seller pages. The URL determines which encrypted API is called (`/api/keywordboard/*` vs brand-specific endpoint).

3. **Brand-specific column schema (11 cols)**: Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket.

4. **DOM-driven (encrypted API)**: Same encryption story as other skills. We read post-decryption state from Vue.

5. **14 sites**: US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA.

6. **localStorage site switching**: `localStorage["site"]` then reload.

7. **Page init 8s**: Same as keyword — heavy Vue mount.

## When this skill returns empty data

Same as keyword skill:
1. Open sorftime in browser
2. Navigate to `/home/choosebrand`
3. Manually open 「类目」dialog and select categories
4. Run `fetch_brands.py` while that session is active
5. Script reads the now-populated VM state

## Architecture note

| | brand | keyword | bestseller | product |
|---|---|---|---|---|
| VM | side-Keyword | side-Keyword | (bestseller VM) | productboard VM |
| Filter gated | YES | YES | NO | NO |
| Per fetch | variable | variable | 100 ASINs | ~20 ASINs |

## See also

- `references/api_notes.md` — encrypted API + column schema
- `references/environment.md` — Windows/bash quirks
- `references/analysis_recipe.md` — state report template
- `scripts/fetch_brands.py` — main scraper (state probe)
- `scripts/analyze.py` — multi-station report generator
