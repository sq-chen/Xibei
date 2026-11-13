# -*- coding: utf-8 -*-
"""
01_命中率与分布快照.py
====================
分析内容（对应论文"样本与指标描述"）：
① 四类词的命中帖数/占比与命中次数分布（均值/SD/中位/最大 + 直方图，展示计数右偏）；
② 虚伪帖×三类情绪交叉结构：虚伪帖内同时命中 0/1/2/3 类情绪的比例；
③ 帖子长度对照：各类命中帖 vs 未命中帖的 text_len 箱线图
   （为机制分析中"虚伪帖更长、粗对比优势被长度吸收"提供描述证据）。

输出：描述性统计结果/dist_snapshot.csv、hyp_emotion_crosstab.csv、
     命中次数分布.png、帖长对照箱线图.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import (CATS, CAT_COLS, EMO_CATS, EMO_COLS, OUT_DIR,
                     load_data, save_fig, to_csv)

d = load_data()
n = len(d)
print("数据:", n, "帖")

# ---------- ① 整体命中率与分布 ----------
rows = []
for cat in CATS:
    col = CAT_COLS[cat]
    hit = d[col] > 0
    rows.append({
        "类别": cat,
        "命中帖数": int(hit.sum()),
        "命中占比%": round(100 * hit.mean(), 1),
        "次数均值": round(d[col].mean(), 3),
        "次数SD": round(d[col].std(), 3),
        "次数中位": int(d[col].median()),
        "次数最大": int(d[col].max()),
        "命中帖内均值": round(d.loc[hit, col].mean(), 3),
    })
snap = pd.DataFrame(rows)
to_csv(snap, "dist_snapshot.csv")
print(snap.to_string(index=False))

# 总体命中率柱状图（替换原命中次数分布直方图：直方图信息量低，
# "命中次数高度右偏"用文字说明即可；这张图直接呈现四类词命中率的对比）
fig, ax = plt.subplots(figsize=(6, 4.5))
rates = snap["命中占比%"]
colors = {"虚伪": "#4C72B0", "愤怒": "#C44E52", "厌恶": "#55A868", "鄙视": "#8172B2"}
ax.bar(snap["类别"], rates, width=0.55,
       color=[colors[c] for c in snap["类别"]], edgecolor="white")
for i, v in enumerate(rates):
    ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=11)
ax.set_ylabel("命中率 %")
ax.set_title(f"四类词总体命中率（n={n:,} 帖）")
ax.set_ylim(0, max(rates) * 1.18)
save_fig("总体命中率.png")

# ---------- ② 虚伪帖 × 三情绪交叉结构 ----------
hyp = d[d["hyp_hit_binary_cad"] == 1]
n_emo = ((hyp["anger_hit_cad"] > 0).astype(int)
         + (hyp["disgust_hit_cad"] > 0).astype(int)
         + (hyp["contempt_hit_cad"] > 0).astype(int))
cross = pd.DataFrame({
    "同时命中情绪数": [0, 1, 2, 3],
    "虚伪帖数": [(n_emo == k).sum() for k in range(4)],
    "占比%": [round(100 * (n_emo == k).mean(), 1) for k in range(4)],
})
to_csv(cross, "hyp_emotion_crosstab.csv")
print("\n=== 虚伪帖内同时命中情绪数 ===")
print(cross.to_string(index=False))

# 全体样本：虚伪命中 × 各情绪命中 的 2×2 交叉表
crosstab_rows = []
for cat in EMO_CATS:
    col = EMO_COLS[cat]
    c = pd.crosstab(d["hyp_hit_binary_cad"], d[col] > 0)
    crosstab_rows.append({
        "情绪": cat,
        "虚伪帖命中率%": round(100 * (d.loc[d["hyp_hit_binary_cad"] == 1, col] > 0).mean(), 1),
        "非虚伪帖命中率%": round(100 * (d.loc[d["hyp_hit_binary_cad"] == 0, col] > 0).mean(), 1),
    })
print("\n=== 虚伪帖 vs 非虚伪帖 情绪命中率（描述层）===")
print(pd.DataFrame(crosstab_rows).to_string(index=False))

# ---------- ③ 帖长对照（命中 vs 未命中） ----------
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, cat in zip(axes.flat, CATS):
    hit = d[CAT_COLS[cat]] > 0
    data = [d.loc[~hit, "text_len"], d.loc[hit, "text_len"]]
    ax.boxplot(data, labels=["未命中", "命中"], showfliers=False)
    ax.set_title(f"{cat}词：命中帖 vs 未命中帖的正文长度")
    ax.set_ylabel("字符数")
save_fig("帖长对照箱线图.png")
print("\n已写入:", OUT_DIR)
