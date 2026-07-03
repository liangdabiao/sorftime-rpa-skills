# sorftime-checkkeyword Skill

Keyword research module for sorftime.com. **Experimental** — page has 6+ complex sub-tables.

## Pages

- `/home/checkkeyword` — keyword analysis page
- 5 sub-modes: 查产品流量结构, 反查关键词, 反查出单词, 查关键词流量趋势, 查关键词广告策略

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/common.py` | Shared helpers (trigger via dialog or direct keyword) |
| `scripts/fetch_checkkeyword.py` | Main scraper |
| `scripts/analyze.py` | Report generator |

## Usage

```bash
# Reverse keyword lookup by ASIN
python scripts/fetch_checkkeyword.py --station US --mode reverse --queries B0CHX1W1XY
```

## Known Limitations

- Page has ~6 tables with different column structures
- Some sub-modes may require specific dialog flows (onKeywordBoxOpen sequence)
- Results stored as col0-colN columns (dynamic) due to variable table structures
- See references/environment.md for detailed table descriptions
