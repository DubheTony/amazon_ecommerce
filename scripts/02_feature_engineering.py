"""
02_feature_engineering.py — 特征工程（规划第3.1-3.3节）
依赖：data/processed/delivered_orders.csv（01的输出）
输出：data/processed/delivered_features.csv
"""

import pandas as pd
import numpy as np
import os
import sys
import io
import warnings
warnings.filterwarnings('ignore')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── 配置 ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IN_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delivered_orders.csv')
CATALOG_PATH = os.path.join(BASE_DIR, 'anilsharma87-sales', 'P & L March 2021.xlsx')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'delivered_features.csv')
OVERLAP_OUT = os.path.join(BASE_DIR, 'data', 'processed', 'sku_overlap.csv')


def load_data():
    """加载清洗后的 Delivered 订单"""
    df = pd.read_csv(IN_PATH, parse_dates=['Order_Date'])
    print(f"加载 Delivered 订单: {len(df)} 条, {df['Channel'].nunique()} 个渠道")
    for ch, cnt in df['Channel'].value_counts().items():
        print(f"  {ch}: {cnt}")
    return df


def compute_contribution_margin(df):
    """3.1 贡献毛利计算"""
    df['Contribution_Margin'] = df['Payment'] - df['TP']

    # margin_rate：Net_Amount 须为正数
    mask = df['Net_Amount'] > 0
    df['Margin_Rate'] = np.nan
    df.loc[mask, 'Margin_Rate'] = df.loc[mask, 'Contribution_Margin'] / df.loc[mask, 'Net_Amount']

    n_nan = (~mask).sum()
    if n_nan > 0:
        print(f"\n  [!] {n_nan} 条 Net_Amount<=0，Margin_Rate 置为 NaN")

    # 验证 Payment = Net_Amount + Commission + Shipping + Other + TCS + TDS
    # 注意：GST 不在 Deduction 中（规划约束2展开式有误，已修正）
    df['Payment_Manual'] = (df['Net_Amount']
                            + df['Commission']
                            + df['Shipping']
                            + df['Other']
                            + df['TCS']
                            + df['TDS'])
    match = abs(df['Payment'] - df['Payment_Manual']) < 0.01
    match_rate = match.mean() * 100
    print(f"  Payment 手动验证吻合率: {match_rate:.1f}%")
    if match_rate < 100:
        print(f"  [!] 不匹配: {(~match).sum()} 条")

    # 描述统计
    print(f"\n  贡献毛利描述统计:")
    print(f"    均值={df['Contribution_Margin'].mean():.2f}, "
          f"中位数={df['Contribution_Margin'].median():.2f}, "
          f"P5~P95=[{df['Contribution_Margin'].quantile(0.05):.2f}~{df['Contribution_Margin'].quantile(0.95):.2f}]")
    print(f"    亏损订单（贡献毛利<0）: {(df['Contribution_Margin'] < 0).sum()} 条 ({(df['Contribution_Margin'] < 0).mean()*100:.1f}%)")

    # 删除验证辅助列
    df.drop(columns=['Payment_Manual'], inplace=True)

    return df


def create_derived_features(df):
    """3.2 衍生特征"""
    print(f"\n  ── 衍生特征 ──")

    # 折扣率（已有 Dis.%）
    df['Has_Discount'] = df['Discount_Pct'] > 0
    has_disc_pct = df['Has_Discount'].mean() * 100
    print(f"  有折扣订单占比: {has_disc_pct:.1f}%")

    # 平台费率 = (|Commission| + |Shipping| + |Other|) / Net_Amount
    mask = df['Net_Amount'] > 0
    df['Fee_Rate'] = np.nan
    df.loc[mask, 'Fee_Rate'] = (
        df.loc[mask, 'Commission'].abs()
        + df.loc[mask, 'Shipping'].abs()
        + df.loc[mask, 'Other'].abs()
    ) / df.loc[mask, 'Net_Amount']
    print(f"  平台费率: 均值={df['Fee_Rate'].mean():.3f}, "
          f"中位数={df['Fee_Rate'].median():.3f}")

    # TP 比例 = TP / Net_Amount（成本占收入比重）
    df['TP_Ratio'] = np.nan
    df.loc[mask, 'TP_Ratio'] = df.loc[mask, 'TP'] / df.loc[mask, 'Net_Amount']
    print(f"  TP/Net_Amount: 均值={df['TP_Ratio'].mean():.3f}, "
          f"中位数={df['TP_Ratio'].median():.3f}")

    # 渠道类型：从渠道名推断 B2B vs B2C
    df['Channel_Type'] = df['Channel'].apply(
        lambda x: 'B2B' if 'B2B' in x else 'B2C'
    )
    b2b_count = (df['Channel_Type'] == 'B2B').sum()
    print(f"  渠道类型: B2B={b2b_count}, B2C={len(df)-b2b_count}")

    return df


def load_catalog_and_merge(df):
    """3.3 Catalog 关联 + 跨渠道产品重叠分析"""
    print(f"\n  ── Catalog 关联 ──")

    catalog = pd.read_excel(CATALOG_PATH, sheet_name='Catalog', engine='openpyxl')
    catalog = catalog.dropna(axis=0, how='all').dropna(axis=1, how='all')
    print(f"  Catalog 加载: {len(catalog)} 条")

    # 重命名 Catalog 列
    cat_rename = {
        'Sku': 'SKU',
        'Category': 'Cat_Category',
        'Weight': 'Cat_Weight',
        'TP 1': 'Cat_TP1',
        'TP 2': 'Cat_TP2',
        'MRP Old': 'Cat_MRP_Old',
        'Final MRP Old': 'Cat_Final_MRP',
    }
    catalog = catalog.rename(columns=cat_rename)
    # 只保留需要的列
    cat_cols = ['SKU', 'Cat_Category', 'Cat_Weight', 'Cat_TP1', 'Cat_TP2',
                'Cat_MRP_Old', 'Cat_Final_MRP']
    # 再加渠道 MRP 列
    mrp_cols = [c for c in catalog.columns if 'MRP' in c]
    catalog = catalog[[c for c in cat_cols + mrp_cols if c in catalog.columns]]

    # 合并
    before = len(df)
    df = df.merge(catalog[['SKU'] + [c for c in catalog.columns if c != 'SKU']],
                  on='SKU', how='left')
    matched = df['Cat_Category'].notna().sum()
    print(f"  Catalog 匹配率: {matched}/{before} = {matched/before*100:.1f}%")

    # 跨渠道产品重叠分析
    print(f"\n  ── 跨渠道产品重叠分析 ──")
    sku_channels = df.groupby('SKU')['Channel'].apply(set)
    multi_channel_skus = sku_channels[sku_channels.apply(len) > 1]
    print(f"  出现在多个渠道的 SKU: {len(multi_channel_skus)} 个")
    if len(multi_channel_skus) > 0:
        multi_order_count = df[df['SKU'].isin(multi_channel_skus.index)].shape[0]
        print(f"  涉及订单数: {multi_order_count}/{before} ({multi_order_count/before*100:.1f}%)")
        # 输出重叠 SKU 在各渠道的对比
        overlap_data = []
        for sku in list(multi_channel_skus.index)[:20]:  # 展示前 20 个
            sku_df = df[df['SKU'] == sku]
            for ch in sku_df['Channel'].unique():
                ch_data = sku_df[sku_df['Channel'] == ch]
                overlap_data.append({
                    'SKU': sku,
                    'Channel': ch,
                    'Count': len(ch_data),
                    'Mean_Margin': ch_data['Contribution_Margin'].mean(),
                    'Mean_Margin_Rate': ch_data['Margin_Rate'].mean(),
                    'Mean_Discount': ch_data['Discount_Pct'].mean(),
                })
        overlap_df = pd.DataFrame(overlap_data)
        overlap_df.to_csv(OVERLAP_OUT, index=False)
        print(f"  重叠 SKU 对比已保存: {OVERLAP_OUT}")

        # 按 SKU 统计毛利率差异
        print(f"\n  同款产品跨渠道毛利差异（示例，最多 5 个 SKU）:")
        for sku in list(multi_channel_skus.index)[:5]:
            sku_df = df[df['SKU'] == sku]
            chs = sku_df.groupby('Channel').agg(
                n=('Contribution_Margin', 'count'),
                mean_margin=('Contribution_Margin', 'mean'),
                mean_rate=('Margin_Rate', 'mean'),
                mean_disc=('Discount_Pct', 'mean')
            ).round(2)
            print(f"\n    SKU={sku}:")
            print(f"    {chs.to_string()}")
    else:
        print(f"  各渠道销售的 SKU 无交集")
        print(f"  => 渠道利润差异可能主要来自产品组合差异而非渠道效率差异")

    return df


def main():
    print("="*60)
    print("  02_feature_engineering.py — 特征工程")
    print("="*60)

    df = load_data()

    # 3.1 贡献毛利
    print(f"\n{'='*60}")
    print(f"  3.1 贡献毛利计算")
    print(f"{'='*60}")
    df = compute_contribution_margin(df)

    # 3.2 衍生特征
    print(f"\n{'='*60}")
    print(f"  3.2 衍生特征")
    print(f"{'='*60}")
    df = create_derived_features(df)

    # 3.3 Catalog 关联 + 产品重叠
    print(f"\n{'='*60}")
    print(f"  3.3 Catalog 关联与产品重叠分析")
    print(f"{'='*60}")
    df = load_catalog_and_merge(df)

    # 保存
    df.to_csv(OUT_PATH, index=False)
    print(f"\n{'='*60}")
    print(f"  [OK] 特征数据已保存: {OUT_PATH}")
    print(f"  列数: {len(df.columns)}")
    print(f"  行数: {len(df)}")
    print(f"  下一步：运行 03_channel_analysis.py / 04_product_analysis.py / 05_price_analysis.py")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
