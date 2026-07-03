"""Shared helpers for sorftime-checkproduct skill.

Usage:
    from common import call, evaluate, navigate, ensure_check_page, find_searchbox_vm,
                      trigger_product_search, wait_for_search, read_results_table, write_csv
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

D_PARAM = "JTdCJTIycGFyZW50JTIyJTNBJTIyY2hlY2twcm9kdWN0XzElMjIlMkMlMjJ0eXBlJTIyJTNBJTIyMSUyMiUyQyUyMnN0ZXAlMjIlM0ElMjIxJTIyJTJDJTIydmlld3MlMjIlM0ElMjJjaGVja3Byb2R1Y3QlMjIlN0Q="


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
    """Navigate to /home/checkproduct with site=i param."""
    site_param = SITE_MAP.get(site_code, "1")
    url = f"https://seller.sorftime.com/home/checkproduct?d={D_PARAM}&i={site_param}"
    navigate(url, session, new_tab=True)
    time.sleep(8.0)


def find_searchbox_vm(session):
    """Find the searchBox Vue VM on the page."""
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


def trigger_product_search(asins, session):
    """Set ASIN input and trigger onProductSearch().

    asins: list of ASIN strings or comma-separated string.

    Full sequence:
      1. Set data fields on searchBox VM
      2. Call onCheckBoxOpen -> onAsinDataChange -> onAsinCheckedChange -> onAsinDataOk
      3. Call onProductSearch()
    """
    if isinstance(asins, list):
        asin_str = ",".join(asins)
        asin_list = asins
    else:
        asin_str = asins
        asin_list = [a.strip() for a in asin_str.split(",") if a.strip()]

    asin_json = json.dumps(asin_list)
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
        "const cb=sb._data.checkBox;"
        "cb.asinCheck.textarea='" + asin_str + "';"
        "cb.asinCheck.checked=true;"
        "cb.asinCheck.data=" + asin_json + ";"
        "cb.search='" + asin_str + "';"
        "cb.searchList='" + asin_str + "';"
        "sb._data.keywordSearch='" + asin_str + "';"
        "sb._data.keywordSearchList='" + asin_str + "';"
        "sb._data.hasValue=true;"
        "try{sb.onCheckBoxOpen();}catch(e){}"
        "try{sb.onAsinDataChange('" + asin_str + "');}catch(e){}"
        "try{sb.onAsinCheckedChange(true);}catch(e){}"
        "try{sb.onAsinDataOk();}catch(e){}"
        "try{sb.onProductSearch();return'triggered';}"
        "catch(e){return'error:'+e.message;}"
        "})()"
    )
    out = evaluate(code, session)
    return out.get("data", {}).get("value", "")


def wait_for_search(timeout=30, session=None):
    """Poll btnLoading until false or timeout. Returns True if completed."""
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


def read_results_table(session):
    """Read product results from the DOM .el-table.

    The table has ~15 visible td columns in body rows:
      0=(checkbox), 1=title(ASIN), 2=month_sales, 3=amount,
      4=year_sales, 5=price, 6=category, 7=hidden_profit,
      8=ad_spend, 9=ship_method, 10=seller_type, 11=brand,
      12=rating, 13=reviews, 14=listing_date

    Returns list of dicts.
    """
    code = (
        "(function(){"
        "const table=document.querySelector('.el-table');"
        "if(!table)return JSON.stringify({err:'no_table'});"
        "const bodyRows=table.querySelectorAll('.el-table__body-wrapper tbody tr');"
        "const rows=[];"
        "for(const row of bodyRows){"
        "const cols=Array.from(row.querySelectorAll('td')).map(td=>td.textContent.trim());"
        "const cc=cols.length;"
        "const titleCol=cols[1]||'';"
        "const m=titleCol.match(/\\(B0[A-Z0-9]{7,9}\\)/);"
        "const asin=m?m[0].replace(/[()]/g,''):(titleCol.match(/B0[A-Z0-9]{7,9}/)?titleCol.match(/B0[A-Z0-9]{7,9}/)[0]:'');"
        "const title=asin?titleCol.split(asin)[0].replace(/[()]/g,'').trim():titleCol.slice(0,200);"
        "const r={"
        "asin:asin,"
        "title:title"
        "};"
        "if(cc>2)r.month_sales=cols[2];"
        "if(cc>3)r.month_sales_amount=cols[3];"
        "if(cc>4)r.year_sales=cols[4];"
        "if(cc>5)r.price=cols[5];"
        "if(cc>6)r.category=cols[6];"
        "if(cc>7)r.hidden_profit_score=cols[7];"
        "if(cc>8)r.ad_spend_index=cols[8];"
        "if(cc>9)r.ship_method=cols[9];"
        "if(cc>10)r.seller_type=cols[10];"
        "if(cc>11)r.brand=cols[11];"
        "if(cc>12)r.rating=cols[12];"
        "if(cc>13)r.reviews=cols[13];"
        "if(cc>14)r.listing_date=cols[14];"
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
    """Write rows (list of dicts) to CSV."""
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
