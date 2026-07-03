"""Aggregate sorftime bestseller CSV → multi-station Markdown report.

Reads the combined CSV produced by fetch_bestseller.py and emits:
  - Top 10 ASINs per station (by monthly sales)
  - Brand concentration (which brands dominate each station's Top 100s)
  - Price band distribution per station
  - Cross-station brand repeats (global brands)
  - Cross-station ASIN repeats (truly global products)
  - Seller concentration (top sellers per station)

Usage:
    python analyze.py --bestseller data/by_station.csv --out-md reports/by_station.md
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load_rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def safe_float(s, default=0.0):
    try:
        return float(s) if s else default
    except (ValueError, TypeError):
        return default


def safe_int(s, default=0):
    try:
        return int(float(s)) if s else default
    except (ValueError, TypeError):
        return default


def dedupe(rows):
    """Remove duplicate (station, asin) pairs."""
    seen = set()
    out = []
    for r in rows:
        key = (r.get("station", ""), r.get("asin", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def top_per_station(rows, n=10):
    """Top N products per station by sale_count."""
    by_station = defaultdict(list)
    for r in rows:
        by_station[r.get("station", "?")].append(r)
    lines = []
    for st, items in by_station.items():
        items.sort(key=lambda r: safe_int(r.get("sale_count")), reverse=True)
        st_name = items[0].get("station_name", "") if items else ""
        lines.append(f"\n### {st} ({st_name})")
        lines.append("\n| # | ASIN | 标题 | 品牌 | 月销量 | 价格 | 评分 | 评论 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, it in enumerate(items[:n], 1):
            title = (it.get("name") or "")[:50].replace("|", "/")
            lines.append(
                f"| {i} | {it.get('asin','')} | {title} | {it.get('brand','')} | "
                f"{safe_int(it.get('sale_count')):,} | ${safe_float(it.get('price')):.2f} | "
                f"{safe_float(it.get('score')):.1f} | {safe_int(it.get('comment_count')):,} |"
            )
    return "\n".join(lines)


def cross_station_asins(rows, top_n_per_station=50):
    """ASINs appearing in multiple stations' top-N."""
    by_station = defaultdict(set)
    for r in rows:
        st = r.get("station", "?")
        rank = safe_int(r.get("rank"))
        asin = r.get("asin", "")
        if rank and rank <= top_n_per_station and asin:
            by_station[st].add(asin)
    if len(by_station) < 2:
        return "_（仅一个站点，无法跨站对比）_"
    all_asins = Counter()
    for st, asins in by_station.items():
        for a in asins:
            all_asins[a] += 1
    repeats = [(a, c) for a, c in all_asins.items() if c >= 2]
    repeats.sort(key=lambda x: -x[1])
    if not repeats:
        return f"_（无 ASIN 同时进入多站点 Top {top_n_per_station}）_"
    lines = [f"| ASIN | 进入站点数 | 站点列表 |", "|---|---|---|"]
    for asin, cnt in repeats[:20]:
        sts = [s for s, asins in by_station.items() if asin in asins]
        lines.append(f"| {asin} | {cnt} | {', '.join(sorted(sts))} |")
    return "\n".join(lines)


def cross_station_brands(rows, top_n_asins_per_station=30):
    """Brands appearing in multiple stations' top-N ASINs."""
    by_station = defaultdict(Counter)
    for r in rows:
        st = r.get("station", "?")
        rank = safe_int(r.get("rank"))
        brand = (r.get("brand") or "").strip()
        if rank and rank <= top_n_asins_per_station and brand:
            by_station[st][brand] += 1
    if len(by_station) < 2:
        return "_（仅一个站点，无法跨站对比）_"
    all_brands = Counter()
    brand_stations = defaultdict(set)
    for st, brands in by_station.items():
        for b in brands:
            all_brands[b] += 1
            brand_stations[b].add(st)
    repeats = [(b, c) for b, c in all_brands.items() if c >= 2]
    repeats.sort(key=lambda x: -x[1])
    if not repeats:
        return f"_（无品牌同时进入多站点 Top {top_n_asins_per_station}）_"
    lines = ["| 品牌 | 进入站点数 |", "|---|---|"]
    for brand, _ in repeats[:20]:
        sts = sorted(brand_stations[brand])
        lines.append(f"| {brand} | {len(sts)} ({', '.join(sts)}) |")
    return "\n".join(lines)


def brand_concentration(rows):
    """Top brands per station by total sale_count across their products."""
    by_station = defaultdict(lambda: defaultdict(lambda: {"sales": 0, "products": 0}))
    for r in rows:
        st = r.get("station", "?")
        brand = (r.get("brand") or "").strip()
        if not brand:
            continue
        by_station[st][brand]["sales"] += safe_int(r.get("sale_count"))
        by_station[st][brand]["products"] += 1
    lines = ["| 站点 | Top 5 品牌 (产品数 / 总月销量) |", "|---|---|"]
    for st, brands in by_station.items():
        top = sorted(brands.items(), key=lambda x: -x[1]["sales"])[:5]
        cells = [f"{b}({v['products']}/{v['sales']:,})" for b, v in top]
        lines.append(f"| {st} | {', '.join(cells)} |")
    return "\n".join(lines)


def price_band_distribution(rows):
    """Bucket products by price into bands per station."""
    bands = [(0, 15), (15, 30), (30, 50), (50, 100), (100, 200), (200, float("inf"))]
    labels = ["<$15", "$15-30", "$30-50", "$50-100", "$100-200", "$200+"]
    by_station = defaultdict(lambda: defaultdict(int))
    for r in rows:
        st = r.get("station", "?")
        price = safe_float(r.get("price"))
        for (lo, hi), label in zip(bands, labels):
            if lo <= price < hi:
                by_station[st][label] += 1
                break
    if not by_station:
        return "_（无价格数据）_"
    header = "| 站点 | " + " | ".join(labels) + " |"
    sep = "|---|" + "---|" * len(labels)
    lines = [header, sep]
    for st, dist in by_station.items():
        row = [st] + [str(dist.get(l, 0)) for l in labels]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def seller_concentration(rows, top_n=5):
    """Top sellers per station by product count."""
    by_station = defaultdict(Counter)
    for r in rows:
        st = r.get("station", "?")
        seller = (r.get("seller") or "").strip()
        if seller:
            by_station[st][seller] += 1
    lines = ["| 站点 | Top 5 卖家 (产品数) |", "|---|---|"]
    for st, sellers in by_station.items():
        top = sellers.most_common(top_n)
        cells = [f"{s}({n})" for s, n in top]
        lines.append(f"| {st} | {', '.join(cells)} |")
    return "\n".join(lines)


def category_breakdown(rows):
    """Categories scraped per station + best category by total sales."""
    by_station_cat = defaultdict(lambda: defaultdict(int))
    for r in rows:
        st = r.get("station", "?")
        cat = (r.get("category_name") or "").split("(")[0] or "(unknown)"
        by_station_cat[st][cat] += 1
    lines = ["| 站点 | 类目数 | Top 3 类目（条数） |", "|---|---|---|"]
    for st, cats in by_station_cat.items():
        top = sorted(cats.items(), key=lambda x: -x[1])[:3]
        cells = [f"{c}({n})" for c, n in top]
        lines.append(f"| {st} | {len(cats)} | {', '.join(cells)} |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bestseller", required=True,
                   help="Combined bestseller CSV from fetch_bestseller.py")
    p.add_argument("--out-md", required=True, help="Output Markdown report path.")
    args = p.parse_args()

    rows = dedupe(load_rows(args.bestseller))
    if not rows:
        raise SystemExit(f"no rows in {args.bestseller}")

    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    sources = [args.bestseller]
    station_count = len({r.get("station") for r in rows})
    cat_count = len({(r.get("station"), r.get("category_slug")) for r in rows})

    with out.open("w", encoding="utf-8") as f:
        f.write(f"""# sorftime 多站点 Best Seller 对比报告

**抓取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **样本量**: {len(rows)} 条 ASIN | **站点数**: {station_count} | **类目数**: {cat_count} | **数据源**: `{', '.join(sources)}`

---

## 一、各站点 Top 10 商品（按月销量）
{top_per_station(rows, 10)}

**核心洞察**: _（每个站点的销量头部 ASIN = 该市场的"主战场"；不同站点的差异 = 本地化竞争格局）_

---

## 二、跨站点重复 ASIN（Top 50 内）
{cross_station_asins(rows, 50)}

**洞察方向**：
- 多站点出现的 ASIN = 全球热销品（学习其 listing 国际化策略）
- 这些 ASIN 没覆盖的站点 = 蓝海机会
- 跨站点评论数差异 = 该站点运营时间或资源投入

---

## 三、跨站点重复品牌（Top 30 ASIN 内）
{cross_station_brands(rows, 30)}

**洞察方向**：
- 跨站点品牌 = 全球化玩家（供应链 + 品牌力双强）
- 优先研究这些品牌的产品线 + 国际化定价

---

## 四、各站点品牌集中度（按品牌总销量 Top 5）
{brand_concentration(rows)}

**洞察方向**：
- 头部品牌占总销量比重高 = 品牌集中（红海，新进入者难）
- 多 ASIN 的品牌 = 产品线丰富（标杆）

---

## 五、价格带分布
{price_band_distribution(rows)}

**洞察方向**：
- 主流价格带 = 大众接受度最高（用户期望价位）
- 高价格带集中 = 高端化市场（日/英/德）
- 低价带集中 = 性价比驱动市场（印度/墨西哥）

---

## 六、卖家集中度
{seller_concentration(rows)}

**洞察方向**：
- 同一卖家多个 Top ASIN = 该卖家主导该站点
- Amazon 自己占多数 = Amazon Basics 主导品类

---

## 七、各站点类目覆盖
{category_breakdown(rows)}

**洞察方向**：
- 不同站点的类目结构差异 = 当地消费偏好
- 同一品类在不同站点的销量差 = 优先扩张目标

---

## 八、行动建议（模板）

| 角色 | 建议（根据上方数据填写）|
|---|---|
| **跨境新手** | _（优先跨站点 ASIN 没覆盖的市场；找各站点 Top 类目的差异化机会）_ |
| **成熟品牌** | _（看跨站点品牌的 ASIN 矩阵，找产品线空白）_ |
| **PPC 投手** | _（Top 10 ASIN 的关键词值得埋词）_ |

---

## 报告复现命令

```bash
# Step 1: 拉取每个站点的 Best Seller 数据
python <skill>/scripts/fetch_bestseller.py --station US,JP,GB \\
    --out <out-dir>/bestseller_by_station.csv

# Step 2: 生成报告
python <skill>/scripts/analyze.py \\
    --bestseller <out-dir>/bestseller_by_station.csv \\
    --out-md <report>.md
```

`<skill>` = `.claude/skills/sorftime-bestseller` for project install.
""")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
