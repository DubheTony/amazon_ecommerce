import base64
import os

# 本脚本在项目根目录，图表由 scripts/ 生成到 output/ 下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, 'output')


def b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


fee = b64(os.path.join(OUT_DIR, 'fee_structure.png'))
disc_dist = b64(os.path.join(OUT_DIR, 'discount_distribution.png'))
disc_vs = b64(os.path.join(OUT_DIR, 'discount_vs_margin.png'))
monthly = b64(os.path.join(OUT_DIR, 'monthly_margin_trend.png'))

html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>利润导向电商销售分析</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "SimHei", "Noto Sans SC", sans-serif; background: #f0f0f0; color: #222; }

.slide {
    display: none; width: 1024px; max-width: 100vw; min-height: 100vh;
    background: #fff; padding: 52px 68px;
    margin: 0 auto; position: relative;
}

.slide.active { display: block; }

/* Typography */
h1 { font-size: 40px; font-weight: 700; margin-bottom: 24px; line-height: 1.3; }
h2 { font-size: 28px; font-weight: 700; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #222; line-height: 1.4; }
h3 { font-size: 20px; font-weight: 600; margin: 24px 0 10px; line-height: 1.5; }
h4 { font-size: 17px; font-weight: 600; margin: 14px 0 8px; }
p { font-size: 16px; line-height: 2.0; margin-bottom: 10px; }
ul, ol { padding-left: 22px; margin-bottom: 12px; }
li { font-size: 16px; line-height: 1.9; margin-bottom: 6px; }

/* Tables */
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }
th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: center; }
th { background: #f5f5f5; font-weight: 600; }
td { background: #fff; }
tr:nth-child(even) td { background: #fafafa; }

/* Code blocks */
pre { background: #f8f8f8; padding: 12px 18px; border-left: 4px solid #666; font-size: 14px; line-height: 1.7; overflow-x: auto; margin: 12px 0; }

/* Images */
img { max-width: 92%; height: auto; display: block; margin: 16px auto; border: 1px solid #ddd; border-radius: 3px; }

/* Navigation */
.nav {
    position: fixed; bottom: 0; left: 0; right: 0; height: 52px;
    background: #fff; border-top: 1px solid #ddd;
    display: flex; align-items: center; justify-content: center; gap: 24px;
    font-size: 15px; z-index: 100;
}
.nav button {
    background: #444; color: #fff; border: none; padding: 8px 32px;
    cursor: pointer; font-size: 15px; border-radius: 3px;
}
.nav button:hover { background: #666; }
.nav button:disabled { background: #ccc; cursor: default; }
.page-num { color: #888; min-width: 80px; text-align: center; }

/* Title slide */
.title-slide {
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    text-align: center; min-height: 100vh;
}
.title-slide h1 { font-size: 46px; margin-bottom: 24px; }
.title-slide p { font-size: 19px; color: #555; margin-bottom: 6px; }
.subtitle { color: #999; font-size: 15px; margin-top: 36px; }

/* Layout helpers */
.col2 { display: flex; gap: 36px; margin: 10px 0; }
.col2 > div { flex: 1; min-width: 0; }

/* Callout boxes */
.callout { background: #f8f8f6; padding: 14px 20px; margin: 16px 0; border-radius: 2px; font-size: 15px; line-height: 1.8; }

@media (max-width: 768px) {
    .slide { padding: 24px 20px; }
    h1 { font-size: 28px; }
    h2 { font-size: 22px; }
    h3 { font-size: 17px; }
    .col2 { flex-direction: column; gap: 20px; }
    table { font-size: 12px; }
    th, td { padding: 5px 6px; }
}
</style>
</head>
<body>
'''

slides = []

# ─── Slide 1: Title ───
slides.append('''<div class="slide active" id="s0">
<div class="title-slide">
<h1>基于 Python 语言的<br>利润导向电商销售分析</h1>
<p>多渠道损益拆解 · 费用结构对比 · 折扣策略评估</p>
<p style="font-size:14px; color:#aaa; margin-top:40px;">对原随机森林预测方案的方法论批判与替代分析</p>
<p class="subtitle">小组成员：A · B · C</p>
</div>
</div>''')

# ─── Slide 2: 4P 为何不能用于利润预测 ───
slides.append('''<div class="slide" id="s1">
<h2>一、4P 为何不能用于利润预测</h2>
<p>原方案以 4P（产品、价格、渠道、促销）作为特征框架建立利润预测模型。这一方向存在根本性问题：4P 是一个营销管理分类框架，描述的是"企业可控的营销要素有哪些"，而非"利润由哪些变量因果决定"。将 4P 直接用作机器学习特征，相当于把超市的货架分类标签（饮料、零食、日化）当作销售额的预测因子——分类正确但因果无关。</p>
<h3>三个具体问题</h3>
<ul>
<li><b>内部高度相关</b>：价格影响促销力度，渠道选择影响最终售价，品类决定定价区间。4P 各维度互相缠绕，不具备作为独立特征输入的基本条件。</li>
<li><b>循环论证</b>：原方案将 Net_Amount 标注为 Price 特征。贡献毛利本就等于 Net_Amount 减去各项费用。用 Net_Amount 预测贡献毛利必然高度相关，特征重要性 81.5% 是一句"正确的废话"。</li>
<li><b>事后 ≠ 事前</b>：真正有意义的利润预测需要的是上架前可知的信息——产品参数、目标渠道、计划定价。本数据集恰好不具备这类前瞻性变量。</li>
</ul>
</div>''')

# ─── Slide 3: ML 为什么不妥 ───
slides.append('''<div class="slide" id="s2">
<h2>一（续）· 机器学习为何不适用</h2>
<h3>目标泄漏</h3>
<p>Net_Amount 本身就是贡献毛利的组成部分（贡献毛利 = Net_Amount &minus; 费用 &minus; TP）。用 Net_Amount 预测贡献毛利，数学上等价，没有信息增益。特征重要性排名中 Net_Amount 占 81.5% 不是模型发现的规律，是会计恒等式的必然结果。</p>
<h3>输入输出颠倒</h3>
<p>模型使用的 Payment、Commission、Shipping 等变量与利润同时发生。真正预测应当使用品类、目标渠道、计划定价等事前可获特征。本数据集缺失这类变量，利润分析只能做描述性拆解而非预测。</p>
<h3>样本不适合</h3>
<p>1,392 条订单中 Myntra 占 53%，4 个渠道不足 10 条。RMSE=0.01474 看似精度极高，实因目标信息已藏在 Net_Amount 中——这是数据构造性关系，不是模型的学习能力。</p>
<h3>时间不成立</h3>
<p>有效月份仅 5 个月（2020.11&sim;2021.03），"年""天"列为常量。在如此短的时间跨度内，任何"预测"本质上都是对历史均值的拟合。季节性、趋势性等时间效应无法识别。</p>
</div>''')

# ─── Slide 4: 数据集 + 输入输出 + 数据约束 ───
slides.append('''<div class="slide" id="s3">
<h2>一（续）· 数据集与输入输出</h2>
<h3>数据集概要</h3>
<p>Kaggle 平台 ANil 整理的电子商务销售数据集，时间跨度 2020.08&sim;2021.03。核心分析文件 P&amp;L March 2021.xlsx 含 12 个渠道损益表，最终分析使用 1,392 条 Delivered 订单（含 Net_Amount、TP、Commission、Shipping、GST、Other、TCS、TDS 等字段）。其余数据文件因缺乏成本数据或无法关联产品主数据，不可用于利润分析。</p>
<div class="col2">
<div>
<h4>输入（每笔订单已知信息）</h4>
<ul>
<li>产品标识：SKU、Style、Category、尺寸、重量</li>
<li>销售渠道：12 个渠道之一</li>
<li>金额：Net_Amount、MRP、Discount_Pct</li>
<li>成本：TP（贸易价格）</li>
<li>费用：Commission、Shipping、GST、Other、TCS、TDS</li>
</ul>
</div>
<div>
<h4>输出（分析结论）</h4>
<ul>
<li>贡献毛利 = Payment &minus; TP</li>
<li>毛利率 = 贡献毛利 / Net_Amount</li>
<li>各渠道费用结构拆解与亏损率</li>
<li>品类盈利表现</li>
<li>折扣力度对利润的影响曲线</li>
</ul>
</div>
</div>
<h3>数据约束</h3>
<div class="col2">
<div>
<table>
<tr><th>约束项</th><th>说明</th></tr>
<tr><td>样本量</td><td>1,392 条，来自 12 个渠道</td></tr>
<tr><td>渠道不平衡</td><td>Myntra 占 53%；4 个渠道 n &lt; 10</td></tr>
<tr><td>Portal_Payment</td><td>批次变量，同 Net_Amount 最多 27 种值</td></tr>
<tr><td>Mirraw B2B</td><td>取消订单 Portal_Payment 为正值（均 27.67）</td></tr>
</table>
</div>
<div>
<table>
<tr><th>约束项</th><th>说明</th></tr>
<tr><td>Meesho 异常</td><td>折扣率 &minus;13.04%，可能为加价</td></tr>
<tr><td>时间限制</td><td>含 COVID-19 + 排灯节，不可外推</td></tr>
<tr><td>利润口径</td><td>贡献毛利（非净利润）</td></tr>
<tr><td>可用性</td><td>事后利润拆解，不能做事前预测</td></tr>
</table>
</div>
</div>
</div>''')

# ─── Slide 5: 研究目标 + 数据预处理 ───
slides.append('''<div class="slide" id="s4">
<h2>二、研究目标</h2>
<div class="col2">
<div>
<h4>目标一：利润拆解</h4>
<p>从 Net_Amount 出发，逐项扣除成本与费用，展示各渠道的"收入→利润"转化链条。回答：钱被谁赚走了——平台还是卖家？</p>
<h4>目标二：渠道间盈利比较</h4>
<p>控制产品变量（相同 SKU 跨渠道），比较各渠道贡献毛利水平与费用结构。回答：同一件商品在哪个渠道卖最赚钱？</p>
</div>
<div>
<h4>目标三：亏损诊断</h4>
<p>区分亏损原因是成本过高（TP &gt; Net_Amount）还是费用过高（平台扣费吞噬全部利润）。</p>
<h4>目标四：折扣效果评估</h4>
<p>量化折扣对利润的侵蚀程度，找出"亏本赚吆喝"的折扣临界点。</p>
</div>
</div>
<h2 style="margin-top:28px">三、数据预处理</h2>
<h3>数据分流</h3>
<table>
<tr><th>类别</th><th>数量</th><th>用途</th></tr>
<tr><td>Delivered</td><td>1,392</td><td>核心利润分析</td></tr>
<tr><td>Cancelled</td><td>363</td><td>取消罚款统计（渠道级独立列示，不分摊）</td></tr>
<tr><td>Returned</td><td>283</td><td>退货统计（退款总额约 &minus;272,116 INR，不含退货物流成本）</td></tr>
</table>
<h3>已知数据问题</h3>
<ul>
<li>Peachmode FB B2C（7 行）和 Mirraw B2B（11 行 Cancelled）Order_Date 为 datetime.time(0,0)，已转为 NaT</li>
<li>Meesho 5 条 Delivered 中有 1 条 TP=0 被剔除，实际可用 4 条</li>
<li>Mirraw B2B 取消订单 Portal_Payment 正值原因未明，不作强行修正</li>
<li>原 ML 方案的 One-hot / 频率编码在此不适用——本分析以描述性统计和分组对比为主</li>
</ul>
</div>''')

# ─── Slide 6: 利润公式验证 + 各渠道数据 ───
slides.append('''<div class="slide" id="s5">
<h2>四、利润公式验证与关键定义</h2>
<p>规划文档曾给出一版包含 GST 的展开式，经实际数据验证有误。GST <b>不在</b> Deduction（扣费合计）中——Net_Amount 已含 GST，卖方另行向政府申报。</p>
<pre>Payment = Net_Amount + Commission + Shipping + Other + TCS + TDS
贡献毛利 = Payment &minus; TP</pre>
<p>其中 Commission 至 TDS 均为<b>负值</b>（平台扣费）。该公式在全部 1,392 条订单上吻合率 100%。</p>
<div class="callout">原 ML 模型同时使用 Net_Amount 作为特征预测贡献毛利。由于贡献毛利 = Net_Amount &minus; 费用 &minus; TP，用 Net_Amount 预测贡献毛利必然高度相关（特征重要性 81.5%）。这不是 ML 发现的规律，是会计恒等式。</div>
<h3>贡献毛利的限定</h3>
<p>以下项目未被扣除：固定成本（仓库、人员、软件）、退货损失、广告费、仓储费、包装材料费、平台月费、支付网关手续费。因此所有"利润"指贡献毛利，不可对标净利润。</p>
<h2 style="margin-top:28px">四（续）· 各渠道关键数据</h2>
<table>
<tr><th>渠道</th><th>n</th><th>占比</th><th>平均贡献毛利</th><th>平均 Net</th><th>平均 TP</th><th>亏损率</th></tr>
<tr><td>Myntra</td><td>738</td><td>53.0%</td><td>106.83</td><td>879.25</td><td>409.34</td><td style="color:#c33">17.1%</td></tr>
<tr><td>Flipkart</td><td>223</td><td>16.0%</td><td>172.36</td><td>830.21</td><td>415.47</td><td>6.3%</td></tr>
<tr><td>Amazon</td><td>202</td><td>14.5%</td><td>177.65</td><td>850.18</td><td>371.25</td><td>0.5%</td></tr>
<tr><td>Peachmode FB B2C</td><td>78</td><td>5.6%</td><td>186.56</td><td>1199.19</td><td>425.20</td><td>3.9%</td></tr>
<tr><td>Amazon FBA</td><td>64</td><td>4.6%</td><td>170.21</td><td>797.53</td><td>355.72</td><td>6.3%</td></tr>
<tr><td>Peachmode Os B2C</td><td>32</td><td>2.3%</td><td>147.52</td><td>1034.84</td><td>380.19</td><td>0.0%</td></tr>
<tr><td>Mirraw B2B</td><td>24</td><td>1.7%</td><td>92.01</td><td>418.21</td><td>318.23</td><td>0.0%</td></tr>
<tr><td>Mirraw B2C</td><td>17</td><td>1.2%</td><td>352.50</td><td>868.82</td><td>376.94</td><td>0.0%</td></tr>
</table>
<div class="callout">Myntra 占比 53.0%，禁止发布全局汇总统计量。所有分析在分渠道层面进行。</div>
</div>''')

# ─── Slide 7: 相关性分析 + SKU 重叠 ───
slides.append('''<div class="slide" id="s6">
<h2>五、核心变量相关性分析</h2>
<div class="col2">
<div>
<h3>贡献毛利与各变量 Pearson 相关系数</h3>
<ul>
<li><b>Net_Amount</b>：r &asymp; 0.45——中等正相关。但高 Net_Amount 订单往往也是高 TP，毛利绝对值高而毛利率未必高。</li>
<li><b>Discount_Pct</b>：r &asymp; &minus;0.32——弱负相关。折扣超 70% 后亏损率急剧攀升。</li>
<li><b>Fee_Rate</b>（平台费率）：r &asymp; &minus;0.28——弱负相关。在渠道对比层面此关系更显著。</li>
<li><b>TP_Ratio</b>（成本占比）与 Margin_Rate：<b>r &asymp; &minus;0.55</b>——强负相关，是利润最直接的侵蚀因素。</li>
</ul>
</div>
<div>
<h3>跨渠道 SKU 重叠分析</h3>
<p>共 <b>103</b> 个 SKU 出现在多个渠道（涉及 962 单，占总订单 69.1%）。这一数据基础使我们能在控制产品变量的前提下直接比较渠道效率。</p>
<p><b>示例：SKU = Os103_4171_L</b></p>
<table>
<tr><th>渠道</th><th>n</th><th>平均贡献毛利</th><th>平均折扣率</th></tr>
<tr><td>Amazon</td><td>5</td><td>175.06</td><td>55.4%</td></tr>
<tr><td>Flipkart</td><td>9</td><td>185.27</td><td>58.5%</td></tr>
<tr><td>Myntra</td><td>27</td><td>137.62</td><td>54.5%</td></tr>
<tr><td>Peachmode FB B2C</td><td>11</td><td>159.13</td><td>44.6%</td></tr>
</table>
<p>同一产品在不同渠道的利润差异可达 50&sim;180 INR，且渠道排名与折扣率不完全对应。利润差异主因是渠道费用结构（佣金率、运费标准），而非产品本身。</p>
<div class="callout" style="font-size:14px">原 ML 方案做"统一利润预测"不可靠——利润高度依赖渠道特定的费用结构，而这些费用在事前不可知。</div>
</div>
</div>
</div>''')

# ─── Slide 8: 渠道费用结构（含图） ───
slides.append(f'''<div class="slide" id="s7">
<h2>六、渠道费用结构拆解</h2>
<p>将每笔订单的 Net_Amount 拆解为 TP（成本）、GST（税金）、Commission（佣金）、Shipping（运费）、Other（其他费用）、TCS/TDS（预扣税）和剩余贡献毛利。堆叠柱状图直观展示各渠道的"收入去哪了"。</p>
<img src="data:image/png;base64,{fee}" alt="各渠道费用结构堆叠图">

<div class="col2">
<div>
<h4>Myntra（n=738，亏损率 17.1%）</h4>
<p>Net_Amount=879 → 成本 TP=409（46.5%）+ 佣金=&minus;148（16.8%）+ 运费=&minus;66（7.5%）+ 其他=&minus;29（3.3%）→ <b>贡献毛利=107（12.2%）</b></p>
</div>
<div>
<h4>Amazon（n=202，亏损率 0.5%）</h4>
<p>Net_Amount=850 → 成本 TP=371（43.6%）+ 佣金=&minus;165（19.4%）+ 运费=&minus;81（9.5%）+ 其他=&minus;33（3.9%）→ <b>贡献毛利=178（20.9%）</b></p>
</div>
</div>
<p>核心发现：Myntra 毛利率（12.2%）远低于 Amazon（20.9%）。主因并非佣金率差异（Myntra 16.8% vs Amazon 19.4%），而是 Myntra 的运费占比（7.5%）和 TP 占比（46.5%）相对更高，叠加亏损订单集中。</p>
</div>''')

# ─── Slide 9: 亏损诊断 + 品类分析 ───
slides.append('''<div class="slide" id="s8">
<h2>六（续）· 亏损诊断与品类分析</h2>
<div class="col2">
<div>
<h3>亏损订单诊断</h3>
<p>总亏损订单 <b>148 单</b>（占 10.6%），其中 <b>126 单集中在 Myntra</b>。</p>
<table>
<tr><th>亏损原因</th><th>占比</th></tr>
<tr><td>费用过高（Net_Amount &gt; TP 但扣费后为负）</td><td style="color:#c33"><b>98.0%</b></td></tr>
<tr><td>成本倒挂（TP &gt; Net_Amount）</td><td><b>2.0%</b></td></tr>
</table>
<p>亏损的核心问题是平台费用吞噬利润空间。以 Myntra 为例，平均每单佣金加运费合计约 214 INR，当 Net_Amount 较低或折扣较高时，这笔费用足以将利润压为负值。</p>
</div>
<div>
<h3>品类盈亏分析</h3>
<table>
<tr><th>品类</th><th>n</th><th>平均贡献毛利</th><th>毛利率</th><th>亏损率</th></tr>
<tr><td>Kurta</td><td>1,072</td><td>138.26</td><td>15%</td><td>7.7%</td></tr>
<tr><td>Kurta Set</td><td>219</td><td>145.95</td><td>10%</td><td style="color:#c33"><b>27.9%</b></td></tr>
<tr><td>Tops</td><td>87</td><td>134.89</td><td>17%</td><td>0.0%</td></tr>
</table>
<p>Kurta Set 亏损率（27.9%）远超其他品类。主因是平均 TP（598）远高于 Kurta（363），而售价差异不足以覆盖成本差距——Kurta 平均 Net=818，Kurta Set 平均 Net=1,172，Net 增幅（43%）远不及 TP 增幅（65%）。Tops 在全部 87 单中未出现亏损，毛利率 17% 为三大品类最高。</p>
</div>
</div>
</div>''')

# ─── Slide 10: 折扣区间分析（含分布图） ───
slides.append(f'''<div class="slide" id="s9">
<h2>七、折扣策略与利润</h2>
<h3>折扣区间 vs 亏损率</h3>
<div class="col2">
<div>
<table>
<tr><th>折扣区间</th><th>n</th><th>平均贡献毛利</th><th>亏损率</th></tr>
<tr><td>0&ndash;20%</td><td>5</td><td>379.73</td><td>0.0%</td></tr>
<tr><td>20&ndash;40%</td><td>77</td><td>253.83</td><td>2.6%</td></tr>
<tr><td>40&ndash;60%</td><td>1,029</td><td>157.53</td><td>1.5%</td></tr>
<tr><td>60&ndash;80%</td><td>253</td><td>31.43</td><td style="color:#c33"><b>49.8%</b></td></tr>
<tr><td>80&ndash;100%</td><td>23</td><td>44.60</td><td>21.7%</td></tr>
</table>
<p>40&ndash;60% 是最常见区间（1,029 单），亏损率仅 1.5%。超过 60% 后亏损率跃至 49.8%，超过 70% 则达 78.9%。各渠道中 Mirraw B2B（76.4%）、Limeroad（62.3%）、Flipkart（59.7%）折扣力度最高。</p>
</div>
<div>
<img src="data:image/png;base64,{disc_dist}" alt="折扣区间分布" style="margin:8px auto;">
</div>
</div>
</div>''')

# ─── Slide 11: 折扣与利润散点图 ───
slides.append(f'''<div class="slide" id="s10">
<h2>七（续）· 折扣与利润的权衡</h2>
<div class="col2">
<div>
<img src="data:image/png;base64,{disc_vs}" alt="折扣 vs 毛利散点图" style="margin:8px auto;">
</div>
<div>
<h3>同渠道内部分析</h3>
<p>在所有样本量充足的渠道中，高折扣订单的贡献毛利均显著低于低折扣订单。</p>
<p>以 Myntra 为例：高折扣组（387 单）平均毛利 55.71，低折扣组（351 单）平均毛利 163.19——差距近 3 倍。Amazon 两组差距也在 2 倍以上。</p>
<h3>数据局限</h3>
<p>当前数据中没有体现"以量补价"效果——折扣组的平均利润显著更低。但这可能是因为数据集未捕捉"不打折就卖不掉"的情况。缺少销量弹性数据（折扣能换取多少额外销量）是本分析的根本局限，不是建模能弥补的。</p>
</div>
</div>
</div>''')

# ─── Slide 12: 时间稳定性（含图）+ ML 对比 ───
slides.append(f'''<div class="slide" id="s11">
<h2>八、分析结果稳健性检验</h2>
<div class="col2">
<div>
<h3>时间切分敏感性测试</h3>
<p>将数据按日期排序后三等分：</p>
<ul>
<li>早期（2020.11&sim;2021.02 中）：122.25（数据量少，含低毛利渠道 Mirraw B2B）</li>
<li>中期（2021.02）：148.91</li>
<li>晚期（2021.03）：146.44</li>
</ul>
<p>三期极差 26.66，中期与晚期接近。早期偏低主因是 2020.11&sim;2021.01 仅 32 单且 Mirraw B2B 集中。整体敏感性在合理范围。</p>
<h3>渠道利润稳定性</h3>
<p>样本量 &ge; 64 的 6 个主要渠道，月度均值走势无异常波动。Myntra 在 2 月（381 单）与 3 月（350 单）的亏损率接近，说明亏损非单月偶发。</p>
</div>
<div>
<img src="data:image/png;base64,{monthly}" alt="月度毛利走势">
<h3 style="margin-top:12px">与原 ML 方案的对比</h3>
<table style="font-size:13px">
<tr><th>维度</th><th>原 ML 方案</th><th>本方案</th></tr>
<tr><td>目标</td><td>预测利润数值</td><td>拆解利润从哪来</td></tr>
<tr><td>输入</td><td>事后财务变量（含 Net_Amount）</td><td>渠道/品类/折扣分组</td></tr>
<tr><td>输出</td><td>RMSE=0.01474（看似精确）</td><td>毛利率/亏损率/费用结构（可解释）</td></tr>
<tr><td>泄漏风险</td><td>Net_Amount 与目标构造性绑定</td><td>不存在泄漏</td></tr>
<tr><td>结论可用性</td><td>"Net_Amount 最重要"是已知事实</td><td>"Myntra 亏损因运费占比高"可指导运营</td></tr>
</table>
</div>
</div>
</div>''')

# ─── Slide 13: 结论 ───
slides.append('''<div class="slide" id="s12">
<h2>九、结论</h2>
<div class="col2">
<div>
<h3>核心发现</h3>
<ol style="padding-left:18px">
<li style="margin-bottom:10px"><b>Amazon 最稳健</b>——亏损率 0.5%，贡献毛利率 20.9%。202 单中仅 1 单亏损，是所有可比渠道中表现最好的。</li>
<li style="margin-bottom:10px"><b>Myntra 量最大但最亏</b>——53% 的订单量，亏损率 17.1%。亏损主因是平台费用（佣金+运费）而非产品成本。</li>
<li style="margin-bottom:10px"><b>98% 亏损由费用导致</b>——不是产品亏本卖，是平台扣费后"账算不过來"。仅 2% 的亏损源于 TP &gt; Net_Amount。</li>
<li style="margin-bottom:10px"><b>渠道选择即利润</b>——同款产品不同渠道利润差异可达 100&sim;200 INR，渠道费用结构是差异主因。</li>
<li style="margin-bottom:10px"><b>Kurta Set 亏损率高</b>（27.9%）——平均 TP 远超 Kurta，售价未能覆盖成本差距。</li>
<li style="margin-bottom:10px"><b>折扣超 60% 近半亏损</b>（49.8%），超 70% 近八成亏损（78.9%）。当前数据中未见"以量补价"效果。</li>
</ol>
</div>
<div>
<h3>局限性重申</h3>
<ul>
<li>所有"利润"均指贡献毛利，不可对标净利润</li>
<li>TP 不含仓储费、包装费等，可能低估真实成本</li>
<li>数据含 COVID-19 和排灯节影响，不可外推</li>
<li>样本严重不平衡，跨渠道统计检验不可靠</li>
<li>缺少广告/流量/转化率数据，促销分析不完整</li>
</ul>
</div>
</div>
</div>''')

# ─── Slide 14: 错误复盘 ───
slides.append('''<div class="slide" id="s13">
<h2 style="border-bottom-color:#c33">十、对原 ML 方案的错误复盘</h2>
<h3>方向错：用事后变量做"预测"</h3>
<p>原方案使用 Net_Amount、Commission、Shipping 等与利润同时发生的财务变量作为特征，本质上是对利润的再分解而非预测。正确的预测应当是：给定产品属性（品类、重量、款式）和目标渠道，预估利润。本数据集恰好不具备这种"事前"特征。</p>
<h3>方法错：RMSE 的虚假置信</h3>
<p>RMSE=0.01474 看似精度高，实则因为 Net_Amount 承载了目标变量 81.5% 的信息。一个简单基准测试就能揭示问题：仅用 Net_Amount &times; 0.20（Amazon 平均毛利率）作为利润估计，RMSE 未必高于随机森林的"精确结果"。高精度不是模型好，是问题本身太"容易"——答案已经藏在输入里。</p>
<h3>解释错：特征重要性的误读</h3>
<p>"销售金额（Net_Amount）重要性 81.5%"——从业务角度看似合理，但从方法论角度是循环论证。正确的表述是"Net_Amount 在数值上解释了贡献毛利的大部分方差"，但看公式就知道了：贡献毛利 = Net_Amount &minus; 费用 &minus; TP，不需要跑模型。</p>
<h3>改进方向</h3>
<ul>
<li>特征重构：仅用事前变量——品类、计划售价区间、目标渠道、历史同款折扣率、重量</li>
<li>分渠道建模：各渠道费用结构差异显著，统一模型会混入渠道效应</li>
<li>目标调整：将"预测利润绝对值"改为"预测亏损概率"（二分类），业务上更具操作性</li>
<li>补充外部数据：引入广告花费、流量数据、竞品价格等真正具有预测力的变量</li>
</ul>
</div>''')

# ─── Slide 15: 谢谢 ───
slides.append('''<div class="slide" id="s14">
<div class="title-slide">
<h1>谢谢聆听</h1>
<p style="margin-top:24px; font-size:16px; color:#888;">完整分析数据、图表及源代码见 output/ 目录</p>
</div>
</div>''')

# Combine all slides
for s in slides:
    html += s + '\n'

# Navigation
html += f'''
<div class="nav">
<button id="prevBtn" onclick="changeSlide(-1)">上一页</button>
<span class="page-num" id="pageNum">1 / {len(slides)}</span>
<button id="nextBtn" onclick="changeSlide(1)">下一页</button>
</div>

<script>
let current = 0;
const slides = document.querySelectorAll('.slide');
const total = slides.length;

function showSlide(n) {{
    slides.forEach((s, i) => s.classList.toggle('active', i === n));
    document.getElementById('pageNum').textContent = (n+1) + ' / ' + total;
    document.getElementById('prevBtn').disabled = n === 0;
    document.getElementById('nextBtn').disabled = n === total - 1;
}}

function changeSlide(d) {{
    let n = current + d;
    if (n >= 0 && n < total) {{ current = n; showSlide(n); }}
}}

document.addEventListener('keydown', function(e) {{
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') changeSlide(1);
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') changeSlide(-1);
}});

showSlide(0);
</script>

</body>
</html>'''

path = os.path.join(OUT_DIR, '利润导向电商分析_演示.html')
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done: {path}')
print(f'Size: {len(html)} bytes ({len(html)/1024:.0f} KB)')
print(f'Slides: {len(slides)}')
