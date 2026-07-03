"""sorftime bestseller fetcher.

For each requested station, walks every top-level category in the Amazon
Best Sellers tree and dumps TOP100 products per category. Reads the
decrypted result straight out of the page's Vue VM (sorftime encrypts
API bodies, so direct fetch() is impossible — see common.py docstring).

Usage:
  python fetch_bestseller.py --station US --out data/us_bestseller.csv
  python fetch_bestseller.py --station US,JP,GB --out data/by_station.csv
"""
import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", required=True,
                    help="Comma-separated site codes: US,JP,GB,DE,FR,IT,ES,CA,IN,MX,AE,AU,BR,SA")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--categories", default=None,
                    help="Comma-separated category slugs (default: all top-level)")
    ap.add_argument("--max-categories", type=int, default=None,
                    help="Cap categories per station (debug)")
    args = ap.parse_args()

    stations = [s.strip().upper() for s in args.station.split(",")]
    invalid = [s for s in stations if s not in common.CODE_TO_SITE]
    if invalid:
        sys.exit(f"Unknown station(s): {invalid}. Valid: {sorted(common.CODE_TO_SITE)}")

    wanted = args.categories.split(",") if args.categories else None
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows = []
    base_fields = [
        "station", "station_name", "category_slug", "category_name",
        "rank", "asin", "name", "brand", "price", "sale_count",
        "sale_estimate", "gross_profit", "fba_fee", "deliver",
        "score", "comment_count", "seller", "seller_nationality",
        "sale_time", "sale_time_day", "asin_url", "image_url",
        "node_id", "single_price",
    ]
    seen_keys = set()  # (station, category_slug, asin) dedup

    session = common.DEFAULT_SESSION

    for idx, code in enumerate(stations):
        site = common.CODE_TO_SITE[code]
        cn_name = common.STATION_NAMES[code]
        print(f"\n=== [{idx+1}/{len(stations)}] {code} ({cn_name}, site={site}) ===")

        common.ensure_bestseller_page(session, site=site)
        # Wait for zTree to be ready (varies by network)
        cats = []
        for _ in range(40):
            res = common.get_categories(session)
            if isinstance(res, list):
                cats = res
                break
            time.sleep(0.5)
        if not cats:
            print(f"  WARN: zTree never loaded for {code}, skipping")
            continue
        print(f"  {len(cats)} top-level categories available")

        if wanted:
            cats = [c for c in cats if c["slug"] in wanted]
        if args.max_categories:
            cats = cats[:args.max_categories]

        for ci, cat in enumerate(cats):
            print(f"  [{ci+1}/{len(cats)}] {cat['slug']} ({cat['name'][:30]})...", end=" ", flush=True)
            rows = common.select_category(cat["slug"], session, max_wait=25)
            if not isinstance(rows, list):
                print(f"FAIL ({rows})")
                continue
            count_new = 0
            for r in rows:
                key = (code, cat["slug"], r.get("ASIN"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                row = {
                    "station": code,
                    "station_name": cn_name,
                    "category_slug": cat["slug"],
                    "category_name": cat["name"],
                    "rank": r.get("Number"),
                    "asin": r.get("ASIN"),
                    "name": r.get("Name"),
                    "brand": r.get("Brand"),
                    "price": r.get("Price"),
                    "sale_count": r.get("SaleCount"),
                    "sale_estimate": r.get("SaleEstimate"),
                    "gross_profit": r.get("GrossProfit"),
                    "fba_fee": r.get("FBAFee"),
                    "deliver": r.get("Deliver"),
                    "score": r.get("Score"),
                    "comment_count": r.get("CommentCount"),
                    "seller": r.get("Solder"),
                    "seller_nationality": r.get("SolderNationality"),
                    "sale_time": r.get("SaleTime"),
                    "sale_time_day": r.get("SaleTimeDay"),
                    "asin_url": f"https://www.amazon.{common._tld(code)}/dp/{r.get('ASIN')}" if r.get("ASIN") else "",
                    "image_url": r.get("Image"),
                    "node_id": r.get("NodeId"),
                    "single_price": r.get("SinglePrice"),
                }
                all_rows.append(row)
                count_new += 1
            print(f"{len(rows)} rows, {count_new} new")

    # Write CSV
    extra = []
    seen = set(base_fields)
    for r in all_rows:
        for k in r.keys():
            if k not in seen:
                extra.append(k)
                seen.add(k)
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=base_fields + extra, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
