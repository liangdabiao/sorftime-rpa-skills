# sorftime 选品牌 API/Architecture Notes

Same encryption story as `sorftime-bestseller/references/api_notes.md`. This file documents the choosebrand-specific details.

## Page state

```
[init]
  ↓ navigate to /home/choosebrand
[page load]
  ↓ Vue mounts, side-Keyword VM inits (8s)
  ↓ side-Keyword._data.keywordData.List === []
  ↓ side-Keyword._data.table.node.data === []
  ↓ side-Keyword._data.table.node.options === [11 brand-specific cols]
  ↓ side-Keyword._data.screen.select === ""
[board ready, no data]
  ↓ UI shows: "已选全部类目" + "请先添加分析类目"
  ↓ encrypted POSTs fire on load (return empty)
[per category trigger — UI dialog needed]
  ↓ user opens 「类目」dialog, picks categories
  ↓ screen.select = "nodeId1,nodeId2,..."
  ↓ encrypted POST to brand board API
  ↓ response decrypted → table.node.data populates
```

## Brand column schema (11 cols)

| Prop | Label | Meaning |
|---|---|---|
| `Name` | Category | Category name |
| `TopTypeName` | Ssdl | Top type |
| `SaleCount` | Yxl | Sales count (monthly) |
| `AveragePrice` | Pjjg | Average price |
| `NewProductSaleCount` | Xpxlzb | New product sales share |
| `ProductCount` | Cpslzb | Product count share |
| `AvgComentCount` | Pjpjsl | Avg review count |
| `AvgScore` | Pjxj | Avg rating |
| `SaleCountPrevThree` | Qscpppmj | Sales 3 months ago |
| `BusySeason` | BusySeason | Busy season chart |
| `CyclicalMarket` | Zqsc | Cyclical market |

## Vue VM discovery

```
#app
  └── root.__vue__
        └── $children (depth ~3)
              └── name === 'side-Keyword'
                    └── _data:
                          keywordData: {List, ...}
                          table: {node, ...}  ← brand data lives here
                          screen: {select, nodeData, ...}
                          site: "01"
```

The `side-Keyword` VM is reused (despite the name) — same Vue instance, different API endpoint based on URL.

## Likely API endpoints

| Endpoint | Purpose |
|---|---|
| `api.sorftime.com/api/brandboard/query*` (or similar) | Brand board fetch |

We never call these directly — encryption makes that impossible.

## Site code mapping (14 markets)

Same as other skills:
US=1, GB=2, DE=3, FR=4, IN=5, CA=6, JP=7, ES=8, IT=9, MX=10, AE=11, AU=12, BR=13, SA=14.
