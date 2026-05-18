import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split, RepeatedKFold, GridSearchCV
from sklearn.metrics import mean_squared_error

# 加载数据（假设df_regression_dummy已经存在）
# 这里使用原始数据，不进行对数变换

# 使用原始利润作为目标变量
y_original = df_regression_dummy['Profit'].copy()  # 使用原始利润，而不是Profit_smoothed
X_original = df_regression_dummy.drop(columns=['Profit_smoothed', 'Profit', 'Date']).copy()

print("=== 取消对数变换的随机森林模型 ===")
print(f"X形状: {X_original.shape}")
print(f"y形状: {y_original.shape}")
print(f"目标变量统计: 均值={y_original.mean():.2f}, 标准差={y_original.std():.2f}")
print(f"利润范围: [{y_original.min():.2f}, {y_original.max():.2f}]")
print(f"负利润数量: {(y_original < 0).sum()} ({((y_original < 0).sum()/len(y_original))*100:.2f}%)")
print(f"零利润数量: {(y_original == 0).sum()} ({((y_original == 0).sum()/len(y_original))*100:.2f}%)")
print(f"正利润数量: {(y_original > 0).sum()} ({((y_original > 0).sum()/len(y_original))*100:.2f}%)")

# 绘制原始利润分布
plt.figure(figsize=(10, 6))
plt.hist(y_original, bins=50, edgecolor='black', alpha=0.7)
plt.title('原始利润分布（取消对数变换）')
plt.xlabel('利润')
plt.ylabel('频数')
plt.grid(True, alpha=0.3)
plt.show()

# 转换为numpy数组用于模型训练
X_train_original = X_original.values
Y_train_original = y_original.values

print("\n=== 随机森林模型训练（使用原始利润） ===")

# 初步选择 max_features
max_features = [.6, .65, .7, .75, .8, .85, .9, .95]
test_scores = list()

for max_feature in max_features:
    clf = RandomForestRegressor(n_estimators=100, max_features=max_feature,
                               random_state=42)
    test_score = np.sqrt(-cross_val_score(clf, X_train_original, Y_train_original, cv=3,
                                         scoring='neg_mean_squared_error'))
    test_scores.append(np.mean(test_score))

plt.figure(figsize=(8, 5))
plt.plot(max_features, test_scores, marker='o')
plt.title("Max Features vs CV Error (原始利润)")
plt.xlabel("Max Features")
plt.ylabel("RMSE")
plt.grid(True, alpha=0.3)
plt.show()

best_idx = np.argmin(test_scores)
best_max_features = max_features[best_idx]
print(f"初步最佳 max_features: {best_max_features}")

# 细化 max_features 搜索
max_features_refined = [best_max_features-0.02, best_max_features-0.01, best_max_features, 
                       best_max_features+0.01, best_max_features+0.02]
max_features_refined = [round(mf, 2) for mf in max_features_refined if 0 < mf < 1]

test_scores_refined = list()
for max_feature in max_features_refined:
    clf = RandomForestRegressor(n_estimators=100, max_features=max_feature,
                               random_state=42)
    test_score = np.sqrt(-cross_val_score(clf, X_train_original, Y_train_original, cv=3,
                                         scoring='neg_mean_squared_error'))
    test_scores_refined.append(np.mean(test_score))

if len(max_features_refined) > 1:
    plt.figure(figsize=(8, 5))
    plt.plot(max_features_refined, test_scores_refined, marker='o')
    plt.title("细化 Max Features vs CV Error (原始利润)")
    plt.xlabel("Max Features")
    plt.ylabel("RMSE")
    plt.grid(True, alpha=0.3)
    plt.show()

    best_idx_refined = np.argmin(test_scores_refined)
    best_max_features_refined = max_features_refined[best_idx_refined]
    print(f"细化后最佳 max_features: {best_max_features_refined}")
else:
    best_max_features_refined = best_max_features

# 调整 min_samples_leaf
X_tr, X_val, y_tr, y_val = train_test_split(X_train_original, Y_train_original, test_size=0.2, random_state=42)

leaf_candidates = [1, 2, 3, 5, 10, 20, 50]
val_errors = []
train_errors = []

print("\n=== 调整 min_samples_leaf ===")
for leaf in leaf_candidates:
    rf = RandomForestRegressor(n_estimators=100, max_features=best_max_features_refined,
                               min_samples_leaf=leaf, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    train_rmse = np.sqrt(mean_squared_error(y_tr, rf.predict(X_tr)))
    val_rmse = np.sqrt(mean_squared_error(y_val, rf.predict(X_val)))
    train_errors.append(train_rmse)
    val_errors.append(val_rmse)
    print(f"leaf={leaf:2d} | train RMSE={train_rmse:.2f} | val RMSE={val_rmse:.2f}")

best_leaf = leaf_candidates[np.argmin(val_errors)]
print(f"\n最佳 min_samples_leaf = {best_leaf}")

# 训练最终模型
best_rf = RandomForestRegressor(n_estimators=100, max_features=best_max_features_refined,
                                min_samples_leaf=best_leaf, random_state=42, n_jobs=-1)
best_rf.fit(X_tr, y_tr)
final_train_rmse = np.sqrt(mean_squared_error(y_tr, best_rf.predict(X_tr)))
final_val_rmse = np.sqrt(mean_squared_error(y_val, best_rf.predict(X_val)))
print(f"\n最终模型性能:")
print(f"训练集 RMSE: {final_train_rmse:.2f}")
print(f"验证集 RMSE: {final_val_rmse:.2f}")

if final_val_rmse > final_train_rmse * 1.1:
    print("存在过拟合，可继续增大 leaf 或减少 max_features")
else:
    print("泛化良好")

# 5折交叉验证
scores = cross_val_score(best_rf, X_train_original, Y_train_original, cv=5,
                         scoring='neg_mean_squared_error', n_jobs=-1)
rmse_cv = np.sqrt(-scores.mean())
print(f"\n5折交叉验证 RMSE: {rmse_cv:.2f}")

# 特征重要性分析
print("\n=== 特征重要性分析（原始利润） ===")
best_rf.fit(X_train_original, Y_train_original)
importances = pd.Series(best_rf.feature_importances_, index=X_original.columns).sort_values(ascending=False)

print("特征重要性排序:")
for i, (feature, importance) in enumerate(importances.items()):
    print(f"{i+1:2d}. {feature:20s}: {importance:.6f}")

# 绘制特征重要性条形图
plt.figure(figsize=(12, 8))
importances.plot(kind='bar')
plt.title('特征重要性（原始利润）')
plt.xlabel('特征')
plt.ylabel('重要性')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.grid(True, alpha=0.3, axis='y')
plt.show()

# 绘制前7个重要特征的散点图
important_features = importances.head(7).index.tolist()
print(f"\n前7个重要特征: {important_features}")

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i, feature in enumerate(important_features[:6]):
    axes[i].scatter(X_original[feature], y_original, alpha=0.3, s=10)
    axes[i].set_xlabel(feature)
    axes[i].set_ylabel('Profit')
    axes[i].set_title(f'{feature} vs Profit')
    axes[i].grid(True, alpha=0.3)

# 隐藏多余的子图
for i in range(len(important_features[:6]), 6):
    axes[i].axis('off')

plt.tight_layout()
plt.show()

# 绘制特征相关性热力图
print("\n=== 特征相关性热力图 ===")
numeric_features = X_original.select_dtypes(include=[np.number]).columns
correlation_matrix = X_original[numeric_features].corr()

plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, 
            annot=True, 
            fmt='.2f', 
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8})
plt.title('特征间相关性热力图（原始数据）', fontsize=16)
plt.tight_layout()
plt.show()

# 打印相关性最高的特征对
print("相关性最高的特征对：")
corr_pairs = correlation_matrix.unstack().sort_values(ascending=False)
corr_pairs = corr_pairs[corr_pairs < 0.99]  # 去除自相关
print(corr_pairs.head(10))

print("\n=== 模型总结 ===")
print(f"1. 使用原始利润作为目标变量（未进行对数变换）")
print(f"2. 最佳参数: max_features={best_max_features_refined}, min_samples_leaf={best_leaf}")
print(f"3. 模型性能: 5折CV RMSE = {rmse_cv:.2f}")
print(f"4. 最重要的特征: {importances.index[0]} (重要性: {importances.iloc[0]:.4f})")
print(f"5. 前5个重要特征占总重要性的: {importances.head(5).sum()*100:.1f}%")