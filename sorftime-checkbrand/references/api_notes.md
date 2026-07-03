# sorftime-checkbrand API Notes

## Architecture

Brand search page uses the same `searchBox` Vue VM as other check modules. API calls go through AES encryption — direct calls are not possible.

## searchBox VM State (brand-specific)

### Brand Input Fields

| Field | Path | Type | Notes |
|---|---|---|---|
| Search text | `brand.search` | string | Main input text |
| Search data | `brand.searchData` | string | Mirror of search |
| Search data str | `brand.searchDataStr` | string | Stringified search data |
| Textarea show | `brand.textareaShow` | boolean | Must be `true` |
| Search mode | `brand.model` | number | 1=品牌名称, 2=ASIN, 3=卖家名称, 4=卖家公司, 5=热搜关键词 |
| Match type | `brand.wayType` | number | 1=精准匹配, 0=模糊匹配 |

### Mode Options (`brand.modelData`)

| value | label | placeholder |
|---|---|---|
| 1 | 按品牌名称查 | 多品牌之间一行一个品牌，最多支持100个品牌查询 |
| 2 | 按ASIN查 | 请输入ASIN查询相关的品牌 |
| 3 | 按卖家名称查 | 请输入卖家名称查询此卖家相关的品牌 |
| 4 | 按卖家公司查 | 按公司名称搜索 |
| 5 | 按热搜关键词查找 | 请输入关键词（暂仅支持ABA热搜词） |

### Trigger Method

- `onBrandSearch()` — executes the brand search. No dialog sequence needed (unlike checkproduct).

### Loading State

- `btnLoading` — true during API call, false when done (same as checkproduct)

### Result Storage

Brand results are in the DOM `.el-table` element, same as checkproduct. Read body rows after `btnLoading` goes false.

## Brand Summary Table Columns

The table has 18 data columns with a two-row header:

| Index | Key | Description |
|---|---|---|
| 0 | — | checkbox |
| 1 | brand | 品牌名称 |
| 2 | total_products | 总产品数 |
| 3 | total_sellers | 总卖家数 |
| 4 | top100_products | 卖进Top100产品 |
| 5 | top100_new_products | 卖进Top100新品 |
| 6 | product_count_ratio | 产品数量占比 |
| 7 | monthly_sales_sum | Listing月销量和 |
| 8 | monthly_sales_amount_sum | Listing月销额和 |
| 9 | avg_price | 平均价格 |
| 10 | avg_reviews | 平均评价数 |
| 11 | head_product_sales_ratio | 头部产品销量占比 |
| 12 | new_product_count | 指定月份新品数 |
| 13 | new_seller_count | 新品卖家数 |
| 14 | new_avg_price | 新品平均价格 |
| 15 | new_avg_rating | 新品平均星级 |
| 16 | new_avg_reviews | 新品平均评价数 |
| 17 | new_avg_sales | 新品平均销量 |
