# sorftime-checkseller Analysis Recipe

## Report Sections

### 1. 查询概览
- Query count, station count, search mode, report time

### 2. 卖家概要
- Unique sellers, stations, Top400 sellers, total products

### 3. 跨站点卖家对比
- Sellers appearing in multiple stations

### 4. 各站点详情
- Per-station seller breakdown

### 5. 卖家指标对比
- All rows sorted by station + seller

## Usage
```bash
python scripts/analyze.py --results data/sellers.csv --out-md reports/seller_report.md
```
