---
name: sorftime-seller
description: Probe sorftime 选卖家 (/home/chooseseller) page state across 14 Amazon marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill — the seller page reuses the same side-Keyword VM as keyword/brand pages with the same 11-column schema (Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket). Filter-gated page — requires manual category dialog interaction to populate data. Skill reads populated rows when available and emits state summary CSV.
---

# sorftime-seller

Probe **Amazon seller board** from **sorftime 选卖家** (`/home/chooseseller`).

This page shares Vue infrastructure with keyword/brand pages. Same filter-gated limitation.

## Quick start

```bash
python scripts/fetch_sellers.py --station US --out data/us_seller_state.csv
python scripts/fetch_sellers.py --station US,JP,GB --out data/seller_state.csv
python scripts/analyze.py --sellers data/seller_state.csv \
    --out-md reports/seller_state.md
```

## Requirements

- **Kimi WebBridge daemon** running and extension connected
- **sorftime login** in the same browser profile
- Python 3.10+ (no third-party packages)

## What you get

A CSV with one row per station, summarizing the side-Keyword VM state on the seller page:

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

1. **Filter-gated page**: seller page requires explicit category dialog interaction.

2. **Reuses side-Keyword VM**: same VM as keyword/brand pages. URL determines which API endpoint is called.

3. **Same column schema as brand**: 11 cols (Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket).

4. **DOM-driven (encrypted API)**: Same encryption story. Read post-decryption state from Vue.

5. **14 sites**: US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA.

6. **localStorage site switching**: same as other skills.

7. **Page init 8s**: same as keyword/brand.

## When this skill returns empty data

Same as keyword/brand:
1. Open sorftime in browser
2. Navigate to `/home/chooseseller`
3. Manually open 「类目」dialog and select categories
4. Run `fetch_sellers.py` while session is active

## Architecture note

| | seller | brand | keyword | bestseller | product |
|---|---|---|---|---|---|
| VM | side-Keyword | side-Keyword | side-Keyword | (bestseller VM) | productboard VM |
| Filter gated | YES | YES | YES | NO | NO |
| Schema | 11 seller cols | 11 brand cols | 11 keyword cols | TOP100 ASINs | ~20 ASINs |

## See also

- `references/api_notes.md` — encrypted API + column schema
- `references/environment.md` — Windows/bash quirks
- `references/analysis_recipe.md` — state report template
- `scripts/fetch_sellers.py` — main scraper
- `scripts/analyze.py` — multi-station report generator
