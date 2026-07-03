"""Aggregate sorftime product-board CSV → multi-station Markdown report."""
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
        return float(s) if s not in (None, "", "-9999") else default
    except (ValueError, TypeError):
        return default


def safe_int(s, default=0):
    try:
        return int(float(s)) if s not in (None, "", "-9999") else default
    except (ValueError, TypeError):
        return default


def dedupe(rows):
    seen = set()
    out = []
    for r in rows:
        key = (r.get("station"), r.get("asin"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def top_per_station(rows, n=10):
    by_station = defaultdict(list)
    for r in rows:
        by_station[r.get("station", "?")].append(r)
    lines = []
    for st, items in by_station.items():
        items.sort(key=lambda r: safe_int(r.get("page_sale_count")), reverse=True)
        st_name = items[0].get("station_name", "") if items else ""
        lines.append(f"\n### {st} ({st_name})")
        lines.append("\n| # | ASIN | 标题 | 品牌 | 月销量 | 价格 | 评分 | 评论 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, it in enumerate(items[:n], 1):
            title = (it.get("name") or "")[:50].replace("|", "/")
            lines.append(
                f"| {i} | {it.get('asin','')} | {title} | {it.get('brand','')} | "
                f"{safe_int(it.get('page_sale_count')):,} | ${safe_float(it.get('price')):.2f} | "
                f"{safe_float(it.get('score')):.1f} | {safe_int(it.get('comment_count')):,} |"
            )
    return "\n".join(lines)


def cross_station_asins(rows):
    by_station = defaultdict(set)
    for r in rows:
        asin = r.get("asin", "")
        if asin:
            by_station[r.get("station", "?")].add(asin)
    if len(by_station) < 2:
        return "_（仅一个站点，无法跨站对比）_"
    all_asins = Counter()
    for st, asins in by_station.items():
        for a in asins:
            all_asins[a] += 1
    repeats = [(a, c) for a, c in all_asins.items() if c >= 2]
    repeats.sort(key=lambda x: -x[1])
    if not repeats:
        return "_（无 ASIN 同时出现在多站点）_"
    lines = ["| ASIN | 进入站点数 | 站点列表 |", "|---|---|---|"]
    for asin, _ in repeats[:20]:
        sts = [s for s, asins in by_station.items() if asin in asins]
        lines.append(f"| {asin} | {len(sts)} | {', '.join(sorted(sts))} |")
    return "\n".join(lines)


def brand_concentration(rows):
    by_station = defaultdict(lambda: defaultdict(lambda: {"sales": 0, "products": 0}))
    for r in rows:
        st = r.get("station", "?")
        brand = (r.get("brand") or "").strip()
        if not brand:
            continue
        by_station[st][brand]["sales"] += safe_int(r.get("page_sale_count"))
        by_station[st][brand]["products"] += 1
    lines = ["| 站点 | Top 5 品牌 (产品数 / 总月销量) |", "|---|---|"]
    for st, brands in by_station.items():
        top = sorted(brands.items(), key=lambda x: -x[1]["sales"])[:5]
        cells = [f"{b}({v['products']}/{v['sales']:,})" for b, v in top]
        lines.append(f"| {st} | {', '.join(cells)} |")
    return "\n".join(lines)


def price_band_distribution(rows):
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--products", required=True, help="Combined products CSV")
    p.add_argument("--out-md", required=True, help="Output Markdown report path")
    args = p.parse_args()

    rows = dedupe(load_rows(args.products))
    if not rows:
        raise SystemExit(f"no rows in {args.products}")

    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    station_count = len({r.get("station") for r in rows})

    with out.open("w", encoding="utf-8") as f:
        f.write(f"""# sorftime 多站点选品对比报告

**抓取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **样本量**: {len(rows)} 条 ASIN | **站点数**: {station_count} | **数据源**: `{args.products}`

> sorftime 免费会员每站点仅暴露约 20 个 ASIN 的完整字段（ASIN/Name/Brand）；其余行 ASIN 显示为 `--`。本报告基于此 ~20 个未遮蔽 ASIN。

---

## 一、各站点 Top 10 商品（按月销量）

{top_per_station(rows, 10)}

**核心洞察**: _（每个站点的头部 ASIN = 该市场的"主战场"；不同站点的差异 = 本地化竞争格局）_

---

## 二、跨站点重复 ASIN

{cross_station_asins(rows)}

**洞察方向**：
- 多站点出现的 ASIN = 全球热销品
- 这些 ASIN 没覆盖的站点 = 蓝海机会

---

## 三、各站点品牌集中度

{brand_concentration(rows)}

---

## 四、价格带分布

{price_band_distribution(rows)}

---

## 五、行动建议（模板）

| 角色 | 建议 |
|---|---|
| **跨境新手** | _（优先跨站 ASIN 未覆盖的市场；价格带分析找差异化空间）_ |
| **成熟品牌** | _（看跨站品牌的 ASIN 矩阵）_ |

---

## 报告复现命令

```bash
python <skill>/scripts/fetch_products.py --station US,JP,GB \\
    --out <out-dir>/products_by_station.csv
python <skill>/scripts/analyze.py \\
    --products <out-dir>/products_by_station.csv \\
    --out-md <report>.md
```

`<skill>` = `.claude/skills/sorftime-product` for project install.
""")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
