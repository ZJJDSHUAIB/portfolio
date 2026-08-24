# -*- coding: utf-8 -*-
"""
作品一 · PUBG 分层阈值敏感性验证
====================================================
验证:改变"高伤害"阈值(P60/P75/P90),5 类玩家比例是否稳定。
如果比例随阈值剧烈变化 → 分层不稳定,结论不可靠。
如果比例相对稳定 → 分层是稳健的规则模型。
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUT = "output/pubg"
os.makedirs(OUT, exist_ok=True)

# ========== 读取 + 清洗 ==========
print("读取数据...")
SRC = "data/pubg/extracted/train_V2.csv"
df_all = pd.read_csv(SRC)
df_all = df_all.rename(columns={
    'damageDealt': '伤害', 'kills': '击杀', 'walkDistance': '步行',
    'winPlacePerc': '名次', 'matchType': '模式', 'matchDuration': '时长',
    'weaponsAcquired': '捡武器',
    'rideDistance': '乘车距离', 'swimDistance': '游泳距离',
})
标准 = ['solo', 'solo-fpp', 'duo', 'duo-fpp', 'squad', 'squad-fpp']
df_all = df_all[df_all['模式'].isin(标准)]
df_all = df_all[(df_all['时长'] >= 30) & (df_all['时长'] <= 3600)]
总移 = df_all['步行'] + df_all['乘车距离'] + df_all['游泳距离']
df_all = df_all[总移 <= 100000]
四排 = df_all[df_all['模式'] == 'squad-fpp'].copy()
print(f"四排数据: {len(四排):,} 行")

# ========== 敏感性验证 ==========
print("\n" + "=" * 60)
print("阈值敏感性验证:改变'高伤害'阈值")
print("=" * 60)

结果 = {}
for q in [0.6, 0.75, 0.9]:
    高伤害 = 四排['伤害'] >= 四排['伤害'].quantile(q)
    零伤害 = 四排['伤害'] == 0
    高名次 = 四排['名次'] >= 0.5
    低名次 = 四排['名次'] < 0.3

    四排['分层'] = '潜力型(成长中)'
    四排.loc[高伤害 & 高名次, '分层'] = '核心高手(全能)'
    四排.loc[高伤害 & 低名次, '分层'] = '战斗型(有天赋但存活差)'
    四排.loc[零伤害 & 高名次, '分层'] = '生存型(苟活无输出)'
    四排.loc[零伤害 & 低名次, '分层'] = '双弱型(流失风险)'

    share = 四排['分层'].value_counts(normalize=True).round(3)
    结果[f"P{int(q*100)}"] = share
    print(f"\n--- 高伤害阈值 = P{int(q*100)} ---")
    print(share)

# 汇总对比表
对比 = pd.DataFrame(结果).T
对比['核心+战斗合计'] = 对比.get('核心高手(全能)', 0) + 对比.get('战斗型(有天赋但存活差)', 0)
print("\n" + "=" * 60)
print("阈值敏感性对比汇总")
print("=" * 60)
print(对比.round(3))
print("\n判断:若各阈值下分层占比相对稳定 → 分层稳健")

# 保存
对比.to_csv(os.path.join(OUT, "sensitivity_summary.csv"), encoding="utf-8-sig")

# ========== 图表(Halo 暗色) ==========
HALO_BG = "#0A0B0F"; HALO_BORDER = "#2A2D38"
HALO_PRIMARY = "#5B6BFF"; HALO_INFO = "#3DD7E5"; HALO_WARN = "#F5D547"
HALO_SUCCESS = "#2BE08C"; HALO_ERROR = "#FF3A5C"
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

segs = ["核心高手(全能)", "潜力型(成长中)", "战斗型(有天赋但存活差)", "生存型(苟活无输出)", "双弱型(流失风险)"]
colors = [HALO_SUCCESS, HALO_PRIMARY, HALO_ERROR, HALO_INFO, HALO_WARN]
qs = ["P60", "P75", "P90"]
x = np.arange(len(qs))
width = 0.15

fig, ax = plt.subplots(figsize=(11, 5.5))
for i, seg in enumerate(segs):
    vals = [对比.loc[q, seg] if seg in 对比.columns else 0 for q in qs]
    ax.bar(x + i * width - (len(segs)-1)*width/2, vals, width, color=colors[i], edgecolor=HALO_BORDER, label=seg)
ax.set_title("玩家分层阈值敏感性验证(高伤害 P60/P75/P90)", fontsize=14, pad=16)
ax.set_xticks(x)
ax.set_xticklabels(qs)
ax.set_ylabel("占比")
ax.set_ylim(0, 0.7)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, ncol=3, fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "04_sensitivity.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("\n图表已保存: output/pubg/04_sensitivity.png")
