# sorftime-checkseller Environment Notes

## Page Layout
- URL: `/home/checkseller?d=<d_param>&i=<site_code>`
- 4 search modes via `checkseller.model`
- Result table with two-row header and 19 data columns

## Search Flow

1. Set `checkseller.model` (1-4)
2. Set `checkseller.search = text`
3. Set `checkseller.textareaShow = true`
4. Set `keywordSearch = text`, `hasValue = true`
5. Call `onSellerSearch()`
6. Poll `btnLoading`
7. Read DOM `.el-table`

## Known Issues

- **Notification overlay**: Seller name column shows a "我已知晓，不再提醒" notification with product JSON. Seller name is in a visible `<span>` inside the cell.
- **Seller name extraction**: Use visible span elements (skip tooltip/notification text).
- **Fuzzy matching**: Searching by seller name may return multiple results with similar names.
