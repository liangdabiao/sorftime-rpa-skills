#!/usr/bin/env python3
"""sorftime-checkproduct: Scrape product details by ASIN(s) across Amazon marketplaces.

Usage:
    # Single ASIN, single station
    python scripts/fetch_checkproduct.py --station US --asins B0CHX1W1XY --out data/product.csv

    # Multiple ASINs, multiple stations
    python scripts/fetch_checkproduct.py --station US,JP,GB --asins B0CHX1W1XY,B0BDHZ8Q63 --out data/products.csv

    # From CSV input file
    python scripts/fetch_checkproduct.py --station US --input asins.csv --out data/products.csv
"""

import sys, os, time, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (
    ensure_check_page, find_searchbox_vm, trigger_product_search,
    wait_for_search, read_results_table, write_csv, close_session,
    SITE_MAP, CODE_MAP
)


def parse_asins(args_asins, args_input):
    """Parse ASINs from CLI arg or CSV file."""
    if args_asins:
        return [a.strip() for a in args_asins.split(",") if a.strip()]
    if args_input:
        import csv
        asins = []
        with open(args_input, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    cell = cell.strip()
                    if cell and (cell.startswith("B0") or len(cell) == 10):
                        asins.append(cell)
        return asins
    return []


def fetch_station(site_code, asins, session_name, sleep_after=5):
    """Fetch product data for one station. Returns list of result dicts."""
    print(f"  [{site_code}] Navigating to checkproduct page...")
    ensure_check_page(site_code, session_name)

    if not find_searchbox_vm(session_name):
        print(f"  [{site_code}] WARNING: searchBox VM not found")
        return []

    print(f"  [{site_code}] Searching for {len(asins)} ASIN(s): {', '.join(asins[:3])}...")
    result = trigger_product_search(asins, session_name)
    if result != "triggered":
        print(f"  [{site_code}] Trigger failed: {result}")
        return []

    print(f"  [{site_code}] Waiting for results...")
    completed = wait_for_search(timeout=30, session=session_name)
    time.sleep(sleep_after)

    rows = read_results_table(session_name)
    print(f"  [{site_code}] Got {len(rows)} result(s)")

    # Add station field
    for r in rows:
        r["station"] = site_code
        r["site"] = CODE_MAP.get(site_code, site_code)

    return rows


def main():
    parser = argparse.ArgumentParser(description="sorftime-checkproduct: Scrape product details by ASIN")
    parser.add_argument("--station", default="US", help="Comma-separated site codes (US,JP,GB...)")
    parser.add_argument("--asins", help="Comma-separated ASINs to search")
    parser.add_argument("--input", help="CSV file with ASINs (one per row/cell)")
    parser.add_argument("--out", default="data/checkproduct_results.csv", help="Output CSV path")
    parser.add_argument("--sleep-per-station", type=int, default=3, help="Extra sleep between stations")
    args = parser.parse_args()

    asins = parse_asins(args.asins, args.input)
    if not asins:
        print("ERROR: No ASINs provided. Use --asins or --input.")
        sys.exit(1)

    sites = [s.strip().upper() for s in args.station.split(",")]
    print(f"ASINs: {len(asins)} — {', '.join(asins[:5])}{'...' if len(asins) > 5 else ''}")
    print(f"Stations: {', '.join(sites)}")

    all_rows = []
    for i, site in enumerate(sites):
        session_name = f"checkproduct_{site.lower()}"
        rows = fetch_station(site, asins, session_name, sleep_after=args.sleep_per_station)
        all_rows.extend(rows)

        # Close session if not last
        if i < len(sites) - 1:
            try:
                close_session(session_name)
            except:
                pass
            time.sleep(2)

    if all_rows:
        write_csv(args.out, all_rows)
        print(f"\nTotal: {len(all_rows)} rows → {args.out}")
    else:
        print("\nNo data collected. Check page state (e.g., need to select sub-mode in browser first).")


if __name__ == "__main__":
    main()
