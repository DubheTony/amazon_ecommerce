"""
01_load_validate.py — 数据加载与清洗（规划第2.1-2.4节）
输出：验证报告（控制台）+ 清洗后数据文件（data/processed/）
"""

import pandas as pd
import numpy as np
import os
import sys
import io
import warnings
warnings.filterwarnings('ignore')

# Windows GBK 兼容输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── 配置 ───────────────────────────────────────────────────────
XLSX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'anilsharma87-sales', 'P & L March 2021.xlsx')
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       'data', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)

# 规划中列出的12个渠道表（含Delivered订单）
CHANNEL_SHEETS = [
    'Amazon', 'Amazon FBA', 'Flipkart', 'Myntra', 'Limeroad', 'Meesho',
    'Mirraw B2B', 'Mirraw B2C', 'Cbazaar', 'Snapdeal',
    'Peachmode Fourbuttons B2C', 'Peachmode Os B2C'
]

# 列名映射（标准列名 -> 统一英文名）
COLUMN_MAP = {
    'Mode': 'Mode',
    'Order Id': 'Order_ID',
    'Invoice Id': 'Invoice_ID',
    'City': 'City',
    'State': 'State',
    'Order Date': 'Order_Date',
    'Style': 'Style',
    'Size': 'Size',
    'SKU': 'SKU',
    'Category': 'Category',
    'Weight': 'Weight',
    'Quantity': 'Quantity',
    'TP': 'TP',
    'MRP': 'MRP',
    'Dis.%': 'Discount_Pct',
    'Net Amount': 'Net_Amount',
    'GST': 'GST',
    'Commission Charges': 'Commission',
    'Shipping Charges': 'Shipping',
    'Other Charges': 'Other',
    'T.C.S.': 'TCS',
    'T.D.S.': 'TDS',
    'Advertisement': 'Advertisement',
    'Deduction': 'Deduction',
    'Payment': 'Payment',
    'Portal Payment': 'Portal_Payment',
    'Portal Payment Difference': 'Portal_Payment_Diff',
    'TP Difference': 'TP_Diff',
}

# ─── 辅助函数 ───────────────────────────────────────────────────

def load_channel_sheet(sheet_name):
    """加载单张渠道表，统一列名，返回 DataFrame"""
    df = pd.read_excel(XLSX_PATH, sheet_name=sheet_name, engine='openpyxl')
    # 丢弃完全空的行和列
    df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
    # 重命名已知列，未知列丢弃
    rename_map = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    # 只保留已映射的列
    keep_cols = list(rename_map.values())
    df = df[[c for c in keep_cols if c in df.columns]]
    df['Channel'] = sheet_name

    # 修复：部分行 Order_Date 为 datetime.time(0,0)（Excel 缺省日期），强制转 NaT
    if 'Order_Date' in df.columns:
        before = df['Order_Date'].isna().sum()
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
        after = df['Order_Date'].isna().sum()
        new_nat = after - before
        if new_nat > 0:
            print(f"  [!] Order_Date: {new_nat} 行从 time 转 NaT（原始数据缺日期）")

    return df


def report_validation(df, name):
    """输出单渠道的质量检查报告"""
    n_total = len(df)
    n_delivered = (df['Mode'] == 'Delivered').sum()
    n_cancelled = (df['Mode'] == 'Cancelled').sum()
    n_returned = (df['Mode'] == 'Returned').sum() if 'Returned' in df['Mode'].values else 0

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  总行数: {n_total}")
    print(f"  Delivered: {n_delivered} | Cancelled: {n_cancelled} | Returned: {n_returned}")

    if n_delivered == 0:
        print("  [!]  无 Delivered 订单，跳过后续检查")
        return None

    deliv = df[df['Mode'] == 'Delivered'].copy()

    # 日期范围
    if 'Order_Date' in deliv.columns and deliv['Order_Date'].notna().any():
        valid_dates = deliv['Order_Date'].dropna()
        if len(valid_dates) > 0:
            print(f"  日期范围: {valid_dates.min()} ~ {valid_dates.max()}")

    # 数值列检查
    for col in ['Net_Amount', 'TP', 'Payment', 'Portal_Payment']:
        if col in deliv.columns:
            non_null = deliv[col].notna().sum()
            print(f"  {col}: {non_null}/{n_delivered} 非空")

    # TP 与 Net Amount 比例范围
    valid = deliv[(deliv['Net_Amount'] > 0) & (deliv['TP'] > 0)]
    if len(valid) > 0:
        ratio = valid['TP'] / valid['Net_Amount']
        print(f"  TP/Net_Amount 比例: 中位数={ratio.median():.2f}, "
              f"P5~P95=[{ratio.quantile(0.05):.2f}~{ratio.quantile(0.95):.2f}]")

    # 异常值标记：严重亏损订单（Net Amount - Payment > TP，即亏掉成本还更多）
    if 'Payment' in deliv.columns and 'TP' in deliv.columns:
        severe_loss = deliv[deliv['Payment'] - deliv['TP'] < -deliv['TP']]
        if len(severe_loss) > 0:
            print(f"  [!]  严重亏损订单（贡献毛利 < -TP）: {len(severe_loss)} 条")

    # ─── 利润公式验证（规划2.2节）──────────────────────────
    print(f"\n  ── 利润公式验证 ──")

    # Payment - TP vs Portal Payment - TP
    method_pay = (deliv['Payment'] - deliv['TP']).dropna()
    method_portal = (deliv['Portal_Payment'] - deliv['TP']).dropna()

    if len(method_pay) > 0 and len(method_portal) > 0:
        print(f"  Payment-TP:     均值={method_pay.mean():.2f}, 标准差={method_pay.std():.2f}")
        print(f"  PortalPay-TP:   均值={method_portal.mean():.2f}, 标准差={method_portal.std():.2f}")

        # Portal Payment 批次变量验证：相同 Net Amount 下 Portal Payment 的离散度
        grouped = deliv.groupby('Net_Amount')['Portal_Payment'].nunique()
        multi = grouped[grouped > 1]
        if len(multi) > 0:
            print(f"  [!]  同一 Net Amount 下 Portal_Payment 有多种值: {len(multi)} 组")
            if len(multi) > 0:
                exam = multi.sort_values(ascending=False).head(3)
                for na_val in exam.index:
                    vals = deliv[deliv['Net_Amount'] == na_val]['Portal_Payment'].unique()
                    print(f"     Net Amount={na_val}: Portal_Payment={sorted(vals)}")
            print(f"  → Portal_Payment 是批次变量，不应按逐笔订单使用")
            print(f"  → 采用 Payment - TP 作为利润基准 ✓")
        else:
            print(f"  → Portal_Payment 在各 Net Amount 组内一致，可能也是逐笔值")

    # ─── Payment 与 Net Amount + Deduction 等价性检查 ──
    print(f"\n  ── Payment 等价性验证 ──")
    if 'Deduction' in deliv.columns:
        calc_payment = deliv['Net_Amount'] + deliv['Deduction']
        match = abs(deliv['Payment'] - calc_payment) < 0.01
        match_rate = match.mean() * 100
        print(f"  Payment == Net_Amount + Deduction 吻合率: {match_rate:.1f}%")
        if match_rate < 100:
            mismatches = deliv[~match]
            print(f"  [!]  不匹配的订单数: {len(mismatches)}")
            print(f"  不匹配示例:")
            print(mismatches[['Net_Amount', 'Deduction', 'Payment']].head(3).to_string())

        # Deduction 符号一致性检查
        neg_pct = (deliv['Deduction'] < 0).mean() * 100
        pos_pct = (deliv['Deduction'] > 0).mean() * 100
        zero_pct = (deliv['Deduction'] == 0).mean() * 100
        print(f"  Deduction 负值占比: {neg_pct:.1f}%, 正值: {pos_pct:.1f}%, 零: {zero_pct:.1f}%")
    else:
        print(f"  无 Deduction 列，跳过等价性验证")

    # ─── Payment 合理性筛查（规划约束1补充） ──────────────────
    print(f"\n  ── Payment 合理性筛查 ──")
    # (1) Net Amount > 0 但 Payment = 0
    suspicious_zero = deliv[(deliv['Net_Amount'] > 0) & (deliv['Payment'] == 0)]
    if len(suspicious_zero) > 0:
        print(f"  [!]  Net Amount>0 但 Payment=0: {len(suspicious_zero)} 条（可能未结算）")
    else:
        print(f"  ✓ Net Amount>0 的订单均有 Payment>0")

    # (2) Payment 为大幅负数但 Mode=Delivered
    neg_payment = deliv[deliv['Payment'] < -10]
    if len(neg_payment) > 0:
        print(f"  [!]  Payment < -10 的 Delivered 订单: {len(neg_payment)} 条（可能为退款订单误标记）")
    else:
        print(f"  ✓ 无异常负值 Payment")

    # (3) Payment 最小值/最大值
    print(f"  Payment 范围: [{deliv['Payment'].min():.2f}, {deliv['Payment'].max():.2f}]")

    return {
        'name': name,
        'n_delivered': n_delivered,
        'n_cancelled': n_cancelled,
        'n_returned': n_returned,
        'payment_tp_mean': method_pay.mean(),
        'payment_tp_std': method_pay.std(),
        'portal_tp_mean': method_portal.mean(),
        'portal_tp_std': method_portal.std(),
    }


# ─── 主流程 ─────────────────────────────────────────────────────

def main():
    print("="*60)
    print("  01_load_validate.py — 数据加载与清洗")
    print("="*60)

    all_delivered = []
    all_cancelled = []
    all_returned = []
    validation_results = []

    # 2.1: 逐渠道加载
    for sheet in CHANNEL_SHEETS:
        print(f"\n──  正在加载: {sheet}  ──")
        try:
            df = load_channel_sheet(sheet)
        except Exception as e:
            print(f"  [FAIL] 加载失败: {e}")
            continue

        if df.empty:
            print(f"  [!]  {sheet} 加载后为空，跳过")
            continue

        # 分流：Delivered / Cancelled / Returned
        delivered = df[df['Mode'] == 'Delivered'].copy()
        cancelled = df[df['Mode'] == 'Cancelled'].copy()
        returned = df[df['Mode'] == 'Returned'].copy() if 'Returned' in df['Mode'].values else pd.DataFrame()

        # 报告
        result = report_validation(df, sheet)
        if result:
            validation_results.append(result)

        # 2.1-5: Delivered 剔除 TP 或 Net Amount 为 NaN/0 的行
        if not delivered.empty:
            before = len(delivered)
            delivered = delivered.dropna(subset=['TP', 'Net_Amount'])
            delivered = delivered[(delivered['TP'] > 0) & (delivered['Net_Amount'] > 0)]
            after = len(delivered)
            if before != after:
                print(f"  过滤无效 TP/Net_Amount: {before} → {after}")
            all_delivered.append(delivered)

        all_cancelled.append(cancelled)
        if not returned.empty:
            all_returned.append(returned)

    # 2.3: 取消订单分析
    print(f"\n{'='*60}")
    print(f"  取消订单分析（规划2.3节）")
    print(f"{'='*60}")
    cancelled_total = pd.concat(all_cancelled, ignore_index=True) if all_cancelled else pd.DataFrame()
    if not cancelled_total.empty:
        for sheet in CHANNEL_SHEETS:
            ch_data = cancelled_total[cancelled_total['Channel'] == sheet]
            if ch_data.empty:
                continue
            penalty = ch_data['Portal_Payment'].sum()
            n_deliv = sum(r['n_delivered'] for r in validation_results if r['name'] == sheet)
            n_canc = len(ch_data)
            total_orders = n_deliv + n_canc
            cancel_rate = n_canc / total_orders * 100 if total_orders > 0 else 0
            print(f"  {sheet:35s} 取消率={cancel_rate:5.1f}%  "
                  f"({n_canc}/{total_orders}), 罚款总额={penalty:8.2f}")
    else:
        print("  无取消订单数据")

    # Returned 订单统计
    if all_returned:
        returned_total = pd.concat(all_returned, ignore_index=True)
        print(f"\n  ── 退货（Returned）订单统计（规划约束6）──")
        for sheet in CHANNEL_SHEETS:
            ch_data = returned_total[returned_total['Channel'] == sheet]
            if not ch_data.empty:
                refund = ch_data['Net_Amount'].sum() if 'Net_Amount' in ch_data.columns else 0
                print(f"  {sheet:35s} Returned={len(ch_data):3d}, 退款总额={refund:8.2f}")
    else:
        print(f"\n  无 Returned 订单记录")
        print(f"  [!]  数据源未包含退货记录，贡献毛利可能被系统性高估（约束6）")

    # 2.4: 合并并保存
    print(f"\n{'='*60}")
    print(f"  保存清洗后数据")
    print(f"{'='*60}")

    if all_delivered:
        df_delivered = pd.concat(all_delivered, ignore_index=True)

        # 样本不平衡检查（规划约束5）
        total = len(df_delivered)
        myntra_n = (df_delivered['Channel'] == 'Myntra').sum()
        myntra_pct = myntra_n / total * 100
        print(f"\n  Delivered 订单总数: {total}")
        print(f"  Myntra 占比: {myntra_n}/{total} = {myntra_pct:.1f}%")
        if myntra_pct > 50:
            print(f"  [!]  Myntra 占比 > 50%（{myntra_pct:.1f}%），全局汇总统计量丧失意义，禁止发布汇总统计量")

        # 检查小渠道（n < 10）
        ch_counts = df_delivered['Channel'].value_counts()
        small = ch_counts[ch_counts < 10]
        if not small.empty:
            print(f"  [!]  小样本渠道（n<10）:")
            for ch, n in small.items():
                print(f"     {ch}: n={n} — 结论不可泛化")

        out_path = os.path.join(OUT_DIR, 'delivered_orders.csv')
        df_delivered.to_csv(out_path, index=False)
        print(f"\n  [OK] Delivered 订单已保存: {out_path} ({len(df_delivered)} 条)")

    if not cancelled_total.empty:
        out_path = os.path.join(OUT_DIR, 'cancelled_orders.csv')
        cancelled_total.to_csv(out_path, index=False)
        print(f"  [OK] Cancelled 订单已保存: {out_path} ({len(cancelled_total)} 条)")

    if all_returned:
        df_returned = pd.concat(all_returned, ignore_index=True)
        out_path = os.path.join(OUT_DIR, 'returned_orders.csv')
        df_returned.to_csv(out_path, index=False)
        print(f"  [OK] Returned 订单已保存: {out_path} ({len(df_returned)} 条)")

    # ─── 汇总对比表（规划2.2节关键输出）────────────────────
    print(f"\n{'='*60}")
    print(f"  利润公式汇总对比表（验证门输出1）")
    print(f"{'='*60}")
    if validation_results:
        summary = pd.DataFrame(validation_results)
        summary.columns = ['渠道', 'Delivered', 'Cancelled', 'Returned',
                           'Payment-TP均值', 'Payment-TP标准差',
                           'Portal-TP均值', 'Portal-TP标准差']
        print(summary.to_string(index=False))

    print(f"\n{'='*60}")
    print(f"  01_load_validate.py 执行完毕")
    print(f"  下一步：审查验证报告，确认利润基准成立后运行")
    print(f"  02_feature_engineering.py")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
