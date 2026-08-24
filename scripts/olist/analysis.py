# -*- coding: utf-8 -*-
"""
作品二 · Olist 电商分析
====================================================
分析思路(由张君杰完成分析,本脚本固化):
1. 关联订单/支付/客户,按 customer_unique_id 聚合为"客户档案"
2. 发现 96.9% 客户只买 1 单(长尾分布)
3. 按消费分位数分 4 档,发现"高价值"靠单次高消费而非复购
4. 对比复购客户 vs 单次客户:复购消费高 1.95 倍
5. 聚焦"高价值单次客户"(前 20%),作为复购转化靶心
"""
import pandas as pd
import numpy as np
import os

BASE = "data/olist/extracted/"
OUT = "output/olist"
os.makedirs(OUT, exist_ok=True)

# ========== 1. 读数据 ==========
print("=" * 60)
print("步骤1: 读取数据")
print("=" * 60)
orders = pd.read_csv(BASE + "olist_orders_dataset.csv")
customers = pd.read_csv(BASE + "olist_customers_dataset.csv")
payments = pd.read_csv(BASE + "olist_order_payments_dataset.csv")
print(f"订单: {len(orders):,} | 客户记录: {len(customers):,} | 支付: {len(payments):,}")

# ========== 2. 关联 + 聚合 ==========
print("\n" + "=" * 60)
print("步骤2: 订单-客户-支付关联,按客户聚合")
print("=" * 60)
# 订单-客户(拿 customer_unique_id)
df = orders.merge(customers, on="customer_id", how="left")
# 支付按订单聚合(一个订单可能多笔支付)
pay = payments.groupby("order_id")["payment_value"].sum().reset_index()
df = df.merge(pay, on="order_id", how="left")

# 按客户聚合
客户汇总 = df.groupby("customer_unique_id").agg(
    总消费=("payment_value", "sum"),
    订单数=("order_id", "count"),
).reset_index()
print(f"客户总数: {len(客户汇总):,}")
print(f"平均消费: {客户汇总['总消费'].mean():.1f} | 中位数: {客户汇总['总消费'].median():.1f}")

# ========== 3. 订单数分布(长尾) ==========
print("\n" + "=" * 60)
print("步骤3: 订单数分布")
print("=" * 60)
单次占比 = (客户汇总["订单数"] == 1).mean()
print(f"只买1单的客户占比: {单次占比:.1%}")
print("→ 96.9% 客户只买 1 单,长尾分布")

# ========== 4. 按消费分位数分层 ==========
print("\n" + "=" * 60)
print("步骤4: 消费分位数 4 档分层")
print("=" * 60)
客户汇总["价值档"] = pd.qcut(客户汇总["总消费"], 4, labels=["低", "中低", "中高", "高"])
分层统计 = 客户汇总.groupby("价值档").agg(
    人数=("总消费", "count"),
    平均消费=("总消费", "mean"),
    平均订单数=("订单数", "mean"),
).round(1)
print(分层统计)
print("→ 各档平均订单数几乎都是 1,说明'高价值'靠单次高消费而非复购")

# ========== 5. 复购 vs 单次 ==========
print("\n" + "=" * 60)
print("步骤5: 复购客户 vs 单次客户")
print("=" * 60)
复购客户 = 客户汇总[客户汇总["订单数"] >= 2]
单次客户 = 客户汇总[客户汇总["订单数"] == 1]
复购均值 = 复购客户["总消费"].mean()
单次均值 = 单次客户["总消费"].mean()
print(f"复购客户: {len(复购客户):,}人, 平均消费: {复购均值:.1f}")
print(f"单次客户: {len(单次客户):,}人, 平均消费: {单次均值:.1f}")
print(f"复购/单次 倍数: {复购均值/单次均值:.2f}x")

# ========== 6. 高价值单次客户(复购转化靶心) ==========
print("\n" + "=" * 60)
print("步骤6: 高价值单次客户(复购转化靶心)")
print("=" * 60)
阈值 = 单次客户["总消费"].quantile(0.8)
高价值单次 = 单次客户[单次客户["总消费"] >= 阈值]
print(f"单次客户: {len(单次客户):,}人")
print(f"高价值单次(消费>={阈值:.1f}): {len(高价值单次):,}人")
print(f"  平均消费: {高价值单次['总消费'].mean():.1f}")
print(f"  占单次客户: {len(高价值单次)/len(单次客户):.1%}")

# ========== 保存 ==========
客户汇总.to_parquet(os.path.join(OUT, "customer_summary.parquet"), index=False)
print("\n客户汇总已保存: output/olist/customer_summary.parquet")
