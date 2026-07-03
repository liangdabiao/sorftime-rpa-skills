#!/usr/bin/env python3
"""sorftime-checkbrand: Scrape brand data across Amazon marketplaces.

Usage:
    # Single brand query, single station
    python scripts/fetch_checkbrand.py --station US --mode brand --queries Anker --out data/brand.csv

    # Multiple queries, multiple stations
    python scripts/fetch_checkbrand.py --station US,JP,GB --mode brand \
        --queries "Anker,Baseus" --out data/brands.csv

    # Other modes: asin, seller-name, seller-company, keyword
    python scripts/fetch_checkbrand.py --station US --mode asin --queries B0CHX1W1XY

    # From CSV input file
    python scripts/fetch_checkbrand.py --station US --mode brand --input brands.csv --out data/brands.csv
"""

import sys, os, time, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (
    ensure_check_page, find_searchbox_vm, trigger_brand_search,
    wait_for_brand_search, read_brand_table, write_csv, close_session,
    SITE_MAP, CODE_MAP, MODE_MAP, MODE_DISPLAY
)


def parse_queries(args_queries, args_input):
    """Parse queries from CLI arg or CSV file."""
    if args_queries:
        return [q.strip() for q in args_queries.split(",") if q.strip()]
    if args_input:
        with open(args_input, "r", encoding="utf-8-sig") as f:
            import csv
            reader = csv.reader(f)
            queries = []
            for row in reader:
                for cell in row:
                    cell = cell.strip()
                    if cell:
                        queries.append(cell)
            return queries
    return []


def fetch_station(site_code, mode, queries, session_name, sleep_after=5):
    """Fetch brand data for one station. Returns list of result dicts."""
    print(f"  [{site_code}] Navigating to checkbrand page...")
    ensure_check_page(site_code, session_name)

    if not find_searchbox_vm(session_name):
        print(f"  [{site_code}] WARNING: searchBox VM not found")
        return []

    all_rows = []
    for query in queries:
        print(f"  [{site_code}] Searching {MODE_DISPLAY.get(mode, mode)}: '{query}'...")
        result = trigger_brand_search(query, mode=mode, session=session_name)
        if result != "triggered":
            print(f"  [{site_code}] Trigger failed: {result}")
            continue

        completed = wait_for_brand_search(timeout=30, session=session_name)
        time.sleep(sleep_after)

        rows = read_brand_table(session_name)
        print(f"  [{site_code}] Got {len(rows)} result(s) for '{query}'")

        for r in rows:
            r["station"] = site_code
            r["site"] = CODE_MAP.get(site_code, site_code)
            r["query"] = query
            r["mode"] = MODE_DISPLAY.get(mode, str(mode))

        all_rows.extend(rows)

    return all_rows


def main():
    parser = argparse.ArgumentParser(description="sorftime-checkbrand: Scrape brand data")
    parser.add_argument("--station", default="US", help="Comma-separated site codes (US,JP,GB...)")
    parser.add_argument("--mode", default="brand",
                        choices=["brand", "asin", "seller-name", "seller-company", "keyword"],
                        help="Search mode (default: brand)")
    parser.add_argument("--queries", help="Comma-separated search queries")
    parser.add_argument("--input", help="CSV file with queries (one per row)")
    parser.add_argument("--out", default="data/checkbrand_results.csv", help="Output CSV path")
    parser.add_argument("--sleep-per-station", type=int, default=3, help="Extra sleep between stations")
    args = parser.parse_args()

    queries = parse_queries(args.queries, args.input)
    if not queries:
        print("ERROR: No queries provided. Use --queries or --input.")
        sys.exit(1)

    mode = MODE_MAP.get(args.mode, 1)
    sites = [s.strip().upper() for s in args.station.split(",")]
    print(f"Mode: {MODE_DISPLAY.get(mode, mode)} ({args.mode})")
    print(f"Queries ({len(queries)}): {', '.join(queries[:5])}{'...' if len(queries) > 5 else ''}")
    print(f"Stations: {', '.join(sites)}")

    all_rows = []
    for i, site in enumerate(sites):
        session_name = f"checkbrand_{site.lower()}"
        rows = fetch_station(site, mode, queries, session_name, sleep_after=args.sleep_per_station)
        all_rows.extend(rows)

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
        print("\nNo data collected. Check page state.")


if __name__ == "__main__":
    main()
