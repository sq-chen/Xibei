# -*- coding: utf-8 -*-
"""
02_时间序列.py
============
分析内容（对应论文"舆情演变"小节）：
① 按小时聚合：发帖量、虚伪命中率、三类情绪命中率的逐小时走势（标注 P1/P2/P3 分界）；
② 阶段对比：P1/P2/P3 的虚伪与三类情绪命中率 + 两两比例 z 检验。

输出：描述性统计结果/hyp_timeline_hourly.csv、emotion_timeline_hourly.csv、
     phase_comparison.csv、时间序列.png、阶段对比.png
"""
from __future__ import annotations

from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import (CATS, CAT_COLS, EMO_CATS, EMO_COLS, PHASE_ORDER,
                     load_data, prop_z, save_fig, to_csv)

d = load_data()

# ---------- ① 按小时聚合 ----------
d["hour"] = d["hours_since_start"].astype(int)
hourly = d.groupby("hour").agg(
    发帖量=("ID", "size"),
    **{f"{cat}命中率": (CAT_COLS[cat], lambda s: (s > 0).mean()) for cat in CATS},
).reset_index()
to_csv(hourly, "hyp_timeline_hourly.csv")

# 三情绪单独一份（论文引用方便）
emo_hourly = d.groupby("hour").agg(
    发帖量=("ID", "size"),
    **{f"{cat}命中率": (EMO_COLS[cat], lambda s: (s > 0).mean()) for cat in EMO_CATS},
).reset_index()
to_csv(emo_hourly, "emotion_timeline_hourly.csv")

# 阶段分界小时（P2/P3 起始）
phase_start = d.groupby("phase")["hour"].min().to_dict()

fig, ax = plt.subplots(figsize=(12, 5))
for cat in CATS:
    ax.plot(hourly["hour"], hourly[f"{cat}命中率"] * 100, label=f"{cat}词命中率")
for p, x in [("P2", phase_start.get("P2")), ("P3", phase_start.get("P3"))]:
    if x is not None:
        ax.axvline(x, color="gray", linestyle="--", linewidth=1)
        ax.text(x, ax.get_ylim()[1] * 0.95, p, ha="left", color="gray")
ax.set_xlabel("事件起点后小时数（2025-09-10 16:55 起）")
ax.set_ylabel("命中率 %")
ax.set_title("虚伪与三类情绪命中率的逐小时走势")
ax.legend(loc="upper right")
save_fig("时间序列.png")

# ---------- ② 阶段对比 ----------
rows = []
for cat in CATS:
    col = CAT_COLS[cat]
    rates = {}
    for p in PHASE_ORDER:
        sub = d[d["phase"] == p]
        rates[p] = (sub[col] > 0).mean()
    rows.append({"类别": cat, **{f"{p}命中率%": round(100 * rates[p], 1) for p in PHASE_ORDER}})
ph = pd.DataFrame(rows)
to_csv(ph, "phase_comparison_rates.csv")

# 两两 z 检验
zt = []
for cat in CATS:
    col = CAT_COLS[cat]
    for p1, p2 in combinations(PHASE_ORDER, 2):
        s1, s2 = d[d["phase"] == p1], d[d["phase"] == p2]
        r1 = (s1[col] > 0).mean(); r2 = (s2[col] > 0).mean()
        z, pval = prop_z(r1, len(s1), r2, len(s2))
        zt.append({"类别": cat, "对比": f"{p1} vs {p2}",
                   "z": round(z, 2), "p": round(pval, 4)})
zt_df = pd.DataFrame(zt)
to_csv(zt_df, "phase_comparison.csv")
print(zt_df.to_string(index=False))

# 阶段柱状图（虚伪 + 三情绪）
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(CATS))
width = 0.25
for i, p in enumerate(PHASE_ORDER):
    ax.bar(x + (i - 1) * width, ph[f"{p}命中率%"], width, label=p)
ax.set_xticks(x); ax.set_xticklabels(CATS)
ax.set_ylabel("命中率 %")
ax.set_title("事件三阶段（P1/P2/P3）的命中率对比")
ax.legend()
save_fig("阶段对比.png")
print("\n已写入")
