# -*- coding: utf-8 -*-
"""
14_情绪命中率图表.py
====================
汇报用图：情绪命中率（表现层）
  左：四类词典总体命中率（全样本 84,032 帖）
  右：三类道德情绪在 伪善帖 vs 非伪善帖 中的命中率对照（附比例 z 检验显著性）
输出：直接写入 vault media（E:\\文档\\obsidian\\毕设\\汇报\\media\\微博_情绪命中率.png）
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

from _common import load_data, CATS, CAT_COLS, EMO_CATS, EMO_COLS

d = load_data()
n = len(d)
hyp = d["hyp_hit_cad"] > 0

# ---------- 1. 总体命中率 ----------
overall = {c: round((d[col] > 0).mean() * 100, 1) for c, col in CAT_COLS.items()}
print("总体命中率:", overall)

# ---------- 2. 伪善帖 vs 非伪善帖 三类情绪命中率 + z 检验 ----------
cmp_rows = []
for c in EMO_CATS:
    col = EMO_COLS[c]
    p1 = (d.loc[hyp, col] > 0).mean()
    p0 = (d.loc[~hyp, col] > 0).mean()
    n1, n0 = int(hyp.sum()), int((~hyp).sum())
    p_pool = (p1 * n1 + p0 * n0) / (n1 + n0)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n0))
    z = (p1 - p0) / se
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    cmp_rows.append((c, p1 * 100, p0 * 100, z, pval))
    print(f"{c}: 伪善帖 {p1*100:.1f}% vs 非伪善帖 {p0*100:.1f}% | z={z:.1f} p={pval:.2e}")

# ---------- 3. 绘图 ----------
COLORS = {"伪善": "#c0392b", "愤怒": "#c0392b", "厌恶": "#e67e22", "鄙视": "#8e44ad"}
HYP_C, NON_C = "#c0392b", "#7f8c8d"

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

# 左：总体命中率
ax = axes[0]
cats = list(CATS)
vals = [overall[c] for c in cats]
bars = ax.bar(cats, vals, color=[COLORS[c] for c in cats], alpha=.9, width=.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + .6, f"{v}%", ha="center", fontsize=11)
ax.set_ylim(0, 28)
ax.set_ylabel("帖子占比 (%)")
ax.set_title(f"总体命中率（N={n:,} 帖）", fontsize=12)
ax.spines[["top", "right"]].set_visible(False)

# 右：伪善帖 vs 非伪善帖 三类情绪
ax = axes[1]
x = np.arange(len(EMO_CATS))
w = .36
v1 = [r[1] for r in cmp_rows]
v0 = [r[2] for r in cmp_rows]
b1 = ax.bar(x - w / 2, v1, w, label="伪善帖", color=HYP_C, alpha=.9)
b0 = ax.bar(x + w / 2, v0, w, label="非伪善帖", color=NON_C, alpha=.85)
for xi, (b_, v) in enumerate(zip(b1, v1)):
    ax.text(b_.get_x() + b_.get_width() / 2, v + 3.2, f"{v:.1f}%", ha="center", fontsize=9)
    ax.text(b_.get_x() + b_.get_width() / 2, v + .8, "***", ha="center", fontsize=10, color="black")
for xi, (b_, v) in enumerate(zip(b0, v0)):
    ax.text(b_.get_x() + b_.get_width() / 2, v + 3.2, f"{v:.1f}%", ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(EMO_CATS)
ax.set_ylabel("命中率 (%)")
ax.set_ylim(0, 48)
ax.set_title("三类道德情绪命中率：伪善帖 vs 非伪善帖", fontsize=12)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout(rect=(0, 0.04, 1, 1))
fig.text(0.99, 0.015, "注：星号为两类帖子命中率的比例 z 检验，*** p<.001", ha="right", fontsize=9, color="gray")
dst = r"E:\文档\obsidian\毕设\汇报\media\微博_情绪命中率.png"
os.makedirs(os.path.dirname(dst), exist_ok=True)
plt.savefig(dst, dpi=150)
plt.close()
print("\nsaved:", dst)
