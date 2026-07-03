# Environment & Shell Quirks

Same as `sorftime-keyword/references/environment.md`. Read this before writing shell or evaluate JS for this skill.

## sorftime-specific quirks for seller

### Filter-gated page (same as keyword/brand)
The 选卖家 page requires explicit category dialog interaction before data populates.

### Reuses side-Keyword VM
Shared Vue infrastructure with keyword/brand. URL determines mode.

### Seller-specific column schema
11 columns: Name, TopTypeName, SaleCount, AveragePrice, NewProductSaleCount, ProductCount, AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason, CyclicalMarket. (Identical to brand schema.)

### Page init takes 8s
Same as keyword/brand.

### `localStorage["site"]` requires reload
Same as other skills.

### GBK encoding on Windows
Always use `encoding="utf-8-sig"`.

## Common pitfalls

### All stations show `table_data_len=0`
Expected behavior without UI interaction.

### VM found but column schema doesn't match
Verify URL is `/home/chooseseller`. Both keyword/brand/seller pages have side-Keyword VM with same schema, but the underlying API differs.
