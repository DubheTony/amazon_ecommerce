# Amazon 电商多渠道损益分析

源自 Kaggle 数据集作者 **anilsharma87** 发布的电商销售数据，目的是做多渠道损益分析。

## 数据准备（跑脚本前必看）

原始 xlsx 共约 130MB，**没有放进本仓库**。请先把这 7 个文件放到 `anilsharma87-sales/` 目录下：

```
anilsharma87-sales/
├── P & L March 2021.xlsx              # 核心：19 张表，含 Catalog + 12 个渠道损益表
├── Amazon Sale Report.xlsx
├── May-2022.xlsx
├── Sale Report.xlsx
├── International sale Report.xlsx
├── Cloud Warehouse Compersion Chart.xlsx
└── Expense IIGF.xlsx
```

`input/` 下的 CSV 是早期从这些 xlsx 导出的产物，公式引用大量断裂（`#REF!`），已被 xlsx 取代，
同样不在仓库里。`scripts/` 里的脚本读的是 `anilsharma87-sales/P & L March 2021.xlsx`。

## 目录结构

```
amazon-ecommerce/
├── anilsharma87-sales/        # 原始 xlsx（自行准备，不纳入版本控制）
├── input/                     # 旧代码用的 CSV 导出（自行准备，已弃用）
├── research_plan/
│   └── channel_profit_analysis_plan.md   # 分析方案
├── scripts/                   # 分析脚本，按序号执行
│   ├── 01_load_validate.py
│   ├── 02_feature_engineering.py
│   ├── 03_channel_analysis.py
│   ├── 04_product_analysis.py
│   ├── 05_price_analysis.py
│   └── 06_summary.py
├── gen_html.py                # 生成演示用 HTML
├── 1.ipynb                    # 旧版 Jupyter（含错误：Cost_Price=0）
├── random_forest_no_log.py    # 旧版脚本（依赖 notebook 变量，不可独立运行）
├── requirements.txt
└── 介绍.txt                   # 数据集说明
```

## 关键数据约束

- **唯一可用利润数据**：`P & L March 2021.xlsx` 各渠道表的 Delivered 订单（约 1,393 条）
- **不可恢复的数据**：Amazon Sale Report（128,975 条）没有成本价，也无法关联到 Catalog 的 TP
- **原始文件不要改**：xlsx 是只读源

## 分析起点

见 `research_plan/channel_profit_analysis_plan.md`
