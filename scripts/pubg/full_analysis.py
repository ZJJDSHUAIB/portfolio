# -*- coding: utf-8 -*-
"""
作品一 · PUBG 玩家行为与价值分层分析
=====================================
数据源:Kaggle PUBG Finish Placement Prediction 训练集(444万行玩家对局行为)
本脚本将 Jupyter 中探索验证过的分析成果固化,并输出作品所需的图表。

分析脉络:
  1. 读数据 + 列名中文化
  2. 清洗(过滤特殊模式/异常时长/异常距离)
  3. 聚焦四排第一人称(squad-fpp)
  4. 击杀数分布(发现幂律分布)
  5. 表现分布(名次均匀)
  6. 玩家分层:战斗维度(伤害) × 生存维度(名次)
  7. 分层验证(每类的核心特征)
  8. 名次=0 的异常审计(发现"落地成盒")
  9. 输出运营落地方案
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import json, os

# ========== 全局配置 ==========
SRC = "data/pubg/extracted/train_V2.csv"
OUT = "output/pubg"
os.makedirs(OUT, exist_ok=True)

# 图表统一风格
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def savefig(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] 保存图表: {name}")

# ========== 1. 读数据 ==========
print("=" * 60)
print("步骤1: 读入全量数据")
print("=" * 60)
df_all = pd.read_csv(SRC)
print(f"原始数据: {len(df_all):,} 行, {df_all.shape[1]} 列")

# ========== 2. 列名中文化 ==========
print("\n" + "=" * 60)
print("步骤2: 列名中文化")
print("=" * 60)
df_all = df_all.rename(columns={
    'Id': '玩家ID', 'groupId': '队伍ID', 'matchId': '对局ID',
    'assists': '助攻', 'boosts': '能量道具', 'damageDealt': '造成伤害',
    'DBNOs': '击倒数', 'headshotKills': '爆头击杀', 'heals': '治疗道具',
    'killPlace': '击杀排名', 'killPoints': '击杀分', 'kills': '击杀数',
    'killStreaks': '连杀数', 'longestKill': '最远击杀',
    'matchDuration': '对局时长(秒)', 'matchType': '游戏模式',
    'maxPlace': '最差名次', 'numGroups': '队伍数', 'rankPoints': '段位分',
    'revives': '救援数', 'rideDistance': '乘车距离', 'roadKills': '载具击杀',
    'swimDistance': '游泳距离', 'teamKills': '队友击杀',
    'vehicleDestroys': '摧毁载具', 'walkDistance': '步行距离',
    'weaponsAcquired': '捡武器数', 'winPoints': '胜点', 'winPlacePerc': '完赛名次'
})

# ========== 3. 清洗 ==========
print("\n" + "=" * 60)
print("步骤3: 数据清洗")
print("=" * 60)
标准模式 = ['solo', 'solo-fpp', 'duo', 'duo-fpp', 'squad', 'squad-fpp']
df_all = df_all[df_all['游戏模式'].isin(标准模式)]
df_all = df_all[(df_all['对局时长(秒)'] >= 30) & (df_all['对局时长(秒)'] <= 3600)]
总移动 = df_all['步行距离'] + df_all['乘车距离'] + df_all['游泳距离']
df_all = df_all[总移动 <= 100000]
print(f"清洗后: {len(df_all):,} 行 (保留 {len(df_all)/4446696*100:.1f}%)")

# ========== 4. 聚焦四排 ==========
print("\n" + "=" * 60)
print("步骤4: 聚焦四排第一人称(squad-fpp)")
print("=" * 60)
四排 = df_all[df_all['游戏模式'] == 'squad-fpp'].copy()
print(f"四排数据: {len(四排):,} 行, 占全量 {len(四排)/len(df_all):.1%}")
print("(选择理由: 四排是最主流模式, 玩家最多, 有代表性)")

# ========== 5. 击杀数分布 ==========
print("\n" + "=" * 60)
print("步骤5: 击杀数分布(发现幂律分布)")
print("=" * 60)
fig, ax = plt.subplots(figsize=(10, 6))
kill_dist = 四排['击杀数'].value_counts().sort_index()
ax.bar(kill_dist.index[:15], kill_dist.values[:15], color="#1f77b4")
ax.set_title("击杀数分布(PUBG 四排)")
ax.set_xlabel("击杀数")
ax.set_ylabel("玩家数")
savefig(fig, "01_kill_distribution.png")

零杀占比 = (四排['击杀数'] == 0).mean()
print(f"0 击杀玩家占比: {零杀占比:.1%}")
print("→ 超过一半玩家一局 0 杀, 呈典型幂律分布")

# ========== 6. 表现分布 ==========
print("\n" + "=" * 60)
print("步骤6: 完赛名次分布")
print("=" * 60)
print(四排['完赛名次'].describe().round(3))

# ========== 7. 玩家分层(最终模型) ==========
print("\n" + "=" * 60)
print("步骤7: 玩家价值分层(战斗×生存)")
print("=" * 60)
# 战斗维度: 造成伤害(投入/潜力)
# 生存维度: 完赛名次(存活/留存)
高伤害 = 四排['造成伤害'] >= 四排['造成伤害'].quantile(0.75)
零伤害 = 四排['造成伤害'] == 0
高名次 = 四排['完赛名次'] >= 0.5
低名次 = 四排['完赛名次'] < 0.3

四排['最终分层'] = '潜力型(成长中)'
四排.loc[高伤害 & 高名次, '最终分层'] = '核心高手(全能)'
四排.loc[高伤害 & 低名次, '最终分层'] = '战斗型(有天赋但存活差)'
四排.loc[零伤害 & 高名次, '最终分层'] = '生存型(苟活无输出)'
四排.loc[零伤害 & 低名次, '最终分层'] = '双弱型(流失风险)'

分层占比 = 四排['最终分层'].value_counts(normalize=True).round(3)
print("分层占比:")
print(分层占比)

# 分层占比图
fig, ax = plt.subplots(figsize=(9, 6))
colors = {"核心高手(全能)": "#2ca02c", "潜力型(成长中)": "#1f77b4",
           "战斗型(有天赋但存活差)": "#d62728", "生存型(苟活无输出)": "#ff7f0e",
           "双弱型(流失风险)": "#9467bd"}
order = ["核心高手(全能)", "潜力型(成长中)", "战斗型(有天赋但存活差)",
         "生存型(苟活无输出)", "双弱型(流失风险)"]
ax.bar(order, [分层占比.get(x, 0) for x in order],
       color=[colors[x] for x in order])
ax.set_title("玩家价值分层占比")
ax.set_xlabel("玩家分层")
ax.set_ylabel("占比")
ax.set_ylim(0, 0.65)
ax.tick_params(axis="x", rotation=20)
savefig(fig, "02_segment_share.png")

# ========== 8. 分层验证 ==========
print("\n" + "=" * 60)
print("步骤8: 分层验证(每类核心特征)")
print("=" * 60)
验证列 = ['造成伤害', '完赛名次', '步行距离', '击杀数', '捡武器数']
验证结果 = 四排.groupby('最终分层')[验证列].median().round(1)
print(验证结果)
验证结果.to_csv(os.path.join(OUT, "segment_validate.csv"), encoding="utf-8-sig")

# 分层特征对比图(雷达/柱状)
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ax, col in zip(axes, ['造成伤害', '步行距离', '完赛名次']):
    data = [四排[四排['最终分层'] == x][col].median() for x in order]
    ax.bar(order, data, color=[colors[x] for x in order])
    ax.set_title(f"各分层 {col} 中位数")
    ax.tick_params(axis="x", rotation=20)
fig.suptitle("玩家分层特征对比")
fig.tight_layout()
savefig(fig, "03_segment_features.png")

# ========== 9. 名次=0 异常审计 ==========
print("\n" + "=" * 60)
print("步骤9: 名次=0 玩家审计(发现'落地成盒')")
print("=" * 60)
零名次 = 四排[四排['完赛名次'] == 0]
print(f"名次=0 玩家: {len(零名次):,} 人 ({len(零名次)/len(四排):.2%})")
print(f"  平均步行距离: {零名次['步行距离'].mean():.0f} 米")
print(f"  平均对局时长: {零名次['对局时长(秒)'].mean():.0f} 秒")
print(f"  平均击杀: {零名次['击杀数'].mean():.1f}")
print("→ 步行45米=开局落地即死, 是'落地成盒'群体, 非异常数据")

# ========== 10. 运营落地方案 ==========
print("\n" + "=" * 60)
print("步骤10: 运营落地方案")
print("=" * 60)
# 用数据算出的关键数字支撑方案
双弱 = 四排[四排['最终分层'] == '双弱型(流失风险)']
生存 = 四排[四排['最终分层'] == '生存型(苟活无输出)']
战斗 = 四排[四排['最终分层'] == '战斗型(有天赋但存活差)']
核心 = 四排[四排['最终分层'] == '核心高手(全能)']

plan = [
    {
        "segment": "双弱型(流失风险)",
        "share": float(分层占比.get("双弱型(流失风险)", 0)),
        "problem": "落地成盒: 平均步行仅45米, 0伤害, 游戏体验差",
        "actions": [
            "新手保护匹配: 前几局安排 AI/人机, 给首次击杀的正反馈",
            "落地引导: 新手教学提示跳野外人少区域, 避免热门点被秒",
            "战斗教学: 靶场/训练场, 建立战斗自信",
            "匹配优化: 让落地成盒玩家匹配水平相近者"
        ]
    },
    {
        "segment": "生存型(苟活无输出)",
        "share": float(分层占比.get("生存型(苟活无输出)", 0)),
        "problem": f"在线时长高(名次{生存['完赛名次'].median():.2f})但几乎无输出(伤害{生存['造成伤害'].median():.0f})",
        "actions": [
            "激励参与战斗: 战斗任务、伤害成就奖励",
            "展示伤害统计: 让玩家看到自己的战斗贡献",
            "引导收集资源: 把'苟'转化为'积累'的成就感"
        ]
    },
    {
        "segment": "战斗型(有天赋但存活差)",
        "share": float(分层占比.get("战斗型(有天赋但存活差)", 0)),
        "problem": f"伤害高({战斗['造成伤害'].median():.0f})但存活差(名次{战斗['完赛名次'].median():.2f})",
        "actions": [
            "跑圈教学: 提示占点时机、毒圈推进节奏",
            "生存技巧引导: 让天赋转化为名次",
            "潜力识别: 标记为'高潜力玩家'重点培养"
        ]
    },
    {
        "segment": "潜力型(成长中)",
        "share": float(分层占比.get("潜力型(成长中)", 0)),
        "problem": "中坚主体, 1-3杀或中等伤害",
        "actions": [
            "常规活跃活动: 保持在线粘性",
            "成长激励: 段位晋升、累计击杀里程碑"
        ]
    },
    {
        "segment": "核心高手(全能)",
        "share": float(分层占比.get("核心高手(全能)", 0)),
        "problem": "高伤害高存活, 顶尖玩家",
        "actions": [
            "竞技激励: 段位/天梯、大神身份标识",
            "内容产出: 邀请做教学/直播/攻略",
            "社区 KOL 培养"
        ]
    },
]

with open(os.path.join(OUT, "ops_plan.json"), "w", encoding="utf-8") as f:
    json.dump({"segments": plan}, f, ensure_ascii=False, indent=2)
print("运营方案已输出: output/pubg/ops_plan.json")

print("\n" + "=" * 60)
print("全部完成! 输出在 output/pubg/ 目录")
print("=" * 60)
