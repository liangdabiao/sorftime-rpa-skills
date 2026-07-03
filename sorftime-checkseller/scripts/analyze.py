#!/usr/bin/env python3
"""Analyze checkseller results and generate cross-station comparison report."""

import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPORT_TEMPLATE = """# sorftime-checkseller 跨站点对比报告

## 查询概览
- **查询数量**: {query_count}
- **站点数量**: {station_count}
- **查询模式**: {query_mode}
- **数据时间**: {report_time}

## 卖家概要

{seller_summary}

## 跨站点卖家对比

{cross_station_table}

## 各站点详情

{station_details}

## 卖家指标对比

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


def build_seller_summary(rows):
    sellers = set(r.get("seller", "") for r in rows if r.get("seller"))
    stations = set(r.get("station", "") for r in rows)
    total_products = sum(int(r.get("total_products", "0").replace(",", "") or "0") for r in rows)
    top400_sellers = sum(1 for r in rows if r.get("top400_products") and r["top400_products"] not in ("--", ""))
    lines = [
        f"- **卖家数**: {len(sellers)}",
        f"- **站点数**: {len(stations)}",
        f"- **进入Top400卖家数**: {top400_sellers}",
        f"- **总产品数**: {total_products:,}",
    ]
    return "\n".join(lines)


def build_cross_station_table(rows):
    by_seller = {}
    for r in rows:
        seller = r.get("seller", "")
        if not seller:
            continue
        by_seller.setdefault(seller, []).append(r)

    multi = {s: rs for s, rs in by_seller.items() if len(set(r.get("station", "") for r in rs)) > 1}
    if not multi:
        return "没有跨站点的卖家。\n"

    lines = []
    for seller, rs in sorted(multi.items()):
        lines.append(f"\n### {seller}")
        header = "| 站点 | 查询词 | 总产品数 | 总品牌数 | Top400产品 | 月销量和 | 月销额和 | 均价 |"
        sep = "|------|--------|----------|----------|------------|----------|----------|------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('station', '')} "
                f"| {r.get('query', '')} "
                f"| {r.get('total_products', '')} "
                f"| {r.get('total_brands', '')} "
                f"| {r.get('top400_products', '')} "
                f"| {r.get('monthly_sales_sum', '')} "
                f"| {r.get('monthly_sales_amount_sum', '')} "
                f"| {r.get('avg_price', '')} |"
            )
    return "\n".join(lines)


def build_station_details(rows):
    by_station = {}
    for r in rows:
        by_station.setdefault(r.get("station", "?"), []).append(r)

    lines = []
    for station, rs in sorted(by_station.items()):
        lines.append(f"\n### {station} ({len(rs)} sellers)\n")
        header = "| 卖家 | 查询词 | 模式 | 国家/地区 | 总产品数 | Top400产品 | 月销量和 | 均价 |"
        sep = "|------|--------|------|-----------|----------|------------|----------|------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('seller', '')} "
                f"| {r.get('query', '')} "
                f"| {r.get('mode', '')} "
                f"| {r.get('seller_country', '')} "
                f"| {r.get('total_products', '')} "
                f"| {r.get('top400_products', '')} "
                f"| {r.get('monthly_sales_sum', '')} "
                f"| {r.get('avg_price', '')} |"
            )
    return "\n".join(lines)


def build_metrics_comparison(rows):
    lines = ["| 站点 | 卖家 | 总品牌数 | 月销量和 | 月销额和 | 平均评价数 | 头部产品占比 |"]
    sep = "|------|------|----------|----------|----------|------------|-------------|"
    lines.append(sep)
    for r in sorted(rows, key=lambda x: (x.get("station", ""), x.get("seller", ""))):
        lines.append(
            f"| {r.get('station', '')} "
            f"| {r.get('seller', '')} "
            f"| {r.get('total_brands', '')} "
            f"| {r.get('monthly_sales_sum', '')} "
            f"| {r.get('monthly_sales_amount_sum', '')} "
            f"| {r.get('avg_reviews', '')} "
            f"| {r.get('head_product_sales_ratio', '')} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate checkseller analysis report")
    parser.add_argument("--results", required=True, help="CSV from fetch_checkseller.py")
    parser.add_argument("--out-md", default="reports/checkseller_report.md", help="Output markdown path")
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
        seller_summary=build_seller_summary(rows),
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
