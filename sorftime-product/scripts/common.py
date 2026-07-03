"""Shared helpers for sorftime-product scripts.

DOM-driven skill: sorftime encrypts API request/response bodies with an
obfuscated AES routine, so we cannot call api.sorftime.com directly.
Instead we drive the page's own Vue instance to load data (init /
onPageSizeChange / onPagingChange), then read decrypted rows out of
productboard.data.

Free-tier cap: only ~20 ASINs per fetch are unmasked (ASIN/Name/Brand
visible). Rows beyond rank 20 show ASIN="--" with numeric fields
visible (but not useful for cross-reference). We read 100 rows but
filter to only emit unmasked ones.

Same 14 Amazon markets as bestseller (US/GB/DE/FR/IN/CA/JP/ES/IT/MX/
AE/AU/BR/SA). Site switching via localStorage + reload.
"""
import json
import time
import urllib.request
from pathlib import Path

DAEMON = "http://127.0.0.1:10086"
DEFAULT_SESSION = "sorftime-product"
PRODUCT_URL = "https://seller.sorftime.com/home/chooseproduct"

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


def ensure_product_page(session, site=None, sleep_after=7.0):
    """Navigate to the chooseproduct page (and optionally set site first)."""
    if site is not None:
        call("navigate", {"url": PRODUCT_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(4.0)
        evaluate(f'localStorage.setItem("site","{site}")', session)
        evaluate('location.reload()', session)
        time.sleep(sleep_after)
    else:
        call("navigate", {"url": PRODUCT_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(sleep_after)


def find_vm(session):
    """Return the productboard Vue VM (or {err: ...})."""
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('topAsinList') && dk.includes('productboard')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  return JSON.stringify({ok: true});
})()
"""
    res = evaluate(code, session)
    return res


def set_page_size(size, session):
    """Change page size (default 20 → up to 100)."""
    code = f"""
(function () {{
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {{
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('topAsinList') && dk.includes('productboard')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  }};
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({{err: 'no vm'}});
  vm.onPageSizeChange({size});
  return JSON.stringify({{ok: true}});
}})()
"""
    return evaluate(code, session)


def wait_for_data(session, expected_len=20, max_wait=20.0, poll=0.7):
    """Wait for productboard.data to populate."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        state = vm_state(session)
        if state.get("dataLen", 0) >= expected_len:
            return True
        time.sleep(poll)
    return False


def vm_state(session):
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('topAsinList') && dk.includes('productboard')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  return JSON.stringify({
    dataLen: vm._data.productboard.data.length,
    visibleAsin: vm._data.productboard.data.filter(r => r.ASIN && r.ASIN !== '--').length,
    pageIndex: vm._data.page.pageIndex,
    pageSize: vm._data.page.pageSize,
    totalCount: vm._data.page.totalCount
  });
})()
"""
    return evaluate(code, session)


def read_products(session):
    """Read productboard.data rows (raw)."""
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('topAsinList') && dk.includes('productboard')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm'});
  return JSON.stringify(vm._data.productboard.data || []);
})()
"""
    res = evaluate(code, session)
    if isinstance(res, list):
        return res
    return res or []


def write_csv(path, rows, base_fields):
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
