# sorftime 关键词趋势选品 API/Architecture Notes

Same encryption story as `sorftime-bestseller/references/api_notes.md`. This file documents the choosekeyword-specific details and the unfinished filter-gated UI-flow investigation.

## Page state

```
[init]
  ↓ navigate to /home/choosekeyword
[page load]
  ↓ Vue mounts, side-Keyword VM inits, axios inits (8s)
  ↓ side-Keyword._data.keywordData.List === []
  ↓ side-Keyword._data.table.node.data === []
  ↓ side-Keyword._data.table.node.options === [11 column schema]
  ↓ side-Keyword._data.screen.select === ""
  ↓ side-Keyword._data.screen.nodeData === {}
  ↓ sideMarket._data.categoryListData === []  (lazy)
[board ready, no data]
  ↓ UI shows: "已选全部类目" (filter chip) + "请先添加分析类目" (empty state)
  ↓ encrypted POSTs to /api/keywordboard/* fire on load (return empty)
[per category trigger — NOT YET REVERSE-ENGINEERED]
  ↓ user clicks 「类目」chip → opens dialog
  ↓ user picks categories in tree
  ↓ user clicks confirm
  ↓ side-Keyword._data.screen.select = "nodeId1,nodeId2,..."
  ↓ side-Keyword._data.screen.nodeData = {nodeId1: {...}, ...}
  ↓ encrypted POST /api/keywordboard/querykeywordboard?site=NN
  ↓ response decrypted → keywordData.List populates
[read]
  ↓ read keywordData.List — array of keyword rows with 11+ fields
```

## Key endpoints (observed via network capture on page load)

| Endpoint | Purpose |
|---|---|
| `api.sorftime.com/api/keywordboard/querykeywordboard?site=NN` | Main keyword board fetch |
| `api.sorftime.com/api/keywordboard/querykeywordofflinemonth?site=NN` | Offline month data |
| `api.sorftime.com/api/keywordboard/querykeywordhistoryweek?site=NN` | History week data |
| `api.sorftime.com/api/keywordboard/calculatorWeek?site=NN` | Week calculator |

We never call these directly — encryption makes that impossible.

## Response schema (when populated)

Each row in `keywordData.List` has fields including (sample):

| Field | Type | Meaning |
|---|---|---|
| `Keyword` | str | The keyword text |
| `SearchVolume` | int | Search volume |
| `SearchVolumeTrend` | obj | Trend chart data |
| `Top` | int | Top product count |
| `TopDiff` | num | Top diff |
| `SearchConversionRate` | num | Conversion rate |
| `Relevance` | num | Relevance score |
| `FlowSource` | obj | Flow source breakdown |
| `SearchRank` | int | Search rank |
| `NaturalRank` | int | Natural rank |
| `Bid` | num | Suggested bid (CPC) |

The exact fields depend on which `Options` columns are enabled (11 default columns visible).

## Vue VM discovery

```
#app
  └── root.__vue__
        └── $children (depth ~3)
              └── name === 'side-Keyword'
                    └── _data:
                          keywordData: {List, Options, ...}
                          table: {node, seller, empty, ...}
                          screen: {select, nodeData, ...}
                          loadData: [...3 bools]
                          site: "01"
```

Plus a secondary `sideMarket` VM (depth ~5) that holds `categoryListData` (empty on this page until dialog opened).

## side-Keyword methods of interest

| Method | Purpose |
|---|---|
| `init()` | Page init |
| `loadKeyword()` | Main keyword fetch (calls encrypted POST) |
| `searchKeyword()` | Search keyword (uses screen state) |
| `initNodeData()` | Init category tree |
| `initSortCloumn()` | Init column sort |
| `onkeywordDataClick(row)` | Row click handler |
| `onColumnItemClick(...)` | Column click handler |
| `getKeywordParam()` | Builds request params |

## Unfinished investigation: programmatic category selection

Goal: trigger `loadKeyword()` and have it actually return data, without UI dialog.

Tried approaches that did NOT work:

1. **Direct `loadKeyword()` call**: returns immediately, no API call. The method may bail if `screen.select` is empty.
2. **Set `screen.select = "amazon_1,amazon_2,amazon_3"` then call `loadKeyword()`**: still no data. The method probably validates `screen.nodeData` keys map to objects.
3. **Set both `screen.select` and `screen.nodeData` then call `loadKeyword()`**: still no data. The method may require specific format or specific Vue reactive events.
4. **Click 「立即筛选」 (apply filter) button via JS**: no effect on data state.
5. **Trigger `searchKeyword()`**: no effect (likely same path).

Likely missing piece: the method probably checks for a specific `screen` shape populated by the category dialog's `confirm` handler. Reverse-engineering this requires:

- Reading the app.js bundle for `loadKeyword` / `searchKeyword` source
- Tracing what `screen.select` and `screen.nodeData` look like AFTER user-driven category selection (capture once, replay)
- Or: emulating the dialog's confirm event with proper reactive triggers (`Vue.set` for reactivity)

This is left as future work.

## Site code mapping (14 markets)

Same as other skills:
US=1, GB=2, DE=3, FR=4, IN=5, CA=6, JP=7, ES=8, IT=9, MX=10, AE=11, AU=12, BR=13, SA=14.
