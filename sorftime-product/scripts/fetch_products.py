"""sorftime product-board fetcher.

For each requested station, navigates to chooseproduct page, bumps
page-size to 100 (rich page-1 data), reads productboard.data, and
filters out masked rows. Free tier exposes ~20 unmasked ASINs per
station per fetch — beyond that, ASIN/Name/Brand show as "--".

Usage:
  python fetch_products.py --station US --out data/us_products.csv
  python fetch_products.py --station US,JP,GB --out data/by_station.csv
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
    ap.add_argument("--page-size", type=int, default=100,
                    help="Page size (default 100, sorftime ignores beyond)")
    args = ap.parse_args()

    stations = [s.strip().upper() for s in args.station.split(",")]
    invalid = [s for s in stations if s not in common.CODE_TO_SITE]
    if invalid:
        sys.exit(f"Unknown station(s): {invalid}. Valid: {sorted(common.CODE_TO_SITE)}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base_fields = [
        "station", "station_name", "rank", "asin", "parent_asin", "name",
        "brand", "price", "single_price", "gross_profit", "fba_fee",
        "page_sale_count", "page_sale_volume", "year_sale_count",
        "score", "comment_count", "deliver", "seller_nationality",
        "node_id", "update_time", "image_url", "asin_url",
    ]
    all_rows = []
    session = common.DEFAULT_SESSION

    for idx, code in enumerate(stations):
        site = common.CODE_TO_SITE[code]
        cn_name = common.STATION_NAMES[code]
        print(f"\n=== [{idx+1}/{len(stations)}] {code} ({cn_name}, site={site}) ===")

        common.ensure_product_page(session, site=site)
        # Wait for VM ready
        for _ in range(40):
            if common.find_vm(session).get("ok"):
                break
            time.sleep(0.5)
        else:
            print(f"  WARN: VM never ready for {code}, skipping")
            continue

        common.set_page_size(args.page_size, session)
        if not common.wait_for_data(session, expected_len=args.page_size, max_wait=20):
            state = common.vm_state(session)
            print(f"  WARN: data not ready ({state}), attempting anyway")

        rows = common.read_products(session)
        if not isinstance(rows, list):
            print(f"  FAIL: {rows}")
            continue

        count_new = 0
        for i, r in enumerate(rows, 1):
            asin = r.get("ASIN")
            if not asin or asin == "--":
                continue  # masked row
            row = {
                "station": code,
                "station_name": cn_name,
                "rank": i,
                "asin": asin,
                "parent_asin": r.get("ParentAsin"),
                "name": r.get("Name"),
                "brand": r.get("Brand"),
                "price": r.get("Price"),
                "single_price": r.get("SinglePrice"),
                "gross_profit": r.get("GrossProfit"),
                "fba_fee": r.get("FBAFee"),
                "page_sale_count": r.get("PageSaleCount"),
                "page_sale_volume": r.get("PageSaleVolume"),
                "year_sale_count": r.get("YearSaleCount"),
                "score": r.get("Score"),
                "comment_count": r.get("CommentCount"),
                "deliver": r.get("Deliver"),
                "seller_nationality": r.get("SolderNationality"),
                "node_id": r.get("NodeId") or r.get("TopNodeID"),
                "update_time": r.get("UpdateTimeStr"),
                "image_url": r.get("Image"),
                "asin_url": f"https://www.amazon.{common._tld(code)}/dp/{asin}",
            }
            all_rows.append(row)
            count_new += 1
        print(f"  Read {len(rows)} rows, {count_new} unmasked")

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
