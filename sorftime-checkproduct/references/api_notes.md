# sorftime-checkproduct API Notes

## Architecture

The checkproduct page uses the same `searchBox` Vue VM as all other check modules. All API requests go through an obfuscated AES encryption layer — direct API calls to `api.sorftime.com` are impossible.

## Key API Endpoints (observed via network capture)

| Endpoint | Purpose |
|---|---|
| `/api/productboard/queryproductoverviewdata` | Main product detail query |
| `/api/productboard/queryproductboardtrend` | Product trend data |
| `/api/productBoard/queryqueryhistorydata` | Search history |
| `/api/productBoard/savequeryhistory` | Save search to history |

## searchBox VM State

### Input Fields

| Field | Path | Type | Notes |
|---|---|---|---|
| ASIN textarea | `checkBox.asinCheck.textarea` | string | Comma-separated ASINs |
| ASIN checked | `checkBox.asinCheck.checked` | boolean | Must be `true` |
| ASIN data | `checkBox.asinCheck.data` | string[] | Parsed ASIN array |
| Search text | `keywordSearch` | string | Mirror of ASIN input |
| Search list | `keywordSearchList` | string | Mirror of ASIN input |
| Has value | `hasValue` | boolean | Must be `true` |

### Trigger Methods (call in order)

1. `onCheckBoxOpen()` — opens ASIN checkbox dialog
2. `onAsinDataChange(value)` — passes ASIN data
3. `onAsinCheckedChange(true)` — checks checkbox
4. `onAsinDataOk()` — confirms ASIN dialog
5. `onProductSearch()` — executes the product search

All methods are native-bound (`[native code]`), not Vue-defined. They can be called directly on the VM instance.

### Loading State

| Field | When true | When false |
|---|---|---|
| `btnLoading` | API call in progress | Search complete |

### Result Storage

Product results are stored in the DOM `.el-table` element, NOT in the searchBox VM's reactive state. After `btnLoading` goes false, read results from `document.querySelector('.el-table').querySelectorAll('tbody tr')`.

### Table Column Layout

The table has ~15 visible data `td` cells per row:

| Index | Column | Notes |
|---|---|---|
| 0 | (checkbox) | Selection |
| 1 | Product title + ASIN | ASIN in `(B0XXXXXXXX)` or bare text |
| 2 | Listing月销量 | Monthly sales estimate |
| 3 | Listing月销额 | Sales amount |
| 4 | Listing年销量 | Yearly sales estimate |
| 5 | 实际价格 | Price (margin \| FBA fee) |
| 6 | 类目 | Category / BSR path |
| 7 | 隐赚指数 | Hidden profit; `--` if not enough data |
| 8 | 广告花费指数 | Ad spend index |
| 9 | 发货方式 | FBA / FBM |
| 10 | BBX卖家属性 | 第三方 / 亚马逊自营 |
| 11 | 品牌 | Brand name |
| 12 | 评分星级 | 1.0 – 5.0 |
| 13 | 评价数量 | Review count |
| 14 | 上架时间 | Date + days since listing |

## Error States

- **暂无数据**: ASIN not found or no data available for that ASIN
- **shibai.jpg**: The page shows a failure image when the API returns an error
- **btnLoading stays false**: Search not triggered correctly — missing dialog sequence
