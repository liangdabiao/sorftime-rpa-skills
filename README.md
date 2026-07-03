# sorftime-rpa

Browser-RPA + 数据分析项目，针对 **sorftime.com** (亚马逊卖家分析 SPA)。覆盖 6 个「选品」模块和 5 个「查」模块，每个模块独立 skill。

## 模块覆盖

### 简单使用

1，安装好 **Kimi WebBridge**（ https://www.kimi.com/zh-cn/features/webbridge ）运行且扩展已连接
2，在codex/claude code 安装好 sorftime-rpa skills

`
❯ 请利用 sorftime skill  对 美国蓝牙耳机市场进行全面调研，写详细分析报告给我
❯ 请利用 sorftime skill  对 美国拍照摄影设备市场进行全面调研，写详细分析报告给我
`

### 选品模块

| Skill | sorftime 路径 | 模式 | 数据可用性 |
|---|---|---|---|
| **sorftime-bestseller** | `/home/bestseller` | DOM-driven, 每类目触发 | ✅ 完整 TOP100 |
| **sorftime-product** | `/home/chooseproduct` | DOM-driven, 自动加载 | ⚠️ 每站 ~20 个未遮蔽 ASIN（免费层） |
| **sorftime-market** | `/home/choosemarketblock` | DOM-driven, `initData(nodeId)` | ⚠️ 仅 `marketTrendChartData`（20 条/触发） |
| **sorftime-keyword** | `/home/choosekeyword` | DOM-driven, 筛选门控 | ⚠️ 需手动选类目才能填充 |
| **sorftime-brand** | `/home/choosebrand` | DOM-driven, 筛选门控 | ⚠️ 需手动选类目才能填充 |
| **sorftime-seller** | `/home/chooseseller` | DOM-driven, 筛选门控 | ⚠️ 需手动选类目才能填充 |

### 查模块（新品）

| Skill | sorftime 路径 | 输入 | 输出维度 |
|---|---|---|---|
| **sorftime-checkproduct** | `/home/checkproduct` | ASIN（批量，最多 ~100） | 产品详情：价格/销量/评价/BSR/品牌/卖家 |
| **sorftime-checkbrand** | `/home/checkbrand` | 品牌名 / ASIN / 卖家名 / 卖家公司 / 热搜词 | 品牌矩阵：产品数/卖家数/Top100/销量/均价 |
| **sorftime-checkseller** | `/home/checkseller` | 卖家名 / ASIN / 品牌名 / 热搜词 | 卖家店铺：产品数/Top400/月销量/均价 |
| **sorftime-checkmarket** | `/home/checkmarket` | 类目名 / ASIN / 关键词 | 市场概况：月销量/均价/新品占比/星级/周期 |
| **sorftime-checkkeyword** | `/home/checkkeyword` | ASIN / 关键词（实验性） | 多表结构：流量来源/ABA关键词/热搜趋势 |

**14 站点全支持**：US/GB/DE/FR/IN/CA/JP/ES/IT/MX/AE/AU/BR/SA

## 架构

- **kimi-webbridge 驱动**：通过本地 daemon (`http://127.0.0.1:10086`) 控制浏览器
- **DOM-driven 抓取**：sorftime 的 API 用 AES 加密请求/响应（`{v:3, k, d}` 格式），直接调用不可能。每个 skill 驱动 Vue VM 自带的方法（`treeItemClick`, `initData`, `onPageSizeChange` 等）触发加密 POST，然后从 Vue reactive state 读取解密后的数据
- **Python stdlib only**：无第三方依赖
- **CSV + Markdown 报告**：每个 skill 都有 `fetch_*.py` + `analyze.py`

## 快速开始

```bash
# 1. 检查 WebBridge daemon
~/.kimi-webbridge/bin/kimi-webbridge status

# 2. 抓取（示例：bestseller 3 站点）
python .claude/skills/sorftime-bestseller/scripts/fetch_bestseller.py \
    --station US,JP,GB --out data/best.csv

# 3. 生成对比报告
python .claude/skills/sorftime-bestseller/scripts/analyze.py \
    --bestsellers data/best.csv --out-md reports/best.md

# 4. 查模块（示例：checkproduct ASIN 反查）
python .claude/skills/sorftime-checkproduct/scripts/fetch_checkproduct.py \
    --station US,JP --asins B0CHX1W1XY --out data/product_check.csv

# 5. 查模块：品牌矩阵
python .claude/skills/sorftime-checkbrand/scripts/fetch_checkbrand.py \
    --station US,JP --mode brand --queries "Anker,Baseus" --out data/brands.csv
```

## 项目结构

```
sorftime-rpa/
├── README.md                    (本文，中文主版本)
├── README.en.md                 (英文版)
├── CLAUDE.md                    (Claude Code 项目指南)
├── phase1_investigation.md      (调研笔记)
├── .claude/skills/
│   ├── sorftime-bestseller/     (✅ 选品-畅销榜)
│   ├── sorftime-product/        (⚠️ 选品-免费层限制)
│   ├── sorftime-market/         (⚠️ 选市场-部分面板)
│   ├── sorftime-keyword/        (⚠️ 选品-筛选门控)
│   ├── sorftime-brand/          (⚠️ 选品-筛选门控)
│   ├── sorftime-seller/         (⚠️ 选品-筛选门控)
│   ├── sorftime-checkproduct/   (✅ 查-ASIN 产品详情)
│   ├── sorftime-checkbrand/     (✅ 查-品牌矩阵)
│   ├── sorftime-checkseller/    (✅ 查-卖家信息)
│   ├── sorftime-checkmarket/    (✅ 查-细分市场)
│   └── sorftime-checkkeyword/   (🔬 查-关键词, 实验性)
├── data/                        (CSV 输出)
└── reports/                     (Markdown 报告)
```

## 已知限制

### sorftime API 加密
sorftime 用混淆的 AES routine 加密所有 API 请求/响应。直接调用 `api.sorftime.com/*` 不可能。所有 skill 都通过驱动 Vue VM 的内置方法间接调用。

### 免费层遮蔽
- **bestseller**: 完全开放（每类目 TOP100 完整）
- **product**: 每站点 ~20 个未遮蔽 ASIN（其余 ASIN/Name/Brand 显示为 `"--"`）
- **market**: `marketTrendChartData` 暴露（每触发 20 条趋势商品）；其他面板需更深的 UI 交互
- **keyword/brand/seller**: 筛选门控页面，必须先手动开「类目」对话框选类目才能填充数据

### 筛选门控页面（keyword/brand/seller）
这 3 个页面共用 `side-Keyword` Vue VM，但要求用户在浏览器 UI 中：
1. 打开「类目」对话框
2. 选择具体类目
3. 关闭对话框

之后 `keywordData.List` / `table.node.data` 才会填充。脚本会读取 VM 当前状态，所以如果用户在同会话中已选类目，脚本就能读到数据。**完整 reverse-engineer 类目对话框的 Vue 组件交互**留作未来工作。

## 14 站点映射

| Code | Site | 中文 |
|---|---|---|
| 1 | US | 美国 |
| 2 | GB | 英国 |
| 3 | DE | 德国 |
| 4 | FR | 法国 |
| 5 | IN | 印度 |
| 6 | CA | 加拿大 |
| 7 | JP | 日本 |
| 8 | ES | 西班牙 |
| 9 | IT | 意大利 |
| 10 | MX | 墨西哥 |
| 11 | AE | 阿联酋 |
| 12 | AU | 澳大利亚 |
| 13 | BR | 巴西 |
| 14 | SA | 沙特 |

切换站点：`localStorage.setItem("site", "<code>")` + `location.reload()`（URL `?i=` 参数无效）

## 姊妹项目

- **`fastmoss-rpa`** — TikTok Shop 分析（fastmoss.com）
- **`sellersprite-rpa`** — 亚马逊 卖家精灵分析（sellersprite.com，10 站点）

sorftime-rpa 复用了这两个项目的 DOM-driven 模式和报告模板。

## 工具依赖

- **Python 3.10+**（仅用 stdlib）
- **Kimi WebBridge**：`~/.kimi-webbridge/bin/kimi-webbridge status`
- **bash shell**（Windows 上 Git Bash 即可）




### 特别感谢：
https://linux.do 社区佬友