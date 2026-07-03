# sorftime-checkbrand Environment Notes

## Page Layout
- URL: `/home/checkbrand?d=<d_param>&i=<site_code>`
- Site code via `i=` URL param: `1` = US, `7` = JP, `2` = GB, etc.
- 5 search modes in the search box area (not tabs on top)

## Search Flow

1. **Select mode**: Set `brand.model` (1-5)
2. **Enter text**: Set `brand.search`
3. **Trigger**: Call `onBrandSearch()`
4. **Wait**: Poll `btnLoading`
5. **Read**: Extract from DOM `.el-table`

## Key Differences from checkproduct

| Aspect | checkproduct | checkbrand |
|--------|-------------|------------|
| Input field | `checkBox.asinCheck.textarea` | `brand.search` |
| Dialog sequence | onCheckBoxOpen→onAsinDataChange→... | None needed |
| Trigger method | `onProductSearch()` | `onBrandSearch()` |
| Result type | Product-level (1 row/ASIN) | Brand summary (1 row/brand) |
| Row data | ~15 product columns | ~15 brand metrics columns |

## Input Modes

- **品牌名称**: Single brand name per query (multi-line input not supported via CLI)
- **ASIN**: Single ASIN to find associated brands
- **卖家名称**: Seller name to find seller's brands
- **卖家公司**: Company name search
- **热搜关键词**: ABA hot keywords to find relevant brands

## Known Issues

- **Brand name text includes junk**: Column 1 contains tooltip text like "产品图片产品链接品牌报告销量趋势运营类目分析分析品牌产品"
- **One row per brand**: Unlike checkproduct which returns many rows per query, brand search returns a single summary row per brand
- **Session per station**: Each station needs a fresh session (new tab group)
