# sorftime-checkproduct Analysis Recipe

## Report Sections

### 1. 查询概览
- ASIN count
- Station count
- Date/time of report generation

### 2. 跨站点对比
For ASINs found in multiple stations:
- Per-ASIN comparison table: station, month_sales, year_sales, price, rating, reviews, brand, listing_date

### 3. 各站点详情
Per-station breakdown:
- Table: ASIN, month_sales, year_sales, price, rating, reviews, brand, listing_date

### 4. 价格对比
All rows sorted by ASIN + station:
- ASIN, station, price, seller_type, ship_method

### 5. 评价与星级对比
All rows sorted by ASIN + station:
- ASIN, station, rating, reviews, month_sales

## Usage
```bash
python scripts/analyze.py --results data/products.csv --out-md reports/report.md
```
