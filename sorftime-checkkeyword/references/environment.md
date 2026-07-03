# sorftime-checkkeyword Environment Notes

## Page Layout
- URL: `/home/checkkeyword?d=<d_param>&i=<site_code>`
- 5 sub-mode buttons at top: 查产品流量结构, 反查关键词, 反查出单词, 查关键词流量趋势, 查关键词广告策略
- Date range selector: "最近30天"
- "查询" button to submit

## Table Structure

The keyword page has ~6 tables loaded simultaneously:

| Index | Type | Columns |
|-------|------|---------|
| 0 | 子体流量占比 | 子体, 总流量占比, 自然-广告流量构成 |
| 1 | 流量来源 | 子体, 流量来源, 全部关键词, 自然流量词, SP/SB/SBV广告流量词 |
| 2 | ABA关键词 | 关键词, 热搜趋势, 曝光形式, 流量来源 |
| 3 | (same as 1) | Duplicate |
| 4 | 关键词+趋势 | (similar to 2) |
| 5 | Empty placeholder | — |

## Known Complexities

- Multiple tables require different reading strategies
- Dialog sequence needed for ASIN reverse-lookup mode
- Some modes may not populate all tables
- Complex page layout makes single-read approach difficult
