# -*- coding: utf-8 -*-
"""
重新生成暗底图表(Halo 设计系统配色)
生成作品一需要的 3 张暗色图表,匹配 Halo 暗色前端。
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

OUT = "output/pubg"
os.makedirs(OUT, exist_ok=True)

# ========== Halo 配色 ==========
HALO_BG      = "#0A0B0F"   # background
HALO_SURFACE = "#14151C"   # surface
HALO_ELEV    = "#1E2029"   # elevated
HALO_BORDER  = "#2A2D38"   # border
HALO_PRIMARY = "#5B6BFF"   # primary 靛蓝
HALO_INFO    = "#3DD7E5"   # info 青
HALO_WARN    = "#F5D547"   # warning 琥珀
HALO_SUCCESS = "#2BE08C"   # success 绿
HALO_ERROR   = "#FF3A5C"   # error 红
HALO_TEXT    = "#F2F4F8"   # on-surface
HALO_TEXT2   = "#9AA0AE"   # muted

# ========== 全局暗色风格 ==========
plt.rcParams["figure.facecolor"] = HALO_BG
plt.rcParams["axes.facecolor"]   = HALO_BG
plt.rcParams["savefig.facecolor"]= HALO_BG
plt.rcParams["axes.edgecolor"]   = HALO_BORDER
plt.rcParams["axes.labelcolor"]  = HALO_TEXT2
plt.rcParams["xtick.color"]      = HALO_TEXT2
plt.rcParams["ytick.color"]      = HALO_TEXT2
plt.rcParams["text.color"]       = HALO_TEXT
plt.rcParams["axes.titlecolor"]  = HALO_TEXT
plt.rcParams["grid.color"]       = HALO_BORDER
plt.rcParams["grid.alpha"]       = 0.4
plt.rcParams["font.family"]      = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"]       = 150

def savefig(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {name}")

# ========== 读数据并清洗 ==========
print("读取数据...")
SRC = "data/pubg/extracted/train_V2.csv"
df_all = pd.read_csv(SRC)
df_all = df_all.rename(columns={
    'damageDealt': '伤害', 'kills': '击杀', 'walkDistance': '步行',
    'winPlacePerc': '名次', 'matchType': '模式', 'matchDuration': '时长',
    'weaponsAcquired': '捡武器', 'assists': '助攻', 'boosts': '能量',
    'rideDistance': '乘车距离', 'swimDistance': '游泳距离',
})
标准 = ['solo', 'solo-fpp', 'duo', 'duo-fpp', 'squad', 'squad-fpp']
df_all = df_all[df_all['模式'].isin(标准)]
df_all = df_all[(df_all['时长'] >= 30) & (df_all['时长'] <= 3600)]
总移 = df_all['步行'] + df_all['乘车距离'] + df_all['游泳距离']
df_all = df_all[总移 <= 100000]
四排 = df_all[df_all['模式'] == 'squad-fpp'].copy()
print(f"四排数据: {len(四排):,} 行")

# ========== 图1: 击杀数分布(幂律) ==========
print("生成图1: 击杀数分布...")
fig, ax = plt.subplots(figsize=(10, 5))
kd = 四排['击杀'].value_counts().sort_index()
x = kd.index[:15].values
y = kd.values[:15]
colors = [HALO_PRIMARY if v == 0 else HALO_ELEV for v in x]
ax.bar(x.astype(str), y, color=colors, edgecolor=HALO_BORDER, width=0.7)
ax.set_title("击杀数分布(PUBG 四排)", fontsize=14, pad=16)
ax.set_xlabel("击杀数")
ax.set_ylabel("玩家数")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
零杀 = (四排['击杀'] == 0).mean()
ax.text(0.98, 0.95, f"0 击杀占比 {零杀:.1%}", transform=ax.transAxes,
        ha="right", va="top", fontsize=13, color=HALO_WARN, fontweight="bold")
fig.tight_layout()
savefig(fig, "01_kill_distribution_dark.png")

# ========== 图2: 玩家分层占比 ==========
print("生成图2: 玩家分层占比...")
高伤 = 四排['伤害'] >= 四排['伤害'].quantile(0.75)
零伤 = 四排['伤害'] == 0
高名 = 四排['名次'] >= 0.5
低名 = 四排['名次'] < 0.3
四排['分层'] = '潜力型(成长中)'
四排.loc[高伤 & 高名, '分层'] = '核心高手(全能)'
四排.loc[高伤 & 低名, '分层'] = '战斗型(有天赋但存活差)'
四排.loc[零伤 & 高名, '分层'] = '生存型(苟活无输出)'
四排.loc[零伤 & 低名, '分层'] = '双弱型(流失风险)'
share = 四排['分层'].value_counts(normalize=True)

order = ['核心高手(全能)', '潜力型(成长中)', '战斗型(有天赋但存活差)',
         '生存型(苟活无输出)', '双弱型(流失风险)']
seg_colors = {
    '核心高手(全能)': HALO_SUCCESS,
    '潜力型(成长中)': HALO_PRIMARY,
    '战斗型(有天赋但存活差)': HALO_ERROR,
    '生存型(苟活无输出)': HALO_INFO,
    '双弱型(流失风险)': HALO_WARN,
}
fig, ax = plt.subplots(figsize=(10, 5))
vals = [share.get(o, 0) for o in order]
bars = ax.bar(order, vals, color=[seg_colors[o] for o in order],
              edgecolor=HALO_BORDER, width=0.6)
ax.set_title("玩家价值分层占比", fontsize=14, pad=16)
ax.set_xlabel("玩家分层")
ax.set_ylabel("占比")
ax.set_ylim(0, 0.65)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"{v:.1%}", ha="center", va="bottom", fontsize=12, color=HALO_TEXT2)
ax.tick_params(axis="x", labelrotation=15)
fig.tight_layout()
savefig(fig, "02_segment_share_dark.png")

# ========== 图3: 分层特征对比 ==========
print("生成图3: 分层特征对比...")
验证列 = ['伤害', '名次', '步行', '击杀', '捡武器']
med = 四排.groupby('分层')[验证列].median()
feat_cols = ['伤害', '步行', '名次']
feat_colors = [HALO_PRIMARY, HALO_INFO, HALO_WARN]
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharey=False)
for ax, col, c in zip(axes, feat_cols, feat_colors):
    data = [med.loc[o, col] for o in order]
    bars = ax.bar(order, data, color=c, edgecolor=HALO_BORDER, width=0.6)
    ax.set_title(f"各分层 {col} 中位数", fontsize=12, pad=12)
    ax.tick_params(axis="x", labelrotation=30, labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
fig.suptitle("玩家分层特征对比", fontsize=14, y=1.02)
fig.tight_layout()
savefig(fig, "03_segment_features_dark.png")

print("全部暗色图表生成完成")
