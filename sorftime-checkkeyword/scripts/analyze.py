#!/usr/bin/env python3
"""Analyze checkkeyword results and generate report."""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPORT_TEMPLATE = """# sorftime-checkkeyword 查询报告

## 查询概览
- **查询数量**: {query_count}
- **站点数量**: {station_count}
- **查询模式**: {query_mode}
- **数据时间**: {report_time}

## 表结构摘要

{table_summary}

## 各表数据

{table_details}

---
*报告生成时间: {report_time}*
"""


def load_csv(path):
    import csv
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_table_summary(rows):
    by_table = {}
    for r in rows:
        key = f"Table {r.get('table_idx', '?')} ({r.get('headers', '')[:50]})"
        by_table.setdefault(key, set()).add(r.get("query", ""))
    lines = []
    for table, queries in sorted(by_table.items()):
        lines.append(f"- **{table}**: {len(queries)} query(s)")
    return "\n".join(lines)


def build_table_details(rows):
    by_station = {}
    for r in rows:
        station = r.get("station", "?")
        by_station.setdefault(station, []).append(r)

    lines = []
    for station, rs in sorted(by_station.items()):
        lines.append(f"\n### {station}\n")
        for r in rs:
            lines.append(f"**{r.get('query', '')}** — Table {r.get('table_idx', '?')}")
            cols = {k: v for k, v in r.items() if k.startswith("col") and v}
            if cols:
                lines.append("| Col | Value |")
                lines.append("|-----|-------|")
                for k, v in sorted(cols.items()):
                    lines.append(f"| {k} | {v[:80]} |")
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate checkkeyword report")
    parser.add_argument("--results", required=True, help="CSV from fetch_checkkeyword.py")
    parser.add_argument("--out-md", default="reports/checkkeyword_report.md")
    args = parser.parse_args()

    rows = load_csv(args.results)
    if not rows:
        print("No data to analyze.")
        return

    from datetime import datetime
    query_set = set(r.get("query", "") for r in rows if r.get("query"))
    station_set = set(r.get("station", "") for r in rows)
    modes = set(r.get("mode", "") for r in rows if r.get("mode"))

    report = REPORT_TEMPLATE.format(
        query_count=len(query_set),
        station_count=len(station_set),
        query_mode=", ".join(sorted(modes)) if modes else "N/A",
        report_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        table_summary=build_table_summary(rows),
        table_details=build_table_details(rows),
    )

    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to {args.out_md}")


if __name__ == "__main__":
    main()
