"""
04_product_analysis.py — 产品维度分析（4P-Product）（规划第5节）
依赖：data/processed/delivered_features.csv（02的输出）
输出：图表 + data/processed/category_summary.csv
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


def category_analysis(df):
    """5.1 品类分析"""
    print(f"\n{'='*60}")
    print(f"  5.1 品类分析")
    print(f"{'='*60}")

    # 整体品类统计
    cat_stats = df.groupby('Category').agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Median_Margin=('Contribution_Margin', 'median'),
        Mean_Rate=('Margin_Rate', 'mean'),
        Loss_Rate=('Contribution_Margin', lambda x: (x < 0).mean() * 100),
        Mean_Discount=('Discount_Pct', 'mean'),
        Mean_Net=('Net_Amount', 'mean'),
        Mean_TP=('TP', 'mean'),
    ).round(2).sort_values('N', ascending=False)
    print(cat_stats.to_string())
    cat_stats.to_csv(os.path.join(OUT_DIR, 'category_stats.csv'))

    # 各渠道内的品类表现
    print(f"\n  ── 按渠道 × 品类的毛利率 ──")
    cross = df.groupby(['Channel', 'Category']).agg(
        N=('Contribution_Margin', 'count'),
        Mean_Margin=('Contribution_Margin', 'mean'),
        Mean_Rate=('Margin_Rate', 'mean'),
    ).round(2)
    print(cross.to_string())

    return cat_stats


def tp_cost_analysis(df):
    """5.2 TP 成本分析"""
    print(f"\n{'='*60}")
    print(f"  5.2 TP 成本分析")
    print(f"{'='*60}")

    # 成本加成率 (Net_Amount - TP) / TP
    mask = df['TP'] > 0
    df['Markup_Rate'] = np.nan
    df.loc[mask, 'Markup_Rate'] = (df.loc[mask, 'Net_Amount'] - df.loc[mask, 'TP']) / df.loc[mask, 'TP']

    print(f"  成本加成率（(Net_Amount-TP)/TP）:")
    print(f"    均值={df['Markup_Rate'].mean():.2f}, "
          f"中位数={df['Markup_Rate'].median():.2f}, "
          f"P5~P95=[{df['Markup_Rate'].quantile(0.05):.2f}~{df['Markup_Rate'].quantile(0.95):.2f}]")

    # 不同渠道的成本加成策略
    ch_markup = df.groupby('Channel')['Markup_Rate'].agg(['mean', 'median', 'count']).round(2)
    ch_markup = ch_markup.reindex([c for c in CHANNEL_ORDER if c in ch_markup.index])
    print(f"\n  各渠道成本加成率:")
    print(ch_markup.to_string())

    # TP 与 Weight 的关系
    weight_valid = df['Cat_Weight'].notna()
    if weight_valid.any():
        weight_series = pd.to_numeric(df.loc[weight_valid, 'Cat_Weight'], errors='coerce')
        valid = weight_series.notna() & (weight_series > 0)
        if valid.any():
            corr = df.loc[valid, 'TP'].corr(weight_series[valid])
            print(f"\n  TP 与 Weight 相关系数: {corr:.3f}")

    return ch_markup


def main():
    print("="*60)
    print("  04_product_analysis.py — 产品维度分析")
    print("="*60)

    df = load_data()

    cat_stats = category_analysis(df)
    ch_markup = tp_cost_analysis(df)

    print(f"\n{'='*60}")
    print(f"  04 完成。输出文件:")
    print(f"  - output/category_stats.csv")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
