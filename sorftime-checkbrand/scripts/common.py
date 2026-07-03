"""Shared helpers for sorftime-checkbrand skill.

Usage:
    from common import call, evaluate, ensure_check_page, find_searchbox_vm,
                      trigger_brand_search, wait_for_brand_search,
                      read_brand_table, write_csv, close_session
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

D_PARAM = "JTdCJTIycGFyZW50JTIyJTNBJTIyY2hlY2ticmFuZF8xJTIyJTJDJTIydHlwZSUyMiUzQSUyMjElMjIlMkMlMjJzdGVwJTIyJTNBJTIyMSUyMiUyQyUyMnZpZXdzJTIyJTNBJTIyY2hlY2ticmFuZCUyMiU3RA=="

MODE_MAP = {
    "brand": 1,
    "asin": 2,
    "seller-name": 3,
    "seller-company": 4,
    "keyword": 5
}
MODE_LABEL = {v: k for k, v in MODE_MAP.items()}
MODE_DISPLAY = {1: "按品牌名称查", 2: "按ASIN查", 3: "按卖家名称查", 4: "按卖家公司查", 5: "按热搜关键词查"}


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
    """Navigate to /home/checkbrand with site=i param."""
    site_param = SITE_MAP.get(site_code, "1")
    url = f"https://seller.sorftime.com/home/checkbrand?d={D_PARAM}&i={site_param}"
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


def trigger_brand_search(text, mode=1, session=None):
    """Set brand search input and trigger onBrandSearch().

    mode: 1=品牌名称, 2=ASIN, 3=卖家名称, 4=卖家公司, 5=热搜关键词
    text: search text (single or multi-line for brand mode)
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
        "const b=sb._data.brand;"
        "b.search='" + text_escaped + "';"
        "b.textareaShow=true;"
        "sb._data.keywordSearch='" + text_escaped + "';"
        "sb._data.hasValue=true;"
        "try{sb.onBrandSearch();return'triggered';}"
        "catch(e){return'error:'+e.message;}"
        "})()"
    )
    out = evaluate(code, session)
    return out.get("data", {}).get("value", "")


def wait_for_brand_search(timeout=30, session=None):
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


def read_brand_table(session):
    """Read brand search results from the DOM .el-table.

    Brand summary table has 18 columns (two-row header):
      0=checkbox, 1=brand_name, 2=total_products, 3=total_sellers,
      4=top100_products, 5=top100_new_products, 6=product_count_ratio,
      7=monthly_sales_sum, 8=monthly_sales_amount_sum, 9=avg_price,
      10=avg_reviews, 11=head_product_sales_ratio,
      12=new_product_count, 13=new_seller_count, 14=new_avg_price,
      15=new_avg_rating, 16=new_avg_reviews, 17=new_avg_sales

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
        "let brandName=cols[1]||'';"
        "const cleanBrand=brandName.replace(/产品图片|产品链接|品牌报告|销量趋势|运营类目分析|分析品牌产品|该品牌中销量最高的前\\d+名产品，点击产品图片可跳转对应的产品链接/g,'').trim();"
        "const r={"
        "brand:cleanBrand.split(/\\s+/)[0]"
        "};"
        "if(cc>2)r.total_products=(cols[2].match(/^\\d+/)||[''])[0];"
        "if(cc>3)r.total_sellers=cols[3];"
        "if(cc>4)r.top100_products=cols[4];"
        "if(cc>5)r.top100_new_products=cols[5];"
        "if(cc>6)r.product_count_ratio=cols[6];"
        "if(cc>7)r.monthly_sales_sum=cols[7];"
        "if(cc>8)r.monthly_sales_amount_sum=cols[8];"
        "if(cc>9)r.avg_price=cols[9];"
        "if(cc>10)r.avg_reviews=cols[10];"
        "if(cc>11)r.head_product_sales_ratio=cols[11];"
        "if(cc>12)r.new_product_count=cols[12];"
        "if(cc>13)r.new_seller_count=cols[13];"
        "if(cc>14)r.new_avg_price=cols[14];"
        "if(cc>15)r.new_avg_rating=cols[15];"
        "if(cc>16)r.new_avg_reviews=cols[16];"
        "if(cc>17)r.new_avg_sales=cols[17];"
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
