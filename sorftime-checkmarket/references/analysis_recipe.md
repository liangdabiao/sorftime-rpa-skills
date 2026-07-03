# sorftime-checkmarket Analysis Recipe

## Report Sections

### 1. 查询概览
- Query count, station count, search mode, report time

### 2. 市场概要
- Unique categories, stations, total monthly sales

### 3. 跨站点市场对比
- Markets appearing in multiple stations

### 4. 各站点详情
- Per-station market breakdown

### 5. 市场指标对比
- All rows sorted by station + category

## Usage
```bash
python scripts/analyze.py --results data/market.csv --out-md reports/market_report.md
```
