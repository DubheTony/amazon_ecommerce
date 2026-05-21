"""
05_price_analysis.py — 价格策略分析（4P-Price & 4P-Promotion）（规划第6、7节）
依赖：data/processed/delivered_features.csv（02的输出）
输出：图表 + data/processed/discount_analysis.csv
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
    df = pd.read_csv(IN_PATH)
    print(f"加载数据: {len(df)} 条")
    return df


def discount_margin_relationship(df):
    """6.1 折扣与贡献毛利关系"""
    print(f"\n{'='*60}")
    print(f"  6.1 折扣与贡献毛利关系")
    print(f"{'='*60}")

    # 折扣率分段
    bins = [-1, 0, 20, 40, 60, 80, 100]
    labels = ['0%', '0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    df['Discount_Bin'] = pd.cut(df['Discount_Pct'], bins=bins, labels=labels)

    disc_stats = df.groupby('Discount_Bin', observed=False).agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Median_Margin=('Contribution_Margin', 'median'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
        Mean_Net=('Net_Amount', 'mean'),
        Mean_TP=('TP', 'mean'),
    ).round(2)
    print("折扣区间 vs 贡献毛利:")
    print(disc_stats.to_string())

    # 折扣与毛利率的关系（散点图，每渠道不同颜色）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 左：折扣 vs 贡献毛利
    for ch in df['Channel'].unique():
        ch_data = df[df['Channel'] == ch]
        axes[0].scatter(ch_data['Discount_Pct'], ch_data['Contribution_Margin'],
                       alpha=0.3, s=8, label=ch)
    axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0].set_xlabel('折扣率 (%)')
    axes[0].set_ylabel('贡献毛利 (INR)')
    axes[0].set_title('折扣率 vs 贡献毛利')
    axes[0].legend(fontsize=6, ncol=2)

    # 右：折扣 vs 毛利率
    for ch in df['Channel'].unique():
        ch_data = df[df['Channel'] == ch]
        axes[1].scatter(ch_data['Discount_Pct'], ch_data['Margin_Rate'],
                       alpha=0.3, s=8, label=ch)
    axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[1].set_xlabel('折扣率 (%)')
    axes[1].set_ylabel('毛利率')
    axes[1].set_title('折扣率 vs 毛利率')
    axes[1].legend(fontsize=6, ncol=2)

    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'discount_vs_margin.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\n  已保存: {path}")

    # 折扣区间的订单量分布
    fig, ax = plt.subplots(figsize=(10, 5))
    disc_counts = df['Discount_Bin'].value_counts().reindex(labels)
    ax.bar(disc_counts.index, disc_counts.values, color='#55A868', width=0.6)
    ax.set_xlabel('折扣区间')
    ax.set_ylabel('订单数')
    ax.set_title('不同折扣区间的订单量分布')
    for i, v in enumerate(disc_counts.values):
        ax.text(i, v + 10, str(v), ha='center', fontsize=10)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'discount_distribution.png')
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  已保存: {path}")

    # 各渠道平均折扣
    ch_disc = df.groupby('Channel')['Discount_Pct'].agg(['mean', 'median', 'std', 'count']).round(2)
    ch_disc = ch_disc.reindex([c for c in CHANNEL_ORDER if c in ch_disc.index])
    print(f"\n各渠道平均折扣率:")
    print(ch_disc.to_string())

    # 折扣倒挂分析：高折扣是否亏损
    print(f"\n  ── 折扣倒挂分析 ──")
    for thresh in [50, 60, 70]:
        high_disc = df[df['Discount_Pct'] >= thresh]
        if len(high_disc) > 0:
            loss_rate = (high_disc['Contribution_Margin'] < 0).mean() * 100
            print(f"  折扣 ≥ {thresh}%: {len(high_disc)} 单, 亏损率 {loss_rate:.1f}%")

    return disc_stats


def price_structure(df):
    """6.2 MRP vs 实际售价 vs TP"""
    print(f"\n{'='*60}")
    print(f"  6.2 MRP vs 实际售价 vs TP")
    print(f"{'='*60}")

    # 售价相对于 MRP 的折扣
    mask = df['MRP'] > 0
    df['MRP_Discount_Rate'] = np.nan
    df.loc[mask, 'MRP_Discount_Rate'] = (df.loc[mask, 'MRP'] - df.loc[mask, 'Net_Amount']) / df.loc[mask, 'MRP'] * 100

    print(f"  相对于 MRP 的折扣率:")
    print(f"    均值={df['MRP_Discount_Rate'].mean():.1f}%, "
          f"中位数={df['MRP_Discount_Rate'].median():.1f}%")

    # 各渠道的三层价格结构
    for ch in CHANNEL_ORDER:
        ch_data = df[df['Channel'] == ch]
        if len(ch_data) == 0:
            continue
        avg_mrp = ch_data['MRP'].mean()
        avg_net = ch_data['Net_Amount'].mean()
        avg_tp = ch_data['TP'].mean()
        avg_payment = ch_data['Payment'].mean()
        print(f"  {ch:35s} MRP={avg_mrp:7.0f} → Net={avg_net:7.0f} → TP={avg_tp:7.0f} → Payment={avg_payment:7.0f}")


def promotion_analysis(df):
    """7.1 促销分析（有限）"""
    print(f"\n{'='*60}")
    print(f"  7.1 促销分析（有限）")
    print(f"{'='*60}")

    # 有无折扣订单的对比
    has_disc = df[df['Has_Discount']]
    no_disc = df[~df['Has_Discount']]
    print(f"  有折扣: {len(has_disc)} 单, 平均贡献毛利={has_disc['Contribution_Margin'].mean():.2f}")
    print(f"  无折扣: {len(no_disc)} 单, 平均贡献毛利={no_disc['Contribution_Margin'].mean():.2f}")

    # 同渠道内高折扣 vs 低折扣
    print(f"\n  同渠道内高/低折扣对比（中位数为界）:")
    for ch in CHANNEL_ORDER:
        ch_data = df[df['Channel'] == ch]
        if len(ch_data) < 5:
            continue
        median_disc = ch_data['Discount_Pct'].median()
        high = ch_data[ch_data['Discount_Pct'] >= median_disc]
        low = ch_data[ch_data['Discount_Pct'] < median_disc]
        print(f"  {ch:35s} 高折: n={len(high):3d}, 毛利={high['Contribution_Margin'].mean():7.2f}  |  "
              f"低折: n={len(low):3d}, 毛利={low['Contribution_Margin'].mean():7.2f}")

    print(f"\n  [!] Promotion 维度仅含折扣率，缺少广告投入、流量来源、促销活动标记等数据")


def main():
    print("="*60)
    print("  05_price_analysis.py — 价格与促销分析")
    print("="*60)

    df = load_data()

    discount_margin_relationship(df)
    price_structure(df)
    promotion_analysis(df)

    print(f"\n{'='*60}")
    print(f"  05 完成。输出文件:")
    print(f"  - output/discount_vs_margin.png")
    print(f"  - output/discount_distribution.png")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
