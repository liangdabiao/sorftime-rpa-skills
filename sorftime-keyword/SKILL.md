---
name: sorftime-keyword
description: Probe sorftime 关键词趋势选品 (/home/choosekeyword) page state across 14 Amazon marketplaces (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA). DOM-driven skill that navigates + probes the side-Keyword Vue VM to read whatever keyword data is currently populated. NOTE: this page is filter-gated — unlike bestseller/product which auto-load, the keyword board only populates after the user manually opens the 类目 dialog and selects categories. The skill reads populated rows when available and emits a state summary CSV documenting which stations need further UI interaction. Full UI-flow automation (open tree dialog → select categories → close → trigger loadKeyword) is left as future work.
---

# sorftime-keyword

Probe **Amazon keyword trend board** from **sorftime 关键词趋势选品** (`/home/choosekeyword`).

This page is a filter-gated keyword board. The default UI shows "已选全部类目" (all categories selected) in the filter chip, but the underlying `side-Keyword.keywordData.List` is empty until a user explicitly opens the 「类目」tree dialog and picks specific categories.

**This skill is diagnostic-focused**: it navigates, probes the Vue VM state, and reads whatever data IS populated. For full automation (programmatic category selection), see `references/api_notes.md` for the unfinished investigation path.

## Quick start

```bash
# Single station probe
python scripts/fetch_keywords.py --station US \
    --out data/us_keyword_state.csv

# Multi-station probe
python scripts/fetch_keywords.py --station US,JP,GB \
    --out data/keyword_state.csv

# Generate state report
python scripts/analyze.py --keywords data/keyword_state.csv \
    --out-md reports/keyword_state.md
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
| `vm_found` | Whether side-Keyword VM was located (true/false) |
| `loading` | Page's loading flag |
| `table_data_len` | Rows in `table.node.data` (0 if filter not applied) |
| `table_total_count` | `page.totalCount` |
| `column_count` | Number of columns in `table.node.options` (always ~11) |
| `screen_select` | Selected categories string (empty if nothing picked) |
| `screen_nodeData_keys` | Comma-separated selected node IDs |
| `site` | The numeric site code |
| `sample_row_json` | First row JSON if populated |

## CLI flags

| Flag | Notes |
|---|---|
| `--station` | Required. Comma-separated site codes |
| `--out` | Required. CSV output path |
| `--sleep` | Page init sleep (default 8.0s) |

## Gotchas

1. **Filter-gated page**: this is the ONLY sorftime 选品 page that doesn't auto-populate on navigation. The other 5 (bestseller, product, market, brand, seller) all load data on page nav or single-click category trigger.

2. **DOM-driven (encrypted API)**: POST to `/api/keywordboard/querykeywordboard?site=NN` with AES-encrypted body. Response is also encrypted (`{v:3, k, d}` format). We can't call this directly; the VM-driven approach reads post-decryption state from Vue.

3. **UI flow needed for data**: to actually populate keyword rows, the user must:
   - Click the 「类目」chip in the filter bar
   - In the popover dialog, navigate the category tree
   - Tick specific categories
   - Click confirm
   - Then `keywordData.List` populates from the encrypted response

4. **Pagination 20/page**: when data IS populated, default page size is 20.

5. **Column schema fixed**: `table.node.options` is an 11-column schema including Top, SearchVolume, SearchConversionRate, KeywordTrend, TopDiff, etc. These are always populated regardless of data state.

6. **`sideMarket` VM also present**: keyword page has a `sideMarket` VM at depth ~5 with `categoryListData` (empty until category dialog opens). This is the same VM as the market page.

7. **14 sites (not 10)**: US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA.

8. **localStorage site switching**: same as bestseller — `localStorage["site"]` then reload.

9. **Page init 8s**: keyword page is heavier than bestseller (more sub-VMs, more dialogs); use `--sleep 8`.

## When this skill returns empty data

The CSV will show `table_data_len=0` for stations where the category dialog hasn't been used. To get real data:

1. Open sorftime in browser
2. Navigate to `/home/choosekeyword`
3. Manually open 「类目」dialog and select categories
4. Run `fetch_keywords.py` while that browser session is still active
5. The script reads the now-populated VM state

For programmatic category selection, see `references/api_notes.md` (unfinished investigation).

## Architecture note

| | keyword | bestseller | product |
|---|---|---|---|
| Filter gated | YES (UI dialog needed) | NO (auto) | NO (auto) |
| Per fetch | variable (often 0 without UI) | 100 ASINs | ~20 unmasked |
| Surface | Diagnostic only | Full TOP100 | Partial (ASIN-mask) |

## See also

- `references/api_notes.md` — encrypted API + unfinished UI-flow investigation
- `references/environment.md` — Windows/bash/jq/heredoc quirks
- `references/analysis_recipe.md` — state report template
- `scripts/fetch_keywords.py` — main scraper (state probe)
- `scripts/analyze.py` — multi-station state report generator
