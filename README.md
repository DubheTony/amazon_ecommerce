# Amazon 电商多渠道损益分析

对 Kaggle 数据集作者 **anilsharma87** 发布的电商销售数据做的分析，落点是多渠道的利润拆解。

这个项目同时也在复盘早先一版「随机森林预测利润」的方案为什么走不通——那版模型的特征里
包含了与利润同时发生的财务变量，属于拿结果解释结果。本方案改用描述性统计和分组对比，
结论见演示页第十节。

## 口径与边界（先看这里，不然容易误读）

- **文中所有「利润」都指贡献毛利，不是净利润。** 贡献毛利只扣了平台侧的费用，
  没有扣固定成本（仓库、人员、软件）、退货损失、广告费、仓储费、包装材料费、平台月费、
  支付网关手续费。**不能拿它对标净利润。**
- **计算公式**：`Payment = Net_Amount + Commission + Shipping + Other + TCS + TDS`，
  `贡献毛利 = Payment − TP`。GST 不在扣费项里——`Net_Amount` 已含 GST。
  这个式子在全部 1,392 条订单上吻合。
- **样本严重不平衡**：Myntra 占 53.0%，另有 4 个渠道样本量不足 10 条。
  因此全部分析只在分渠道层面做，**不出全局汇总统计量**。
- **只能做事后拆解，不能做事前预测。** 数据里没有「上架前可知」的变量
  （品类、目标渠道、计划定价等），所以利润没法在结果出来之前算出来。
- 数据覆盖 COVID-19 和排灯节，**不可外推**。

## 数据准备（跑脚本前必看）

原始 xlsx 共约 130MB，**没有放进本仓库**。请先把这 7 个文件放到 `anilsharma87-sales/` 目录下：

```text
anilsharma87-sales/
├── P & L March 2021.xlsx              # 核心：12 个渠道的损益表
├── Amazon Sale Report.xlsx
├── May-2022.xlsx
├── Sale Report.xlsx
├── International sale Report.xlsx
├── Cloud Warehouse Compersion Chart.xlsx
└── Expense IIGF.xlsx
```

其余几个文件缺成本数据、也无法关联到产品主数据，做不了利润分析，只有 `P & L March 2021.xlsx`
用得上。`scripts/` 里的脚本读的正是这一个文件。

`input/` 下的 CSV 是早期从这些 xlsx 导出的产物，公式引用大量断裂（`#REF!`），已被 xlsx 取代，
同样不在仓库里。

## 目录结构

```text
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
├── 利润导向电商分析_演示.html    # 分析汇报（15 页，浏览器直接打开）
├── 汇报主线思维导图.html        # 汇报提纲与思维导图
├── gen_html.py                # 把 output/ 下的图表和结论合成上面那份演示页
├── 1.ipynb                    # 旧版 Jupyter（含错误：Cost_Price=0）
├── random_forest_no_log.py    # 旧版随机森林脚本（依赖 notebook 变量，不可独立运行）
├── requirements.txt
└── 介绍.txt                   # 数据集说明
```

## 重新生成演示页

`scripts/` 跑完会在 `output/` 下生成图表（该目录不进版本控制），然后：

```bash
python gen_html.py
```

它把 `output/` 下的 4 张图和结论合成演示页，写回 `output/利润导向电商分析_演示.html`。
仓库根目录那份是同一份内容的成品拷贝，方便点开就看——所以演示页末尾写的「见 output/ 目录」
指的是脚本产物目录，clone 下来时是空的，跑完脚本才有。

## 主要结论

- Amazon 最稳：亏损率 0.5%，贡献毛利率 20.9%，202 单里只有 1 单亏损
- Myntra 量最大也最亏：占 53% 的订单，亏损率 17.1%，主因是平台费用（佣金+运费）而非产品成本
- 98% 的亏损是费用造成的，只有 2% 源于成本倒挂（TP > Net_Amount）
- 同款商品换个渠道卖，利润能差 100~200 INR，差异主要来自渠道费用结构
- 折扣超过 60% 后亏损率跳到 49.8%，超过 70% 达 78.9%；当前数据里没看到「以量补价」的效果

## 分析起点

见 `research_plan/channel_profit_analysis_plan.md`
