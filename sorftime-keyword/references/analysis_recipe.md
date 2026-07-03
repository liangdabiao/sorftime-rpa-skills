# sorftime 多站点关键词状态报告

> Auto-filled by `scripts/analyze.py --out-md <path>`. Curly-brace tokens are placeholders.

**抓取时间**: {scrape_date} | **站点数**: {station_count} | **有数据站点**: {populated_count} / {total}

> sorftime 选关键词 (`/home/choosekeyword`) 是筛选门控的关键词榜单。
> 此页面要求用户先在浏览器手动开「类目」对话框选类目，否则数据为空。
> 本报告记录每站点 VM 当前状态。

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
| **本脚本捕获到数据** | 在浏览器同会话中，本站点的「类目」已选 — 可在 CSV 中查看 keyword rows |
| **本脚本未捕获数据** | 在 sorftime 页面手动打开「类目」对话框 → 选类目 → 关闭对话框 → 重跑 `fetch_keywords.py` |
| **想要全自动** | 需要 reverse-engineer 类目对话框的 Vue 组件 — 见 `references/api_notes.md` |

---

## 报告复现命令

```bash
python <path-to-skill>/scripts/fetch_keywords.py --station US,JP,GB \
    --out <out-dir>/kw_state.csv
python <path-to-skill>/scripts/analyze.py \
    --keywords <out-dir>/kw_state.csv \
    --out-md <report>.md
```

`<path-to-skill>` = `.claude/skills/sorftime-keyword` for project install.
