# Environment & Shell Quirks

Same as `sorftime-bestseller/references/environment.md`. Read this before writing shell or evaluate JS for this skill.

## sorftime-specific quirks for keyword

### Filter-gated page (unique to this skill)
The 选关键词 page is the only one of sorftime's 6 选品 modules that doesn't auto-populate on navigation. All others (bestseller, product, market, brand, seller) populate data either immediately or after a single category click. The keyword page requires the user to open the 「类目」dialog and select specific categories before data appears.

### Two VMs to be aware of
The keyword page has both `side-Keyword` (master) and `sideMarket` (with `categoryListData`). When probing VM state, distinguish them by `$options.name`:
- `name === 'side-Keyword'` — the master VM with keywordData/table/screen
- `name === 'sideMarket'` — secondary, with categoryListData (often empty)

### 11-column fixed schema
`table.node.options` always has 11 columns: Name (category), Top, SearchVolume, SearchConversionRate, KeywordTrend, TopDiff, FlowSource, SearchRank, NaturalRank, Bid, Relevance. These are defined at page init; the data array is what's missing.

### Page init takes 8s
Heavier than bestseller (which needs 7s). The page mounts multiple sub-VMs (side-Keyword, sideMarket, keyword-Trend, keyword-Monopoly, keywordMenuDetail, etc.). Use `--sleep 8`.

### `localStorage["site"]` requires reload
Same as other skills — set localStorage then `location.reload()` then wait 8s.

### Empty state vs populated state
The empty state shows: "请先添加分析类目" + button "添加类目". When populated, the same area shows the keyword table. The button is rendered conditionally based on `table.node.data.length === 0`.

### Sample-size confusion
The pagination footer shows "符合条件数据 14570 条" but `table.node.page.totalCount` reads 0. This is because the footer number refers to the global keyword universe count, not the current filtered query result. Trust `totalCount` from the VM state, not the footer text.

### GBK encoding on Windows
Always use `encoding="utf-8-sig"` when reading/writing CSVs (bundled `write_csv` does this).

### No `jq` on Windows
Use Python for JSON parsing. The bundled scripts use Python's stdlib only.

## Common pitfalls

### "side-Keyword VM not found"
Page hasn't finished loading. Wait the full 8s. If still missing, check that you're on `/home/choosekeyword` (not a redirect).

### All stations show `table_data_len=0`
Expected behavior without UI interaction. See SKILL.md → "When this skill returns empty data".

### `loadKeyword()` returns immediately
The method has internal guards. Setting `screen.select` alone isn't enough — the method likely checks for proper nodeData objects and Vue reactive state set by the dialog. See `references/api_notes.md` → Unfinished investigation.

### `searchKeyword()` doesn't help
Despite the name, this method uses the same screen state and has the same issue.

### Network capture shows encrypted blobs
Don't try to decrypt manually — the AES key is derived from the obfuscated app.js bundle. Drive the page's own VM instead.
