# sorftime-checkmarket API Notes

## searchBox VM State (market-specific)

### Input Fields

| Field | Path | Type | Notes |
|---|---|---|---|
| Search text | `market.search` | string | Main input |
| Textarea show | `market.textareaShow` | boolean | Must be `true` |
| Search mode | `market.model` | number | 1-7 |
| Loading | `checkMarketBtnLoading` | boolean | NOT `btnLoading` |

### Trigger Method

- `onMarketSearchClick()` — executes market search.

### Market Table Columns (12)

| Index | Key | Description |
|---|---|---|
| 0 | — | checkbox |
| 1 | category | 类目名称 |
| 2 | parent_category | 所属大类 |
| 3 | monthly_sales | Listing月销量 |
| 4 | avg_price | 平均价格 |
| 5 | new_product_ratio | 新品占比 |
| 6 | fba_self_ratio | 自营/FBA占比 |
| 7 | avg_reviews | 评价数 |
| 8 | avg_rating | 星级 |
| 9 | head_sales_ratio | 头部占比 |
| 10 | sales_distribution | 销量分布 |
| 11 | is_seasonal | 周期市场 |
