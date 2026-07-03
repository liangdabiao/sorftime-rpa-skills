# sorftime 多站点 Best Seller 对比报告

> This template is auto-filled by `scripts/analyze.py --out-md <path>`.
> Curly-brace tokens like `{top_per_station}` are placeholders — do **not** rename them or `analyze.py` rendering will fail.
> After generation, fill in the insight paragraphs (italics placeholders) by interpreting the tables.

**抓取时间**: {scrape_date} | **样本量**: {sample} 条 ASIN | **站点数**: {station_count} | **类目数**: {category_count} | **数据源**: `{source_files}`

---

## 一、各站点 Top 10 商品（按月销量）

{top_per_station}

**核心洞察**: _（看每个站点的销量头部 ASIN：直接竞品；不同站点的差异 = 本地化竞争格局）_

---

## 二、跨站点重复 ASIN（Top 50 内）

{cross_station_asins}

**洞察方向**：
- 多站点出现的 ASIN = 全球热销品（学习其 listing 国际化策略）
- 这些 ASIN 没覆盖的站点 = 蓝海机会
- 跨站点评论数差异 = 该站点运营时间或资源投入

---

## 三、跨站点重复品牌（Top 30 ASIN 内）

{cross_station_brands}

**洞察方向**：
- 跨站点品牌 = 全球化玩家（供应链 + 品牌力双强）
- 优先研究这些品牌的产品线 + 国际化定价

---

## 四、各站点品牌集中度

{brand_concentration}

**洞察方向**：
- 头部品牌占总销量比重高 = 品牌集中（红海，新进入者难）
- 多 ASIN 的品牌 = 产品线丰富（标杆）

---

## 五、价格带分布

{price_band_distribution}

**洞察方向**：
- 主流价格带 = 大众接受度最高（用户期望价位）
- 高价格带集中 = 高端化市场（日/英/德/阿联酋/沙特）
- 低价带集中 = 性价比驱动市场（印度/墨西哥/巴西）

---

## 六、卖家集中度

{seller_concentration}

**洞察方向**：
- 同一卖家多个 Top ASIN = 该卖家主导该站点
- Amazon 自己占多数 = Amazon Basics 主导品类

---

## 七、各站点类目覆盖

{category_breakdown}

**洞察方向**：
- 不同站点的类目结构差异 = 当地消费偏好（如 JP 有"DIY・工具・ガーデン"专类，US 没有）
- 同一品类在不同站点的销量差 = 优先扩张目标
- 站点类目数差异 = sorftime 对该市场的覆盖深度

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
python <path-to-skill>/scripts/fetch_bestseller.py --station US,JP,GB \
    --out <out-dir>/bestseller_by_station.csv

# Step 2: 生成报告
python <path-to-skill>/scripts/analyze.py \
    --bestseller <out-dir>/bestseller_by_station.csv \
    --out-md <report>.md
```

`<path-to-skill>` = the directory holding this skill's `SKILL.md` (`.claude/skills/sorftime-bestseller` for project install, `~/.claude/skills/sorftime-bestseller` for user install).
