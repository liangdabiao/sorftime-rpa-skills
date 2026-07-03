# sorftime-checkmarket Environment Notes

## Page Layout
- URL: `/home/checkmarket?d=<d_param>&i=<site_code>`
- 6 search modes via `market.model`
- Uses `checkMarketBtnLoading` (not `btnLoading`)

## Search Flow

1. Set `market.model` (search mode)
2. Set `market.search = text`
3. Set `market.textareaShow = true`
4. Set `keywordSearch = text`, `keywordSubject = text`, `hasValue = true`
5. Call `onMarketSearchClick()`
6. Poll `checkMarketBtnLoading`
7. Read DOM `.el-table`

## Known Issues

- Uses different loading key (`checkMarketBtnLoading`) than other check modules
- Category name includes notification overlay similar to seller name column
