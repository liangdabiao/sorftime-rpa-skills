# sorftime-checkbrand Analysis Recipe

## Report Sections

### 1. 查询概览
- Query count
- Station count
- Search mode
- Date/time of report generation

### 2. 品牌概要
- Total unique brands found
- Total product count across brands
- Total seller count

### 3. 跨站点品牌对比
For brands found in multiple stations:
- Per-brand comparison table: station, total_products, total_sellers, top100, sales, price, reviews

### 4. 各站点详情
Per-station breakdown:
- Table: brand, query, mode, total_products, total_sellers, top100, sales, price

### 5. 品牌指标对比
All rows sorted by station + brand:
- station, brand, product_count_ratio, bs_top100_product_count, monthly_sales, head_product_sales_ratio

## Usage
```bash
python scripts/analyze.py --results data/brands.csv --out-md reports/brand_report.md
```
