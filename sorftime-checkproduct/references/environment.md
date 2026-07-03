# sorftime-checkproduct Environment Notes

## Page Layout
- URL: `/home/checkproduct?d=<d_param>&i=<site_code>`
- Site code via `i=` URL param: `1` = US, `7` = JP, `2` = GB, etc.
- Level 1 tabs: 查ASIN (default, selected), 查关联产品, 查品牌产品, 查卖家产品, 热搜关键词查产品, 查低价产品
- Sub-mode cards: 指定asin查产品 (default, selected), 按名称查产品, 包含词查产品, 按属性查产品

## Key Observations

### Page State Machine
1. **Landing**: searchBox VM mounts, keyData = `"checkProductList1"`
2. **Input**: User enters ASIN(s) → textarea populates
3. **Search**: onProductSearch() → API called → btnLoading = true
4. **Results**: btnLoading = false → table populated in DOM

### Multi-ASIN Search
- Comma-separated ASINs: `"B07Z42VNCZ,B0CHX1W1XY"`
- Up to 50 ASINs per batch
- Each ASIN gets its own row in the results table
- "暂无数据" row for ASINs not found

### Sub-mode Buttons Have No Click Handlers
The 4 sub-mode cards (指定asin查产品, 按名称查产品, 包含词查产品, 按属性查产品) are rendered as StaticText with NO click event listeners. The `.cur` class is controlled by Vue reactive state, not user clicks. To switch sub-mode programmatically:
- Change `checkBox.mateValue` (1=指定asin, 2=按名称查产品)

### Native Methods
`onProductSearch()` and other trigger methods are `[native code]` — bound functions from imported modules, not Vue-defined. They must be called on the VM instance, not standalone.

### Free Tier Limitations
- Monthly sales: 10000 cap
- Price: `--` when hidden by Amazon
- ASIN monthly sales: `--` when not disclosed
- Hidden profit: `--` for new products

### Known Issues
- **Title text includes junk**: The product title column includes tooltip text like "取消确定专属客服专属客服" from hover elements inside the TD. Post-processing needed.
- **No data rows**: ASINs with no data show "暂无数据" in the title column — the row is still returned with empty other fields.
- **Session cross-contamination**: Each site needs a fresh session (new tab group). Reusing a session between stations causes stale state.
