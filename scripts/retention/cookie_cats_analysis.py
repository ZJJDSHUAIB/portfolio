# -*- coding: utf-8 -*-
"""
作品:用户生命周期与留存分析(Cookie Cats)
============================================
数据源:Cookie Cats 移动游戏 AB 测试数据(9 万用户)
核心问题:关卡"门"位置(gate_30 vs gate_40)如何影响留存?
分析:
1. 整体 D1/D7 留存率
2. AB 组(gate 位置)留存差异 + 显著性检验
3. 行为(游戏局数)与留存的关系
4. 运营落地方案
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

SRC = "data/cookie_cats/Cookie_Cats_cleaned_v01.csv"
OUT = "output/retention"
os.makedirs(OUT, exist_ok=True)

# ========== 暗色风格 ==========
HALO_BG="#0A0B0F"; HALO_BORDER="#2A2D38"; HALO_PRIMARY="#5B6BFF"
HALO_INFO="#3DD7E5"; HALO_WARN="#F5D547"; HALO_SUCCESS="#2BE08C"; HALO_ERROR="#FF3A5C"
plt.rcParams["figure.facecolor"]=HALO_BG; plt.rcParams["axes.facecolor"]=HALO_BG
plt.rcParams["savefig.facecolor"]=HALO_BG; plt.rcParams["axes.edgecolor"]=HALO_BORDER
plt.rcParams["axes.labelcolor"]="#9AA0AE"; plt.rcParams["xtick.color"]="#9AA0AE"
plt.rcParams["ytick.color"]="#9AA0AE"; plt.rcParams["text.color"]="#F2F4F8"
plt.rcParams["axes.titlecolor"]="#F2F4F8"; plt.rcParams["grid.color"]=HALO_BORDER
plt.rcParams["grid.alpha"]=0.4
plt.rcParams["font.family"]=["Microsoft YaHei","SimHei","sans-serif"]
plt.rcParams["axes.unicode_minus"]=False

def savefig(fig,name):
    fig.savefig(os.path.join(OUT,name),dpi=150,bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {name}")

print("="*60)
print("用户生命周期与留存分析(Cookie Cats)")
print("="*60)

df = pd.read_csv(SRC)
print(f"总用户: {len(df):,}")

# ========== 1. 整体留存 ==========
print("\n"+"="*60)
print("步骤1: 整体 D1/D7 留存率")
print("="*60)
print(f"D1(次日)留存率: {df['retention_1'].mean():.2%}")
print(f"D7(7日)留存率: {df['retention_7'].mean():.2%}")
print(f"D7/D1 = {df['retention_7'].mean()/df['retention_1'].mean():.2f}(7日留存占次日的比例)")

# ========== 2. AB 组对比 ==========
print("\n"+"="*60)
print("步骤2: AB 组(gate位置)留存差异")
print("="*60)
g30=df[df['version']=='gate_30']; g40=df[df['version']=='gate_40']
print(f"gate_30: {len(g30):,}人 | gate_40: {len(g40):,}人")
print(f"D1:  gate_30={g30['retention_1'].mean():.2%} vs gate_40={g40['retention_1'].mean():.2%}")
print(f"D7:  gate_30={g30['retention_7'].mean():.2%} vs gate_40={g40['retention_7'].mean():.2%}")
for col in ['retention_1','retention_7']:
    t=pd.crosstab(df['version'],df[col])
    chi2,p,_,_=stats.chi2_contingency(t)
    print(f"{col}: p={p:.4f} {'显著' if p<0.05 else '不显著'}")

# AB 对比图
fig,ax=plt.subplots(figsize=(8,5))
labels=['gate_30\n(30关放门)','gate_40\n(40关放门)']
for i,(g,col,color) in enumerate([(g30,'retention_1',HALO_PRIMARY),(g40,'retention_1',HALO_WARN),(g30,'retention_7',HALO_INFO),(g40,'retention_7',HALO_ERROR)]):
    pass
d1=[g30['retention_1'].mean(),g40['retention_1'].mean()]
d7=[g30['retention_7'].mean(),g40['retention_7'].mean()]
x=np.arange(2); w=0.3
b1=ax.bar(x-w/2,d1,w,label='D1 次日留存',color=HALO_PRIMARY,edgecolor=HALO_BORDER)
b2=ax.bar(x+w/2,d7,w,label='D7 7日留存',color=HALO_INFO,edgecolor=HALO_BORDER)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel('留存率'); ax.set_ylim(0,0.55)
ax.set_title('gate 位置对留存的影响(AB 测试)',fontsize=14,pad=16)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.legend(frameon=False)
for bars in [b1,b2]:
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.01,f'{bar.get_height():.1%}',ha='center',va='bottom',fontsize=11)
fig.tight_layout(); savefig(fig,'01_ab_retention.png')

# ========== 3. 行为与留存 ==========
print("\n"+"="*60)
print("步骤3: 游戏局数行为与留存关系")
print("="*60)
df['局数档']=pd.cut(df['sum_gamerounds'],bins=[-1,1,10,50,float('inf')],labels=['0-1局\n新手','2-10局\n探索','11-50局\n活跃','50+局\n核心'])
g=df.groupby('局数档',observed=True).agg(人数=('userid','count'),D1=('retention_1','mean'),D7=('retention_7','mean')).round(4)
print(g)

fig,ax=plt.subplots(figsize=(10,5))
idx=g.index.astype(str)
ax.bar(idx,g['D1'],color=HALO_PRIMARY,edgecolor=HALO_BORDER,alpha=0.8,label='D1')
ax.bar(idx,g['D7'],color=HALO_SUCCESS,edgecolor=HALO_BORDER,label='D7')
ax.set_ylabel('留存率'); ax.set_ylim(0,0.9)
ax.set_title('早期游戏局数与留存的关系',fontsize=14,pad=16)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout(); savefig(fig,'02_behavior_retention.png')

df.to_parquet(os.path.join(OUT,'cookie_cats_processed.parquet'),index=False)
print("\n处理完成,数据已保存")
