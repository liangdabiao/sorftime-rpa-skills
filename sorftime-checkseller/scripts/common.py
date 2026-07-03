"""Shared helpers for sorftime-checkseller skill."""

import json, urllib.request, time, csv, io, os, re

DAEMON = "http://127.0.0.1:10086/command"

SITE_MAP = {
    "US": "1", "GB": "2", "DE": "3", "FR": "4",
    "IN": "5", "CA": "6", "JP": "7", "ES": "8",
    "IT": "9", "MX": "10", "AE": "11", "AU": "12",
    "BR": "13", "SA": "14"
}
CODE_MAP = {v: k for k, v in SITE_MAP.items()}

D_PARAM = "JTdCJTIycGFyZW50JTIyJTNBJTIyY2hlY2tzZWxsZXJfMSUyMiUyQyUyMnR5cGUlMjIlM0ElMjIxJTIyJTJDJTIyc3RlcCUyMiUzQSUyMjElMjIlMkMlMjJ2aWV3cyUyMiUzQSUyMmNoZWNrc2VsbGVyJTIyJTdE"

MODE_MAP = {"asin": 1, "brand": 2, "seller": 3, "keyword": 4}
MODE_DISPLAY = {1: "按ASIN查", 2: "按品牌名称查", 3: "按卖家名称查", 4: "按热搜关键词查"}


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
    """Navigate to /home/checkseller with site=i param."""
    site_param = SITE_MAP.get(site_code, "1")
    url = f"https://seller.sorftime.com/home/checkseller?d={D_PARAM}&i={site_param}"
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


def trigger_seller_search(text, mode=3, session=None):
    """Set seller search input and trigger onSellerSearch().

    mode: 1=ASIN, 2=品牌名称, 3=卖家名称(default), 4=热搜关键词
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
        "const cs=sb._data.checkseller;"
        "cs.model=" + str(mode) + ";"
        "cs.search='" + text_escaped + "';"
        "cs.textareaShow=true;"
        "sb._data.keywordSearch='" + text_escaped + "';"
        "sb._data.hasValue=true;"
        "try{sb.onSellerSearch();return'triggered';}"
        "catch(e){return'error:'+e.message;}"
        "})()"
    )
    out = evaluate(code, session)
    return out.get("data", {}).get("value", "")


def wait_for_seller_search(timeout=30, session=None):
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


def read_seller_table(session):
    """Read seller search results from the DOM .el-table.

    Seller table has 19 columns:
      0=checkbox, 1=seq, 2=seller_name, 3=seller_country_company,
      4=total_products, 5=total_brands, 6=top400_products, 7=top400_brands,
      8=monthly_sales_sum, 9=monthly_sales_amount_sum, 10=avg_price,
      11=avg_reviews, 12=head_product_sales_ratio, 13=new_product_count,
      14=new_brand_count, 15=new_avg_price, 16=new_avg_rating,
      17=new_avg_reviews, 18=new_avg_sales

    Seller name is extracted from the visible <span> inside col 2.
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
        "let sellerName=cols[2]||'';"
        "try{"
        "const spans=tds[2].querySelectorAll('span');"
        "for(const sp of spans){"
        "if(sp.offsetParent!==null&&sp.children.length===0){"
        "const t=sp.textContent.trim();"
        "if(t&&!t.includes('我已知晓')&&!t.includes('产品看板')&&!t.includes('运营类目')&&!t.includes('分析卖家')&&t.length<60){sellerName=t;break;}"
        "}"
        "}"
        "}catch(e){}"
        "const r={"
        "seller:sellerName"
        "};"
        "if(cc>3)r.seller_country=cols[3];"
        "if(cc>4)r.total_products=(cols[4].match(/^[\\d,]+/)||[''])[0].replace(/,/g,'');"
        "if(cc>5)r.total_brands=cols[5];"
        "if(cc>6)r.top400_products=cols[6];"
        "if(cc>7)r.top400_brands=cols[7];"
        "if(cc>8)r.monthly_sales_sum=cols[8];"
        "if(cc>9)r.monthly_sales_amount_sum=cols[9];"
        "if(cc>10)r.avg_price=cols[10];"
        "if(cc>11)r.avg_reviews=cols[11];"
        "if(cc>12)r.head_product_sales_ratio=cols[12];"
        "if(cc>13)r.new_product_count=cols[13];"
        "if(cc>14)r.new_brand_count=cols[14];"
        "if(cc>15)r.new_avg_price=cols[15];"
        "if(cc>16)r.new_avg_rating=cols[16];"
        "if(cc>17)r.new_avg_reviews=cols[17];"
        "if(cc>18)r.new_avg_sales=cols[18];"
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
