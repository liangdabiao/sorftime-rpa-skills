# Environment & Shell Quirks

Same as `sorftime-bestseller/references/environment.md`. Read this before writing shell or evaluate JS for this skill.

## sorftime-specific quirks for product

### `--9999` sentinel
sorftime uses `-9999` to mean "unknown" or "not tracked". Filter these out before numeric aggregation:
```python
def safe_int(s, default=0):
    try:
        return int(float(s)) if s not in (None, "", "-9999") else default
    except (ValueError, TypeError):
        return default
```

### ASIN mask "--"
Free tier masks ASIN/Name/Brand as `"--"` after rank ~20. The bundled fetch script auto-filters these. If you write custom logic, always check `r.get("ASIN") not in ("", "--")`.

### Page init takes 7s
chooseproduct page is heavier than bestseller — full board with 100+ column schema. `ensure_product_page` waits 7s by default; `find_vm` retries for 20s.

### VM is 6 levels deep
The productboard VM is buried under AI-sidebars, dialogs, drawers. The bundled `find_vm()` walks `$children` recursively. Don't hardcode the path — Vue component order can change.

### Page-size persistence
Setting `pageSize=100` writes to `localStorage["productBoardPageSize"]`. Subsequent reloads preserve this. To start fresh per session, the bundled `ensure_product_page` doesn't reset; if you see old page-size leaking across stations, add:
```python
evaluate('localStorage.removeItem("productBoardPageSize")', session)
```
before navigate.

### Large response payloads
Each productboard.data row has 141 fields × 100 rows = ~14k JSON keys per fetch. When debugging with `JSON.stringify`, always `.slice(0, N)` to avoid flooding context window. The bundled `evaluate()` uses Python urllib (not curl) so it's safer than heredoc.

## Common pitfalls

### "evaluate: vm is undefined"
The page hasn't finished loading. Wait for `find_vm(session).ok == True`.

### All rows show ASIN="--"
You're past page 1 or free-tier mask kicked in. The script filters these; if all 100 rows are masked, the page may be in a different state — reload and retry.

### `PageSaleCount=10000` for everything
This is the free-tier cap on sales counts (values >= 10000 are clipped). For real sales numbers you need a paid plan.
