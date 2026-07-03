# sorftime-checkkeyword API Notes

## searchBox VM State (keyword-specific)

| Field | Path | Notes |
|---|---|---|
| Search text | `keywordSearch` | Direct keyword input |
| Search list | `keywordSearchList` | Mirror of keywordSearch |
| Dialog data | `keywordCheck.multipleCheck` | ASIN reverse-lookup dialog |
| Type | `keywordType` | 1=模糊, 2=精准 |
| Temp type | `keywordTempType` | Template type |

## Trigger Methods

- `onKeywordSearch()` — main search trigger
- Dialog sequence: `onKeywordBoxOpen()` → `onKeywordDataChange()` → `onKeywordCheckedChange()` → `onKeywordDataOk()`

## Table Layout (6 tables)

| Idx | Content |
|-----|---------|
| 0 | 子体流量占比/自然-广告流量构成 |
| 1 | 子体流量来源/关键词列表 |
| 2 | ABA关键词数据/热搜趋势 |
| 3 | 流量来源(重复) |
| 4 | 关键词+趋势 |
| 5 | 暂无数据 placeholder |
