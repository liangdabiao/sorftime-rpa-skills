# sorftime-checkkeyword Analysis Recipe

## Report Sections

### 1. 查询概览
- Query count, station count, search mode, report time

### 2. 表结构摘要
- Which tables had data per query

### 3. 各表数据
- Raw per-table output

## Usage
```bash
python scripts/analyze.py --results data/keywords.csv --out-md reports/keyword_report.md
```
