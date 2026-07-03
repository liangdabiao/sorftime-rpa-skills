# sorftime 多站点选品对比报告

> Auto-filled by `scripts/analyze.py --out-md <path>`. Curly-brace tokens are placeholders.

**抓取时间**: {scrape_date} | **样本量**: {sample} 条 ASIN | **站点数**: {station_count} | **数据源**: `{source_files}`

> sorftime 免费会员每站点仅暴露约 20 个 ASIN 的完整字段（ASIN/Name/Brand）；其余行 ASIN 显示为 `--`。本报告基于此 ~20 个未遮蔽 ASIN。

---

## 一、各站点 Top 10 商品（按月销量）

{top_per_station}

---

## 二、跨站点重复 ASIN

{cross_station_asins}

---

## 三、各站点品牌集中度

{brand_concentration}

---

## 四、价格带分布

{price_band_distribution}

---

## 五、行动建议（模板）

| 角色 | 建议 |
|---|---|
| **跨境新手** | _（优先跨站 ASIN 未覆盖的市场；价格带分析找差异化空间）_ |
| **成熟品牌** | _（看跨站品牌的 ASIN 矩阵）_ |

---

## 报告复现命令

```bash
python <path-to-skill>/scripts/fetch_products.py --station US,JP,GB \
    --out <out-dir>/products_by_station.csv
python <path-to-skill>/scripts/analyze.py \
    --products <out-dir>/products_by_station.csv \
    --out-md <report>.md
```

`<path-to-skill>` = `.claude/skills/sorftime-product` for project install.
