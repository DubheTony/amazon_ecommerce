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

## 关键逻辑约束（必须先理解这些再写代码）

### 约束 1：利润公式的选择依据

计算利润的候选公式有两个，结果差异巨大：

| 方法 | 公式 | Amazon 均值 | 依据 |
|------|------|-----------|------|
| **Payment - TP（采用）** | `Payment - TP` | **177.65** | Payment = Net Amount + Deduction（平台扣费后预期净额），是合同层面的正确利润 |
| Portal Payment - TP（不采用） | `Portal Payment - TP` | **22.42** | Portal Payment 是批次对账编号（同一 Net Amount=849 的订单有 27 种不同值），非逐笔现金结算 |

**验证方法**：在 01_load_validate.py 中，对每个渠道的 Delivered 订单计算两种利润、输出对比表，确认 Payment - TP 的方差远小于 Portal Payment - TP（后者因批次汇总导致方差膨胀）。

**⚠️ Payment 可靠性的额外验证**：Payment 是平台系统计算出的"预期净额"，不一定等于实际到账金额。即使 Payment - TP 方差更小，也不能自动证明 Payment 反映真实现金流。须额外检查：
1. 各渠道是否存在 Net Amount > 0 但 Payment = 0 的订单（可能为未结算订单）
2. 同一渠道内 Payment 是否始终等于 Net Amount + Deduction（后续 2.2 节已设验证门），吻合率须达 100%，否则说明 Payment 列本身存在取值异常
3. 各渠道 Payment 的最小值是否合理（如 Payment 为大幅负数且非取消订单，可能为退款订单误标记为 Delivered）
- **若以上任一项异常**：应在报告中标注该渠道的 Payment 可信度评级为"可疑"，该渠道的利润分析结论附加警告。

### 约束 2：本文"利润"实为"贡献毛利"

计划全篇的"利润"实际含义是：

```
贡献毛利 = Payment - TP
         = Net Amount + Deduction(负值) - TP
         = Net Amount - (GST + |Commission| + |Shipping| + |Other| + |TCS| + |TDS|) - TP
```

此数值**不包含**：
- 固定成本（仓库租金、人员工资、软件订阅、包装耗材）
- 取消订单的隐性成本（见约束 3）
- TP 之外的其他变动成本（见约束 4）
- **退货退款损失 + 退货物流成本**（退货退货Order若被标记为非Delivered则不包含在当前数据中，见约束6）
- **平台月费/订阅费**（如 Amazon Professional Seller Plan 月费）
- **广告费（PPC）**（即使无数据，也需在结论中说明其对利润的可能影响）
- **支付网关手续费**（通常为交易金额的1-3%）
- **入仓物流费、仓储超期费、包装材料费**

**输出结论时每处"利润"必须带有注释或限定词，不可直接称之为"净利润"**。

### 约束 3：取消订单有真实成本，必须单独分析

取消订单（Mode=Cancelled）的特征：
- 所有收入费用列为 0（Net Amount=0, TP=0, 各项费用=0）
- 但 Portal Payment 非零，如 Amazon 渠道取消订单 Portal Payment ≈ **-87.48**（平台对卖家的罚款）

分析步骤：
1. 统计各渠道取消率、取消罚款总额
2. 将取消罚款总额作为**渠道级别的独立损失项**列示，**不做**按订单数量分摊到 Delivered 订单上的"调整后贡献毛利"计算

> **为什么不分摊？** 取消罚款是渠道运营层面的风险成本，不是每个 Delivered 订单的边际成本。分摊只是让所有订单减去同一固定值，不改变订单排序也不揭示结构差异。取消罚款应单独呈现为渠道整体运营效率的一个指标。

3. 若某渠道取消率显著高于其他渠道，需单独标注（可能反映该渠道的定价/库存/履约策略问题）

### 约束 4（原约束4）：TP 可能低估真实成本

TP（Trade Price，贸易价格）是卖家将商品移交给渠道时的内部结算价，但可能不包含：
- 入仓物流费（从工厂到仓库的运输）
- 仓储费（Cloud Warehouse Compersion Chart 显示有按 cft 或按件的仓储费）
- 包装材料费
- 质检费

**处理方式**：定性说明 TP 低估成本的幅度，不做定量调整（因缺乏这些费用的订单级分摊数据）。

### 约束 5：渠道样本严重不平衡

| 渠道 | Delivered 订单数 | 占比 |
|------|----------------|------|
| Myntra | 738 | 53.0% |
| Flipkart | 223 | 16.0% |
| Amazon | 202 | 14.5% |
| Peachmode Fourbuttons B2C | 78 | 5.6% |
| Amazon FBA | 64 | 4.6% |
| Peachmode Os B2C | 32 | 2.3% |
| Mirraw B2B | 24 | 1.7% |
| Mirraw B2C | 17 | 1.2% |
| Limeroad | 5 | 0.4% |
| Meesho | 5 | 0.4% |
| Snapdeal | 3 | 0.2% |
| Cbazaar | 2 | 0.1% |

**处理规则**：
- 渠道汇总统计表必须标注 n
- 单独列一个"其他渠道"分组合并 Limeroad/Meesho/Snapdeal/Cbazaar（n ≤ 5 的渠道）
- 不做跨渠道的统计检验（样本不均等使检验不可靠）
- **全局汇总统计量（如整体平均毛利率）丧失汇总意义，不应发布。所有分析在分渠道层面进行**
- Myntra 主导的分析结论必须在标题注明"（Myntra 主导）"

### 约束 6：退货（Return）订单的处理

P&L 渠道表的 Mode 字段若存在 Return 记录，其成本结构完全不同于 Cancelled 和 Delivered：
- 退货产生退款损失（需全额退还 Net Amount）
- 退货产生逆向物流成本
- 退回商品可能产生折损或折价处理成本

Return 记录若存在应被**排除**出 Delivered 分析集，同时单独统计：
1. 各渠道 Return 订单量及占比
2. Return 订单的总退款金额
3. 在局限性声明中说明：因缺乏退货物流成本数据，退货的真实损失被低估

> 若 P&L 渠道表中不存在 Mode='Return' 的记录，则在局限性中注明"数据源未包含退货记录，贡献毛利可能被系统性高估"。

### 约束 7：季节性偏差——数据时段不可外推

数据时间范围为 2020.08–2021.03，该时段存在两个系统性偏差源：
1. **COVID-19 疫情高峰期**：电商购物行为、物流效率、平台费用政策均处于非常态
2. **印度排灯节（Diwali，通常在10-11月）**：电商大规模促销期，销售结构异于平时

**处理方式**：
- 所有描述性统计（均值、毛利率等）仅限"样本期间内"，不得外推至其他时段
- 若数据日期有日粒度，应绘制月度订单量和毛利率走势图，观察是否存在单月异常
- 在局限性中明确标注这两个偏差源，警示读者

### 约束 8：Dis.% 跨渠道口径一致性

Dis.% 是数据集中唯一的促销相关字段，但各平台对"折扣"的定义可能不同：
- 有的平台按 MRP 计算折扣率： `(MRP - Net Amount) / MRP`
- 有的平台按下单时的历史售价计算
- 有的平台将优惠券抵扣计入折扣

**处理方式**：跨渠道比较 Dis.% 时附加说明"各平台折扣计算口径可能不同"。折扣率分析以渠道内比较为主，跨渠道排名仅作参考。

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
1. 遍历上述 sheet，读取全部行（包含 Cancelled 和 Delivered，各有用处）
2. 统一列名（各表结构一致，但需确认所有列名完全相同）
3. 筛选数据（按 Mode 分流）：
   - `Mode == 'Delivered'` 的订单 → 用于核心利润分析
   - `Mode == 'Cancelled'` 的订单 → 用于取消罚款分析
   - `Mode == 'Return'` 的订单（若存在）→ 单独统计退货损失，排除出利润分析
4. 转换类型：`Order Date` → datetime，`Net Amount`/`TP`/费用列 → float
5. Delivered 订单剔除 TP 或 Net Amount 为 NaN/0 的行

### 2.2 质量检查 + 利润公式验证（⚠️ 关键节点）

每张渠道表检查：
- 行数、缺失率、负值合理性
- TP 与 Net Amount 的比例范围
- 日期范围
- 异常值标记（如 Net Amount < TP 的严重亏损订单）

**Deduction 符号约定检查**（所有渠道一致则通过）：
```python
# 核心检查：Payment 是否始终等于 Net Amount + Deduction
# 若 Deduction 在某些渠道为正、另一些为负，但 Payment == Net Amount + Deduction 仍成立，
# 说明 Deduction 的符号约定不影响计算结果，但中间处理时须统一符号方向
deduction_consistency = check_sign_convention(df, deduction_sign='negative')
# 输出每渠道 Deduction 正负比例，确认全数据集符号一致
# 若符号方向不统一，在展开式计算中统一取绝对值
```

**Payment 合理性筛查**：
```python
# 检查是否存在异常 Payment 值
# (1) Net Amount > 0 但 Payment = 0 的订单 → 可能为未结算订单，标记可疑
# (2) Payment 为大幅负数但 Mode = Delivered → 可能为退款订单误标记
# (3) 各渠道 Payment 最小值、最大值、负值占比
# 输出可疑订单清单，供人工审查
```

**利润公式验证**（每张渠道表单独输出）：
```python
# 候选公式对比
method_payment = Payment - TP                    # 采用
method_portal  = Portal_Payment - TP             # 不采用（批次变量）

# 验证：同一 Net Amount 下 Portal Payment 的离散度
# 若 Net Amount = 849 的订单有 20+ 种不同的 Portal Payment => 批次变量确认
print(f'Payment-TP mean={mp.mean():.2f}, Portal-TP mean={mpt.mean():.2f}')
print(f'Payment-TP 更稳定，是正确利润基准')
```

**验证通过标准**：`Payment - TP` 的方差显著小于 `Portal Payment - TP`，且 Payment 与 Net Amount - Deduction 完全吻合。

### 2.3 取消订单成本分析

对每个渠道的 Cancelled 订单：

```python
# 取消罚款 = Portal Payment（取消订单无收入，此值为负数平台罚款）
cancelled_penalty = cancelled['Portal Payment'].sum()
cancelled_rate = len(cancelled) / (len(delivered) + len(cancelled))
```

输出：各渠道取消率、罚款总额、平均每单罚款。

> 取消罚款**不作为**调整项加到 Delivered 订单利润上，而是作为渠道运营效率指标独立列示在最终摘要表中。详见约束3所述。

### 2.4 合并数据集

12 个渠道表纵向合并，新增 `channel` 列标识来源。保存两个版本：
- `data/processed/delivered_orders.csv` — Delivered 订单（核心分析用）
- `data/processed/cancelled_orders.csv` — Cancelled 订单（罚款分析用）

---

## 三、阶段二：特征工程

### 3.1 贡献毛利计算（⚠️ 见关键逻辑约束 1 & 2）

```python
# Payment 本身已等于 Net Amount + Deduction（各平台费用之和的相反数）
# 所以 Payment = Net Amount - GST - |Commission| - |Shipping| - |Other| - |TCS| - |TDS|
contribution_margin = Payment - TP
```

验证等价性：
```python
# 这两个必须一致
assert abs(Payment - (Net Amount + Deduction)) < 0.01
# 手动计算验证
manual = (Net Amount - GST - abs(Commission_Charges) - abs(Shipping_Charges) 
          - abs(Other_Charges) - abs(T.C.S.) - abs(T.D.S.))
assert abs(Payment - manual) < 0.01
```

同时计算：
- `margin_rate = contribution_margin / Net Amount` 其中 Net Amount 须为正数；若 Net Amount ≤ 0，该条记录的 margin_rate 置为 NaN 并在报告中计数
- **注意**：取消罚款已在约束3中改为渠道级独立指标，不做逐单分摊，因此不计算 `adjusted_margin`

### 3.2 衍生特征

| 特征 | 计算方式 |
|------|---------|
| 折扣率 | 已有 `Dis.%` |
| 平台费率 | `(abs(Commission) + abs(Shipping) + abs(Other)) / Net Amount` |
| TP 比例 | `TP / Net Amount`（成本占收入比重） |
| 是否有促销折扣 | `Dis.% > 0` |
| 渠道类型 | B2C vs B2B（从渠道名推断） |

### 3.3 Catalog 关联 + 跨渠道产品重叠分析

**Catalog 关联**：将 Catalog 中的 `Category`、`Weight`、`TP1/TP2`、各渠道 MRP 关联到订单数据。
关键路径：P&L 渠道表中的 SKU 格式为 `Os211_3011_3XL`，Catalog 的 SKU 格式为 `Os211_3011_3XL` — 经检查部分 SKU 格式一致。但 Catalog 共有 SKU 1,330 条，需确认实际匹配率。

**跨渠道产品重叠分析**（关联前须确认此步可行性）：
- 同一 SKU 是否出现在多个渠道的 Delivered 订单中？
- 若是，对比该 SKU 在各渠道的贡献毛利、毛利率、折扣率 → 这是控制产品变量后最干净的渠道对比
- 若否（各渠道 SKU 无交集），则在 4P-Product 和 4P-Place 交叉分析结论中注明"不同渠道销售的产品结构不同，渠道利润差异可能主要来自产品组合差异而非渠道效率差异"

> 关键逻辑：如果 Myntra 卖的是 Kurta 而 Amazon 卖的是 Tops，那么"Myntra 渠道利润更高"可能是产品选择的结果而非渠道运营效率的结果。此处的产品重叠分析是区分这两个解释的关键。

---

## 四、阶段三：渠道利润对比分析（4P-Place）

### 4.1 单变量统计

各渠道维度：
- 订单量、平均贡献毛利、毛利率中位数、贡献毛利分布（直方图）
- 亏损订单占比、亏损深度（平均亏损额）
- 净收入（Net Amount）、成本（TP）、费用结构各自占比

### 4.2 渠道费用结构拆解

堆叠柱状图：每渠道的 Net Amount 被拆分为：
```
TP（成本） + GST（税金） + Commission（佣金）
+ Shipping（运费） + Other（其他费用） + 贡献毛利（Payment - TP）
```

注意：图中标注为"贡献毛利"而非"利润"，图注中说明不含固定成本。

### 4.3 亏损订单的渠道分布

哪些渠道亏损率最高？亏损原因是什么（成本过高 vs 费用过高）？

---

## 五、阶段四：产品维度分析（4P-Product）

### 5.1 品类分析

按 `Category` 分组统计：Kurta、Kurta Set、Tops、Gown 各自的：
- 平均贡献毛利、毛利率、订单量
- 各渠道内的品类表现差异
- 亏损率

### 5.2 TP 成本分析

TP（贸易价格）与 Net Amount（售价）的关系：
- 成本加成率分布 `(Net Amount - TP) / TP`
- 不同渠道的成本加成策略差异
- TP 与重量、品类的相关性

⚠️ TP 是贸易价格，不等同于完全成本（见约束 4），此处分析的"成本占比"基线可能存在系统性低估。

---

## 六、阶段五：价格策略分析（4P-Price）

### 6.1 折扣与贡献毛利

- 折扣率 `Dis.%` 与毛利率的关系（是否存在倒挂）
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

## 七b、时间维度分析（补充分析）

尽管数据仅覆盖 2020.08–2021.03，仍应做以下时间维度检查以评估数据稳定性：

### 7b.1 月度订单分布
- 各渠道 Delivered 订单的月度数量分布（确认是否均匀分布，排除80%订单集中在某一个月的情况）
- 若分布严重不均，说明样本的代表性进一步受限

### 7b.2 月度毛利率走势
- 各渠道贡献毛利率的月度趋势折线图
- 观察是否存在单月异常波动（如某月集中出现大量亏损订单）

### 7b.3 时间切片的敏感性测试
- 将数据按时间三等分（早/中/晚期），分别计算各渠道的平均毛利率
- 若三期结果差异显著，说明分析结果对时间窗口敏感，结论可靠性降低

> 时间分析的目的是**验证而非扩展**：这8个月的数据是否内部稳定？如果仅3个月就贡献了全部利润，则整体均值有严重误导性。

---

## 八、阶段七：局限性声明与结论框架

### 8.1 必须明确的局限性

| 局限性 | 影响 |
|--------|------|
| **分析的实为贡献毛利，不是净利润** | 不含固定成本，数值偏高。不可与财务报表的"净利润"直接对比 |
| **TP 可能不完全等于 COGS** | TP 是贸易价格，不含仓储、包装等间接变动成本，贡献毛利可能被高估 |
| **Portal Payment 是批次变量，非现金结算** | 不能用于逐笔利润计算。已验证 Payment-TP 是正确基准 |
| **取消订单有罚款成本** | 已单独统计列示为渠道级运营损失，但无法确定是否有其他未列出的隐性成本 |
| 时间跨度仅 2020.08–2021.03，含 COVID-19 高峰期和排灯节 | 无法分析季节性、年同比趋势，且此期间电商行为可能偏离正常水平，不可外推 |
| 样本量 1,393 条 | 统计显著性受限，跨渠道统计检验不可靠 |
| 渠道严重不平衡 (Myntra 53%) | 汇总统计丧失意义（不作发布），小渠道结论不可泛化 |
| **数据集未包含退货（Return）记录** | 退货退款损失+退货物流成本未被计入，贡献毛利可能被系统性高估 |
| **Dis.% 跨渠道口径可能不一致** | 各平台计算折扣率规则可能不同，跨渠道折扣率对比存在误导风险 |
| 无广告/流量/转化率数据 | 4P 中 Promotion 分析不完整 |
| Catalog 匹配率可能低 | Product 维度粒度受限 |

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
- **"渠道 A 优于渠道 B"**（样本不平衡、产品结构可能不同、时间窗口受限，无法做因果推断）
- **"取消罚款应该被分摊到 Delivered 订单"**（取消罚款是渠道运营层面的风险成本，分摊到每个 Delivered 订单不改变任何结构信息，详见约束3）
- **"改善 X 能提高利润 YY 元"**（无增量分析数据支撑，无法建立因果关系）

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
   [验证门：Payment-TP vs Portal Payment-TP 对比表]
   [确认 Payment 公式等价于 Net Amount + Deduction]
   [若验证失败 → 停止，排查数据问题]
       ↓
02_feature_engineering.py  (依赖 01 输出)
       ↓
03_channel_analysis.py  ──┐
04_product_analysis.py   ──┤  (均依赖 02 输出，可并行)
05_price_analysis.py     ──┘
       ↓
06_summary.py  (依赖 03-05 的全部或部分输出)
```

### 验证门说明

01 输出必须包含以下诊断报告：
1. 每渠道 `Payment - TP` vs `Portal Payment - TP` 均值对比表
2. 每渠道取消率 + 取消罚款总额
3. 利润公式等价性验证（Payment == Net Amount + Deduction 的吻合率 + Deduction 符号一致性检查）
4. 样本不平衡警示（如果某渠道 n < 10，自动标记；若 Myntra 占比 > 50%，禁止发布汇总统计量）
5. Payment 合理性筛查结果（异常 Payment 订单清单 + 各渠道 Payment 可信度评级）

03/04/05 阶段开始前，先审查此报告，确认利润基准成立后再继续。
