# sorftime 选市场 API/Architecture Notes

Same encryption story as `sorftime-bestseller/references/api_notes.md`. This file documents the choosemarketblock-specific details and the partial-surface reality.

## Page state

```
[init]
  ↓ navigate to /home/choosemarketblock
[page load]
  ↓ Vue mounts, axios inits, categoryListData populates (7s)
[board ready]
  ↓ sideMarket._data.categoryListData === [{nodeId, name, slug, ...}]
  ↓ sideMarket._data.marketType === "..."  (sub-mode indicator)
  ↓ marketTrendChartData === []  (empty until trigger)
  ↓ statisticalData.offlineData === []  (empty until sub-tab click)
  ↓ marketBoard.items === []  (empty until sub-tab click)
[per category]
  ↓ sideMarket.initData(nodeId)
  ↓ encrypted POST → api.sorftime.com/api/marketboard/databoard?site=NN
  ↓ response decrypted → fills marketTrendChartData (20 items)
  ↓ other slices still empty (need sub-tab UI clicks)
[read]
  ↓ read marketTrendChartData — only reliably populated slice
```

## Key endpoints (observed via network capture)

| Endpoint | Purpose |
|---|---|
| `api.sorftime.com/api/marketboard/databoard?site=NN` | Multi-dimensional mode aggregator (triggers on initData) |
| `api.sorftime.com/api/marketboard/...` (other paths) | Sub-tab specific fetches (need clicks to trigger) |

We never call these directly — encryption makes that impossible.

## Response schema (marketTrendChartData items)

Each item has ~6 visible fields (free tier):

| Field | Type | Meaning |
|---|---|---|
| `nodeId` | str | Item's Amazon category node |
| `title` | str | Item title (often "--" beyond rank ~10) |
| `priceShow` | str/num | Price index (avg or representative price) |
| `saleShow` | str/num | Sales volume index (sort key) |
| `searchShow` | str/num | Search popularity index |
| `pricSaleShow` | str/num | Price×sales composite |

## Why only marketTrendChartData?

The dashboard's main panel shows 4 sub-tabs:
1. **多维度选市场** (multi-dimensional) — default; trend chart populates
2. **消费需求选市场** (consumer demand) — different VM, different shape
3. **自营新品选市场** (self-operated new) — different VM
4. **低价商城选市场** (low-price mall) — different VM

Even within 多维度 mode, the right-side detail panels (统计 / 榜单 / 品牌 / 卖家) each require their own click to populate. Free tier exposes the trend chart generously but gates the detail panels.

## Vue VM discovery

```
#app
  └── root.__vue__
        └── $children (depth ~5)
              └── has _data.categoryListData + _data.marketType
                    └── methods: initData(nodeId), onSubTabClick, ...
```

Look for `_data` keys containing both `categoryListData` and `marketType` — that's the sideMarket VM. The bundled `find_side_vm()` handles this traversal.

## Category discovery

```js
sideMarket._data.categoryListData = [
  {nodeId: "amzn-1", name: "电子产品", slug: "electronics", ...},
  {nodeId: "amzn-2", name: "家居", slug: "home-kitchen", ...},
  ...
]
```

Each station has its own list (sizes vary 15-30 categories). The fetch script's `discover_node_ids()` reads this directly.

## initData semantics

```js
sideMarket.initData(nodeId)
  → validates node
  → builds encrypted POST body
  → axios.post → /api/marketboard/databoard?site=NN
  → response decrypted by transformResponse
  → vm._data.marketTrendChartData = [20 items]
  → vm._data.statisticalData stays empty (needs sub-tab clicks)
```

## Multi-station scraping flow

```
for station in [US, JP, GB]:
  navigate to /home/choosemarketblock
  set localStorage["site"] = <site_id>
  reload  (page rebuilds with site-specific category list)
  wait 7s for Vue mount
  read categoryListData → list of nodes
  for node in matched_categories:
    trigger vm.initData(node.nodeId)
    wait 4s
    read marketTrendChartData
    append rows to CSV
```

## Site code mapping (14 markets)

| Site | Code | Name |
|---|---|---|
| 01 (or "1") | US | 美国 |
| 02 | GB | 英国 |
| 03 | DE | 德国 |
| 04 | FR | 法国 |
| 05 | IN | 印度 |
| 06 | CA | 加拿大 |
| 07 | JP | 日本 |
| 08 | ES | 西班牙 |
| 09 | IT | 意大利 |
| 10 | MX | 墨西哥 |
| 11 | AE | 阿联酋 |
| 12 | AU | 澳大利亚 |
| 13 | BR | 巴西 |
| 14 | SA | 沙特 |

sorftime accepts both "01" and "1" formats in localStorage.
