# 多渠道损益分析 — 代码操作规划

## 一、数据源确认

| 来源 | 内容 | 可用利润数据 |
|------|------|------------|
| `P&L March 2021.xlsx` 渠道表 (12个) | 各渠道订单级收入、成本(TP)、费用明细 | **是** — 唯一同时含 Net Amount 和 TP 的来源 |
| `P&L March 2021.xlsx / Catalog` | 产品主数据 (TP1/TP2、MRP、品类、重量) | 仅作为产品属性参考 |
| `May-2022.xlsx / Myntra` | 36,754 条 Delivered 订单 | **否** — CP=0，成本缺失 |
| `May-2022.xlsx / Catalog` | 产品主数据 | 同 P&L Catalog，可单独参考 |
| `Amazon Sale Report.xlsx` | 128,975 条 Amazon 交易流水 | **否** — 无成本数据，无法连接 Catalog |
| `Sale Report.xlsx` (Sale/Return) | 248,520 条会计销售台账 | **否** — SKU 与 Catalog 不兼容 |
| `International sale Report.xlsx` | 37,432 条国际销售记录 | **否** — 无成本数据 |
| `Expense IIGF.xlsx` | 17 条杂项收支 | 不可用于订单级利润分析 |

**结论**：核心可用数据 = 12 个 P&L 渠道表的 Delivered 订单，共约 1,393 条。

---

## 二、阶段一：数据加载与清洗

### 2.1 从 xlsx 加载（不碰 CSV）

目标渠道表清单（含 Delivered 订单的 12 个）：

```
Amazon, Amazon FBA, Flipkart, Myntra, Limeroad, Meesho,
Mirraw B2B, Mirraw B2C, Cbazaar, Snapdeal,
Peachmode Fourbuttons B2C, Peachmode Os B2C
```

**操作步骤**：
1. 遍历上述 sheet，读取全部行
2. 统一列名（各表结构一致，但需确认所有列名完全相同）
3. 筛选 `Mode == 'Delivered'` 的订单
4. 转换类型：`Order Date` → datetime，`Net Amount`/`TP`/费用列 → float
5. 剔除 TP 或 Net Amount 为 NaN/0 的行

### 2.2 质量检查

每张渠道表检查：
- 行数、缺失率、负值合理性
- TP 与 Net Amount 的比例范围
- 日期范围
- 异常值标记（如 Net Amount < TP 的严重亏损订单）

### 2.3 合并数据集

12 个渠道表纵向合并，新增 `channel` 列标识来源。

---

## 三、阶段二：特征工程

### 3.1 利润计算

```python
profit = Net Amount - TP - GST - abs(Commission Charges)
         - abs(Shipping Charges) - abs(Other Charges)
```

同时计算：
- `profit_margin = profit / Net Amount`（利润率）
- `revenue_after_fees = Net Amount - GST - abs(Commission Charges)
   - abs(Shipping Charges) - abs(Other Charges)`（扣除平台费用后净收入，不含成本）

### 3.2 衍生特征

| 特征 | 计算方式 |
|------|---------|
| 折扣率 | 已有 `Dis.%` |
| 平台费率 | `(abs(Commission) + abs(Shipping) + abs(Other)) / Net Amount` |
| TP 比例 | `TP / Net Amount`（成本占收入比重） |
| 是否有促销折扣 | `Dis.% > 0` |
| 渠道类型 | B2C vs B2B（从渠道名推断） |

### 3.3 Catalog 关联（可选）

目标：将 Catalog 中的 `Category`、`Weight`、`TP1/TP2`、各渠道 MRP 关联到订单数据。

关键路径：P&L 渠道表中的 SKU 格式为 `Os211_3011_3XL`，Catalog 的 SKU 格式为 `Os211_3011_3XL` — 经检查部分 SKU 格式一致。但 Catalog 共有 SKU 1,330 条，需确认实际匹配率。

---

## 四、阶段三：渠道利润对比分析（4P-Place）

### 4.1 单变量统计

各渠道维度：
- 订单量、平均利润、利润率中位数、利润分布（直方图）
- 亏损订单占比、亏损深度（平均亏损额）
- 净收入（Net Amount）、成本（TP）、费用结构各自占比

### 4.2 渠道费用结构拆解

堆叠柱状图：每渠道的 Net Amount 被拆分为：
```
TP（成本） + GST（税金） + Commission（佣金）
+ Shipping（运费） + Other（其他费用） + Profit（利润）
```

### 4.3 亏损订单的渠道分布

哪些渠道亏损率最高？亏损原因是什么（成本过高 vs 费用过高）？

---

## 五、阶段四：产品维度分析（4P-Product）

### 5.1 品类分析

按 `Category` 分组统计：Kurta、Kurta Set、Tops、Gown 各自的：
- 平均利润、利润率、订单量
- 各渠道内的品类表现差异
- 亏损率

### 5.2 TP 成本分析

TP（成本价）与 Net Amount（售价）的关系：
- 成本加成率分布 `(Net Amount - TP) / TP`
- 不同渠道的成本加成策略差异
- TP 与重量、品类的相关性

---

## 六、阶段五：价格策略分析（4P-Price）

### 6.1 折扣与利润

- 折扣率 `Dis.%` 与利润率的关系（是否存在倒挂）
- 不同折扣区间的订单量分布
- 高折扣是否带来高订单量？量能否补价？

### 6.2 MRP 与实际售价

- MRP vs Net Amount vs TP 的三层价格结构
- 各渠道实际的售价折扣力度（相对于 MRP）

---

## 七、阶段六：促销分析（4P-Promotion）

### 7.1 可分析范围

Promotion 维度数据有限（仅有折扣率和费用项），可做：
- 折扣力度与订单量的关系（同渠道内）
- 高折扣 vs 低折扣订单的利润对比
- 不同渠道的促销力度差异

### 7.2 局限性记录

数据集缺少：广告投入、流量来源、促销活动标记、优惠券使用情况。Promotion 分析停留在价格折扣层面。

---

## 八、阶段七：局限性声明与结论框架

### 8.1 必须明确的局限性

| 局限性 | 影响 |
|--------|------|
| 时间跨度仅 2020.08–2021.03 | 无法分析季节性、年同比趋势 |
| 样本量 1,393 条 | 统计显著性受限，无法做 ML 预测 |
| 渠道严重不平衡 (Myntra 53%) | 汇总统计会被 Myntra 主导 |
| 无广告/流量/转化率数据 | 4P 中 Promotion 分析不完整 |
| Catalog 匹配率可能低 | Product 维度粒度受限 |
| TP 是否等于完整 COGS？ | TP 可能是贸易价格而非完全成本（不含间接费用） |

### 8.2 可产出结论类型

- "在样本期间，XX 渠道平均利润率最高，费用结构差异主要体现在佣金率"
- "Kurta 品类亏损率低于 Kurta Set，主要原因是 TP 占比过高"
- "折扣率超过 60% 的订单中，XX% 亏损"
- "同款产品在不同渠道的利润差异可达 XX 元，主要来自佣金和运费差异"

### 8.3 不可产出结论类型

- "2022 年渠道利润变化趋势"（无 2022 年 P&L 数据）
- "新品上架的利润预测"（样本量不足且受时间截面限制）
- "广告投入对利润的影响"（无广告数据）
- "跨产品线的利润对比"（Catalog 仅覆盖 Os 系列产品）

---

## 九、文件安排

```
scripts/
├── 01_load_validate.py      # 加载 xlsx 渠道表，清洗，合并
├── 02_feature_engineering.py # 利润计算，衍生特征
├── 03_channel_analysis.py    # 渠道利润对比，费用结构拆解
├── 04_product_analysis.py    # 品类/SKU 维度分析
├── 05_price_analysis.py      # 折扣、定价策略分析
├── 06_summary.py             # 汇总统计，生成报告图表
├── utils.py                  # 通用函数（路径、绘图配置等）
└── config.py                 # 配置常量（渠道列表、列名映射等）
```

各脚本可独立运行，前一脚本输出中间数据到 `data/processed/`，后一脚本从中读取。避免在一个超长 notebook 中运行。

---

## 十、执行顺序与依赖

```
01_load_validate.py  (独立)
       ↓
02_feature_engineering.py  (依赖 01 输出)
       ↓
03_channel_analysis.py  ──┐
04_product_analysis.py   ──┤  (均依赖 02 输出，可并行)
05_price_analysis.py     ──┘
       ↓
06_summary.py  (依赖 03-05 的全部或部分输出)
```
