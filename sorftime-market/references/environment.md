# Environment & Shell Quirks

Same as `sorftime-bestseller/references/environment.md`. Read this before writing shell or evaluate JS for this skill.

## sorftime-specific quirks for market

### Multi-tab dashboard confusion
The 选市场 page has 4 sub-modes (多维度 / 消费需求 / 自营新品 / 低价商城). Each mode is a separate VM. This skill ONLY targets 多维度 (default). If you see another VM with `categoryListData`, verify `marketType` matches before assuming it's the multi-dimensional mode.

### Category tree is a custom Vue component (not zTree)
Unlike bestseller's jQuery zTree, market uses a custom Vue component. Don't try to use `$.fn.zTree.getZTreeObj(...)`. Read `categoryListData` from VM directly:

```python
nodes = evaluate('''
(function () {
  const vm = /* find sideMarket VM */;
  return JSON.stringify(vm._data.categoryListData || []);
})()
''', session)
```

### `localStorage["site"]` requires reload
Setting the site does NOT trigger a re-fetch — Vue doesn't watch this key. Always:
```python
evaluate(f'localStorage.setItem("site","{site}")', session)
evaluate('location.reload()', session)
time.sleep(7.0)  # full re-mount
```

### Trend chart fills last
After `vm.initData(nodeId)`, multiple state slices update asynchronously. `marketTrendChartData` populates within 2-3s; statistical panels need explicit sub-tab clicks. The bundled `fetch_markets.py` waits 4s per node as a safety margin.

### `--9999` sentinel
Same as product skill — `-9999` means "unknown". Filter before numeric aggregation:
```python
def safe_float(s, default=0.0):
    try:
        return float(s) if s not in (None, "", "-9999") else default
    except (ValueError, TypeError):
        return default
```

### Title often masked
Even within the 20 trend items, `title` may show as `"--"` beyond rank ~10. This is normal — the numeric indices (sale_show, search_show, price_show) are still meaningful.

### Page init 7s (heavier than bestseller)
choosemarketblock pulls category list + initial trend chart on load. Vue mount + jQuery inits + first encrypted POST take ~5-7s. `ensure_market_page` defaults to `sleep_after=7.0`.

### GBK encoding on Windows
Windows shell defaults to GBK. When reading CSV in Python, always use `encoding="utf-8-sig"` (the bundled `write_csv` does this).

## Common pitfalls

### "sideMarket VM not found"
Page hasn't finished loading, or you're on a different sub-mode. Wait for `find_side_vm(session).ok == True`.

### Empty trend chart after trigger
Some categories have no trend data (e.g. tiny niches). Check `len(marketTrendChartData)` after `trigger_node` — if 0, the category may be too small to track, or the response was empty.

### All titles show "--"
Normal beyond rank ~10. The numeric indices are still useful; just don't rely on `title` for join keys.

### `--categories` flag doesn't match anything
The script matches by `slug` (URL-style name like "baby-products"), `name` (Chinese display name), or `nodeId`. If none match, it falls back to first 5 discovered nodes. Check stderr for `[station] discovered N nodes` to see what slugs are available.
