#!/usr/bin/env python3
"""sorftime-checkkeyword: Scrape keyword data across Amazon marketplaces.

Usage:
    python scripts/fetch_checkkeyword.py --station US --mode reverse --queries B0CHX1W1XY
    python scripts/fetch_checkkeyword.py --station US,JP --mode traffic --queries B0CHX1W1XY
"""

import sys, os, time, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (
    ensure_check_page, find_searchbox_vm, trigger_keyword_search,
    wait_for_keyword_search, read_keyword_tables, write_csv, close_session,
    SITE_MAP, CODE_MAP, MODE_MAP
)


def parse_queries(args_queries, args_input):
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


def flatten_table_rows(tables, query, site_code, mode_label):
    """Flatten multi-table results into rows with metadata."""
    rows = []
    for t in tables:
        for r in t.get("rows", []):
            row = {
                "query": query,
                "station": site_code,
                "site": CODE_MAP.get(site_code, site_code),
                "mode": mode_label,
                "table_idx": t.get("idx", ""),
                "headers": ";".join(t.get("headers", [])[:5]),
            }
            for i, val in enumerate(r):
                row[f"col{i}"] = val
            rows.append(row)
    return rows


def fetch_station(site_code, mode, queries, session_name, sleep_after=5):
    print(f"  [{site_code}] Navigating to checkkeyword page...")
    ensure_check_page(site_code, session_name)

    if not find_searchbox_vm(session_name):
        print(f"  [{site_code}] WARNING: searchBox VM not found")
        return []

    all_rows = []
    for query in queries:
        print(f"  [{site_code}] Searching mode={mode}: '{query}'...")
        result = trigger_keyword_search(query, mode=mode, session=session_name)
        if result != "triggered":
            print(f"  [{site_code}] Trigger failed: {result}")
            continue

        completed = wait_for_keyword_search(timeout=30, session=session_name)
        if not completed:
            print(f"  [{site_code}] Search timed out")
        time.sleep(sleep_after)

        tables = read_keyword_tables(session_name)
        print(f"  [{site_code}] Got {len(tables)} tables with data")

        rows = flatten_table_rows(tables, query, site_code, str(mode))
        all_rows.extend(rows)

    return all_rows


def main():
    parser = argparse.ArgumentParser(description="sorftime-checkkeyword: Scrape keyword data")
    parser.add_argument("--station", default="US", help="Comma-separated site codes")
    parser.add_argument("--mode", default="reverse",
                        choices=["reverse", "traffic", "root-word", "trend", "ad-strategy"],
                        help="Search mode (default: reverse)")
    parser.add_argument("--queries", help="Comma-separated search queries (ASINs or keywords)")
    parser.add_argument("--input", help="CSV file with queries")
    parser.add_argument("--out", default="data/checkkeyword_results.csv", help="Output CSV path")
    parser.add_argument("--sleep-per-station", type=int, default=3)
    args = parser.parse_args()

    queries = parse_queries(args.queries, args.input)
    if not queries:
        print("ERROR: No queries provided.")
        sys.exit(1)

    sites = [s.strip().upper() for s in args.station.split(",")]
    print(f"Mode: {args.mode}")
    print(f"Queries ({len(queries)}): {', '.join(queries[:5])}")
    print(f"Stations: {', '.join(sites)}")

    all_rows = []
    for i, site in enumerate(sites):
        session_name = f"checkkeyword_{site.lower()}"
        rows = fetch_station(site, args.mode, queries, session_name, sleep_after=args.sleep_per_station)
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
        print("\nNo data collected. Page has 6+ complex sub-tables; see references/environment.md.")


if __name__ == "__main__":
    main()
