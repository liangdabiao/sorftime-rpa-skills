#!/usr/bin/env python3
"""Analyze checkbrand results and generate cross-station comparison report."""

import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPORT_TEMPLATE = """# sorftime-checkbrand 跨站点对比报告

## 查询概览
- **查询数量**: {query_count}
- **站点数量**: {station_count}
- **查询模式**: {query_mode}
- **数据时间**: {report_time}

## 品牌概要

{brand_summary}

## 跨站点品牌对比

{cross_station_table}

## 各站点详情

{station_details}

## 品牌指标对比

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


def build_brand_summary(rows):
    """Build overall brand summary."""
    brands = set(r.get("brand", "") for r in rows if r.get("brand"))
    stations = set(r.get("station", "") for r in rows)
    total_products = sum(int(r.get("total_products", "0").replace(",", "") or "0") for r in rows)
    total_sellers = sum(int(r.get("total_sellers", "0").replace(",", "") or "0") for r in rows)

    lines = [
        f"- **品牌数**: {len(brands)}",
        f"- **站点数**: {len(stations)}",
        f"- **总产品数**: {total_products:,}",
        f"- **总卖家数**: {total_sellers:,}",
    ]
    return "\n".join(lines)


def build_cross_station_table(rows):
    """Build cross-station comparison for brands appearing in multiple stations."""
    by_brand = {}
    for r in rows:
        brand = r.get("brand", "")
        if not brand:
            continue
        by_brand.setdefault(brand, []).append(r)

    multi = {b: rs for b, rs in by_brand.items() if len(set(r.get("station", "") for r in rs)) > 1}
    if not multi:
        return "没有跨站点的品牌。\n"

    lines = []
    for brand, rs in sorted(multi.items()):
        lines.append(f"\n### {brand}")
        header = "| 站点 | 查询词 | 总产品数 | 总卖家数 | Top100产品 | Top100新品 | 月销量和 | 均价 | 平均评价 |"
        sep = "|------|--------|----------|----------|------------|------------|----------|------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('station', '')} "
                f"| {r.get('query', '')} "
                f"| {r.get('total_products', '')} "
                f"| {r.get('total_sellers', '')} "
                f"| {r.get('top100_products', '')} "
                f"| {r.get('top100_new_products', '')} "
                f"| {r.get('monthly_sales_sum', '')} "
                f"| {r.get('avg_price', '')} "
                f"| {r.get('avg_reviews', '')} |"
            )
    return "\n".join(lines)


def build_station_details(rows):
    """Build per-station detail sections."""
    by_station = {}
    for r in rows:
        by_station.setdefault(r.get("station", "?"), []).append(r)

    lines = []
    for station, rs in sorted(by_station.items()):
        lines.append(f"\n### {station} ({len(rs)} brands)\n")
        header = "| 品牌 | 查询词 | 模式 | 总产品数 | 总卖家数 | Top100产品 | Top100新品 | 月销量和 | 平均价格 |"
        sep = "|------|--------|------|----------|----------|------------|------------|----------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('brand', '')} "
                f"| {r.get('query', '')} "
                f"| {r.get('mode', '')} "
                f"| {r.get('total_products', '')} "
                f"| {r.get('total_sellers', '')} "
                f"| {r.get('top100_products', '')} "
                f"| {r.get('top100_new_products', '')} "
                f"| {r.get('monthly_sales_sum', '')} "
                f"| {r.get('avg_price', '')} |"
            )
    return "\n".join(lines)


def build_metrics_comparison(rows):
    """Build metric comparison across stations."""
    lines = ["| 站点 | 品牌 | 产品数占比 | Top100产品数 | Top100新品数 | 月销量和 | 月销额和 | 头部产品占比 |"]
    sep = "|------|------|------------|-------------|-------------|----------|----------|-------------|"
    lines.append(sep)
    for r in sorted(rows, key=lambda x: (x.get("station", ""), x.get("brand", ""))):
        lines.append(
            f"| {r.get('station', '')} "
            f"| {r.get('brand', '')} "
            f"| {r.get('product_count_ratio', '')} "
            f"| {r.get('top100_products', '')} "
            f"| {r.get('top100_new_products', '')} "
            f"| {r.get('monthly_sales_sum', '')} "
            f"| {r.get('monthly_sales_amount_sum', '')} "
            f"| {r.get('head_product_sales_ratio', '')} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate checkbrand analysis report")
    parser.add_argument("--results", required=True, help="CSV from fetch_checkbrand.py")
    parser.add_argument("--out-md", default="reports/checkbrand_report.md", help="Output markdown path")
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
        brand_summary=build_brand_summary(rows),
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
