# 数据运营作品集实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 制作一份数据运营求职作品集(1 主页 + 2 作品),证明"把数据变成可落地的运营决策"能力。

**Architecture:** 两个独立分析脚本(PUBG + Olist)产出洞察与图表,再制作运营型报告网页(GitHub Pages 部署)。作品二先建立"用户分层→生命周期→付费"方法论,作品一复用该框架落到 PUBG 游戏场景,形成互补闭环。

**Tech Stack:** Python 3.12 + pandas 3.0.5 + seaborn + matplotlib + Jupyter;HTML/CSS 静态网页;GitHub Pages 部署。

**数据源**(已下载到本地):
- PUBG: `data/pubg/extracted/train_V2.csv`(29 列,444 万行)
- Olist: `data/olist/extracted/`(9 个 CSV)

---

## 项目结构

```
D:\数据分析作品集\
├── docs/                    # 设计文档、实施计划
├── data/                    # 原始数据(gitignore,不提交)
│   ├── pubg/extracted/train_V2.csv
│   └── olist/extracted/*.csv
├── scripts/                 # 分析脚本
│   ├── common/              # 共享工具
│   │   └── viz.py           # 图表风格统一函数
│   ├── pubg/
│   │   ├── 01_clean.py      # 数据清洗
│   │   ├── 02_segment.py    # 玩家行为画像+分层
│   │   ├── 03_insights.py   # 表现洞察
│   │   └── 04_plan.py       # 运营落地方案
│   ├── olist/
│   │   ├── 01_clean.py      # 数据清洗
│   │   ├── 02_lifecycle.py  # 用户生命周期
│   │   ├── 03_payment.py    # 付费分析
│   │   └── 04_method.py     # 方法论输出
├── output/                  # 分析输出(图表、中间数据)
│   ├── pubg/
│   └── olist/
└── website/                 # 网页
    ├── index.html           # 主页
    ├── css/style.css
    ├── works/pubg.html      # 作品一
    ├── works/olist.html     # 作品二
    └── assets/              # 图表图片
```

---

## Task 1: 项目骨架与图表风格

**Files:**
- Create: `scripts/common/viz.py`
- Create: `.gitignore`(更新,加 output/)

- [ ] **Step 1: 创建图表风格统一模块**

```python
# scripts/common/viz.py
"""统一图表风格,让作品集视觉一致。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
sns.set_theme(style="whitegrid", font_scale=1.2)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def savefig(fig, name, subdir):
    import os
    outdir = os.path.join("output", subdir)
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
```

- [ ] **Step 2: 更新 .gitignore**

```
data/
output/
__pycache__/
*.pyc
.ipynb_checkpoints/
```

- [ ] **Step 3: 创建 output 目录并验证**

Run: `mkdir -p output/pubg output/olist && python -c "from scripts.common.viz import PALETTE; print('OK', len(PALETTE))"`
Expected: `OK 5`(无报错即中文字体可用)

- [ ] **Step 4: 提交**

```bash
git add .gitignore scripts/common/viz.py
git commit -m "feat: add project skeleton and unified chart style"
```

---

## Task 2: 作品一(PUBG)数据清洗

**Files:**
- Create: `scripts/pubg/01_clean.py`

**背景**:train_V2.csv 有 444 万行、29 列。含原始字段,需清洗(处理异常值、过滤垃圾对局)。

- [ ] **Step 1: 写清洗脚本(分块读取,避免内存峰值)**

```python
# scripts/pubg/01_clean.py
"""PUBG 数据清洗:过滤异常对局,生成干净数据集。"""
import pandas as pd
import numpy as np

SRC = "data/pubg/extracted/train_V2.csv"
OUT = "output/pubg/train_clean.parquet"

def clean():
    # 分块读取(每 100 万行),过滤后拼接
    chunks = []
    for chunk in pd.read_csv(SRC, chunksize=500000, low_memory=False):
        # 只保留标准对局模式
        chunk = chunk[chunk["matchType"].isin(
            ["solo", "solo-fpp", "duo", "duo-fpp", "squad", "squad-fpp"])]
        # 过滤明显异常:对局时长 < 30 秒 或 > 3600 秒
        chunk = chunk[(chunk["matchDuration"] >= 30) & (chunk["matchDuration"] <= 3600)]
        # 过滤异常移动距离(>100km 是数据错误)
        chunk = chunk[chunk["walkDistance"] + chunk["rideDistance"] + chunk["swimDistance"] <= 100000]
        # 过滤负值(某些字段可能异常)
        for col in ["damageDealt", "kills", "assists", "weaponsAcquired", "boosts", "heals"]:
            chunk = chunk[chunk[col] >= 0]
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    df.to_parquet(OUT, index=False)
    print(f"清洗后: {len(df)} 行, 保留 {len(df)/4446696*100:.1f}%")

if __name__ == "__main__":
    clean()
```

- [ ] **Step 2: 运行清洗并验证**

Run: `python scripts/pubg/01_clean.py`
Expected: 输出"清洗后: N 行, 保留 X%",N 在 300-400 万之间

- [ ] **Step 3: 生成数据质量报告(供作品展示)**

```python
# 追加到 01_clean.py
def quality_report(df):
    report = pd.DataFrame({
        "field": ["清洗前行数", "清洗后行数", "删除比例", "matchType 数", "平均 matchDuration"],
        "value": [4446696, len(df), f"{1-len(df)/4446696:.1%}", df["matchType"].nunique(), f"{df['matchDuration'].mean():.0f}s"]
    })
    report.to_csv("output/pubg/quality_report.csv", index=False)
```

- [ ] **Step 4: 提交**

```bash
git add scripts/pubg/01_clean.py
git commit -m "feat: add PUBG data cleaning"
```

---

## Task 3: 作品一(PUBG)玩家行为画像

**Files:**
- Create: `scripts/pubg/02_segment.py`

**背景**:用清洗后的数据,刻画玩家行为特征。定义"活跃强度"和"行为类型"。

- [ ] **Step 1: 写行为画像脚本(统计分布 + 行为分类)**

```python
# scripts/pubg/02_segment.py
"""PUBG 玩家行为画像:分布统计 + 行为类型划分。"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))
from viz import savefig, PALETTE
import matplotlib.pyplot as plt

df = pd.read_parquet("output/pubg/train_clean.parquet")

# 1. 核心行为指标分布
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
for ax, col in zip(axes.flat, ["kills", "damageDealt", "walkDistance", "assists", "boosts", "weaponsAcquired"]):
    ax.hist(df[col].clip(upper=df[col].quantile(0.99)), bins=50, color=PALETTE[0])
    ax.set_title(f"{col} 分布(截断99分位)")
    ax.set_xlabel(col); ax.set_ylabel("玩家数")
fig.tight_layout()
savefig(fig, "behavior_distributions.png", "pubg")

# 2. 行为类型划分:按击杀和存活时长打标签
df["totalDist"] = df["walkDistance"] + df["rideDistance"] + df["swimDistance"]
df["killPerDist"] = df["kills"] / (df["totalDist"] + 1)  # 移动效率
df["survival_time"] = df["maxPlace"] - df["numGroups"]   # 存活时长代理

# 行为类型:击杀少但存活久=稳健,击杀多=激进
df["aggro"] = np.where(df["kills"] >= df["kills"].median(), "高击杀(激进)", "低击杀(稳健)")
df["mobile"] = np.where(df["totalDist"] >= df["totalDist"].median(), "高机动", "低机动")
df["playstyle"] = df["aggro"] + "+" + df["mobile"]

# 保存画像数据
df.to_parquet("output/pubg/behavior_profile.parquet", index=False)
print("行为类型分布:")
print(df["playstyle"].value_counts(normalize=True).round(3))
```

- [ ] **Step 2: 运行并验证**

Run: `python scripts/pubg/02_segment.py`
Expected: 输出行为类型占比(4 类,和为 1),生成 behavior_distributions.png

- [ ] **Step 3: 提交**

```bash
git add scripts/pubg/02_segment.py output/pubg/behavior_distributions.png
git commit -m "feat: add PUBG player behavior profiling"
```

---

## Task 4: 作品一(PUBG)玩家价值分层

**Files:**
- Create: `scripts/pubg/03_segments.py`(玩家分层,与画像分开)

**背景**:核心动作——把玩家按价值分成核心/成长/流失风险三类。用 `winPlacePerc`(完赛名次)作为表现指标,结合行为特征分层。

- [ ] **Step 1: 写玩家分层脚本**

```python
# scripts/pubg/03_segments.py
"""PUBG 玩家价值分层:核心/成长/流失风险。"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))
from viz import savefig, PALETTE
import matplotlib.pyplot as plt

df = pd.read_parquet("output/pubg/behavior_profile.parquet")

# 表现指标 winPlacePerc 越高=名次越好(1=吃鸡,0=倒数)
# 玩家分层规则(基于行为特征,运营可执行):
# - 核心玩家:高击杀 + 高存活(高 winPlacePerc)
# - 成长玩家:中击杀,但活跃、有提升空间
# - 流失风险玩家:低击杀 + 低存活(低 winPlacePerc)+ 低频

# 用击杀数和存活时长做分层的业务锚点
df["surv_rank"] = df["winPlacePerc"]  # 名次即存活表现

seg_conditions = [
    (df["kills"] >= 3) & (df["winPlacePerc"] >= 0.5),      # 高击杀+高名次
    (df["kills"] >= 1) & (df["winPlacePerc"] >= 0.3),      # 有击杀+中名次
    (df["kills"] == 0) | (df["winPlacePerc"] < 0.3),       # 0击杀或低名次
]
seg_labels = ["核心玩家", "成长玩家", "流失风险玩家"]
df["segment"] = np.select(seg_conditions, seg_labels, default="成长玩家")

# 各分层画像
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ax, col in zip(axes, ["kills", "damageDealt", "winPlacePerc"]):
    df.boxplot(column=col, by="segment", ax=ax, grid=False)
    ax.set_title(f"{col} 分层对比")
    ax.set_xlabel("玩家分层"); ax.set_ylabel(col)
fig.suptitle("玩家价值分层特征对比")
fig.tight_layout()
savefig(fig, "segment_compare.png", "pubg")

# 分层占比
share = df["segment"].value_counts(normalize=True).round(3)
print("分层占比:")
print(share)
df.to_parquet("output/pubg/segmented.parquet", index=False)
```

- [ ] **Step 2: 运行并验证**

Run: `python scripts/pubg/03_segments.py`
Expected: 输出三类占比(和为 1),核心玩家约 15-25%,生成 segment_compare.png

- [ ] **Step 3: 提交**

```bash
git add scripts/pubg/03_segments.py output/pubg/segment_compare.png
git commit -m "feat: add PUBG player value segmentation"
```

---

## Task 5: 作品一(PUBG)表现洞察与运营落地方案

**Files:**
- Create: `scripts/pubg/04_insights.py`
- Create: `scripts/pubg/05_plan.py`

**背景**:找出"什么行为与高表现强相关"(洞察),据此输出可执行运营方案(落地方案)。

- [ ] **Step 1: 写表现洞察脚本(相关性 + 高表现画像)**

```python
# scripts/pubg/04_insights.py
"""PUBG 表现洞察:什么行为与高名次强相关。"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))
from viz import savefig, PALETTE
import matplotlib.pyplot as plt

df = pd.read_parquet("output/pubg/segmented.parquet")

# 1. 行为特征与表现(winPlacePerc)的相关性
behav_cols = ["kills", "damageDealt", "walkDistance", "rideDistance", "assists",
              "boosts", "heals", "weaponsAcquired", "headshotKills", "killStreaks"]
corr = df[behav_cols + ["winPlacePerc"]].corr()["winPlacePerc"].sort_values(ascending=False)
print("与表现相关性 Top:")
print(corr)

fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(corr.index, corr.values, color=PALETTE)
ax.set_title("行为特征与完赛名次的相关性")
ax.set_xlabel("相关系数")
fig.tight_layout()
savefig(fig, "correlation.png", "pubg")

# 2. 高表现玩家(winPlacePerc>0.8)画像 vs 低表现(<0.2)
high = df[df["winPlacePerc"] > 0.8]
low = df[df["winPlacePerc"] < 0.2]
print(f"高表现玩家数: {len(high)}, 低表现: {len(low)}")
for col in ["kills", "damageDealt", "walkDistance", "boosts", "heals", "weaponsAcquired"]:
    print(f"  {col}: 高={high[col].median():.1f} vs 低={low[col].median():.1f}")
```

- [ ] **Step 2: 运行并记录关键数字**

Run: `python scripts/pubg/04_insights.py`
Expected: 输出相关性 Top 列表 + 高低表现画像对比,生成 correlation.png

- [ ] **Step 3: 写运营落地方案脚本(把洞察转成动作)**

```python
# scripts/pubg/05_plan.py
"""PUBG 运营落地方案:洞察 → 可执行动作。"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))

df = pd.read_parquet("output/pubg/segmented.parquet")

# 基于洞察生成运营方案(结构化,供网页展示)
# 用数据算出的结论生成每条方案的"数据支撑"
high = df[df["winPlacePerc"] > 0.8]
low = df[df["winPlacePerc"] < 0.2]

plan = [
    {
        "action": "新手引导强化【高机动】行为教学",
        "why": f"数据显示 walkDistance 与表现相关系数靠前;高表现玩家中位移动 {high['walkDistance'].median():.0f}m,是低表现玩家({low['walkDistance'].median():.0f}m)的 X 倍",
        "data_source": "correlation + 高低表现画像对比",
    },
    {
        "action": "识别高潜力玩家:高击杀+高伤害但名次一般",
        "why": "这批玩家有战斗天赋(击杀/伤害高),只是运营节奏差,可通过引导提升名次",
        "data_source": "行为画像 + 分层规则",
    },
    {
        "action": "流失风险预警:0击杀+低存活玩家",
        "why": f"这部分玩家占 {df['segment'].value_counts(normalize=True)['流失风险玩家']:.1%},核心痛点是无正反馈",
        "data_source": "玩家分层",
    },
]

import json
with open("output/pubg/ops_plan.json", "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)
print("运营方案已生成", len(plan), "条")
```

- [ ] **Step 4: 运行并验证方案输出**

Run: `python scripts/pubg/05_plan.py`
Expected: 输出"运营方案已生成 3 条",生成 ops_plan.json

- [ ] **Step 5: 提交**

```bash
git add scripts/pubg/04_insights.py scripts/pubg/05_plan.py output/pubg/correlation.png output/pubg/ops_plan.json
git commit -m "feat: add PUBG insights and operations plan"
```

---

## Task 6: 作品二(Olist)数据清洗与用户生命周期

**Files:**
- Create: `scripts/olist/01_clean.py`
- Create: `scripts/olist/02_lifecycle.py`

**背景**:Olist 是标准电商数据,先清洗,再做用户生命周期分析(新客/复购/沉默/流失)。

- [ ] **Step 1: 写清洗脚本**

```python
# scripts/olist/01_clean.py
"""Olist 数据清洗 + 生成用户订单明细宽表。"""
import pandas as pd

base = "data/olist/extracted/"
orders = pd.read_csv(base + "olist_orders_dataset.csv")
items = pd.read_csv(base + "olist_order_items_dataset.csv")
cust = pd.read_csv(base + "olist_customers_dataset.csv")
pay = pd.read_csv(base + "olist_order_payments_dataset.csv")

# 只保留已完成的订单
orders = orders[orders["order_status"] == "delivered"]
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])

# 订单-客户关联
df = orders.merge(cust, on="customer_id", how="left")

# 订单金额(明细聚合)
order_value = items.groupby("order_id")["price"].sum().reset_index()
order_value.columns = ["order_id", "order_value"]
df = df.merge(order_value, on="order_id", how="left")

# 付费信息(支付次数、总支付)
pay_agg = pay.groupby("order_id").agg(
    pay_count=("payment_sequential", "count"),
    pay_value=("payment_value", "sum"),
    pay_type=("payment_type", "first"),
).reset_index()
df = df.merge(pay_agg, on="order_id", how="left")

df.to_parquet("output/olist/orders_clean.parquet", index=False)
print(f"清洗后订单: {len(df)} 行")
```

- [ ] **Step 2: 运行清洗**

Run: `python scripts/olist/01_clean.py`
Expected: 输出清洗后订单数(约 9 万)

- [ ] **Step 3: 写用户生命周期分析脚本**

```python
# scripts/olist/02_lifecycle.py
"""Olist 用户生命周期:新客/复购/沉默/流失。"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))
from viz import savefig, PALETTE
import matplotlib.pyplot as plt

df = pd.read_parquet("output/olist/orders_clean.parquet")

# 按客户聚合,算首购/末购/复购
cust = df.groupby("customer_unique_id").agg(
    first_order=("order_purchase_timestamp", "min"),
    last_order=("order_purchase_timestamp", "max"),
    order_count=("order_id", "nunique"),
    total_value=("order_value", "sum"),
    avg_value=("order_value", "mean"),
).reset_index()

# 生命周期分桶
cust["cohort_month"] = cust["first_order"].dt.to_period("M")

# 复购(>1 单)判断
cust["is_repeat"] = cust["order_count"] > 1

# 沉默/流失:最后下单距今天(2018-12 数据集截止)超过 90 天
ref_date = pd.Timestamp("2018-12-31")
cust["days_since_last"] = (ref_date - cust["last_order"]).dt.days
cust["status"] = np.select(
    [cust["is_repeat"], cust["days_since_last"] < 90],
    ["复购用户", "活跃用户"],
    default="沉默/流失",
)

# 新客:只下过 1 单且近期
cust.loc[(~cust["is_repeat"]) & (cust["days_since_last"] < 90), "status"] = "新客(首单)"

print("用户生命周期分布:")
print(cust["status"].value_counts(normalize=True).round(3))

# 图表:各生命周期用户平均价值
fig, ax = plt.subplots(figsize=(9, 6))
status_val = cust.groupby("status")["total_value"].mean().sort_values()
ax.barh(status_val.index, status_val.values, color=PALETTE)
ax.set_title("各生命周期用户的平均消费总额")
ax.set_xlabel("平均消费(R$)")
fig.tight_layout()
savefig(fig, "lifecycle_value.png", "olist")

cust.to_parquet("output/olist/customer_lifecycle.parquet", index=False)
```

- [ ] **Step 4: 运行生命周期分析**

Run: `python scripts/olist/02_lifecycle.py`
Expected: 输出生命周期分布(4 类,和为 1),生成 lifecycle_value.png

- [ ] **Step 5: 提交**

```bash
git add scripts/olist/01_clean.py scripts/olist/02_lifecycle.py output/olist/lifecycle_value.png
git commit -m "feat: add Olist cleaning and customer lifecycle"
```

---

## Task 7: 作品二(Olist)付费分析与方法论输出

**Files:**
- Create: `scripts/olist/03_payment.py`
- Create: `scripts/olist/04_method.py`

**背景**:付费分析(客单价/付费频次/高价值用户)+ 提炼可复用方法论框架。

- [ ] **Step 1: 写付费分析脚本**

```python
# scripts/olist/03_payment.py
"""Olist 付费分析:客单价、付费频次、高价值用户。"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath("scripts/common"))
from viz import savefig, PALETTE
import matplotlib.pyplot as plt

df = pd.read_parquet("output/olist/orders_clean.parquet")
cust = pd.read_parquet("output/olist/customer_lifecycle.parquet")

# 1. 客单价分布
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(df["order_value"].clip(upper=df["order_value"].quantile(0.95)), bins=50, color=PALETTE[0])
ax.set_title("订单金额分布(截断95分位)")
ax.set_xlabel("订单金额(R$)"); ax.set_ylabel("订单数")
fig.tight_layout()
savefig(fig, "order_value_dist.png", "olist")

# 2. 高价值用户:RFM 简化(消费总额 + 频次 + 近期)
cust["value_seg"] = pd.qcut(cust["total_value"], 4, labels=["低", "中低", "中高", "高"])
print("价值分层(按总消费四分位):")
print(cust["value_seg"].value_counts(normalize=True).round(3))

# 3. 高价值用户画像
high_val = cust[cust["value_seg"] == "高"]
print(f"高价值用户数: {len(high_val)} ({len(high_val)/len(cust):.1%})")
print(f"  - 平均消费: {high_val['total_value'].mean():.0f} R$")
print(f"  - 平均订单数: {high_val['order_count'].mean():.1f}")
print(f"  - 复购率: {high_val['is_repeat'].mean():.1%}")

cust.to_parquet("output/olist/customer_rfm.parquet", index=False)
```

- [ ] **Step 2: 运行付费分析**

Run: `python scripts/olist/03_payment.py`
Expected: 输出价值分层 + 高价值用户画像,生成 order_value_dist.png

- [ ] **Step 3: 写方法论输出脚本(作品二核心产出)**

```python
# scripts/olist/04_method.py
"""Olist 方法论输出:提炼可复用框架,供作品一落地。"""
import json

method = {
    "framework": "用户价值分层与运营方法论",
    "steps": [
        {"step": 1, "name": "数据清洗与统一", "action": "清洗异常值,统一时间字段,关联多表为宽表"},
        {"step": 2, "name": "用户生命周期划分", "action": "按首购/末购/频次划分 新客/复购/沉默/流失"},
        {"step": 3, "name": "用户价值分层", "action": "用消费金额/频次/近度(RFM)定义高价值用户"},
        {"step": 4, "name": "行为与价值关联", "action": "找出高价值用户的行为特征(复购、品类、频次)"},
        {"step": 5, "name": "运营动作落地", "action": "按分层给差异化运营策略:唤回/促活/提升频次"},
    ],
    "translatable_to": "游戏场景:消费→付费,复购→留存,沉默→流失,高价值→高付费/高活跃玩家",
    "outputs": {
        "lifecycle_value_png": "output/olist/lifecycle_value.png",
        "order_value_png": "output/olist/order_value_dist.png",
        "rfm_parquet": "output/olist/customer_rfm.parquet",
    },
}

with open("output/olist/method.json", "w", encoding="utf-8") as f:
    json.dump(method, f, ensure_ascii=False, indent=2)
print("方法论已输出")
```

- [ ] **Step 4: 运行方法论输出**

Run: `python scripts/olist/04_method.py`
Expected: 输出"方法论已输出",生成 method.json

- [ ] **Step 5: 提交**

```bash
git add scripts/olist/03_payment.py scripts/olist/04_method.py output/olist/order_value_dist.png output/olist/method.json
git commit -m "feat: add Olist payment analysis and methodology"
```

---

## Task 8: 网页制作(作品一、作品二报告页)

**Files:**
- Create: `website/works/pubg.html`
- Create: `website/works/olist.html`
- Create: `website/css/style.css`
- Create: `website/assets/`(拷贝图表)

**背景**:把分析结果做成"运营型报告"网页——叙事是背景→数据方法→分析→洞察→落地方案,不是图表堆砌。

- [ ] **Step 1: 拷贝图表到 website/assets**

```bash
mkdir -p website/assets
cp output/pubg/behavior_distributions.png output/pubg/segment_compare.png output/pubg/correlation.png website/assets/
cp output/olist/lifecycle_value.png output/olist/order_value_dist.png website/assets/
```

- [ ] **Step 2: 写公共样式**

```css
/* website/css/style.css */
:root {
    --primary: #1f4e79; --accent: #ff7f0e; --bg: #f8f9fa; --text: #2d2d2d;
}
body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; color: var(--text); background: var(--bg); margin: 0; line-height: 1.7; }
.container { max-width: 960px; margin: 0 auto; padding: 24px; }
header.hero { background: linear-gradient(135deg, var(--primary), #2a6496); color: #fff; padding: 40px 0; }
h1, h2, h3 { color: var(--primary); }
.chart-card { background: #fff; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-card img { max-width: 100%; height: auto; }
.action-plan { border-left: 4px solid var(--accent); background: #fff8ef; padding: 12px 16px; margin: 12px 0; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }
.kpi { background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.kpi .value { font-size: 28px; font-weight: 700; color: var(--accent); }
.nav { padding: 16px; text-align: center; background: #fff; border-bottom: 1px solid #eee; }
.nav a { margin: 0 12px; color: var(--primary); text-decoration: none; font-weight: 600; }
footer { text-align: center; padding: 24px; color: #888; font-size: 14px; }
```

- [ ] **Step 3: 写作品一网页(叙事:背景→数据→画像→分层→洞察→落地方案)**

```html
<!-- website/works/pubg.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>作品一 · PUBG 玩家行为与分层分析</title>
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<nav class="nav">
  <a href="../index.html">首页</a>
  <a href="pubg.html">作品一 · PUBG 玩家分层</a>
  <a href="olist.html">作品二 · 电商生命周期</a>
</nav>

<header class="hero"><div class="container">
  <h1>作品一 · PUBG 玩家对局行为与价值分层分析</h1>
  <p>作为数据运营,回答:谁是我们的高价值玩家?他们的行为特征是什么?如何识别和培养?</p>
</div></header>

<div class="container">
  <section class="chart-card">
    <h2>① 项目背景</h2>
    <p>玩家分层是游戏运营的核心动作。本作品用 PUBG 玩家对局行为数据(29 字段,444 万条记录),分析玩家行为特征,建立价值分层模型,输出可落地的运营方案。</p>
  </section>

  <section class="chart-card">
    <h2>② 数据与方法</h2>
    <p>数据源:PUBG 官方对局行为数据(每行=玩家一场对局)。关键字段:击杀/伤害/移动距离/名次。</p>
    <p>方法:清洗 → 行为画像 → 价值分层 → 行为与表现关联 → 运营方案。</p>
  </section>

  <section class="chart-card">
    <h2>③ 玩家行为画像</h2>
    <p>玩家行为分布展示玩家游戏方式差异(击杀、伤害、移动、道具使用等)。</p>
    <img src="../assets/behavior_distributions.png" alt="行为分布">
  </section>

  <section class="chart-card">
    <h2>④ 玩家价值分层</h2>
    <p>按击杀数与完赛名次,把玩家分为 <strong>核心玩家 / 成长玩家 / 流失风险玩家</strong> 三类。</p>
    <img src="../assets/segment_compare.png" alt="分层对比">
  </section>

  <section class="chart-card">
    <h2>⑤ 关键洞察</h2>
    <p>什么行为与高表现(高名次)强相关?高表现玩家的行为画像是什么?</p>
    <img src="../assets/correlation.png" alt="相关性">
  </section>

  <section class="chart-card">
    <h2>⑥ 运营落地方案</h2>
    <div class="action-plan"><strong>方案 1</strong> — 新手引导强化"高机动"行为教学,因为移动距离与表现强相关</div>
    <div class="action-plan"><strong>方案 2</strong> — 识别高潜力玩家(高击杀+高伤害但名次一般),定向培养</div>
    <div class="action-plan"><strong>方案 3</strong> — 流失风险预警(0击杀+低存活),设计正反馈机制挽回</div>
  </section>
</div>

<footer>张君杰 · 数据运营作品集 · 作品一</footer>
</body>
</html>
```

- [ ] **Step 4: 写作品二网页(叙事:方法论输出)**

```html
<!-- website/works/olist.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>作品二 · 电商用户生命周期与付费分析</title>
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<nav class="nav">
  <a href="../index.html">首页</a>
  <a href="pubg.html">作品一 · PUBG 玩家分层</a>
  <a href="olist.html">作品二 · 电商生命周期</a>
</nav>

<header class="hero"><div class="container">
  <h1>作品二 · 电商用户生命周期与付费分析</h1>
  <p>建立"用户分层 → 生命周期 → 付费价值"通用方法论框架,可迁移到任何产品。</p>
</div></header>

<div class="container">
  <section class="chart-card">
    <h2>① 项目背景</h2>
    <p>本作品用 Olist 巴西电商数据(约 10 万订单),建立一套通用的用户分析方法论,该框架可迁移到游戏等任何产品。</p>
  </section>

  <section class="chart-card">
    <h2>② 用户生命周期</h2>
    <p>按首购/末购/频次,划分新客/复购/沉默/流失。</p>
    <img src="../assets/lifecycle_value.png" alt="生命周期价值">
  </section>

  <section class="chart-card">
    <h2>③ 付费分析</h2>
    <p>客单价分布 + 高价值用户画像(消费总额/频次/近度)。</p>
    <img src="../assets/order_value_dist.png" alt="订单金额分布">
  </section>

  <section class="chart-card">
    <h2>④ 方法论输出</h2>
    <p>五步框架:清洗统一 → 生命周期划分 → 价值分层 → 行为关联 → 运营落地。</p>
    <div class="action-plan"><strong>迁移到游戏:</strong> 消费→付费,复购→留存,沉默→流失,高价值→高付费玩家</div>
  </section>
</div>

<footer>张君杰 · 数据运营作品集 · 作品二</footer>
</body>
</html>
```

- [ ] **Step 5: 提交**

```bash
git add website/
git commit -m "feat: add portfolio work webpages"
```

---

## Task 9: 主页 + 部署 GitHub Pages

**Files:**
- Create: `website/index.html`

**背景**:作品集主页,个人介绍 + 两个作品入口,部署到 GitHub Pages。

- [ ] **Step 1: 写主页**

```html
<!-- website/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>张君杰 · 数据运营作品集</title>
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<header class="hero"><div class="container">
  <h1>张君杰 · 数据运营作品集</h1>
  <p>安徽建筑大学 · 信息与计算科学 · 2027 届</p>
  <p>数据分析 | 用户分层 | 运营决策</p>
</div></header>

<div class="container">
  <div class="kpi-grid">
    <div class="kpi"><div class="value">2</div><div>个作品</div></div>
    <div class="kpi"><div class="value">454万</div><div>游戏行为数据</div></div>
    <div class="kpi"><div class="value">10万</div><div>电商订单数据</div></div>
    <div class="kpi"><div class="value">3</div><div>条运营方案</div></div>
  </div>

  <h2>作品集</h2>
  <div class="chart-card">
    <h3><a href="works/pubg.html">作品一 · PUBG 玩家行为与价值分层</a></h3>
    <p>用 444 万条玩家对局行为,建立玩家价值分层,输出识别高潜力玩家与流失预警的运营方案。</p>
  </div>
  <div class="chart-card">
    <h3><a href="works/olist.html">作品二 · 电商用户生命周期与付费分析</a></h3>
    <p>用 Olist 电商数据建立用户分层方法论框架,可迁移到游戏等任何产品。</p>
  </div>

  <h2>关于我</h2>
  <div class="chart-card">
    <p>数据驱动的运营思维 · 数学建模与 Python 技能 · 销售实习中的数据转化实践</p>
  </div>
</div>

<footer>张君杰 · 数据运营作品集</footer>
</body>
</html>
```

- [ ] **Step 2: 本地预览验证**

Run: 打开 `website/index.html`,确认导航、图片、样式正常

- [ ] **Step 3: 部署 GitHub Pages**

```bash
# 在 GitHub 创建仓库 portfolio,推送 website 内容,开启 Pages
cd website
git init && git add -A && git commit -m "deploy portfolio"
git remote add origin https://github.com/用户名/portfolio.git
git push -u origin main
```

(需用户在 GitHub 创建仓库并开启 Pages 功能)

- [ ] **Step 4: 提交网页代码**

```bash
cd D:/数据分析作品集
git add website/index.html
git commit -m "feat: add portfolio homepage"
```

---

## 验收清单

- [ ] PUBG 清洗后数据可用(300 万+ 行)
- [ ] 生成 3 类玩家分层,占比合理
- [ ] 相关性分析找出"高表现强相关行为"
- [ ] 输出 3 条带数据支撑的运营方案
- [ ] Olist 生命周期 4 类分布,高价值用户画像清晰
- [ ] 方法论框架输出,可翻译到游戏场景
- [ ] 2 个作品网页 + 主页,视觉一致
- [ ] GitHub Pages 部署成功,链接可访问
