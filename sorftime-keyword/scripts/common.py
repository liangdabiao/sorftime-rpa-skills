"""Shared helpers for sorftime-keyword scripts.

DOM-driven skill. The 关键词趋势选品 page (/home/choosekeyword) is a
filter-gated keyword board. Unlike bestseller (which auto-loads on
category click), this page requires the user to explicitly open a
category picker dialog and select categories before any data populates.

Page state shape:
  side-Keyword VM holds:
    - keywordData.List   (results, empty until filter applied)
    - table.node.data    (alt result location, empty until filter)
    - screen.select      (selected category spec string)
    - screen.nodeData    (selected node map)
    - table.node.options (11-column schema, always populated)

API endpoint (encrypted):
  POST https://api.sorftime.com/api/keywordboard/querykeywordboard?site=NN
  Body: AES-encrypted via page's app.js obfuscator
  Response: {v:3, k:"<b64>", d:"<AES ciphertext>"} decrypted by axios
  transformResponse back into JSON

This skill provides navigation + VM probe + raw decryption-via-VM
helpers. Full reverse-engineering of the category dialog is left as
future work — see references/api_notes.md for the unfinished
investigation path.

Same 14 Amazon markets, same localStorage site switching.
"""
import json
import time
import urllib.request
from pathlib import Path

DAEMON = "http://127.0.0.1:10086"
DEFAULT_SESSION = "sorftime-keyword"
KEYWORD_URL = "https://seller.sorftime.com/home/choosekeyword"

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


def ensure_keyword_page(session, site=None, sleep_after=8.0):
    """Navigate to the keyword page; optionally set site via localStorage.

    The page needs ~7-8s to fully mount Vue + initialize the
    side-Keyword VM + fire initial encrypted POSTs.
    """
    if site is not None:
        call("navigate", {"url": KEYWORD_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(4.0)
        evaluate(f'localStorage.setItem("site","{site}")', session)
        evaluate('location.reload()', session)
        time.sleep(sleep_after)
    else:
        call("navigate", {"url": KEYWORD_URL, "newTab": True,
                          "group_title": "sorftime"}, session)
        time.sleep(sleep_after)


def find_side_keyword_vm(session):
    """Return side-Keyword VM presence check.

    side-Keyword is the master VM that owns keywordData, table, screen.
    """
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
    """Read side-Keyword VM state — page summary for diagnostic.

    Returns dict with: loading, data_len, total_count, screen_select,
    options_count (column schema), and the first row if populated.
    """
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
      const kw = d.keywordData;
      return JSON.stringify({
        loading: d.loading,
        table_data_len: table && table.data ? table.data.length : 0,
        table_total: table && table.page ? table.page.totalCount : 0,
        table_page_size: table && table.page ? table.page.pageSize : 0,
        table_options_count: table && table.options ? table.options.length : 0,
        kw_list_len: kw && kw.List ? kw.List.length : 0,
        screen_select: d.screen && d.screen.select,
        screen_nodeData_keys: d.screen && d.screen.nodeData
          ? Object.keys(d.screen.nodeData) : [],
        site: d.site,
        first_row: table && table.data && table.data[0]
          ? JSON.stringify(table.data[0]).slice(0, 800) : null,
        first_kw: kw && kw.List && kw.List[0]
          ? JSON.stringify(kw.List[0]).slice(0, 800) : null
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
