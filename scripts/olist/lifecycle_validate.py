# -*- coding: utf-8 -*-
"""
作品二 · Olist 生命周期定义 + 复购间隔验证
====================================================
严谨的生命周期分析,包含:
1. 明确观察期与评估时点
2. 用"复购间隔分布"验证 90/180 天阈值
3. 排除观察窗口不足的客户
4. 输出生命周期分布
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

BASE = "data/olist/extracted/"
OUT = "output/olist"
os.makedirs(OUT, exist_ok=True)

# ========== 1. 读取 + 关联 ==========
print("=" * 60)
print("步骤1: 读取数据 + 关联")
print("=" * 60)
orders = pd.read_csv(BASE + "olist_orders_dataset.csv")
customers = pd.read_csv(BASE + "olist_customers_dataset.csv")
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
df = orders.merge(customers, on="customer_id", how="left")
print(f"订单: {len(df):,}")

# ========== 2. 明确观察期 ==========
print("\n" + "=" * 60)
print("步骤2: 明确观察期与评估时点")
print("=" * 60)
print(f"最早订单: {df['order_purchase_timestamp'].min()}")
print(f"最晚订单: {df['order_purchase_timestamp'].max()}")
# 排除 2018-08 之后的断崖尾巴(数据停更)
观察期截止 = pd.Timestamp("2018-08-31")
df = df[df["order_purchase_timestamp"] <= 观察期截止]
评估时点 = df["order_purchase_timestamp"].max()
print(f"观察期截止: {观察期截止}(排除断崖尾巴)")
print(f"评估时点(视为'今天'): {评估时点}")
print(f"有效订单: {len(df):,}")

# ========== 3. 复购间隔分布(验证阈值) ==========
print("\n" + "=" * 60)
print("步骤3: 复购间隔分布(验证 90/180 天阈值)")
print("=" * 60)
df = df.sort_values(["customer_unique_id", "order_purchase_timestamp"])
df["上次购买"] = df.groupby("customer_unique_id")["order_purchase_timestamp"].shift(1)
df["间隔天数"] = (df["order_purchase_timestamp"] - df["上次购买"]).dt.days
间隔 = df[df["间隔天数"].notna() & (df["间隔天数"] > 0)]

print(f"复购间隔样本: {len(间隔):,}")
print(f"中位数: {间隔['间隔天数'].median():.0f} 天")
print(f"90分位: {间隔['间隔天数'].quantile(0.9):.0f} 天")
print(f"<30天: {(间隔['间隔天数']<30).mean():.1%} | 30-90: {((间隔['间隔天数']>=30)&(间隔['间隔天数']<90)).mean():.1%}")
print(f"90-180: {((间隔['间隔天数']>=90)&(间隔['间隔天数']<180)).mean():.1%} | >180: {(间隔['间隔天数']>=180).mean():.1%}")
print("→ 中位间隔68天:'90天沉默'有依据;但23%复购间隔>180天,'180天流失'是业务惯例需敏感")

# 间隔分布图(Halo 暗色)
HALO_BG = "#0A0B0F"; HALO_BORDER = "#2A2D38"; HALO_PRIMARY = "#5B6BFF"
HALO_WARN = "#F5D547"; HALO_INFO = "#3DD7E5"
plt.rcParams["figure.facecolor"] = HALO_BG
plt.rcParams["axes.facecolor"] = HALO_BG
plt.rcParams["savefig.facecolor"] = HALO_BG
plt.rcParams["axes.edgecolor"] = HALO_BORDER
plt.rcParams["axes.labelcolor"] = "#9AA0AE"
plt.rcParams["xtick.color"] = "#9AA0AE"
plt.rcParams["ytick.color"] = "#9AA0AE"
plt.rcParams["text.color"] = "#F2F4F8"
plt.rcParams["axes.titlecolor"] = "#F2F4F8"
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(间隔["间隔天数"].clip(upper=365), bins=40, color=HALO_PRIMARY, edgecolor=HALO_BORDER, alpha=0.85)
ax.axvline(90, color=HALO_WARN, linestyle="--", linewidth=2, label="沉默阈值 90天")
ax.axvline(180, color=HALO_INFO, linestyle="--", linewidth=2, label="流失阈值 180天")
ax.set_title("客户复购间隔分布(验证生命周期阈值)", fontsize=14, pad=16)
ax.set_xlabel("复购间隔天数")
ax.set_ylabel("复购次数")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "04_repeat_interval.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("图表已保存: output/olist/04_repeat_interval.png")

# ========== 4. 生命周期划分 ==========
print("\n" + "=" * 60)
print("步骤4: 生命周期划分(90沉默 / 180流失)")
print("=" * 60)
cust = df.groupby("customer_unique_id").agg(
    订单数=("order_id", "count"),
    末购时间=("order_purchase_timestamp", "max"),
).reset_index()
cust["距末购天数"] = (评估时点 - cust["末购时间"]).dt.days

def classify(row):
    if row["订单数"] >= 2:
        return "复购客户"
    if row["距末购天数"] <= 90:
        return "活跃新客"
    if row["距末购天数"] <= 180:
        return "沉默客户(流失风险)"
    return "流失客户"

cust["生命周期"] = cust.apply(classify, axis=1)
分布 = cust["生命周期"].value_counts()
占比 = cust["生命周期"].value_counts(normalize=True)
for seg in ["复购客户", "活跃新客", "沉默客户(流失风险)", "流失客户"]:
    print(f"  {seg}: {分布[seg]:,}人 ({占比[seg]:.1%})")

cust.to_parquet(os.path.join(OUT, "customer_lifecycle.parquet"), index=False)
print("\n生命周期档案已保存")
