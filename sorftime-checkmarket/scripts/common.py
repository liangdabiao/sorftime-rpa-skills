"""Shared helpers for sorftime-checkmarket skill."""

import json, urllib.request, time, csv, io, os, re

DAEMON = "http://127.0.0.1:10086/command"

SITE_MAP = {
    "US": "1", "GB": "2", "DE": "3", "FR": "4",
    "IN": "5", "CA": "6", "JP": "7", "ES": "8",
    "IT": "9", "MX": "10", "AE": "11", "AU": "12",
    "BR": "13", "SA": "14"
}
CODE_MAP = {v: k for k, v in SITE_MAP.items()}

D_PARAM = "JTdCJTIycGFyZW50JTIyJTNBJTIyY2hlY2ttYXJrZXRfMSUyMiUyQyUyMnR5cGUlMjIlM0ElMjIxJTIyJTJDJTIyc3RlcCUyMiUzQSUyMjElMjIlMkMlMjJ2aWV3cyUyMiUzQSUyMmNoZWNrbWFya2V0JTIyJTdE"

MODE_MAP = {"asin": 1, "niche": 2, "keyword": 3, "nodeid": 5, "category": 6, "tree": 7}
MODE_DISPLAY = {1: "查ASIN相关细分市场", 2: "垂直市场挖掘", 3: "热搜关键词查市场", 5: "指定类目查询", 6: "按类目名称查询", 7: "按类目树查询"}


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
    url = f"https://seller.sorftime.com/home/checkmarket?d={D_PARAM}&i={site_param}"
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


def trigger_market_search(text, mode=6, session=None):
    """Set market search input and trigger onMarketSearchClick().

    mode: 1=ASIN, 2=垂直市场挖掘, 3=热搜关键词, 5=指定类目, 6=类目名称(default), 7=类目树
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
        "const m=sb._data.market;"
        "m.model=" + str(mode) + ";"
        "m.search='" + text_escaped + "';"
        "m.textareaShow=true;"
        "sb._data.keywordSearch='" + text_escaped + "';"
        "sb._data.keywordSubject='" + text_escaped + "';"
        "sb._data.hasValue=true;"
        "try{sb.onMarketSearchClick();return'triggered';}"
        "catch(e){return'error:'+e.message;}"
        "})()"
    )
    out = evaluate(code, session)
    return out.get("data", {}).get("value", "")


def wait_for_market_search(timeout=30, session=None):
    """Poll checkMarketBtnLoading until false or timeout."""
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
          return JSON.stringify({loading: sb._data.checkMarketBtnLoading});
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


def read_market_table(session):
    """Read market search results from the DOM .el-table.

    Market table has 12 columns:
      0=checkbox, 1=category_name, 2=parent_category, 3=monthly_sales,
      4=avg_price, 5=new_product_ratio, 6=fba_self_ratio,
      7=avg_reviews, 8=avg_rating, 9=head_sales_ratio,
      10=sales_distribution, 11=is_seasonal
    """
    code = (
        "(function(){"
        "const table=document.querySelector('.el-table');"
        "if(!table)return JSON.stringify({err:'no_table'});"
        "const bodyRows=table.querySelectorAll('.el-table__body-wrapper tbody tr');"
        "const rows=[];"
        "for(const row of bodyRows){"
        "const tds=row.querySelectorAll('td');"
        "const cols=Array.from(tds).map(td=>td.textContent.trim());"
        "const cc=cols.length;"
        "let catName=cols[1]||'';"
        "catName=catName.replace(/我已知晓，不再提醒前往产品看板[\\s\\S]*?(?=[A-Za-z])/,'').trim();"
        "catName=catName.replace(/^\\d+/,'').trim();"
        "catName=catName.replace(/报告\\s*趋势\\s*竞争分析\\s*细分需求\\s*类目单品\\s*新品榜\\s*AI分析.*$/,'').trim();"
        "const r={"
        "category:catName"
        "};"
        "if(cc>2)r.parent_category=cols[2];"
        "if(cc>3)r.monthly_sales=(cols[3].match(/^[\\d,]+/)||[''])[0].replace(/,/g,'');"
        "if(cc>4)r.avg_price=cols[4];"
        "if(cc>5)r.new_product_ratio=cols[5];"
        "if(cc>6)r.fba_self_ratio=cols[6];"
        "if(cc>7)r.avg_reviews=(cols[7].match(/^[\\d,]+/)||[''])[0].replace(/,/g,'');"
        "if(cc>8)r.avg_rating=cols[8];"
        "if(cc>9)r.head_sales_ratio=cols[9];"
        "if(cc>10)r.sales_distribution=cols[10];"
        "if(cc>11)r.is_seasonal=cols[11];"
        "rows.push(r);"
        "}"
        "return JSON.stringify({rows:rows,count:rows.length});"
        "})()"
    )
    out = evaluate(code, session)
    try:
        val = out.get("data", {}).get("value", "{}")
        return json.loads(val).get("rows", [])
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
