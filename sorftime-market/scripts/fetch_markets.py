"""sorftime 选市场 scraper.

Drives sideMarket.initData(nodeId) for each requested category and reads
marketTrendChartData — the only reliably populated slice on the page.

Other slices (statisticalData.offlineData, marketBoard.items) appear to
require additional UI interactions beyond the scope of free-tier scraping;
those are documented as known limitations in SKILL.md.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    SITE_TO_CODE, STATION_NAMES, DAEMON,
    call, ensure_market_page, find_side_vm, trigger_node,
    read_market_trend,
)


DEFAULT_CATEGORIES = [
    "baby-products", "beauty", "health-household", "home-kitchen",
    "kitchen-utensils-gadgets", "sports-outdoors", "toys-games",
    "pet-supplies", "office-products", "automotive",
]


def discover_node_ids(session):
    """Try to read category nodes from the page's categoryListData."""
    code = """
    (function () {
      const root = document.querySelector('#app');
      const seen = new Set();
      const visit = (n, d) => {
        if (d > 8 || !n || seen.has(n)) return [];
        seen.add(n);
        const dk = n._data ? Object.keys(n._data) : [];
        if (dk.includes('categoryListData') && Array.isArray(n._data.categoryListData)) {
          return n._data.categoryListData.map(c => ({
            nodeId: c.nodeId || c.id || '',
            name: c.name || c.title || '',
            slug: c.slug || c.url || ''
          }));
        }
        let out = [];
        if (n.$children) n.$children.forEach(c => { out = out.concat(visit(c, d+1)); });
        return out;
      };
      return JSON.stringify(visit(root.__vue__, 0));
    })()
    """
    import json
    import urllib.request
    body = json.dumps({"action": "evaluate", "args": {"code": code},
                       "session": session}).encode()
    req = urllib.request.Request(f"{DAEMON}/command", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read())
    if not res.get("ok"):
        return []
    data = res["data"]
    if isinstance(data, dict) and data.get("type") == "string":
        try:
            return json.loads(data["value"])
        except Exception:
            return []
    return data if isinstance(data, list) else []


def fetch_station(station_code, categories, sleep_per_node=4.0):
    """Scrape one station: navigate, discover node IDs, trigger each."""
    site_id = next((k for k, v in SITE_TO_CODE.items() if v == station_code), None)
    if site_id is None:
        print(f"[skip] unknown station {station_code}", file=sys.stderr)
        return []

    print(f"[{station_code}] ensuring market page (site={site_id})...",
          file=sys.stderr)
    ensure_market_page(session="sorftime-market", site=site_id, sleep_after=7.0)

    vm = find_side_vm("sorftime-market")
    if not (isinstance(vm, dict) and vm.get("ok")):
        print(f"[{station_code}] sideMarket VM not found; trying anyway",
              file=sys.stderr)

    nodes = discover_node_ids("sorftime-market")
    if nodes:
        print(f"[{station_code}] discovered {len(nodes)} category nodes",
              file=sys.stderr)
    else:
        print(f"[{station_code}] no nodes auto-discovered; "
              f"market page may need manual category selection",
              file=sys.stderr)

    wanted = set(categories)
    matched = [n for n in nodes
               if (n.get("slug") and n["slug"] in wanted)
               or (n.get("name") and n["name"] in wanted)
               or (n.get("nodeId") and n["nodeId"] in wanted)]

    if not matched:
        print(f"[{station_code}] none of {wanted} matched auto-discovered "
              f"slugs; falling back to first 5 nodes", file=sys.stderr)
        matched = nodes[:5] if nodes else []

    rows = []
    for n in matched:
        node_id = n.get("nodeId") or n.get("id") or ""
        name = n.get("name") or n.get("title") or ""
        slug = n.get("slug") or ""
        if not node_id:
            continue
        print(f"[{station_code}] trigger nodeId={node_id} ({name})",
              file=sys.stderr)
        trigger_node(node_id, "sorftime-market")
        time.sleep(sleep_per_node)
        trend = read_market_trend("sorftime-market")
        for i, item in enumerate(trend):
            rows.append({
                "station": station_code,
                "station_name": STATION_NAMES.get(station_code, ""),
                "category_nodeId": node_id,
                "category_name": name,
                "category_slug": slug,
                "trend_rank": i + 1,
                "title": item.get("title", ""),
                "item_nodeId": item.get("nodeId", ""),
                "price_show": item.get("priceShow", ""),
                "sale_show": item.get("saleShow", ""),
                "search_show": item.get("searchShow", ""),
                "pricsale_show": item.get("pricSaleShow",
                                          item.get("pricSaleShow2", "")),
            })
        print(f"[{station_code}] got {len(trend)} trend items",
              file=sys.stderr)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--station", required=True,
                   help="Comma-separated site codes (US,JP,GB,...)")
    p.add_argument("--out", required=True, help="CSV output path")
    p.add_argument("--categories", default=",".join(DEFAULT_CATEGORIES),
                   help="Comma-separated category slugs/names/nodeIds")
    p.add_argument("--sleep-per-node", type=float, default=4.0)
    args = p.parse_args()

    stations = [s.strip().upper() for s in args.station.split(",") if s.strip()]
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    if not stations:
        print("error: --station required", file=sys.stderr)
        sys.exit(2)

    all_rows = []
    for st in stations:
        try:
            all_rows.extend(fetch_station(st, categories, args.sleep_per_node))
        except Exception as e:
            print(f"[{st}] failed: {e}", file=sys.stderr)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not all_rows:
        print("no rows collected; writing empty CSV", file=sys.stderr)
    base_fields = ["station", "station_name", "category_nodeId",
                   "category_name", "category_slug", "trend_rank", "title",
                   "item_nodeId", "price_show", "sale_show", "search_show",
                   "pricsale_show"]
    extra = []
    seen = set(base_fields)
    for r in all_rows:
        for k in r.keys():
            if k not in seen:
                extra.append(k); seen.add(k)
    fields = base_fields + extra
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)
    print(f"wrote {len(all_rows)} rows → {out}")


if __name__ == "__main__":
    main()
