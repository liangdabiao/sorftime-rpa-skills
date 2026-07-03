"""Shared helpers for sorftime-seller scripts.

DOM-driven skill. The 选卖家 page (/home/chooseseller) reuses the same
`side-Keyword` VM as keyword/brand pages — same filter-gated behavior.
The 11-column schema is identical to brand: Name, TopTypeName,
SaleCount, AveragePrice, NewProductSaleCount, ProductCount,
AvgComentCount, AvgScore, SaleCountPrevThree, BusySeason,
CyclicalMarket.

Same limitation as keyword/brand: page requires manual category
dialog interaction to populate data.

Same 14 Amazon markets, same localStorage site switching.
"""
import json
import time
import urllib.request
from pathlib import Path

DAEMON = "http://127.0.0.1:10086"
DEFAULT_SESSION = "sorftime-seller"
SELLER_URL = "https://seller.sorftime.com/home/chooseseller"

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


def ensure_seller_page(session, site=None, sleep_after=8.0):
    if site is not None:
        call("navigate", {"url": SELLER_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(4.0)
        evaluate(f'localStorage.setItem("site","{site}")', session)
        evaluate('location.reload()', session)
        time.sleep(sleep_after)
    else:
        call("navigate", {"url": SELLER_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(sleep_after)


def find_side_keyword_vm(session):
    code = """
    (function () {
      const root = document.querySelector('#app');
      let vm = null;
      const seen = new Set();
      const visit = (n, d) => {
        if (d > 9 || !n || seen.has(n)) return;
        seen.add(n);
        const name = n.$options && (n.$options.name || n.$options._componentTag);
        if (name === 'side-Keyword') vm = n;
        if (n.$children) n.$children.forEach(c => visit(c, d + 1));
      };
      visit(root.__vue__, 0);
      if (!vm) return JSON.stringify({err: 'no side-Keyword'});
      return JSON.stringify({ok: true});
    })()
    """
    return evaluate(code, session)


def read_state(session):
    code = """
    (function () {
      const root = document.querySelector('#app');
      let vm = null;
      const seen = new Set();
      const visit = (n, d) => {
        if (d > 9 || !n || seen.has(n)) return;
        seen.add(n);
        const name = n.$options && (n.$options.name || n.$options._componentTag);
        if (name === 'side-Keyword') vm = n;
        if (n.$children) n.$children.forEach(c => visit(c, d + 1));
      };
      visit(root.__vue__, 0);
      if (!vm) return JSON.stringify({err: 'no side-Keyword'});
      const d = vm._data;
      const table = d.table && d.table.node;
      return JSON.stringify({
        loading: d.loading,
        table_data_len: table && table.data ? table.data.length : 0,
        table_total: table && table.page ? table.page.totalCount : 0,
        table_page_size: table && table.page ? table.page.pageSize : 0,
        table_options_count: table && table.options ? table.options.length : 0,
        table_options_props: table && table.options
          ? table.options.map(o => o.prop) : [],
        table_options_labels: table && table.options
          ? table.options.map(o => o.label) : [],
        kw_list_len: d.keywordData && d.keywordData.List
          ? d.keywordData.List.length : 0,
        screen_select: d.screen && d.screen.select,
        screen_nodeData_keys: d.screen && d.screen.nodeData
          ? Object.keys(d.screen.nodeData) : [],
        site: d.site,
        first_row: table && table.data && table.data[0]
          ? JSON.stringify(table.data[0]).slice(0, 800) : null
      });
    })()
    """
    return evaluate(code, session)


def write_csv(path, rows, base_fields):
    extra = []
    seen = set(base_fields)
    for r in rows:
        for k in r.keys():
            if k not in seen:
                extra.append(k); seen.add(k)
    fields = base_fields + extra
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
