# sorftime-checkbrand Skill

Brand intelligence module for sorftime.com — search brands across 14 Amazon marketplaces and extract brand-level metrics.

## Pages

- `/home/checkbrand` — brand search page
- 5 search modes: 按品牌名称查 (1), 按ASIN查 (2), 按卖家名称查 (3), 按卖家公司查 (4), 按热搜关键词查 (5)

## Workflow

1. `ensure_check_page(site_code, session)` — navigate with `?d=<d_param>&i=<site>`
2. `find_searchbox_vm(session)` — locate the searchBox VM (53 keys, `name === 'searchBox'`)
3. `trigger_brand_search(text, mode, session)` — set brand fields and call onBrandSearch()
4. `wait_for_brand_search(timeout, session)` — poll `btnLoading` until false
5. `read_brand_table(session)` — extract brand summary rows from DOM `.el-table`

## Brand Table Columns

| Index | Field | Description |
|-------|-------|-------------|
| 0 | (checkbox) | Selection |
| 1 | brand_name | Brand name (text mixed with tooltip junk) |
| 2 | total_products | Total products in brand |
| 3 | total_sellers | Total sellers of brand |
| 4 | top100_products | Products in BSR Top100 |
| 5 | top100_new_products | New products in BSR Top100 |
| 6 | product_count_ratio | Brand product count / all products |
| 7 | monthly_sales_sum | Total monthly sales volume |
| 8 | monthly_sales_amount_sum | Total monthly sales amount |
| 9 | avg_price | Average product price |
| 10 | avg_reviews | Average review count |
| 11 | head_product_sales_ratio | Top N products sales share |
| 12 | new_product_count | New products (指定月份) count |
| 13 | new_seller_count | New products seller count |
| 14 | new_avg_price | New products avg price |
| 15 | new_avg_rating | New products avg rating |
| 16 | new_avg_reviews | New products avg reviews |
| 17 | new_avg_sales | New products avg sales |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/common.py` | Shared helpers (navigate, evaluate, trigger, read table) |
| `scripts/fetch_checkbrand.py` | Main scraper — CLI args for station/mode/queries |
| `scripts/analyze.py` | Markdown report generator |

## Usage

```bash
# Single brand, US station
python scripts/fetch_checkbrand.py --station US --mode brand --queries Anker --out data/brand.csv

# Multiple queries, multiple stations
python scripts/fetch_checkbrand.py --station US,JP,GB --mode brand --queries "Anker,Baseus" --out data/brands.csv

# ASIN mode
python scripts/fetch_checkbrand.py --station US --mode asin --queries B0CHX1W1XY

# From CSV
python scripts/fetch_checkbrand.py --station US --mode brand --input brands.csv --out data/brands.csv

# Generate report
python scripts/analyze.py --results data/brands.csv --out-md reports/brand_report.md
```

## Known Limitations

- Brand name from column 1 includes junk text from hover elements (tooltips). Cleaned via regex.
- Each brand search returns a single summary row. For product-level details, use checkproduct.
- Multi-line brand input (one-per-line) is not supported — use separate --queries entries.
- Free tier: some metrics show `--` when data is masked.
