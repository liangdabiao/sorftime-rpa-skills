# sorftime-checkmarket Skill

Market/subcategory intelligence module for sorftime.com — search niche markets across 14 Amazon marketplaces.

## Pages

- `/home/checkmarket` — market search page
- 6 search modes: ASIN (1), 垂直市场挖掘 (2), 热搜关键词 (3), 指定类目 (5), 类目名称 (6, default), 类目树 (7)

## Workflow

1. `ensure_check_page(site_code, session)` — navigate with `?d=<d_param>&i=<site>`
2. `find_searchbox_vm(session)` — locate searchBox VM
3. `trigger_market_search(text, mode, session)` — set market fields, call onMarketSearchClick()
4. `wait_for_market_search(timeout, session)` — poll `checkMarketBtnLoading`
5. `read_market_table(session)` — extract market rows from DOM `.el-table`

## Market Table Columns

| Index | Field | Description |
|-------|-------|-------------|
| 0 | — | checkbox |
| 1 | category | 类目名称 |
| 2 | parent_category | 所属大类 |
| 3 | monthly_sales | Listing月销量 |
| 4 | avg_price | 平均价格 |
| 5 | new_product_ratio | 新品占比 (1/3/6月) |
| 6 | fba_self_ratio | 自营/FBA占比 |
| 7 | avg_reviews | 平均评价数 |
| 8 | avg_rating | 平均星级 |
| 9 | head_sales_ratio | 头部销量占比 |
| 10 | sales_distribution | 销量分布 |
| 11 | is_seasonal | 是否周期市场 |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/common.py` | Shared helpers |
| `scripts/fetch_checkmarket.py` | Main scraper |
| `scripts/analyze.py` | Markdown report generator |

## Usage

```bash
# Search market by category name
python scripts/fetch_checkmarket.py --station US --mode category --queries "wireless charger" --out data/market.csv

# Niche market mining by keyword
python scripts/fetch_checkmarket.py --station US --mode niche --queries "wireless charger"

# Multi-station by ASIN
python scripts/fetch_checkmarket.py --station US,JP,GB --mode asin --queries B0CHX1W1XY

# Generate report
python scripts/analyze.py --results data/market.csv --out-md reports/market_report.md
```

## Known Limitations

- Uses `checkMarketBtnLoading` instead of `btnLoading`
- Category name column has notification overlay text
- Free tier: some metrics show `--`
