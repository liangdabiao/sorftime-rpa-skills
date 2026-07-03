"""sorftime 选卖家 scraper.

LIMITATION: The 选卖家 page (/home/chooseseller) is filter-gated,
same as keyword/brand. The side-Keyword VM reuses the same
infrastructure with seller-specific column schema (same 11 cols as
brand: Name, TopTypeName, SaleCount, etc.). See SKILL.md for details.

This scraper:
  1. Navigates + sets site via localStorage
  2. Probes the side-Keyword VM state
  3. Reads whatever rows ARE populated
  4. Writes a state-summary CSV
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    SITE_TO_CODE, STATION_NAMES,
    ensure_seller_page, find_side_keyword_vm, read_state, write_csv,
)


def fetch_station(station_code, sleep_after=8.0):
    site_id = next((k for k, v in SITE_TO_CODE.items() if v == station_code), None)
    if site_id is None:
        print(f"[skip] unknown station {station_code}", file=sys.stderr)
        return [], {}

    print(f"[{station_code}] navigate to seller page (site={site_id})...",
          file=sys.stderr)
    ensure_seller_page(session="sorftime-seller", site=site_id,
                       sleep_after=sleep_after)

    vm_check = find_side_keyword_vm("sorftime-seller")
    if not (isinstance(vm_check, dict) and vm_check.get("ok")):
        print(f"[{station_code}] side-Keyword VM not found", file=sys.stderr)
        return [], {"station": station_code, "vm_found": False}

    state = read_state("sorftime-seller")
    if not isinstance(state, dict) or state.get("_error"):
        print(f"[{station_code}] state read failed: {state}", file=sys.stderr)
        return [], {"station": station_code, "vm_found": True, "state_err": True}

    data_len = state.get("table_data_len", 0)
    total = state.get("table_total", 0)
    cols = state.get("table_options_count", 0)
    print(f"[{station_code}] VM ready | populated={data_len} | "
          f"total={total} | cols={cols} | screen_select="
          f"{state.get('screen_select', '')[:60]!r}", file=sys.stderr)

    summary_row = {
        "station": station_code,
        "station_name": STATION_NAMES.get(station_code, ""),
        "vm_found": True,
        "loading": state.get("loading"),
        "table_data_len": data_len,
        "table_total_count": total,
        "column_count": cols,
        "column_props": ",".join(state.get("table_options_props", [])),
        "column_labels": ",".join(state.get("table_options_labels", [])),
        "screen_select": state.get("screen_select", ""),
        "screen_nodeData_keys": ",".join(state.get("screen_nodeData_keys", [])),
        "site": state.get("site", ""),
        "sample_row_json": state.get("first_row") or "",
    }
    return [], summary_row


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--station", required=True,
                   help="Comma-separated site codes (US,JP,GB,...)")
    p.add_argument("--out", required=True, help="CSV output path")
    p.add_argument("--sleep", type=float, default=8.0)
    args = p.parse_args()

    stations = [s.strip().upper() for s in args.station.split(",") if s.strip()]
    if not stations:
        print("error: --station required", file=sys.stderr)
        sys.exit(2)

    summaries = []
    for st in stations:
        try:
            _, summary = fetch_station(st, args.sleep)
            summaries.append(summary)
        except Exception as e:
            print(f"[{st}] failed: {e}", file=sys.stderr)
            summaries.append({"station": st, "error": str(e)})

    base_fields = ["station", "station_name", "vm_found", "loading",
                   "table_data_len", "table_total_count", "column_count",
                   "column_props", "column_labels", "screen_select",
                   "screen_nodeData_keys", "site", "sample_row_json", "error"]
    write_csv(args.out, summaries, base_fields)
    print(f"wrote {len(summaries)} station summaries → {args.out}", file=sys.stderr)
    print(f"\nNOTE: 选卖家 page requires manual category selection per station.")
    print(f"If table_data_len=0, see SKILL.md → Gotchas → Filter-gated page.")


if __name__ == "__main__":
    main()
