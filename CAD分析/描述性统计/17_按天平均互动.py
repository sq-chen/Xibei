# -*- coding: utf-8 -*-
"""
17_按天平均互动.py
==================
汇报用图：伪善帖 vs 非伪善帖 的单帖平均互动（转发+评论+点赞均值）按天变化。
展示"前期优势 → 9-15/16 反转为劣势"；事件竖线：9-12 爆发 / 9-13 动员大会 / 9-15 道歉。
输出：毕设/汇报/media/微博_按天_平均互动.png + 描述性统计结果/按天平均互动.csv
"""
import pandas as pd

from _common import load_data, to_csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- 1. 数据 ----------
d = load_data()
d["day"] = d["created_at"].dt.floor("D")
d = d[d["day"].notna()]
d["hyp"] = d["hyp_hit_cad"] > 0

rows = []
for day in sorted(d["day"].unique()):
    dd = d[d["day"] == day]
    rows.append({
        "日期": day.strftime("%m-%d"),
        "伪善帖": dd.loc[dd["hyp"], "total_engagement"].mean(),
        "非伪善帖": dd.loc[~dd["hyp"], "total_engagement"].mean(),
        "所有帖子": dd["total_engagement"].mean(),
        "伪善帖数": int(dd["hyp"].sum()),
        "非伪善帖数": int((~dd["hyp"]).sum()),
    })
tab = pd.DataFrame(rows)
to_csv(tab, "按天平均互动.csv")
print(tab.to_string(index=False, float_format=lambda v: f"{v:.1f}"))

# ---------- 2. 绘图 ----------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(10, 5))
x = list(range(8))
xl = tab["日期"]
ax.plot(x, tab["所有帖子"], "--o", color="#333333", lw=1.8, ms=5, label="所有帖子")
ax.plot(x, tab["非伪善帖"], "-s", color="#4C72B0", lw=2, ms=5, label="非伪善帖")
ax.plot(x, tab["伪善帖"], "-^", color="#C44E52", lw=2, ms=5, label="伪善帖")

# 关键点数值标注：前期优势（9-10/11）与反转（9-15/16）
anno = [(0, "288 vs 33"), (1, "277 vs 45"), (4, "38 vs 50"), (5, "25 vs 43")]
for i, lab in anno:
    y = max(tab["伪善帖"][i], tab["非伪善帖"][i])
    ax.annotate(lab, (x[i], y), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=9, color="#555555")
# 其余点小数值
for i in range(8):
    if i not in dict(anno):
        ax.annotate(f"{tab['伪善帖'][i]:.0f}", (x[i], tab["伪善帖"][i]),
                    textcoords="offset points", xytext=(8, -2), fontsize=8, color="#C44E52")
        ax.annotate(f"{tab['非伪善帖'][i]:.0f}", (x[i], tab["非伪善帖"][i]),
                    textcoords="offset points", xytext=(-14, -10), fontsize=8, color="#4C72B0")
    ax.annotate(f"{tab['所有帖子'][i]:.0f}", (x[i], tab["所有帖子"][i]),
                textcoords="offset points", xytext=(6, 8), fontsize=8, color="#333333")

# 事件竖线
for ev, day in [("9-12 爆发", 1), ("9-13 动员大会", 2), ("9-15 道歉", 4)]:
    ax.axvline(day, color="gray", ls="--", lw=0.9, alpha=0.7)
    ax.text(day, ax.get_ylim()[1] * 0.97, ev, rotation=90, va="top", ha="right",
            fontsize=8.5, color="gray")

ax.set_xticks(x)
ax.set_xticklabels(xl)
ax.set_xlabel("日期（9 月）")
ax.set_ylabel("单帖平均互动（转发+评论+点赞）")
ax.set_title("伪善帖与非伪善帖的单帖平均互动按天变化")
ax.legend(frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
dst = r"E:\文档\obsidian\毕设\汇报\media\微博_按天_平均互动.png"
fig.savefig(dst, dpi=150)
plt.close()
print("已保存：", dst)
