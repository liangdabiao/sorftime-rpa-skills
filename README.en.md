# sorftime-rpa

Browser-RPA + data-analysis project for **sorftime.com** (Amazon seller analytics SPA). Covers 6 "选品" (selection) modules, each as an independent skill.

## Module coverage

| Skill | sorftime path | Mode | Data availability |
|---|---|---|---|
| **sorftime-bestseller** | `/home/bestseller` | DOM-driven, per-category trigger | ✅ Full TOP100 |
| **sorftime-product** | `/home/chooseproduct` | DOM-driven, auto-load | ⚠️ ~20 unmasked ASINs per station (free tier) |
| **sorftime-market** | `/home/choosemarketblock` | DOM-driven, `initData(nodeId)` | ⚠️ Only `marketTrendChartData` (20 items/trigger) |
| **sorftime-keyword** | `/home/choosekeyword` | DOM-driven, filter-gated | ⚠️ Requires manual category selection |
| **sorftime-brand** | `/home/choosebrand` | DOM-driven, filter-gated | ⚠️ Requires manual category selection |
| **sorftime-seller** | `/home/chooseseller` | DOM-driven, filter-gated | ⚠️ Requires manual category selection |

### Query modules (check)

| Skill | sorftime path | Input | Output dimensions |
|---|---|---|---|
| **sorftime-checkproduct** | `/home/checkproduct` | ASIN (batch, up to ~100) | Product details: price/sales/reviews/BSR/brand/seller |
| **sorftime-checkbrand** | `/home/checkbrand` | Brand name / ASIN / seller name / company / keyword | Brand matrix: products/sellers/Top100/sales/avg-price |
| **sorftime-checkseller** | `/home/checkseller` | Seller name / ASIN / brand / keyword | Seller store: products/Top400/monthly-sales/avg-price |
| **sorftime-checkmarket** | `/home/checkmarket` | Category name / ASIN / keyword | Market overview: monthly-sales/avg-price/new-ratio/rating |
| **sorftime-checkkeyword** | `/home/checkkeyword` | ASIN / keyword (experimental) | Multi-table: traffic sources/ABA keywords/trends |

**14 Amazon marketplaces supported**: US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA

## Architecture

- **kimi-webbridge driven**: controls browser via local daemon (`http://127.0.0.1:10086`)
- **DOM-driven scraping**: sorftime's API encrypts request/response bodies with AES (`{v:3, k, d}` format), so direct API calls are impossible. Each skill drives the Vue VM's built-in methods (`treeItemClick`, `initData`, `onPageSizeChange`, etc.) to trigger encrypted POSTs, then reads decrypted data from Vue reactive state
- **Python stdlib only**: no third-party dependencies
- **CSV + Markdown reports**: each skill has `fetch_*.py` + `analyze.py`

## Quick start

```bash
# 1. Check WebBridge daemon
~/.kimi-webbridge/bin/kimi-webbridge status

# 2. Fetch (example: bestseller 3 stations)
python .claude/skills/sorftime-bestseller/scripts/fetch_bestseller.py \
    --station US,JP,GB --out data/best.csv

# 3. Generate comparison report
python .claude/skills/sorftime-bestseller/scripts/analyze.py \
    --bestsellers data/best.csv --out-md reports/best.md

# 4. Check module: ASIN reverse lookup
python .claude/skills/sorftime-checkproduct/scripts/fetch_checkproduct.py \
    --station US,JP --asins B0CHX1W1XY --out data/product_check.csv

# 5. Check module: brand matrix
python .claude/skills/sorftime-checkbrand/scripts/fetch_checkbrand.py \
    --station US,JP --mode brand --queries "Anker,Baseus" --out data/brands.csv
```

## Project structure

```
sorftime-rpa/
├── README.md                    (Chinese primary version)
├── README.en.md                 (this file)
├── CLAUDE.md                    (Claude Code project guide)
├── phase1_investigation.md      (investigation notes)
├── .claude/skills/
│   ├── sorftime-bestseller/     (✅ full TOP100)
│   ├── sorftime-product/        (⚠️ free-tier ~20 ASINs)
│   ├── sorftime-market/         (⚠️ trend chart only)
│   ├── sorftime-keyword/        (⚠️ filter-gated, diagnostic)
│   ├── sorftime-brand/          (⚠️ filter-gated, diagnostic)
│   ├── sorftime-seller/         (⚠️ filter-gated, diagnostic)
│   ├── sorftime-checkproduct/   (✅ ASIN reverse lookup)
│   ├── sorftime-checkbrand/     (✅ brand matrix, 5 modes)
│   ├── sorftime-checkseller/    (✅ seller data, 4 modes)
│   ├── sorftime-checkmarket/    (✅ market overview, 6 modes)
│   └── sorftime-checkkeyword/   (🔬 experimental, 5 sub-modes)
├── data/                        (CSV output)
└── reports/                     (Markdown reports)
```

## Known limitations

### sorftime API encryption
sorftime encrypts all API request/response bodies via an obfuscated AES routine. Direct calls to `api.sorftime.com/*` are impossible. All skills indirectly call the API via Vue VM's built-in methods.

### Free-tier masking
- **bestseller**: fully open (full TOP100 per category)
- **product**: ~20 unmasked ASINs per station (rest show `ASIN="--"`)
- **market**: `marketTrendChartData` exposed (20 trend items per trigger); other panels need deeper UI interaction
- **keyword/brand/seller**: filter-gated pages, must manually open 「类目」dialog first

### Filter-gated pages (keyword/brand/seller)
These 3 pages share the `side-Keyword` Vue VM, but require the user to:
1. Open the 「类目」category dialog
2. Pick specific categories
3. Close the dialog

After that, `keywordData.List` / `table.node.data` populates. Scripts read VM current state, so if the user has selected categories in the same session, the script will pick up the data. **Full reverse-engineering of the category dialog's Vue component interaction** is left as future work.

## 14 site mapping

| Code | Site | Name |
|---|---|---|
| 1 | US | USA |
| 2 | GB | UK |
| 3 | DE | Germany |
| 4 | FR | France |
| 5 | IN | India |
| 6 | CA | Canada |
| 7 | JP | Japan |
| 8 | ES | Spain |
| 9 | IT | Italy |
| 10 | MX | Mexico |
| 11 | AE | UAE |
| 12 | AU | Australia |
| 13 | BR | Brazil |
| 14 | SA | Saudi Arabia |

Site switching:
- **Selection pages** (bestseller/product/market/keyword/brand/seller): `localStorage.setItem("site", "<code>")` + `location.reload()` (URL `?i=` param does NOT work)
- **Check pages** (checkproduct/checkbrand/checkseller/checkmarket/checkkeyword): URL `?i=<code>` works directly

## Sister projects

- **`fastmoss-rpa`** — TikTok Shop analytics (fastmoss.com)
- **`sellersprite-rpa`** — Amazon seller analytics (sellersprite.com, 10 sites)

sorftime-rpa reuses the DOM-driven pattern and report templates from those projects.

## Tooling

- **Python 3.10+** (stdlib only)
- **Kimi WebBridge**: `~/.kimi-webbridge/bin/kimi-webbridge status`
- **bash shell** (Git Bash on Windows works)
