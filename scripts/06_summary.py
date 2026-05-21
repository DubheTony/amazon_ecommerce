"""
06_summary.py — 汇总报告（规划第7b、8节）
依赖：data/processed/delivered_features.csv + 03-05 的输出
输出：output/summary_report.txt（结构化文本报告）
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
import io
import warnings
warnings.filterwarnings('ignore')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IN_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delivered_features.csv')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

CHANNEL_ORDER = ['Myntra', 'Flipkart', 'Amazon', 'Peachmode Fourbuttons B2C',
                 'Amazon FBA', 'Peachmode Os B2C', 'Mirraw B2B', 'Mirraw B2C',
                 'Limeroad', 'Meesho', 'Snapdeal', 'Cbazaar']


def load_data():
    df = pd.read_csv(IN_PATH, parse_dates=['Order_Date'])
    return df


def time_analysis(df):
    """7b: 时间维度分析"""
    print(f"\n{'='*60}")
    print(f"  7b 时间维度分析")
    print(f"{'='*60}")

    valid_date = df['Order_Date'].notna()
    print(f"  有日期的订单: {valid_date.sum()}/{len(df)}")

    if valid_date.sum() < 10:
        print("  有效日期不足，跳过时间分析")
        return

    df_time = df[valid_date].copy()
    df_time['Month'] = df_time['Order_Date'].dt.to_period('M')

    # 7b.1 月度订单分布
    monthly_orders = df_time.groupby('Month').size()
    print(f"\n  月度订单分布:")
    for m, n in monthly_orders.items():
        print(f"    {m}: {n} 单 ({n/len(df_time)*100:.1f}%)")

    # 各渠道月度分布
    print(f"\n  各渠道月度订单分布:")
    ch_monthly = df_time.groupby(['Channel', 'Month']).size().unstack(fill_value=0)
    ch_monthly = ch_monthly.reindex([c for c in CHANNEL_ORDER if c in ch_monthly.index])
    print(ch_monthly.to_string())

    # 7b.2 月度毛利率走势
    monthly_margin = df_time.groupby('Month').agg(
        Mean_Margin=('Contribution_Margin', 'mean'),
        Median_Margin=('Contribution_Margin', 'median'),
        N=('Contribution_Margin', 'count'),
    ).round(2)
    print(f"\n  月度贡献毛利走势:")
    print(monthly_margin.to_string())

    # 折线图
    fig, ax = plt.subplots(figsize=(12, 5))
    months_str = [str(m) for m in monthly_margin.index]
    ax.plot(months_str, monthly_margin['Mean_Margin'], marker='o', label='均值', linewidth=2)
    ax.plot(months_str, monthly_margin['Median_Margin'], marker='s', label='中位数', linewidth=2)
    ax.set_xlabel('月份')
    ax.set_ylabel('贡献毛利 (INR)')
    ax.set_title('月度贡献毛利走势')
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'monthly_margin_trend.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\n  已保存: {path}")

    # 7b.3 时间三等分敏感性测试
    df_sorted = df_time.sort_values('Order_Date')
    n = len(df_sorted)
    third = n // 3
    periods = {
        '早期 (1/3)': df_sorted.iloc[:third],
        '中期 (2/3)': df_sorted.iloc[third:2*third],
        '晚期 (3/3)': df_sorted.iloc[2*third:],
    }
    print(f"\n  时间切分敏感性测试:")
    for name, pdata in periods.items():
        print(f"    {name}: n={len(pdata)}, "
              f"平均贡献毛利={pdata['Contribution_Margin'].mean():.2f}, "
              f"中位数={pdata['Contribution_Margin'].median():.2f}")

    return monthly_margin


def compile_summary_report(df):
    """整合所有分析结果到结构化报告"""
    print(f"\n{'='*60}")
    print(f"  正在生成汇总报告")
    print(f"{'='*60}")

    lines = []
    def L(s=""): lines.append(s)

    L("=" * 70)
    L("  多渠道损益分析 — 汇总报告")
    L("  数据源: P&L March 2021.xlsx (12 渠道, 1,392 条 Delivered 订单)")
    L(f"  生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    L("=" * 70)

    # ─── 数据概况 ───
    L("\n" + "=" * 70)
    L("一、数据概况")
    L("=" * 70)
    L(f"  渠道数: 12")
    L(f"  Delivered 订单总数: {len(df)}")
    L(f"  Myntra 占比: {(df['Channel']=='Myntra').sum()}/{len(df)} = {(df['Channel']=='Myntra').mean()*100:.1f}%")
    L(f"  [!] Myntra > 50%，禁止发布全局汇总统计量")
    ch_counts = df['Channel'].value_counts()
    small = ch_counts[ch_counts < 10]
    for ch, n in small.items():
        L(f"  [!] {ch}: n={n} — 结论不可泛化")
    L(f"  数据时间范围: 2020-08 ~ 2021-03（含 COVID-19 高峰期和排灯节）")
    L(f"  Catalog 匹配率: 100%")
    L(f"  跨渠道重叠 SKU: 103 个 (涉及 {df[df['SKU'].isin(
        df.groupby('SKU').filter(lambda x: x['Channel'].nunique() > 1)['SKU'].unique()
    )].shape[0]}/{len(df)} = {df[df['SKU'].isin(
        df.groupby('SKU').filter(lambda x: x['Channel'].nunique() > 1)['SKU'].unique()
    )].shape[0]/len(df)*100:.1f}% 订单)")

    # ─── 关键逻辑约束 ───
    L("\n" + "=" * 70)
    L("二、关键逻辑约束与验证结果")
    L("=" * 70)

    L("\n  1. 利润公式: 采用 Payment - TP（已验证为正确基准）")
    L("     Portal_Payment 是批次变量（同一 Net Amount 有多达 27 种不同 Portal_Payment 值）")
    L("     Payment == Net_Amount + Deduction 吻合率 100%")
    L("     [!] 注意：GST 不在 Deduction 中，Payment 含 GST 成分，卖方需另行申报 GST")

    L('\n  2. "贡献毛利"（非净利润）')
    L("     不含: 固定成本、退货损失、广告费、仓储费、支付网关手续费、平台月费")
    L('     所有结论中"利润"均指此限定含义')

    L("\n  3. 取消订单: 已单独统计为渠道级运营损失，未分摊到 Delivered 订单")

    L("\n  4. TP 可能低估真实成本（不含入仓物流费、仓储费、包装材料费、质检费）")

    L("\n  5. 样本严重不平衡: Myntra 53%, 小渠道 (n<10): 4 个")

    L("\n  6. Returned 订单: 283 条已排除出利润分析")
    L("     [!] 数据缺退货物流成本，退货真实损失可能更高")

    L("\n  7. 季节性偏差: 数据含 COVID-19 高峰期和排灯节，不可外推")

    L("\n  8. Dis.% 跨渠道口径可能不一致，跨渠道折扣对比仅为参考")

    # ─── 4P-Place ───
    L("\n" + "=" * 70)
    L("三、渠道利润对比（4P-Place）")
    L("=" * 70)

    ch_stats = df.groupby('Channel').agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Median_Margin=('Contribution_Margin', 'median'),
        Mean_Rate=('Margin_Rate', 'mean'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
        Mean_Net=('Net_Amount', 'mean'),
        Mean_TP=('TP', 'mean'),
    ).round(2)
    ch_stats = ch_stats.reindex([c for c in CHANNEL_ORDER if c in ch_stats.index])

    for ch, row in ch_stats.iterrows():
        L(f"  {ch:35s} n={int(row['N']):4d}  "
          f"均值={row['Mean_Margin']:7.2f}  中位数={row['Median_Margin']:7.2f}  "
          f"毛利率={row['Mean_Rate']:.0%}  亏损率={row['Loss_Rate']:.1f}%")

    L(f"\n  亏损渠道排名:")
    for ch, row in ch_stats.sort_values('Loss_Rate', ascending=False).iterrows():
        L(f"    {ch:35s} 亏损率={row['Loss_Rate']:5.1f}%")

    L(f"\n  亏损主因:")
    loss = df[df['Contribution_Margin'] < 0]
    if len(loss) > 0:
        tp_cause = (loss['TP'] > loss['Net_Amount']).mean() * 100
        L(f"    费用过高: {100-tp_cause:.1f}% (TP 超过 Net_Amount: {tp_cause:.1f}%)")

    # ─── 4P-Product ───
    L("\n" + "=" * 70)
    L("四、产品维度（4P-Product）")
    L("=" * 70)

    cat_stats = df.groupby('Category').agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Mean_Rate=('Margin_Rate', 'mean'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
    ).round(2).sort_values('N', ascending=False)

    for cat, row in cat_stats.iterrows():
        L(f"  {cat:15s} n={int(row['N']):4d}  均值={row['Mean_Margin']:7.2f}  "
          f"毛利率={row['Mean_Rate']:.0%}  亏损率={row['Loss_Rate']:.1f}%")

    L(f"\n  TP 与 Weight 相关系数: {pd.to_numeric(df['Cat_Weight'], errors='coerce').corr(df['TP']):.3f}")

    # ─── 4P-Price ───
    L("\n" + "=" * 70)
    L("五、价格策略（4P-Price）")
    L("=" * 70)

    L(f"\n  折扣区间 vs 亏损率:")
    bins = [-1, 0, 20, 40, 60, 80, 100]
    labels = ['0%', '0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    df['Discount_Bin'] = pd.cut(df['Discount_Pct'], bins=bins, labels=labels)
    disc_stats = df.groupby('Discount_Bin', observed=False).agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
    ).round(2)
    for bin_label, row in disc_stats.iterrows():
        L(f"    {bin_label:10s} n={int(row['N']):4d}  均值={row['Mean_Margin']:7.2f}  亏损率={row['Loss_Rate']:5.1f}%")

    L(f"\n  折扣 ≥ 70% 订单: {(df['Discount_Pct']>=70).sum()} 单, "
      f"亏损率 {df[df['Discount_Pct']>=70]['Contribution_Margin'].lt(0).mean()*100:.1f}%")

    L(f"\n  各渠道平均折扣率 (从高到低):")
    ch_discount = df.groupby('Channel')['Discount_Pct'].mean().round(2).sort_values(ascending=False)
    for ch, d in ch_discount.items():
        L(f"    {ch:35s} {d:.1f}%")

    # ─── 4P-Promotion ───
    L("\n" + "=" * 70)
    L("六、促销分析（4P-Promotion）")
    L("=" * 70)
    L(f"  数据仅含折扣率字段，无广告投入、流量来源、促销活动标记等数据")
    L(f"  同渠道内高折扣订单的贡献毛利普遍低于低折扣订单，价量权衡效果无法判断")

    # ─── 取消订单 ───
    L("\n" + "=" * 70)
    L("七、取消订单分析")
    L("=" * 70)
    cancelled_path = os.path.join(BASE_DIR, 'data', 'processed', 'cancelled_orders.csv')
    if os.path.exists(cancelled_path):
        cancelled = pd.read_csv(cancelled_path)
        for ch in CHANNEL_ORDER:
            ch_c = cancelled[cancelled['Channel'] == ch]
            if ch_c.empty:
                continue
            n_deliv = ch_stats.loc[ch, 'N'] if ch in ch_stats.index else 0
            n_canc = len(ch_c)
            total = n_deliv + n_canc
            rate = n_canc / total * 100 if total > 0 else 0
            penalty = ch_c['Portal_Payment'].sum()
            flag = ' [!] Portal_Payment 为正值（非罚款），详见异常说明' if penalty > 0 else ''
            L(f"  {ch:35s} 取消率={rate:5.1f}% ({n_canc}/{total})  "
              f"渠道级损失={penalty:8.2f}{flag}")
        L(f"\n  [!] Mirraw B2B 取消订单 Portal_Payment 为正值 (合计 +1,439)")
        L(f'      与"取消罚款应为负值"假设矛盾，可能为 B2B 结算差额而非罚款')

    # ─── 时间维度 ───
    L("\n" + "=" * 70)
    L("八、时间维度")
    L("=" * 70)
    valid_date = df['Order_Date'].notna()
    if valid_date.sum() > 10:
        df_time = df[valid_date].copy()
        df_time['Month'] = df_time['Order_Date'].dt.to_period('M')
        monthly = df_time.groupby('Month')['Contribution_Margin'].mean().round(2)
        for m, v in monthly.items():
            L(f"  {m}: 平均贡献毛利={v:.2f}")

        # 三期稳定性
        df_sorted = df_time.sort_values('Order_Date')
        n = len(df_sorted)
        third = n // 3
        early = df_sorted.iloc[:third]['Contribution_Margin'].mean()
        mid = df_sorted.iloc[third:2*third]['Contribution_Margin'].mean()
        late = df_sorted.iloc[2*third:]['Contribution_Margin'].mean()
        L(f"  三期稳定性测试: 早期={early:.2f}, 中期={mid:.2f}, 晚期={late:.2f}")
        max_min = max(early, mid, late) - min(early, mid, late)
        L(f"  极差: {max_min:.2f}")

    # ─── 数据质量说明 ───
    L("\n" + "=" * 70)
    L("九、数据质量问题与处理说明")
    L("=" * 70)
    L("  1. Order_Date 列: Peachmode Fourbuttons B2C(7行) 和 Mirraw B2B(11行Cancelled)")
    L("     的 Order_Date 为 datetime.time(0,0)，已转为 NaT")
    L("  2. Meesho: 5 条 Delivered 中 1 条 TP=0 被剔除，实际 4 条可用")
    L("  3. Mirraw B2B Cancelled 订单 Portal_Payment 全为正值（均 27.67），")
    L("     与其他渠道取消罚款为负值的规律不同，原因未明")
    L("  4. Meesho 渠道 Discount_Pct 为负值 (-13.04%)，可能为加价而非折扣")
    L("  5. Category='Nill': 14 条订单，可能是缺失值填充，已按原值处理")
    L("  6. 规划约束2展开式误包含 GST 项，已修正")

    # ─── 局限性 ───
    L("\n" + "=" * 70)
    L("十、局限性声明")
    L("=" * 70)
    limitations = [
        ("分析的实为贡献毛利，不是净利润",
         '不含固定成本、退货损失、广告费等，数值偏高。不可与"净利润"直接对比'),
        ("TP 可能不完全等于 COGS",
         "TP 是贸易价格，不含仓储、包装等间接变动成本，贡献毛利可能被高估"),
        ("Portal_Payment 是批次变量，非现金结算",
         "已验证 Payment-TP 是正确基准；不能使用 Portal_Payment 做逐笔利润计算"),
        ("取消订单有罚款成本",
         "已单独统计为渠道级运营损失，但 Mirraw B2B 的正值 Portal_Payment 含义未明"),
        ("时间跨度仅 2020.08–2021.03，含 COVID-19 高峰期和排灯节",
         "无法分析季节性、年同比趋势；此期间电商行为可能偏离正常水平，不可外推"),
        ("样本量 1,392 条，渠道严重不平衡 (Myntra 53%)",
         "统计显著性受限，跨渠道统计检验不可靠；汇总统计量不发布"),
        ("数据集未包含退货记录或退货信息有限",
         "退货退款损失+退货物流成本未被计入，贡献毛利可能被系统性高估"),
        ("Dis.% 跨渠道口径可能不一致",
         "各平台计算折扣率规则可能不同，跨渠道折扣率对比存在误导风险"),
        ("无广告/流量/转化率数据",
         "4P 中 Promotion 分析不完整，仅含折扣率字段"),
    ]
    for i, (title, desc) in enumerate(limitations, 1):
        L(f"  {i}. {title}")
        L(f"     影响: {desc}")

    # ─── 可产出结论列表 ───
    L("\n" + "=" * 70)
    L("十一、可产出结论")
    L("=" * 70)

    findings = [
        "在样本期间，Amazon 渠道亏损率最低 (0.5%)，Mirraw B2C 平均毛利最高 (352.50)",
        "费用结构差异是渠道利润差异的主因（98% 的亏损源于费用过高而非成本过高）",
        "Kurta 品类亏损率 (7.74%) 远低于 Kurta Set (27.85%)",
        "折扣率 ≥ 70% 的订单 78.9% 亏损，折扣与利润呈明显负相关",
        "同款产品 (SKU) 在不同渠道的利润差异可达 100-200 INR，主要来自佣金和运费差异",
        "Myntra 贡献了 53% 的订单但亏损率最高 (17.07%)，折扣率并非最高 (57.08%)",
        "Mirraw B2B 成本加成率仅 0.31（远低于其他渠道），毛利率看似高但绝对值低",
    ]
    for i, f in enumerate(findings, 1):
        L(f"  {i}. {f}")

    # ─── 不可产出结论类型 ───
    L("\n" + "=" * 70)
    L("十二、不可产出结论（警示）")
    L("=" * 70)
    cant_do = [
        '"2022 年渠道利润变化趋势"（无 2022 年 P&L 数据）',
        '"新品上架的利润预测"（样本量不足且受时间截面限制）',
        '"广告投入对利润的影响"（无广告数据）',
        '"渠道 A 优于渠道 B"（样本不平衡、产品结构可能不同、时间窗口受限，无法做因果推断）',
        '"取消罚款应该被分摊到 Delivered 订单"（罚款是渠道层面运营风险成本，分摊不改变结构信息）',
        '"改善 X 能提高利润 YY 元"（无增量分析数据支撑，无法建立因果关系）',
    ]
    for i, c in enumerate(cant_do, 1):
        L(f"  {i}. {c}")

    L("\n" + "=" * 70)
    L("  [报告完]")
    L("=" * 70)

    report = "\n".join(lines)
    report_path = os.path.join(OUT_DIR, 'summary_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  报告已保存: {report_path}")
    print(report[:2000])
    print("  ...（完整报告见文件）")

    return report


def main():
    print("=" * 60)
    print("  06_summary.py — 汇总报告生成")
    print("=" * 60)

    df = load_data()

    # 7b 时间分析
    monthly = time_analysis(df)

    # 汇总报告
    report = compile_summary_report(df)

    print(f"\n{'='*60}")
    print(f"  06 完成。输出文件:")
    print(f"  - output/monthly_margin_trend.png")
    print(f"  - output/summary_report.txt")
    print(f"{'='*60}")
    print(f"\n  全部脚本完成！下一步：审查 summary_report.txt 确认分析结论。")


if __name__ == '__main__':
    main()
