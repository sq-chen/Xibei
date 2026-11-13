# -*- coding: utf-8 -*-
"""
15_按天情绪命中率图表.py
======================
汇报用图：四类词典命中率按天演化（表现层），叠加发帖量（次轴）与关键事件标注。
输出：vault media（E:\\文档\\obsidian\\毕设\\汇报\\media\\微博_按天_情绪命中率.png）
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

from _common import load_data, CATS, CAT_COLS

d = load_data()
d["date"] = d["created_at"].dt.date
days = sorted(d["date"].unique())
day_labels = [f"{x.month}-{x.day}" for x in days]

hit_rate = {}
for c, col in CAT_COLS.items():
    hit_rate[c] = [round((d.loc[d["date"] == x, col] > 0).mean() * 100, 1) for x in days]

vol = [int((d["date"] == x).sum()) for x in days]
print("天数:", len(days), day_labels)
for c in CATS:
    print(c, hit_rate[c])
print("发帖量:", vol)

COLORS = {"伪善": "#8e44ad", "愤怒": "#c0392b", "厌恶": "#e67e22", "鄙视": "#2471a3"}
EVENTS = {0: "事件爆发\n9-12", 2: "动员大会\n9-13", 5: "道歉致歉信\n9-15"}

fig, ax1 = plt.subplots(figsize=(11, 4.8))
x = np.arange(len(days))
for c in CATS:
    ax1.plot(x, hit_rate[c], marker="o", ms=4, lw=1.8, color=COLORS[c], label=c)
for xi, label in EVENTS.items():
    ax1.axvline(xi, color="gray", ls="--", lw=.9, alpha=.6)
    ax1.text(xi + .08, ax1.get_ylim()[1] * .9, label, fontsize=8, color="gray")
ax1.set_xlabel("日期（2025-09）")
ax1.set_ylabel("词典命中率 (%)")
ax1.set_xticks(x)
ax1.set_xticklabels(day_labels, fontsize=9)
ax1.set_ylim(0, max(max(v) for v in hit_rate.values()) * 1.28)
ax1.legend(loc="upper left", frameon=False, ncol=4, fontsize=9)
ax1.spines[["top"]].set_visible(False)

ax2 = ax1.twinx()
ax2.bar(x, vol, color="#bdc3c7", alpha=.45, width=.62, label="发帖量（次轴）")
ax2.set_ylabel("发帖量（帖）", color="#7f8c8d")
ax2.tick_params(axis="y", labelcolor="#7f8c8d")
ax2.spines[["top"]].set_visible(False)

ax1.set_title("四类词典命中率与发帖量的按天演化", fontsize=12)
plt.tight_layout()
dst = r"E:\文档\obsidian\毕设\汇报\media\微博_按天_情绪命中率.png"
plt.savefig(dst, dpi=150)
plt.close()
print("\nsaved:", dst)
