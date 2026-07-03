# sorftime-checkproduct Skill

## Purpose
Scrape ASIN-level product details from sorftime.com `/home/checkproduct` page — 15 data columns per product including sales, price, rating, brand, and listing age — across 14 Amazon marketplaces.

## Architecture
- **DOM-driven**: sorftime encrypts all API bodies, so the scraper drives the searchBox Vue VM to trigger encrypted POSTs, then reads decrypted results from the DOM table.
- **Input**: ASIN(s) via CLI or CSV file
- **Output**: CSV (one row per ASIN per station) + Markdown cross-station comparison report

## Workflow
1. Navigate to `https://seller.sorftime.com/home/checkproduct?d=<d_param>&i=<site>`
2. Wait 8s for Vue mount + initial API calls
3. Find `searchBox` VM via Vue tree traversal
4. Set ASIN textarea: `checkBox.asinCheck.textarea = asins`
5. Set checkbox: `checkBox.asinCheck.checked = true`
6. Set `keywordSearch` + `checkBox.search` + `<keywordSearchList`
7. Call `onProductSearch()` (native bound function)
8. Poll `btnLoading` until false (search complete)
9. Read results from DOM `.el-table`

## Data Columns (15)
| # | Column | Description | Notes |
|---|--------|-------------|-------|
| 1 | (checkbox) | Selection checkbox | |
| 2 | 产品名称 | Product title + ASIN | ASIN in `(B0XXXXXXXX)` |
| 3 | Listing月销量 | Monthly sales estimate | |
| 4 | Listing年销量 | Yearly sales estimate | |
| 5 | ASIN月销量 | ASIN monthly sales (Amazon) | `--` if hidden by Amazon |
| 6 | 实际价格 | Price + margin + FBA fee | Format: `price (margin \| FBA)` |
| 7 | 类目 | Category / BSR | BSR rank in category tree |
| 8 | 隐赚指数 | Hidden profit score | `--` if not enough data |
| 9 | 广告花费指数 | Ad spend index | `<50 low, 50-150 medium, >150 high` |
| 10 | 发货方式 | Shipping method | FBA / FBM |
| 11 | BBX卖家属性 | Buy Box seller | 第三方 / 亚马逊自营 |
| 12 | 品牌 | Brand name | |
| 13 | 评分星级 | Star rating | 1.0 – 5.0 |
| 14 | 评价数量 | Review count | |
| 15 | 上架时间 | Listing date + age | e.g. `2019-11-122425天` |

## Free-tier Masking
- ASIN monthly sales: `--` when Amazon hides it
- Price margin: partially masked on free tier
- Hidden profit score: `--` for newly-listed products
- Some fields use `--` sentinel for unavailable data

## Limitations
- **Multi-ASIN search**: tested with up to 2 ASINs; batch size limit unknown
- **Sub-mode selection**: the scraper works in "指定asin查产品" (default) mode only. Other sub-modes (按名称查产品, 包含词查产品, 按属性查产品) are not covered
- **Other Level-1 modes**: 查关联产品/查品牌产品/查卖家产品/热搜关键词查产品/查低价产品 require separate state setup — not implemented
- **Pagination**: pagination exists (10/20/30/50 per page) but auto-paging is not implemented

## 14 Sites
US=1, GB=2, DE=3, FR=4, IN=5, CA=6, JP=7, ES=8, IT=9, MX=10, AE=11, AU=12, BR=13, SA=14

## Quick Start
```bash
python .claude/skills/sorftime-checkproduct/scripts/fetch_checkproduct.py \
    --station US,JP,GB --asins B0CHX1W1XY,B0BDHZ8Q63 \
    --out data/checkproduct_results.csv

python .claude/skills/sorftime-checkproduct/scripts/analyze.py \
    --results data/checkproduct_results.csv --out-md reports/checkproduct_report.md
```
