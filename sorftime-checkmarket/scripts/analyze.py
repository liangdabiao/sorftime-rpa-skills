#!/usr/bin/env python3
"""Analyze checkmarket results and generate cross-station comparison report."""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPORT_TEMPLATE = """# sorftime-checkmarket 跨站点对比报告

## 查询概览
- **查询数量**: {query_count}
- **站点数量**: {station_count}
- **查询模式**: {query_mode}
- **数据时间**: {report_time}

## 市场概要

{market_summary}

## 跨站点市场对比

{cross_station_table}

## 各站点详情

{station_details}

## 市场指标对比

{metrics_comparison}

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


def build_market_summary(rows):
    cats = set(r.get("category", "") for r in rows if r.get("category"))
    stations = set(r.get("station", "") for r in rows)
    total_sales = sum(int(r.get("monthly_sales", "0").replace(",", "") or "0") for r in rows)
    lines = [
        f"- **细分市场数**: {len(cats)}",
        f"- **站点数**: {len(stations)}",
        f"- **总月销量**: {total_sales:,}",
    ]
    return "\n".join(lines)


def build_cross_station_table(rows):
    by_cat = {}
    for r in rows:
        cat = r.get("category", "")
        if not cat:
            continue
        by_cat.setdefault(cat, []).append(r)

    multi = {c: rs for c, rs in by_cat.items() if len(set(r.get("station", "") for r in rs)) > 1}
    if not multi:
        return "没有跨站点的市场。\n"

    lines = []
    for cat, rs in sorted(multi.items()):
        lines.append(f"\n### {cat}")
        header = "| 站点 | 月销量 | 均价 | 新品占比 | 平均评价 | 平均星级 | 头部占比 |"
        sep = "|------|--------|------|----------|----------|----------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('station', '')} "
                f"| {r.get('monthly_sales', '')} "
                f"| {r.get('avg_price', '')} "
                f"| {r.get('new_product_ratio', '')} "
                f"| {r.get('avg_reviews', '')} "
                f"| {r.get('avg_rating', '')} "
                f"| {r.get('head_sales_ratio', '')} |"
            )
    return "\n".join(lines)


def build_station_details(rows):
    by_station = {}
    for r in rows:
        by_station.setdefault(r.get("station", "?"), []).append(r)

    lines = []
    for station, rs in sorted(by_station.items()):
        lines.append(f"\n### {station} ({len(rs)} markets)\n")
        header = "| 类目 | 查询词 | 所属大类 | 月销量 | 均价 | 新品占比 | FBA/自营 |"
        sep = "|------|--------|----------|--------|------|----------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('category', '')} "
                f"| {r.get('query', '')} "
                f"| {r.get('parent_category', '')} "
                f"| {r.get('monthly_sales', '')} "
                f"| {r.get('avg_price', '')} "
                f"| {r.get('new_product_ratio', '')} "
                f"| {r.get('fba_self_ratio', '')} |"
            )
    return "\n".join(lines)


def build_metrics_comparison(rows):
    lines = ["| 站点 | 类目 | 月销量 | 平均评价 | 平均星级 | 销量分布 | 周期市场 |"]
    sep = "|------|------|--------|----------|----------|----------|----------|"
    lines.append(sep)
    for r in sorted(rows, key=lambda x: (x.get("station", ""), x.get("category", ""))):
        lines.append(
            f"| {r.get('station', '')} "
            f"| {r.get('category', '')} "
            f"| {r.get('monthly_sales', '')} "
            f"| {r.get('avg_reviews', '')} "
            f"| {r.get('avg_rating', '')} "
            f"| {r.get('sales_distribution', '')} "
            f"| {r.get('is_seasonal', '')} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate checkmarket analysis report")
    parser.add_argument("--results", required=True, help="CSV from fetch_checkmarket.py")
    parser.add_argument("--out-md", default="reports/checkmarket_report.md", help="Output markdown path")
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
        market_summary=build_market_summary(rows),
        cross_station_table=build_cross_station_table(rows),
        station_details=build_station_details(rows),
        metrics_comparison=build_metrics_comparison(rows),
    )

    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to {args.out_md}")


if __name__ == "__main__":
    main()
