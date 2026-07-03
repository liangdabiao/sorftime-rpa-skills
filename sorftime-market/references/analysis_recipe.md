# sorftime 多站点选市场对比报告

> Auto-filled by `scripts/analyze.py --out-md <path>`. Curly-brace tokens are placeholders.

**抓取时间**: {scrape_date} | **样本量**: {sample} 条 trend items | **站点数**: {station_count} | **数据源**: `{source_files}`

> sorftime 选市场 (`/home/choosemarketblock`) 的免费层主要暴露 `marketTrendChartData`
> — 每个类目触发后获得 20 条趋势商品（含 price/sale/search 指数）。
> 详细统计/品牌/卖家面板需更深入的 UI 交互，本报告不覆盖。

---

## 一、各站点 Top 10 趋势商品（按 sale_show）

{top_per_station}

---

## 二、跨站点重复类目

{cross_station_categories}

---

## 三、各站点 × 类目 销量指数汇总

{category_price_index}

---

## 四、站点趋势样本总览

{station_summary}

---

## 五、行动建议（模板）

| 角色 | 建议 |
|---|---|
| **跨境新手** | _（看 sale_show 高但 search_show 低的类目 — 需求强竞争小）_ |
| **成熟品牌** | _（看跨站重复类目的销售指数对比）_ |

---

## 报告复现命令

```bash
python <path-to-skill>/scripts/fetch_markets.py --station US,JP,GB \
    --categories baby-products,beauty,home-kitchen \
    --out <out-dir>/markets_by_station.csv
python <path-to-skill>/scripts/analyze.py \
    --markets <out-dir>/markets_by_station.csv \
    --out-md <report>.md
```

`<path-to-skill>` = `.claude/skills/sorftime-market` for project install.
