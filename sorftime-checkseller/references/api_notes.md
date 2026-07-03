# sorftime-checkseller API Notes

## searchBox VM State (seller-specific)

### Input Fields

| Field | Path | Type | Notes |
|---|---|---|---|
| Search text | `checkseller.search` | string | Main input |
| Search data | `checkseller.searchData` | array | Auto-populated |
| Textarea show | `checkseller.textareaShow` | boolean | Must be `true` |
| Search mode | `checkseller.model` | number | 1=ASIN, 2=品牌, 3=卖家, 4=关键词 |

### Mode Options

| Value | Label | placeholder |
|---|---|---|
| 1 | 按ASIN查 | 请输入ASIN，查找buybox卖家 |
| 2 | 按品牌名称查 | 请输入品牌全称 |
| 3 | 按卖家名称查 | 请输入卖家全称 (default) |
| 4 | 按热搜关键词查找 | 请输入关键词（ABA热搜词） |

### Trigger Method

- `onSellerSearch()` — executes seller search. No dialog sequence needed.

### Seller Table Columns

19 data columns:
| Index | Key | Description |
|---|---|---|
| 0 | — | checkbox |
| 1 | — | 序号 |
| 2 | seller | 卖家名称 |
| 3 | seller_country | 卖家国籍/地区+公司 |
| 4 | total_products | 全部产品数 |
| 5 | total_brands | 总品牌数 |
| 6 | top400_products | Top400产品数 |
| 7 | top400_brands | Top400品牌数 |
| 8 | monthly_sales_sum | 月销量和 |
| 9 | monthly_sales_amount_sum | 月销额和 |
| 10 | avg_price | 平均价格 |
| 11 | avg_reviews | 平均评价数 |
| 12 | head_product_sales_ratio | 头部占比 |
| 13-18 | new_* | 新品指标 |
