#!/usr/bin/env python3
"""Analyze checkproduct results and generate cross-station comparison report."""

import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPORT_TEMPLATE = """# sorftime-checkproduct 跨站点对比报告

## 查询概览
- **ASIN 数量**: {asin_count}
- **站点数量**: {station_count}
- **数据时间**: {report_time}

## 跨站点对比

{cross_station_table}

## 各站点详情

{station_details}

## 价格对比

{price_comparison}

## 评价与星级对比

{review_comparison}

---
*报告生成时间: {report_time}*
"""


def load_csv(path):
    """Load CSV with utf-8-sig."""
    import csv
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_cross_station_table(rows):
    """Build cross-station comparison table for ASINs appearing in multiple stations."""
    by_asin = {}
    for r in rows:
        asin = r.get("asin", "")
        if not asin:
            continue
        by_asin.setdefault(asin, []).append(r)

    multi = {a: rs for a, rs in by_asin.items() if len(rs) > 1}
    if not multi:
        return "没有跨站点的 ASIN。\n"

    lines = []
    for asin, rs in sorted(multi.items()):
        title = rs[0].get("title", "")[:60]
        lines.append(f"\n### {asin} — {title}")
        header = "| 站点 | 月销量 | 年销量 | 价格 | 评分 | 评价数 | 品牌 | 上架时间 |"
        sep = "|------|--------|--------|------|------|--------|------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('station', '')} "
                f"| {r.get('month_sales', '')} "
                f"| {r.get('year_sales', '')} "
                f"| {r.get('price', '')} "
                f"| {r.get('rating', '')} "
                f"| {r.get('reviews', '')} "
                f"| {r.get('brand', '')} "
                f"| {r.get('listing_date', '')} |"
            )
    return "\n".join(lines)


def build_station_details(rows):
    """Build per-station detail sections."""
    by_station = {}
    for r in rows:
        by_station.setdefault(r.get("station", "?"), []).append(r)

    lines = []
    for station, rs in sorted(by_station.items()):
        lines.append(f"\n### {station} ({len(rs)} ASINs)\n")
        header = "| ASIN | 月销量 | 年销量 | ASIN月销 | 价格 | 评分 | 评价数 | 品牌 | 上架时间 |"
        sep = "|------|--------|--------|----------|------|------|--------|------|----------|"
        lines.extend([header, sep])
        for r in rs:
            lines.append(
                f"| {r.get('asin', '')} "
                f"| {r.get('month_sales', '')} "
                f"| {r.get('year_sales', '')} "
                f"| {r.get('asin_month_sales', '')} "
                f"| {r.get('price', '')} "
                f"| {r.get('rating', '')} "
                f"| {r.get('reviews', '')} "
                f"| {r.get('brand', '')} "
                f"| {r.get('listing_date', '')} |"
            )
    return "\n".join(lines)


def build_price_comparison(rows):
    """Build price comparison section."""
    lines = ["| ASIN | 站点 | 价格 | 卖家类型 | 物流方式 |"]
    sep = "|------|------|------|----------|----------|"
    lines.append(sep)
    for r in sorted(rows, key=lambda x: (x.get("asin", ""), x.get("station", ""))):
        lines.append(
            f"| {r.get('asin', '')} "
            f"| {r.get('station', '')} "
            f"| {r.get('price', '')} "
            f"| {r.get('seller_type', '')} "
            f"| {r.get('ship_method', '')} |"
        )
    return "\n".join(lines)


def build_review_comparison(rows):
    """Build review/rating comparison section."""
    lines = ["| ASIN | 站点 | 评分 | 评价数 | 月销量 |"]
    sep = "|------|------|------|--------|--------|"
    lines.append(sep)
    for r in sorted(rows, key=lambda x: (x.get("asin", ""), x.get("station", ""))):
        lines.append(
            f"| {r.get('asin', '')} "
            f"| {r.get('station', '')} "
            f"| {r.get('rating', '')} "
            f"| {r.get('reviews', '')} "
            f"| {r.get('month_sales', '')} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate checkproduct analysis report")
    parser.add_argument("--results", required=True, help="CSV from fetch_checkproduct.py")
    parser.add_argument("--out-md", default="reports/checkproduct_report.md", help="Output markdown path")
    args = parser.parse_args()

    rows = load_csv(args.results)
    if not rows:
        print("No data to analyze.")
        return

    from datetime import datetime

    asin_set = set(r.get("asin", "") for r in rows if r.get("asin"))
    station_set = set(r.get("station", "") for r in rows)

    report = REPORT_TEMPLATE.format(
        asin_count=len(asin_set),
        station_count=len(station_set),
        report_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cross_station_table=build_cross_station_table(rows),
        station_details=build_station_details(rows),
        price_comparison=build_price_comparison(rows),
        review_comparison=build_review_comparison(rows),
    )

    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to {args.out_md}")


if __name__ == "__main__":
    main()
