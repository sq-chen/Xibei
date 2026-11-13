# -*- coding: utf-8 -*-
"""
10_互动类型构成.py
==================
W-1 互动类型构成画像（表现层，纯描述 + 图，不做回归）：
  - 伪善帖 vs 非伪善帖：转发/评论/点赞/总互动的均值、中位数、零互动率、三类互动构成占比
  - 按天分项互动演化（伪善 vs 非伪善）
输出：描述性统计结果/互动构成/互动构成汇总.csv + 互动构成对比.png + 按天分项互动.png
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import load_data, save_fig, to_csv, OUT_DIR, ENGAGE_COLS

OUT = os.path.join(OUT_DIR, "互动构成")
os.makedirs(OUT, exist_ok=True)

d = load_data()
d["hyp"] = d["hyp_hit_cad"] > 0
TYPES = ["转发", "评论", "点赞"]
TYPE_COLS = {"转发": "reposts_count", "评论": "comments_count", "点赞": "attitudes_count"}

# ---------- 1. 汇总表 ----------
rows = []
for hyp, lab in [(True, "伪善帖"), (False, "非伪善帖")]:
    sub = d[d["hyp"] == hyp]
    row = {"组": lab, "N": len(sub)}
    tot_mean = sub["total_engagement"].mean()
    for k, col in {**TYPE_COLS, "总互动": "total_engagement"}.items():
        row[f"{k}_均值"] = round(sub[col].mean(), 1)
        row[f"{k}_中位数"] = int(sub[col].median())
        row[f"{k}_零率%"] = round((sub[col] == 0).mean() * 100, 1)
    for k, col in TYPE_COLS.items():
        row[f"{k}构成占比%"] = round(sub[col].mean() / tot_mean * 100, 1)
    rows.append(row)
tab = pd.DataFrame(rows)
to_csv(tab, os.path.join("互动构成", "互动构成汇总.csv"))
print(tab.to_string(index=False))

# ---------- 2. 图 1：均值对比（分组柱 + log 轴） ----------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
x = np.arange(len(TYPES))
w = 0.38
for gi, (hyp, lab, color) in enumerate([(True, "伪善帖", "#c0392b"), (False, "非伪善帖", "#7f8c8d")]):
    sub = d[d["hyp"] == hyp]
    means = [sub[TYPE_COLS[t]].mean() for t in TYPES]
    axes[0].bar(x + (gi - .5) * w, means, w, label=lab, color=color, alpha=.9)
    for xi, m in zip(x + (gi - .5) * w, means):
        axes[0].text(xi, m, f"{m:.1f}", ha="center", va="bottom", fontsize=8)
axes[0].set_xticks(x); axes[0].set_xticklabels(TYPES)
axes[0].set_ylabel("平均互动次数"); axes[0].set_title("分项互动均值：伪善帖 vs 非伪善帖")
axes[0].legend()
zero = [[(d[(d["hyp"] == h)][TYPE_COLS[t]] == 0).mean() * 100 for t in TYPES]
        for h in (True, False)]
for gi, (lab, z, color) in enumerate(zip(["伪善帖", "非伪善帖"], zero, ["#c0392b", "#7f8c8d"])):
    axes[1].bar(x + (gi - .5) * w, z, w, label=lab, color=color, alpha=.9)
    for xi, v in zip(x + (gi - .5) * w, z):
        axes[1].text(xi, v, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
axes[1].set_xticks(x); axes[1].set_xticklabels(TYPES)
axes[1].set_ylabel("零互动率 (%)"); axes[1].set_title("零互动率：伪善帖 vs 非伪善帖")
axes[1].legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT, "互动构成对比.png"), dpi=150); plt.close()

# ---------- 3. 图 2：按天分项互动演化 ----------
d["date"] = d["created_at"].dt.date
days = sorted(d["date"].unique())
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ai, (t, col) in enumerate(TYPE_COLS.items()):
    for hyp, lab, color, ls in [(True, "伪善帖", "#c0392b", "-"), (False, "非伪善帖", "#7f8c8d", "--")]:
        s = d[d["hyp"] == hyp].groupby("date")[col].mean().reindex(days)
        axes[ai].plot(range(len(days)), s.values, color=color, ls=ls, marker="o", ms=3, label=lab)
    axes[ai].set_title(f"{t}均值演化")
    axes[ai].set_xticks(range(0, len(days), 2))
    axes[ai].set_xticklabels([str(dd)[5:] for dd in days[::2]], fontsize=8, rotation=45)
    axes[ai].legend(fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "按天分项互动.png"), dpi=150); plt.close()

# ---------- 4. 附报：按天分项互动均值表（CSV） ----------
daily = []
for dd_ in days:
    for hyp, lab in [(True, "伪善帖"), (False, "非伪善帖")]:
        sub = d[(d["hyp"] == hyp) & (d["date"] == dd_)]
        row = {"date": str(dd_), "组": lab, "N": len(sub)}
        for k, col in {**TYPE_COLS, "总互动": "total_engagement"}.items():
            row[k] = round(sub[col].mean(), 1)
        daily.append(row)
to_csv(pd.DataFrame(daily), os.path.join("互动构成", "按天分项互动.csv"))
print("\n已导出：描述性统计结果/互动构成/ 目录（汇总表 + 2 图 + 按天表）")
