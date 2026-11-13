# -*- coding: utf-8 -*-
"""
03_虚伪贴情绪面貌.py
==================
分析内容（对应论文"虚伪表述的情绪构成"）：
① 虚伪帖内部：三类情绪命中率条形图（H-obs2 的直观版）；
② 虚伪帖 vs 非虚伪帖：三类情绪命中率并列柱状图 + 比例差异 z 检验表（CSV 含四类）；
③ 虚伪帖内同时命中 0/1/2/3 类情绪的结构饼图。

输出：描述性统计结果/hyp_emotion_share.csv、hyp_vs_nonhyp_emotion.csv、
     hyp_multi_emotion.csv、虚伪帖情绪占比.png、虚伪vs非虚伪.png、多情绪结构.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import (CATS, CAT_COLS, EMO_CATS, EMO_COLS,
                     load_data, prop_z, save_fig, to_csv)

d = load_data()
hyp = d[d["hyp_hit_binary_cad"] == 1]
nonhyp = d[d["hyp_hit_binary_cad"] == 0]
n_hyp, n_non = len(hyp), len(nonhyp)
print(f"虚伪帖 {n_hyp} / 非虚伪帖 {n_non}")

# ---------- ① 虚伪帖内三情绪命中率 ----------
share_rows = []
for cat in EMO_CATS:
    col = EMO_COLS[cat]
    share_rows.append({
        "情绪": cat,
        "虚伪帖内命中率%": round(100 * (hyp[col] > 0).mean(), 1),
        "虚伪帖内命中次数均值": round(hyp[col].mean(), 3),
    })
share = pd.DataFrame(share_rows)
to_csv(share, "hyp_emotion_share.csv")
print(share.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 4.5))
ax.bar(share["情绪"], share["虚伪帖内命中率%"], color=["#C44E52", "#55A868", "#8172B2"])
ax.set_ylabel("命中率 %")
ax.set_title("虚伪帖内三类情绪命中率（n=%d）" % n_hyp)
for i, v in enumerate(share["虚伪帖内命中率%"]):
    ax.text(i, v + 0.3, f"{v:.1f}%", ha="center")
save_fig("虚伪帖情绪占比.png")

# ---------- ② 虚伪 vs 非虚伪：四类命中率 + z 检验 ----------
cmp_rows = []
for cat in CATS:
    col = CAT_COLS[cat]
    r1 = (hyp[col] > 0).mean(); r2 = (nonhyp[col] > 0).mean()
    z, pval = prop_z(r1, n_hyp, r2, n_non)
    cmp_rows.append({
        "类别": cat,
        "虚伪帖命中率%": round(100 * r1, 1),
        "非虚伪帖命中率%": round(100 * r2, 1),
        "差异(百分点)": round(100 * (r1 - r2), 1),
        "z": round(z, 2),
        "p": round(pval, 4),
    })
cmp = pd.DataFrame(cmp_rows)
to_csv(cmp, "hyp_vs_nonhyp_emotion.csv")
print("\n=== 虚伪 vs 非虚伪（比例 z 检验）===")
print(cmp.to_string(index=False))

# 图中只画三类情绪：虚伪帖的"虚伪"命中率按定义为 100%、非虚伪帖为 0%，
# 该类别无信息量（CSV 仍保留四类完整结果）
plot_cmp = cmp[cmp["类别"].isin(EMO_CATS)].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(7.5, 5))
x = np.arange(len(plot_cmp)); w = 0.36
b1 = ax.bar(x - w / 2, plot_cmp["虚伪帖命中率%"], w, label="虚伪帖", color="#C44E52")
b2 = ax.bar(x + w / 2, plot_cmp["非虚伪帖命中率%"], w, label="非虚伪帖", color="#B0B0B0")
for i, pv in enumerate(plot_cmp["p"]):
    star = "***" if pv < 0.001 else ("**" if pv < 0.01 else ("*" if pv < 0.05 else "ns"))
    ax.text(i, max(plot_cmp["虚伪帖命中率%"][i], plot_cmp["非虚伪帖命中率%"][i]) + 0.5,
            star, ha="center", fontsize=11)
ax.set_xticks(x); ax.set_xticklabels(plot_cmp["类别"])
ax.set_ylabel("命中率 %")
ax.set_title("虚伪帖 vs 非虚伪帖的三类情绪命中率（*p<.05 **p<.01 ***p<.001）")
ax.legend()
save_fig("虚伪vs非虚伪.png")

# ---------- ③ 虚伪帖内多情绪结构 ----------
n_emo = ((hyp["anger_hit_cad"] > 0).astype(int)
         + (hyp["disgust_hit_cad"] > 0).astype(int)
         + (hyp["contempt_hit_cad"] > 0).astype(int))
labels = ["纯虚伪（0 类情绪）", "虚伪+1 类情绪", "虚伪+2 类情绪", "虚伪+3 类情绪"]
sizes = [(n_emo == k).sum() for k in range(4)]
multi = pd.DataFrame({"结构": labels, "帖数": sizes,
                      "占比%": [round(100 * s / n_hyp, 1) for s in sizes]})
to_csv(multi, "hyp_multi_emotion.csv")
print("\n=== 虚伪帖多情绪结构 ===")
print(multi.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90,
       colors=["#DDDDDD", "#C44E52", "#8172B2", "#4C72B0"])
ax.set_title("虚伪帖同时命中 CAD 情绪的结构")
save_fig("多情绪结构.png")
print("\n已写入")
