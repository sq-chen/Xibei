# -*- coding: utf-8 -*-
"""
16_按天总互动量.py
==================
汇报用图：伪善帖 / 非伪善帖 / 所有帖子 的总互动量（转发+评论+点赞，按天求和）随时间变化曲线。
表现层描述；标签口径与汇报文档一致（伪善）。事件竖线：9-12 爆发 / 9-13 动员大会 / 9-15 道歉。
输出：毕设/汇报/media/微博_按天_总互动量.png + 描述性统计结果/按天总互动量.csv
"""
import pandas as pd

from _common import load_data, OUT_DIR, to_csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- 1. 数据 ----------
d = load_data()
d["day"] = d["created_at"].dt.floor("D")
d = d[d["day"].notna()]
days = sorted(d["day"].unique())
assert len(days) == 8, f"天数异常: {days}"

d["hyp"] = d["hyp_hit_cad"] > 0
rows = []
for day in days:
    dd = d[d["day"] == day]
    rows.append({
        "日期": day.strftime("%m-%d"),
        "伪善帖总互动": dd.loc[dd["hyp"], "total_engagement"].sum(),
        "非伪善帖总互动": dd.loc[~dd["hyp"], "total_engagement"].sum(),
        "所有帖子总互动": dd["total_engagement"].sum(),
    })
tab = pd.DataFrame(rows)
to_csv(tab, "按天总互动量.csv")
print(tab.to_string(index=False))

# ---------- 2. 绘图 ----------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(10, 5))
x = list(range(8))
xl = tab["日期"]
ax.plot(x, tab["所有帖子总互动"] / 1e4, "-o", color="#333333", lw=2, ms=5,
        label="所有帖子")
ax.plot(x, tab["非伪善帖总互动"] / 1e4, "-s", color="#4C72B0", lw=2, ms=5,
        label="非伪善帖")
ax.plot(x, tab["伪善帖总互动"] / 1e4, "-^", color="#C44E52", lw=2, ms=5,
        label="伪善帖")
# 峰值标注
for col, c in [("所有帖子总互动", "#333333"), ("非伪善帖总互动", "#4C72B0"),
               ("伪善帖总互动", "#C44E52")]:
    i = tab[col].idxmax()
    ax.annotate(f"{tab[col][i]/1e4:.1f}万", (x[i], tab[col][i] / 1e4),
                textcoords="offset points", xytext=(0, 7), ha="center",
                fontsize=9, color=c)
# 事件竖线
for ev, day in [("9-12 爆发", 1), ("9-13 动员大会", 2), ("9-15 道歉", 4)]:
    ax.axvline(day, color="gray", ls="--", lw=0.9, alpha=0.7)
    ax.text(day, ax.get_ylim()[1] * 0.95, ev, rotation=90, va="top", ha="right",
            fontsize=8.5, color="gray")
ax.set_xticks(x)
ax.set_xticklabels(xl)
ax.set_xlabel("日期（9 月）")
ax.set_ylabel("总互动量（万）")
ax.set_title("伪善帖 / 非伪善帖 / 所有帖子 总互动量按天变化")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
dst = r"E:\文档\obsidian\毕设\汇报\media\微博_按天_总互动量.png"
fig.savefig(dst, dpi=150)
plt.close()
print("已保存：", dst)
