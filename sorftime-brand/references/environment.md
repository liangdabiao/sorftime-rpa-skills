# Environment & Shell Quirks

Same as `sorftime-keyword/references/environment.md`. Read this before writing shell or evaluate JS for this skill.

## sorftime-specific quirks for brand

### Filter-gated page (same as keyword)
The 选品牌 page requires explicit category dialog interaction before data populates. Same limitation as keyword page.

### Reuses side-Keyword VM
Despite the name "side-Keyword", this VM is shared by keyword/brand/seller pages. Distinguish by URL: `/home/choosebrand` = brand mode.

### Brand-specific column schema
11 columns: Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket. Always populated regardless of data state.

### Page init takes 8s
Same as keyword — heavy Vue mount.

### `localStorage["site"]` requires reload
Same as other skills.

### GBK encoding on Windows
Always use `encoding="utf-8-sig"`.

## Common pitfalls

### All stations show `table_data_len=0`
Expected behavior without UI interaction. See SKILL.md → "When this skill returns empty data".

### VM found but column schema doesn't match brand
Verify URL is `/home/choosebrand` (not keyword). Both pages have `side-Keyword` VM, but the column schema differs.
