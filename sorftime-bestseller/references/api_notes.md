# sorftime 畅销榜 API/Architecture Notes

## Why DOM-driven?

sorftime's API at `api.sorftime.com/api/bestseller/*` uses **encrypted request and response bodies**. The wire format is:

```json
{
  "v": 3,
  "k": "MjAyNjA3MDMxNzM4MDA=",  // base64 of "20260703173800" (timestamp)
  "d": "LD+U3Lh6uewgUlEPNoj/1fcgq9DG..."  // AES-encrypted JSON payload
}
```

The page encrypts request bodies and decrypts responses via an obfuscated AES routine embedded in the JS bundle (`/1782875408875/js/app.js`). Reversing it is impractical. Direct attempts to call the API fail:

| Approach | Result |
|---|---|
| `fetch()` to api.sorftime.com | TypeError: Failed to fetch (CORS) |
| `XMLHttpRequest` | Status 0 error |
| `jQuery.ajax` (no headers) | 405 Method Not Allowed |
| `jQuery.ajax` + token header | 401 Unauthorized |
| `axios.post` + headers | 401 (signature missing) |

The page itself works fine — its requests return 200. So we use the page as an oracle: trigger the page's own fetch via Vue method, then read the decrypted result from Vue's reactive state.

## State machine

```
[init]
  ↓ navigate to /home/bestseller?d=...&i=1
[page load]
  ↓ Vue mounts, axios bootstrap, jQuery zTree inits (4-7s)
[tree ready]
  ↓ zTree obj "bestseller110" available
  ↓ vm._data.bestsellerData === []
  ↓ vm._data.selectNodeId === 0
[per category]
  ↓ find node by slug in zTree.getNodes()
  ↓ vm.treeItemClick(node)
    → vm.isLoading = true
    → encrypted POST to /api/bestseller/uncrawlernode
    → response decrypted by transformResponse
    → vm.bestsellerData = decrypted.data
    → vm.selectNodeId = node.NodeId
    → vm.isLoading = false
[read]
  ↓ vm._data.bestsellerData → list of 100 rows
```

## Key endpoints observed

These were captured by network sniffing during page load. We never call them directly:

| Endpoint | Method | Purpose |
|---|---|---|
| `api.sorftime.com/api/bestseller/nodeidtree?site=01` | POST | Initial category tree (top-level only) |
| `api.sorftime.com/api/bestseller/nodeiddemo?site=01` | POST | Demo category (free tier preview) |
| `api.sorftime.com/api/bestseller/uncrawlernode?site=01` | POST | Per-category Best Seller list (100 rows) |

`site` query param is zero-padded 2-digit (`01`=US, `07`=JP, `14`=SA).

## Site mapping

sorftime uses numeric IDs (NOT 2-letter codes like sellersprite):

| ID | Code | 中文 | Amazon TLD |
|---|---|---|---|
| 1 | US | 美国 | amazon.com |
| 2 | GB | 英国 | amazon.co.uk |
| 3 | DE | 德国 | amazon.de |
| 4 | FR | 法国 | amazon.fr |
| 5 | IN | 印度 | amazon.in |
| 6 | CA | 加拿大 | amazon.ca |
| 7 | JP | 日本 | amazon.co.jp |
| 8 | ES | 西班牙 | amazon.es |
| 9 | IT | 意大利 | amazon.it |
| 10 | MX | 墨西哥 | amazon.com.mx |
| 11 | AE | 阿联酋 | amazon.ae |
| 12 | AU | 澳大利亚 | amazon.com.au |
| 13 | BR | 巴西 | amazon.com.br |
| 14 | SA | 沙特 | amazon.sa |

## Response schema (decrypted)

Each row in `vm._data.bestsellerData`:

| Field | Type | Meaning |
|---|---|---|
| `Number` | int | 1-100 rank |
| `Image` | url | Product image |
| `NodeId` | str | Category slug (e.g. `baby-products`) |
| `ASIN` | str | Amazon ASIN |
| `Name` | str | Product title |
| `SaleCount` | int | Monthly sales units |
| `SaleEstimate` | float | Monthly revenue (units × price) |
| `Price` | float | Current price |
| `FBAFee` | float | FBA fulfillment fee |
| `GrossProfit` | float | Gross profit after FBA fee |
| `Solder` | str | Seller name (note: typo in API — "Solder" not "Seller") |
| `SolderId` | str | Seller ID |
| `SolderNationality` | str | Seller country |
| `Brand` | str | Brand name |
| `CommentCount` | int | Total review count |
| `RatingMonth` | int | Recent rating delta |
| `RatingStayMonth` | int | Stable rating |
| `SaleTime` | date | First sale date (`YYYY-MM-DD`) |
| `SaleTimeDay` | int | Days since first sale |
| `Deliver` | str | `FBA` or `FBM` |
| `Score` | float | Star rating (0-5) |
| `SinglePrice` | float | Per-unit price (for variations) |
| `IsCollet` | bool | User-collected (favorite) flag |

## Vue VM discovery path

```
#app
  └── root.__vue__
        └── $children[0..n]
              └── ... (deepest level, ~6 levels deep)
                    └── has _data.bestsellerData + _data.bestsellerOption
```

We discover it by traversing `$children` recursively, checking `_data` keys.

## jQuery zTree object

| Object | Where |
|---|---|
| `window.$` / `window.jQuery` | global |
| `$.fn.zTree.getZTreeObj("bestseller110")` | the tree instance |
| `tree.getNodes()` | flat array of top-level nodes |
| `node.NodeId` / `node.nodeId` | category slug |
| `node.id` | numeric id (1..27) |
| `node.tId` | DOM id prefix (e.g. `bestseller110_6`) |
| `node.name` | display name (with Chinese parenthetical) |

## Vue method: treeItemClick

The magic method. Source (heavily obfuscated in production JS):

```js
function treeItemClick(node) {
  this.isLoading = true;
  this.NodeData = node;
  // ... fetch sibling metadata (Object(_0x144dae['D']))
  apiCall({ NodeId: node.NodeId })       // encrypted POST
    .then(resp => {
      if (resp.Code === 0) {
        this.bestsellerData = resp.Data;
      } else {
        this.showType = 2;
        this.bestsellerData = [];
      }
    })
    .catch(err => { this.showType = 2; })
    .finally(() => {
      this.isLoading = false;
      this.selectNodeId = node.NodeId;
    });
}
```

Calling `vm.treeItemClick(node)` triggers the full fetch → render → state-update cycle.

## localStorage keys

| Key | Value | Purpose |
|---|---|---|
| `site` | `"1"` (current site ID) | Site switching — set + reload |
| `token` | `"agXuqGRijz5SykXkdQBjCQ=="` | User auth token |
| `apiplatform` | `"10"` | Platform ID |
| `lang` | `"zh-CN"` | UI language |
| `siteData` | JSON blob with platformKey, webSite, bestSeller URL | Per-site Amazon metadata |
| `ListingOption` | JSON array of UI prefs | Display customization |

## Why "bestseller110"?

The zTree DOM ID prefix. The "110" appears to be a Vue component instance counter — it stays stable across reloads in this project. If it changes in a future sorftime release, the discovery code would need updating (the `getZTreeObj("bestseller110")` call).
