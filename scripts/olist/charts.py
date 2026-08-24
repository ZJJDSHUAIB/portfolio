# -*- coding: utf-8 -*-
"""
作品二 · Olist 图表(Halo 暗色)
生成 3 张图:消费分层 / 复购对比 / 订单数分布
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUT = "output/olist"
os.makedirs(OUT, exist_ok=True)

# Halo 配色
HALO_BG      = "#0A0B0F"
HALO_BORDER  = "#2A2D38"
HALO_PRIMARY = "#5B6BFF"
HALO_INFO    = "#3DD7E5"
HALO_WARN    = "#F5D547"
HALO_SUCCESS = "#2BE08C"
HALO_ERROR   = "#FF3A5C"
HALO_TEXT2   = "#9AA0AE"

plt.rcParams["figure.facecolor"] = HALO_BG
plt.rcParams["axes.facecolor"]   = HALO_BG
plt.rcParams["savefig.facecolor"]= HALO_BG
plt.rcParams["axes.edgecolor"]   = HALO_BORDER
plt.rcParams["axes.labelcolor"]  = HALO_TEXT2
plt.rcParams["xtick.color"]      = HALO_TEXT2
plt.rcParams["ytick.color"]      = HALO_TEXT2
plt.rcParams["text.color"]       = "#F2F4F8"
plt.rcParams["axes.titlecolor"]  = "#F2F4F8"
plt.rcParams["grid.color"]       = HALO_BORDER
plt.rcParams["grid.alpha"]       = 0.4
plt.rcParams["font.family"]      = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

def savefig(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {name}")

客户汇总 = pd.read_parquet("output/olist/customer_summary.parquet")

# ========== 图1: 订单数分布(长尾) ==========
fig, ax = plt.subplots(figsize=(10, 5))
od = 客户汇总["订单数"].value_counts().sort_index()
x = od.index[:10]
y = od.values[:10]
colors = [HALO_PRIMARY if v == 1 else "#1E2029" for v in x]
ax.bar(x.astype(str), y, color=colors, edgecolor=HALO_BORDER, width=0.7)
ax.set_title("客户订单数分布", fontsize=14, pad=16)
ax.set_xlabel("订单数")
ax.set_ylabel("客户数")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
单次占比 = (客户汇总["订单数"] == 1).mean()
ax.text(0.98, 0.95, f"只买1单占 {单次占比:.1%}", transform=ax.transAxes,
        ha="right", va="top", fontsize=13, color=HALO_WARN, fontweight="bold")
fig.tight_layout()
savefig(fig, "01_order_count.png")

# ========== 图2: 消费 4 档分层 ==========
客户汇总["价值档"] = pd.qcut(客户汇总["总消费"], 4, labels=["低", "中低", "中高", "高"])
order = ["低", "中低", "中高", "高"]
g = 客户汇总.groupby("价值档", observed=True).agg(
    平均消费=("总消费", "mean"),
    平均订单=("订单数", "mean"),
)
fig, ax = plt.subplots(figsize=(9, 5))
colors2 = [HALO_ERROR, HALO_WARN, HALO_INFO, HALO_SUCCESS]
vals = [g.loc[o, "平均消费"] for o in order]
bars = ax.bar(order, vals, color=colors2, edgecolor=HALO_BORDER, width=0.6)
ax.set_title("消费分位数 4 档分层(平均消费)", fontsize=14, pad=16)
ax.set_ylabel("平均消费 (R$)")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f"{v:.0f}", ha="center", va="bottom", fontsize=11, color=HALO_TEXT2)
fig.tight_layout()
savefig(fig, "02_value_tiers.png")

# ========== 图3: 复购 vs 单次客户 ==========
复购均值 = 客户汇总[客户汇总["订单数"] >= 2]["总消费"].mean()
单次均值 = 客户汇总[客户汇总["订单数"] == 1]["总消费"].mean()
fig, ax = plt.subplots(figsize=(8, 5))
labels = ["复购客户\n(下单≥2次)", "单次客户\n(仅下1单)"]
vals = [复购均值, 单次均值]
colors3 = [HALO_SUCCESS, HALO_PRIMARY]
bars = ax.bar(labels, vals, color=colors3, edgecolor=HALO_BORDER, width=0.5)
ax.set_title("复购 vs 单次客户平均消费", fontsize=14, pad=16)
ax.set_ylabel("平均消费 (R$)")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f"{v:.0f}", ha="center", va="bottom", fontsize=13, color=HALO_TEXT2)
ax.text(0.5, max(vals) + 25, f"复购价值 x{复购均值/单次均值:.2f}",
        ha="center", fontsize=14, color=HALO_WARN, fontweight="bold")
fig.tight_layout()
savefig(fig, "03_repeat_vs_once.png")

print("作品二图表全部生成完成")
