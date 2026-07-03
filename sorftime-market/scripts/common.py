"""Shared helpers for sorftime-market scripts.

DOM-driven skill. The 选市场 page (/home/choosemarketblock) is a complex
multi-tab dashboard showing aggregated market stats per category. Unlike
bestseller, it has no zTree — categories are selected via a search box.

Strategy: navigate → call sideMarket.initData(nodeId) → read populated
arrays from Vue VM. The page populates `marketTrendChartData` (20 trend
items per fetch) plus a few other state slices.

Same 14 Amazon markets, same localStorage site switching.
"""
import json
import time
import urllib.request
from pathlib import Path

DAEMON = "http://127.0.0.1:10086"
DEFAULT_SESSION = "sorftime-market"
MARKET_URL = "https://seller.sorftime.com/home/choosemarketblock"

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


def ensure_market_page(session, site=None, sleep_after=7.0):
    if site is not None:
        call("navigate", {"url": MARKET_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(4.0)
        evaluate(f'localStorage.setItem("site","{site}")', session)
        evaluate('location.reload()', session)
        time.sleep(sleep_after)
    else:
        call("navigate", {"url": MARKET_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(sleep_after)


def find_side_vm(session):
    """Return sideMarket VM (with initData / categoryListData)."""
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('categoryListData') && dk.includes('marketType')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no sideMarket vm'});
  return JSON.stringify({ok: true});
})()
"""
    return evaluate(code, session)


def trigger_node(node_id, session):
    """Call sideMarket.initData(nodeId) — triggers encrypted POST to
    /api/marketboard/databoard. Returns immediately; check state after."""
    code = f"""
(function () {{
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {{
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('categoryListData') && dk.includes('marketType')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  }};
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({{err: 'no sideMarket vm'}});
  vm.initData({json.dumps(node_id)});
  return JSON.stringify({{ok: true}});
}})()
"""
    return evaluate(code, session)


def read_market_state(session):
    """Read all populated arrays from the market dashboard VMs."""
    code = """
(function () {
  const root = document.querySelector('#app');
  const seen = new Set();
  const probes = [];
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    for (const k of dk) {
      try {
        const v = n._data[k];
        if (Array.isArray(v) && v.length > 0 && v[0] && typeof v[0] === 'object') {
          const sk = Object.keys(v[0]).slice(0, 8);
          if (sk.some(x => /nodeId|nodeID|asin|saleCount|brand|solder|marketId|title|price/i.test(x))) {
            probes.push({
              d,
              name: n.$options && (n.$options.name || n.$options._componentTag),
              key: k,
              len: v.length,
              firstKeys: sk,
              first: JSON.stringify(v[0]).slice(0, 500)
            });
          }
        }
      } catch (e) {}
    }
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  return JSON.stringify(probes);
})()
"""
    return evaluate(code, session)


def read_market_trend(session):
    """Read marketTrendChartData (the most reliably populated slice)."""
    code = """
(function () {
  const root = document.querySelector('#app');
  let vm = null;
  const seen = new Set();
  const visit = (n, d) => {
    if (d > 8 || !n || seen.has(n)) return;
    seen.add(n);
    const dk = n._data ? Object.keys(n._data) : [];
    if (dk.includes('marketTrendChartData')) vm = n;
    if (n.$children) n.$children.forEach(c => visit(c, d + 1));
  };
  visit(root.__vue__, 0);
  if (!vm) return JSON.stringify({err: 'no vm with trend chart'});
  return JSON.stringify(vm._data.marketTrendChartData || []);
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
