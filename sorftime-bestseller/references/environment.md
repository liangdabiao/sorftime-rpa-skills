# Environment & Shell Quirks

Read this before writing any shell command or new evaluate JS for this skill.

This file mirrors `sellersprite-products/references/environment.md`. The rules are identical across all kimi-webbridge-driven skills. sorftime specifics noted where they differ.

## Paths

- Use forward slashes (`/`) in all paths. Backslashes work in some tools but break in JSON strings.
- Use `/dev/null`, NOT `NUL` (Windows) — bash shells handle `/dev/null` correctly even on Windows.
- `~/.kimi-webbridge/` resolves to `<user-home>/.kimi-webbridge/` on any OS.
- Output paths are user-supplied via `--out`. Never assume a specific directory layout — the bundled scripts accept any path and create parent dirs as needed.

## Kimi WebBridge daemon

- Listens on `http://127.0.0.1:10086`.
- Daemon binary: `~/.kimi-webbridge/bin/kimi-webbridge` (status/start/stop/restart/logs subcommands).
- One Chrome/Edge extension connects via WebSocket; the extension ID appears in the `status` JSON.
- If `extension_connected: false` after `start`, ask the user to open their browser.
- This skill uses session name `sorftime-bestseller`. The other 5 sorftime sister skills use `sorftime-<skill>`. No conflict.

## Bash + JSON escaping rules

### `curl` with single-line JSON: works
```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"sorftime-bestseller"}'
```

### Heredoc `<<EOF` with JS regex: BREAKS
Bash eats one backslash layer, so `/\n+/g` arrives malformed.

**Fix**: prefer `.split('\n')` over `.replace(/\n+/g, ...)`. For complex JS, write to a `.js` file and POST via Python `urllib` (no shell layer). The bundled `common.evaluate()` does this for you — never inline complex JS via bash.

### Python urllib is safest
The bundled `common.call()` uses Python `urllib.request`:

```python
import json, urllib.request
req = urllib.request.Request(
    'http://127.0.0.1:10086/command',
    data=json.dumps({'action':'evaluate','args':{'code': code}, 'session': 'sorftime-bestseller'}).encode('utf-8'),
    headers={'Content-Type':'application/json'})
print(urllib.request.urlopen(req).read().decode('utf-8'))
```

## sorftime-specific quirks

### Site switching requires reload
sorftime caches per-site state in Vue at page init. Setting `localStorage["site"]` without reload keeps old data.

```python
# correct sequence
evaluate('localStorage.setItem("site","7")', session)  # JP
evaluate('location.reload()', session)
time.sleep(6.0)  # let zTree re-init
```

### zTree init lag
After page load, `$.fn.zTree.getZTreeObj("bestseller110")` returns null for 4-7s while Vue mounts + axios fetches the category tree. The bundled `ensure_bestseller_page` waits 6s by default; `get_categories` then retries for up to 20s.

### Tab/session reuse across sites
Within a single session, navigating to the bestseller URL switches to that tab if already open. To force a fresh load (e.g. when changing sites), the bundled `ensure_bestseller_page(site=...)` does `navigate` → `setItem` → `reload` rather than just `find_tab`.

### GBK encoding on Windows stdout
Print statements that include Japanese/Arabic/etc. category names may crash on Windows default cp936. Python's print() under bash on Win10 handles UTF-8 fine, but if you see `UnicodeEncodeError`, set `PYTHONIOENCODING=utf-8` before running.

### Best Seller is fully open (no paywall)
Unlike other sorftime modules, Best Seller TOP100 is shown to all logged-in users. No "100k+" masking, no field hiding, no pagination limit. Free tier is identical to paid tier for this module.

## Common pitfalls

### "evaluate: TypeError: ... is not a function"
Means `vm.treeItemClick` doesn't exist — the Vue component hasn't mounted yet or you found the wrong VM. Wait longer for page init, then re-walk `$children`.

### "Response body: {v:3, k:..., d:...}"
You're seeing the encrypted form — axios's transformResponse didn't fire. This happens if you bypass `vm.treeItemClick` and try to call the API directly. Use the Vue method instead.

### "selectNodeId stays 0"
The click didn't propagate to Vue. Verify you're calling `vm.treeItemClick(node)` (not `node.click()` or `dispatchEvent`).
