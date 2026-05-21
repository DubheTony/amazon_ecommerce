"""
03_channel_analysis.py — 渠道利润对比分析（4P-Place）（规划第4节）
依赖：data/processed/delivered_features.csv（02的输出）
输出：图表 + data/processed/channel_summary.csv
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys
import io
import warnings
warnings.filterwarnings('ignore')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── 配置 ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IN_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delivered_features.csv')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# 中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

SMALL_CHANNELS = ['Limeroad', 'Meesho', 'Snapdeal', 'Cbazaar']
CHANNEL_ORDER = ['Myntra', 'Flipkart', 'Amazon', 'Peachmode Fourbuttons B2C',
                 'Amazon FBA', 'Peachmode Os B2C', 'Mirraw B2B', 'Mirraw B2C',
                 'Limeroad', 'Meesho', 'Snapdeal', 'Cbazaar']


def load_data():
    df = pd.read_csv(IN_PATH)
    print(f"加载数据: {len(df)} 条")
    return df


def channel_basic_stats(df):
    """4.1 单变量统计"""
    print(f"\n{'='*60}")
    print(f"  4.1 渠道单变量统计")
    print(f"{'='*60}")

    # 按渠道分组统计
    stats = df.groupby('Channel').agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Median_Margin=('Contribution_Margin', 'median'),
        Std_Margin=('Contribution_Margin', 'std'),
        P5_Margin=('Contribution_Margin', lambda x: x.quantile(0.05)),
        P95_Margin=('Contribution_Margin', lambda x: x.quantile(0.95)),
        Mean_Rate=('Margin_Rate', 'mean'),
        Median_Rate=('Margin_Rate', 'median'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
        Mean_Net=('Net_Amount', 'mean'),
        Mean_TP=('TP', 'mean'),
    ).round(2)

    # 重排
    stats = stats.reindex([c for c in CHANNEL_ORDER if c in stats.index])
    print(stats.to_string())
    stats.to_csv(os.path.join(OUT_DIR, 'channel_stats.csv'))
    print(f"\n  已保存: output/channel_stats.csv")

    # 亏损深度
    print(f"\n  ── 亏损订单深度 ──")
    for ch in CHANNEL_ORDER:
        ch_data = df[df['Channel'] == ch]
        loss = ch_data[ch_data['Contribution_Margin'] < 0]
        if len(loss) > 0:
            avg_loss = loss['Contribution_Margin'].mean()
            print(f"  {ch:35s} 亏损{len(loss):3d}单, 平均亏损{avg_loss:8.2f}")
        else:
            print(f"  {ch:35s} 无亏损订单")

    return stats


def fee_structure_chart(df):
    """4.2 渠道费用结构拆解（堆叠柱状图）"""
    print(f"\n  ── 4.2 渠道费用结构拆解 ──")

    ch_order = [c for c in CHANNEL_ORDER if c in df['Channel'].unique()]

    # 每渠道平均费用结构
    fee_data = []
    for ch in ch_order:
        ch_data = df[df['Channel'] == ch]
        fee_data.append({
            'Channel': ch,
            'TP': ch_data['TP'].mean(),
            'GST': ch_data['GST'].mean(),
            'Commission': ch_data['Commission'].abs().mean(),
            'Shipping': ch_data['Shipping'].abs().mean(),
            'Other': ch_data['Other'].abs().mean(),
            'TCS_TDS': (ch_data['TCS'].abs() + ch_data['TDS'].abs()).mean(),
            'Contribution_Margin': ch_data['Contribution_Margin'].mean(),
        })
    fee_df = pd.DataFrame(fee_data)
    fee_df.to_csv(os.path.join(OUT_DIR, 'fee_structure.csv'), index=False)

    # 堆叠图
    categories = ['TP', 'GST', 'Commission', 'Shipping', 'Other', 'TCS_TDS', 'Contribution_Margin']
    colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2', '#937860', '#8C8C8C']

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(fee_df))
    bottom = np.zeros(len(fee_df))

    for i, cat in enumerate(categories):
        vals = fee_df[cat].values
        ax.bar(x, vals, bottom=bottom, label=cat, color=colors[i], width=0.65)
        bottom += vals

    ax.set_xlabel('渠道', fontsize=12)
    ax.set_ylabel('平均每单金额 (INR)', fontsize=12)
    ax.set_title('各渠道平均每单费用结构拆解', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(fee_df['Channel'], rotation=45, ha='right', fontsize=9)
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'fee_structure.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  已保存: {path}")

    return fee_df


def loss_distribution(df):
    """4.3 亏损订单渠道分布"""
    print(f"\n  ── 4.3 亏损订单渠道分布 ──")

    df['Is_Loss'] = df['Contribution_Margin'] < 0

    loss_by_ch = df.groupby('Channel').agg(
        Total=('Is_Loss', 'count'),
        Loss=('Is_Loss', 'sum'),
        Loss_Rate=('Is_Loss', 'mean'),
    )
    loss_by_ch = loss_by_ch.reindex([c for c in CHANNEL_ORDER if c in loss_by_ch.index])
    print(loss_by_ch.to_string())

    # 亏损原因分析：是成本过高还是费用过高？
    loss_df = df[df['Is_Loss']]
    if len(loss_df) > 0:
        print(f"\n  亏损订单原因分析:")
        loss_df['TP_exceeds_Net'] = loss_df['TP'] > loss_df['Net_Amount']
        loss_df['Fees_excessive'] = (~loss_df['TP_exceeds_Net'])
        tp_cause = loss_df['TP_exceeds_Net'].mean() * 100
        print(f"  TP 超过 Net_Amount（成本过高）: {tp_cause:.1f}%")
        print(f"  费用过高导致亏损: {100-tp_cause:.1f}%")

    return loss_by_ch


def main():
    print("="*60)
    print("  03_channel_analysis.py — 渠道利润对比分析")
    print("="*60)

    df = load_data()

    # 4.1
    stats = channel_basic_stats(df)

    # 4.2
    fee_df = fee_structure_chart(df)

    # 4.3
    loss_dist = loss_distribution(df)

    print(f"\n{'='*60}")
    print(f"  03 完成。输出文件:")
    print(f"  - output/channel_stats.csv")
    print(f"  - output/fee_structure.csv")
    print(f"  - output/fee_structure.png")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
