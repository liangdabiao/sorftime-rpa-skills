# sorftime 选品 API/Architecture Notes

Same encryption story as `sorftime-bestseller/references/api_notes.md`. This file documents the chooseproduct-specific details.

## Page state

```
[init]
  ↓ navigate to /home/chooseproduct
[page load]
  ↓ Vue mounts, axios bootstrap, jQuery inits (7s)
[board ready]
  ↓ vm._data.topAsinList === [2000 ASINs]  (lightweight list of strings)
  ↓ vm._data.productboard.data === [20 rows]  (rich page 1, 141 fields each)
  ↓ vm._data.page.pageSize === 20
  ↓ vm._data.page.totalCount === 5213 (US; varies per site)
[per fetch]
  ↓ vm.onPageSizeChange(N)  → triggers encrypted POST
  ↓ response decrypted by transformResponse
  ↓ vm._data.productboard.data === [N rows] (first 20 unmasked, rest ASIN="--")
  ↓ vm._data.page.pageSize === N
[read]
  ↓ filter rows where ASIN !== "--" && ASIN !== ""  → 20 unmasked rows
```

## Key endpoints (observed via network capture)

| Endpoint | Purpose |
|---|---|
| `api.sorftime.com/api/flowcircle/queryexportproductdetailtime?site=01` | Export time tracking |
| `api.sorftime.com/api/productboard/queryboardtop?site=01` | Default top-board (2000 ASINs) |
| `api.sorftime.com/api/productboard/queryboardlist?site=01` | Paginated board (20/50/100 rows) |
| `api.sorftime.com/api/customercenter/charge?site=01` | Subscription status |
| `api.sorftime.com/api/uc/querycustomerdefaultsite?site=01` | Default site |

We never call these directly — encryption makes that impossible.

## Response schema (decrypted)

Each row in `productboard.data` has **141 fields**. The fetch script extracts the 22 most useful:

| Field | Type | Meaning |
|---|---|---|
| `ASIN` | str | Child ASIN (or "--" if masked) |
| `ParentAsin` | str | Parent / variant root |
| `Name` | str | Title |
| `Brand` | str | Brand |
| `Price` | float | Current price |
| `SinglePrice` | float | Per-unit price (variations) |
| `GrossProfit` | float | FBA profit estimate |
| `FBAFee` | float | FBA fee |
| `PageSaleCount` | int | Monthly sales (caps at 10000+) |
| `PageSaleVolume` | float | Monthly revenue |
| `YearSaleCount` | int | Annual sales (-9999 = unknown) |
| `Score` | float | Star rating (0-5) |
| `CommentCount` | int | Review count |
| `Deliver` | str | `FBA` or `FBM` |
| `SolderNationality` | str | Seller country (note: API typo "Solder") |
| `NodeId` / `TopNodeID` | str | Category node |
| `UpdateTimeStr` | date | Last data refresh |
| `Image` | url | Product image |
| `IsExist` | int | Listing status (3 = active) |
| `BestSellerLp` | int | Best Seller rank |
| `ScorePotential` | float | sorftime's opportunity score |

## Free-tier masking pattern

| Rank | ASIN | Name | Brand | Price | Sales |
|---|---|---|---|---|---|
| 1-20 | full | full | full | full | full (caps 10000) |
| 21-100 | `--` | `--` | `--` | visible | visible |
| 101+ | not loaded | not loaded | not loaded | not loaded | not loaded |

The script auto-filters to only emit rows where `ASIN !== "--" && ASIN !== ""`.

## Vue VM discovery

```
#app
  └── root.__vue__
        └── $children (depth ~6)
              └── has _data.topAsinList + _data.productboard
                    └── methods: init, onPagingChange, onPageSizeChange, onProductListSearch
```

The VM has 100+ methods, but we only use `onPageSizeChange(N)` for fetching.

## Pagination semantics

```js
vm.onPageSizeChange(N)
  → vm.page.pageSize = N
  → localStorage.setItem("productBoardPageSize", N)  // persisted
  → vm.page.pageIndex = 1
  → triggers encrypted fetch (if data exists)
```

```js
vm.onPagingChange(idx)
  → vm.page.pageIndex = idx
  → triggers encrypted fetch
```

For multi-station scraping, we always start at page 1 (just navigate). Pagination beyond page 1 doesn't help because all pages 2+ are fully masked.

## "TopNodeID" vs "NodeId"

`NodeId` is empty for default board rows. `TopNodeID` contains the top-level category (e.g. `amazon_1`). The fetch script falls back to `TopNodeID` if `NodeId` is empty.

## Default page-size persistence

sorftime caches `pageSize` in localStorage (`productBoardPageSize`). So setting it to 100 persists across reloads. To reset to default, set back to 20.
