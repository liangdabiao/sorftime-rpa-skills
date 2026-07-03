# sorftime-checkseller Skill

Seller intelligence module for sorftime.com — search sellers across 14 Amazon marketplaces.

## Pages

- `/home/checkseller` — seller search page
- 4 search modes: 按ASIN查 (1), 按品牌名称查 (2), 按卖家名称查 (3, default), 按热搜关键词查 (4)

## Workflow

1. `ensure_check_page(site_code, session)` — navigate with `?d=<d_param>&i=<site>`
2. `find_searchbox_vm(session)` — locate searchBox VM
3. `trigger_seller_search(text, mode, session)` — set checkseller fields, call onSellerSearch()
4. `wait_for_seller_search(timeout, session)` — poll btnLoading
5. `read_seller_table(session)` — extract seller rows from DOM `.el-table`

## Seller Table Columns

| Index | Field | Description |
|-------|-------|-------------|
| 0 | — | checkbox |
| 1 | — | 序号 |
| 2 | seller | 卖家名称 (extracted from visible span) |
| 3 | seller_country | 卖家国籍/地区 + 公司 |
| 4 | total_products | 全部产品数 |
| 5 | total_brands | 总品牌数量 |
| 6 | top400_products | 卖进Top400产品数 |
| 7 | top400_brands | 卖进Top400品牌数 |
| 8 | monthly_sales_sum | 月销量总和 |
| 9 | monthly_sales_amount_sum | 月销额总和 |
| 10 | avg_price | 平均价格 |
| 11 | avg_reviews | 平均评价数量 |
| 12 | head_product_sales_ratio | 头部产品销量占比 |
| 13 | new_product_count | 新品数量 |
| 14 | new_brand_count | 新品品牌数 |
| 15 | new_avg_price | 新品平均价格 |
| 16 | new_avg_rating | 新品平均星级 |
| 17 | new_avg_reviews | 新品平均评价数量 |
| 18 | new_avg_sales | 新品平均销量 |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/common.py` | Shared helpers |
| `scripts/fetch_checkseller.py` | Main scraper |
| `scripts/analyze.py` | Markdown report generator |

## Usage

```bash
# Search sellers by brand name
python scripts/fetch_checkseller.py --station US --mode brand --queries Anker --out data/seller.csv

# Search by seller name
python scripts/fetch_checkseller.py --station US --mode seller --queries "AnkerDirect" --out data/seller.csv

# Multi-station by ASIN
python scripts/fetch_checkseller.py --station US,JP,GB --mode asin --queries B0CHX1W1XY --out data/sellers.csv

# Generate report
python scripts/analyze.py --results data/sellers.csv --out-md reports/seller_report.md
```

## Known Limitations

- Seller name column (col 2) has notification overlay; seller name is extracted from visible `<span>`
- "暂无数据" shown when no results found
- Free tier: some metrics show `--`
