"""Shared helpers for sorftime-checkkeyword skill.

NOTE: The checkkeyword page is complex with 6+ sub-tables. This is a
best-effort implementation. Some sub-modes may need additional investigation.
"""

import json, urllib.request, time, csv, io, os, re

DAEMON = "http://127.0.0.1:10086/command"

SITE_MAP = {
    "US": "1", "GB": "2", "DE": "3", "FR": "4",
    "IN": "5", "CA": "6", "JP": "7", "ES": "8",
    "IT": "9", "MX": "10", "AE": "11", "AU": "12",
    "BR": "13", "SA": "14"
}
CODE_MAP = {v: k for k, v in SITE_MAP.items()}

D_PARAM = "JTdCJTIycGFyZW50JTIyJTNBJTIyY2hlY2tleXdvcmRfMSUyMiUyQyUyMnR5cGUlMjIlM0ElMjIxJTIyJTJDJTIyc3RlcCUyMiUzQSUyMjElMjIlMkMlMjJ2aWV3cyUyMiUzQSUyMmNoZWNra2V5d29yZCUyMiU3RA=="

MODE_MAP = {
    "traffic": 1,           # 查产品流量结构
    "reverse": 3,           # 反查关键词
    "root-word": 2,         # 反查出单词
    "trend": "trend",       # 查关键词流量趋势
    "ad-strategy": "ad",    # 查关键词广告策略
}
MODE_DISPLAY = {
    1: "查产品流量结构", 3: "反查关键词", 2: "反查出单词",
}


def call(action, args, session):
    body = json.dumps({"action": action, "args": args, "session": session}).encode()
    req = urllib.request.Request(DAEMON, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def evaluate(code, session):
    return call("evaluate", {"code": code}, session)


def navigate(url, session, new_tab=True):
    return call("navigate", {"url": url, "newTab": new_tab, "group_title": "sorftime"}, session)


def ensure_check_page(site_code, session):
    site_param = SITE_MAP.get(site_code, "1")
    url = f"https://seller.sorftime.com/home/checkkeyword?d={D_PARAM}&i={site_param}"
    navigate(url, session, new_tab=True)
    time.sleep(8.0)


def find_searchbox_vm(session):
    code = """(() => {
      const root = document.querySelector('#app');
      const seen = new Set();
      let sb = null;
      const visit = (n, d) => {
        if (d > 12 || !n || seen.has(n)) return;
        seen.add(n);
        const nm = n.$options && (n.$options.name || n.$options._componentTag);
        if (nm === 'searchBox') sb = n;
        if (n.$children) n.$children.forEach(c => visit(c, d + 1));
      };
      visit(root.__vue__, 0);
      return sb ? 'found' : 'not_found';
    })()"""
    out = evaluate(code, session)
    return out.get("data", {}).get("value") == "found"


def trigger_keyword_search(text, mode="reverse", session=None):
    """Set keyword search input and trigger onKeywordSearch().

    mode: 'reverse' (default, by ASIN), 'traffic', 'root-word', 'trend', 'ad-strategy'

    For 'reverse' mode, uses the keywordCheck dialog sequence.
    For other modes, sets keywordSearch directly.
    """
    text_escaped = text.replace("'", "\\'").replace("\n", "\\n")
    code = (
        "(function(){"
        "const root=document.querySelector('#app');"
        "const seen=new Set();let sb=null;"
        "const visit=(n,d)=>{if(d>12||!n||seen.has(n))return;seen.add(n);"
        "const nm=n.$options&&(n.$options.name||n.$options._componentTag);"
        "if(nm==='searchBox')sb=n;"
        "if(n.$children)n.$children.forEach(c=>visit(c,d+1));};"
        "visit(root.__vue__,0);"
        "if(!sb)return'no_vm';"
        "sb._data.keywordSearch='" + text_escaped + "';"
        "sb._data.keywordSearchList='" + text_escaped + "';"
        "sb._data.hasValue=true;"
    )
    if mode == "reverse":
        code += (
            "const kwc=sb._data.keywordCheck;"
            "kwc.multipleCheck.textarea='" + text_escaped + "';"
            "kwc.multipleCheck.checked=true;"
            "kwc.multipleCheck.data=['" + text_escaped + "'];"
            "try{sb.onKeywordBoxOpen();}catch(e){}"
            "try{sb.onKeywordDataChange('" + text_escaped + "');}catch(e){}"
            "try{sb.onKeywordCheckedChange(true);}catch(e){}"
            "try{sb.onKeywordDataOk();}catch(e){}"
        )
    code += (
        "try{sb.onKeywordSearch();return'triggered';}"
        "catch(e){return'error:'+e.message;}"
        "})()"
    )
    out = evaluate(code, session)
    return out.get("data", {}).get("value", "")


def wait_for_keyword_search(timeout=30, session=None):
    """Poll btnLoading until false or timeout."""
    for i in range(timeout):
        code = """(() => {
          const root = document.querySelector('#app');
          const seen = new Set();
          let sb = null;
          const visit = (n, d) => {
            if (d > 12 || !n || seen.has(n)) return;
            seen.add(n);
            const nm = n.$options && (n.$options.name || n.$options._componentTag);
            if (nm === 'searchBox') sb = n;
            if (n.$children) n.$children.forEach(c => visit(c, d + 1));
          };
          visit(root.__vue__, 0);
          if (!sb) return JSON.stringify({loading: true});
          return JSON.stringify({loading: sb._data.btnLoading});
        })()"""
        out = evaluate(code, session)
        try:
            val = out.get("data", {}).get("value", "{}")
            st = json.loads(val)
            if not st.get("loading", True):
                return True
        except (json.JSONDecodeError, TypeError):
            pass
        time.sleep(1)
    return False


def read_keyword_tables(session):
    """Read all keyword result tables from the DOM.

    The keyword page has ~6 tables. Returns all rows from tables with data.
    Each table is keyed by its index and header hints.
    """
    code = (
        "(function(){"
        "const tables=document.querySelectorAll('.el-table');"
        "const result=[];"
        "for(let i=0;i<tables.length;i++){"
        "const body=tables[i].querySelector('.el-table__body-wrapper');"
        "if(!body)continue;"
        "const rows=body.querySelectorAll('tr');"
        "if(rows.length===0)continue;"
        "const headers=Array.from(tables[i].querySelectorAll('.el-table__header-wrapper th')).map(th=>th.textContent.trim().slice(0,40));"
        "const data=[];"
        "for(const row of rows){"
        "const cols=Array.from(row.querySelectorAll('td')).map(td=>td.textContent.trim().slice(0,60));"
        "if(cols.length>1||cols[0].length>0)data.push(cols);"
        "}"
        "if(data.length>0)result.push({idx:i,headers:headers.slice(0,8),rows:data.slice(0,20),totalRows:data.length});"
        "}"
        "return JSON.stringify({tables:result});"
        "})()"
    )
    out = evaluate(code, session)
    try:
        val = out.get("data", {}).get("value", "{}")
        return json.loads(val).get("tables", [])
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def write_csv(path, rows, extra_fields=None):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    if extra_fields:
        for f in extra_fields:
            if f not in fieldnames:
                fieldnames.append(f)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def close_session(session):
    call("close_session", {}, session)
