# Amazon 电商多渠道损益分析

源自 Kaggle ANil 电商销售数据集，原始意图为多渠道损益分析。

## 目录结构

```
amazon_ecommerce/
├── input/                     # CSV 数据（旧代码使用，部分已损坏）
│   ├── Amazon Sale Report.csv
│   ├── P & L March 2021.csv   # 注意：公式引用断裂，#REF! 大量存在
│   └── ...
├── anilsharma87-sales/        # xlsx 原始数据（来源：Kaggle 原版）
│   ├── P & L March 2021.xlsx  # 核心：19 张表，含 Catalog + 12 个渠道损益表
│   ├── May-2022.xlsx
│   ├── Sale Report.xlsx
│   └── ...
├── research_plan/             # 分析方案
│   └── channel_profit_analysis_plan.md
├── scripts/                   # 分析脚本（待按方案编写）
├── 1.ipynb                    # 旧版 Jupyter（含错误：Cost_Price=0）
├── random_forest_no_log.py    # 旧版脚本（依赖 notebook 变量，不可独立运行）
└── 介绍.txt                   # 数据集说明
```

## 关键数据约束

- **唯一可用利润数据**：P&L March 2021.xlsx 各渠道表的 Delivered 订单（~1,393 条）
- **不可恢复的数据**：Amazon Sale Report（128,975 条）无成本价，且无法关联到 Catalog 的 TP
- **原始文件勿直接修改**：xlsx 为只读源，CSV 为旧代码的导出产物，内容不完整

## 分析起点

见 `research_plan/channel_profit_analysis_plan.md`
