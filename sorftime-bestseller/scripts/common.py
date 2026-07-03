"""Shared helpers for sorftime-bestseller scripts.

DOM-driven skill: sorftime encrypts API request/response bodies with an
obfuscated AES routine, so we cannot call api.sorftime.com directly. Instead
we drive the page's own jQuery zTree + Vue instance to load data, then read
the decrypted result out of the Vue VM's reactive state.

Differences vs sellersprite-products (which is API-first):
- No fetch()/post_json() helpers — they would 401 / CORS-fail
- Site switching is via localStorage["site"], not URL param
- 14 Amazon markets (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA), not 10
- Bestseller is a TOP100 list per category (one category per fetch)
"""
import json
import time
import urllib.request
from pathlib import Path

DAEMON = "http://127.0.0.1:10086"
DEFAULT_SESSION = "sorftime-bestseller"
BESTSELLER_URL = "https://seller.sorftime.com/home/bestseller?d=JTdCJTIycGFyZW50JTIyJTNBJTIyYW1hem9uXzElMjIlMkMlMjJ0eXBlJTIyJTNBJTIyMSUyMiUyQyUyMnN0ZXAlMjIlM0ElMjIxJTIyJTJDJTIydmlld3MlMjIlM0ElMjJhbWF6b24lMjIlN0Q%3D&i=1"

# sorftime site id ↔ Amazon marketplace code
# (probed 2026-07-03 via localStorage.setItem("site",N) + checking the
#  siteData localStorage blob which contains webSite URL).
SITE_TO_CODE = {
    "1": "US",   "2": "GB",  "3": "DE",  "4": "FR",  "5": "IN",
    "6": "CA",   "7": "JP",  "8": "ES",  "9": "IT",  "10": "MX",
    "11": "AE",  "12": "AU", "13": "BR", "14": "SA",
}
CODE_TO_SITE = {v: k for k, v in SITE_TO_CODE.items()}

STATION_NAMES = {
    "US": "美国", "GB": "英国", "DE": "德国", "FR": "法国", "IN": "印度",
    "CA": "加拿大", "JP": "日本", "ES": "西班牙", "IT": "意大利", "MX": "墨西哥",
    "AE": "阿联酋", "AU": "澳大利亚", "BR": "巴西", "SA": "沙特",
}


def _tld(code):
    """Amazon TLD for a station code (used for ASIN URLs)."""
    return {
        "US": "com", "GB": "co.uk", "DE": "de", "FR": "fr", "IN": "in",
        "CA": "ca", "JP": "co.jp", "ES": "es", "IT": "it", "MX": "com.mx",
        "AE": "ae", "AU": "com.au", "BR": "com.br", "SA": "sa",
    }.get(code, "com")


def call(action, args, session):
    body = json.dumps({"action": action, "args": args, "session": session}).encode()
    req = urllib.request.Request(f"{DAEMON}/command", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def evaluate(code, session):
    res = call("evaluate", {"code": code}, session)
    if not res.get("ok"):
        return {"_error": res.get("error", {}).get("message", "unknown")}
    data = res["data"]
    if isinstance(data, dict) and data.get("type") == "string":
        try:
            return json.loads(data["value"])
        except Exception:
            return {"raw": data.get("value")}
    return data


def ensure_bestseller_page(session, site=None, sleep_after=6.0):
    """Navigate to the bestseller page (and optionally set site first).

    Always navigates rather than find_tab — WebBridge 502s on evaluate()
    against a non-existent session. Setting site requires a reload anyway
    because the page caches site-specific state in Vue on init.
    """
    if site is not None:
        # Two-step: navigate first to get the right origin, then set
        # localStorage + reload. Otherwise localStorage.setItem fires
        # against whatever origin is currently loaded.
        call("navigate", {"url": BESTSELLER_URL, "newTab": True,
                          "group_title": "sorftime"},
             session)
        time.sleep(4.0)
        evaluate(f'localStorage.setItem("site","{site}")', session)
        evaluate('location.reload()', session)
        time.sleep(sleep_after)
    else:
        call("navigate", {"url": BESTSELLER_URL, "newTab": True,
                          "group_title": "sorftime"},
             session)
        time.sleep(sleep_after)


def get_categories(session):
    """Return list of {id, slug, name} for all top-level categories."""
    code = """
(function () {
  if (!window.jQuery || !window.$.fn.zTree) return JSON.stringify({err: 'no zTree'});
  const t = window.$.fn.zTree.getZTreeObj('bestseller110');
  if (!t) return JSON.stringify({err: 'no tree obj'});
  const nodes = t.getNodes();
  return JSON.stringify(nodes.map(n => ({
    id: n.id, slug: n.NodeId || n.nodeId || null, name: n.name
  })));
})()
"""
    return evaluate(code, session)


def select_category(slug, session, max_wait=20.0, poll=0.7):
    """Trigger Vue's treeItemClick(node) directly and wait for data load.

    sorftime's zTree onClick callback is bound through Vue's @click which
    requires a trusted event — synthetic dispatches don't fire it. The
    cleanest path is calling vm.treeItemClick(node) directly: it's the
    same method Vue binds, and it issues the API call + sets
    bestsellerData + sets selectNodeId.

    Returns the populated bestsellerData array (max 100 rows) or an
    error dict.
    """
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const visit = (n, d) => {
    if (d > 8 || !n) return;
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('bestsellerData')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  const t = window.$.fn.zTree.getZTreeObj('bestseller110');
  if (!t) return JSON.stringify({err: 'no tree obj'});
  const nodes = t.getNodes();
  const match = nodes.find(n => (n.NodeId || n.nodeId) === %SLUG%);
  if (!match) return JSON.stringify({err: 'no match', slug: %SLUG%, available: nodes.map(n => n.NodeId || n.nodeId)});
  vm.treeItemClick(match);
  return JSON.stringify({ok: true, slug: match.NodeId || match.nodeId, name: match.name});
})()
""".replace("%SLUG%", json.dumps(slug))
    res = evaluate(code, session)
    if res.get("err"):
        return res

    deadline = time.time() + max_wait
    last_select = None
    while time.time() < deadline:
        # Both bestsellerData populated AND selectNodeId updated — the
        # API call resolves and sets selectNodeId in a .finally() block.
        state = _vm_state(session)
        if state.get("selectNodeId") == slug and state.get("bestDataLen", 0) > 0:
            return read_bestseller_data(session)
        time.sleep(poll)
    return {"_error": "timeout waiting for bestsellerData", "slug": slug,
            "last_state": state}


def _vm_state(session):
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const visit = (n, d) => {
    if (d > 8 || !n) return;
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('bestsellerData')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  return JSON.stringify({
    bestDataLen: (vm._data.bestsellerData || []).length,
    selectNodeId: vm._data.selectNodeId,
    isLoading: vm._data.isLoading
  });
})()
"""
    return evaluate(code, session)


def read_bestseller_data(session):
    """Pull bestsellerData array out of the Vue VM."""
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const visit = (n, d) => {
    if (d > 8 || !n) return;
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('bestsellerData')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  return JSON.stringify(vm._data.bestsellerData || []);
})()
"""
    res = evaluate(code, session)
    if isinstance(res, list):
        return res
    return res or []


def write_csv(path, rows, base_fields):
    """Write rows to CSV with utf-8-sig (BOM). Dynamic columns appended."""
    extra = []
    seen = set(base_fields)
    for r in rows:
        for k in r.keys():
            if k not in seen:
                extra.append(k)
                seen.add(k)
    fields = base_fields + extra
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
