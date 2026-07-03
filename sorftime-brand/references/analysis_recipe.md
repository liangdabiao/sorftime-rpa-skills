# sorftime 多站点品牌状态报告

> Auto-filled by `scripts/analyze.py --out-md <path>`. Curly-brace tokens are placeholders.

**抓取时间**: {scrape_date} | **站点数**: {station_count} | **有数据站点**: {populated_count} / {total}

> sorftime 选品牌 (`/home/choosebrand`) 复用 keyword 页面的 side-Keyword VM，
> 但使用品牌专用列模式。同样需要先手动选类目才能填充数据。

**列模式**: `{column_props}`

---

## 一、各站点 VM 状态

{state_table}

---

## 二、已填充数据站点

{populated_section}

---

## 三、未填充数据站点

{unpopulated_section}

---

## 四、行动建议

| 场景 | 操作 |
|---|---|
| **本脚本捕获到数据** | 在浏览器同会话中，本站点的「类目」已选 |
| **本脚本未捕获数据** | 在 sorftime 页面手动打开「类目」对话框 → 选类目 → 重跑 `fetch_brands.py` |

---

## 报告复现命令

```bash
python <path-to-skill>/scripts/fetch_brands.py --station US,JP,GB \
    --out <out-dir>/brand_state.csv
python <path-to-skill>/scripts/analyze.py \
    --brands <out-dir>/brand_state.csv \
    --out-md <report>.md
```

`<path-to-skill>` = `.claude/skills/sorftime-brand` for project install.
