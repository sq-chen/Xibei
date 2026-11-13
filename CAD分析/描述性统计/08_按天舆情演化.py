# -*- coding: utf-8 -*-
"""
08_按天舆情演化.py
==================
导师意见补充：描述性统计/热词/聚类具体到**按天**，反映舆情演变。
时间口径：宽表 days_since_start（24h 天，天 0 = 2025-09-10 16:55 起 7 小时，其余整天）。

内容：
① 每日发帖量 + 虚伪/三情绪命中率（折线+柱组合图）；
② 每日热词 top20（名动形 token 词频，停用词同 05；图取 top10）；
③ 每日主题份额（全局 NMF 十主题 dominant 分配 × 天，堆叠面积图）；
④ 每日虚伪帖 vs 非虚伪帖平均互动量。

输出：描述性统计结果/按天舆情/
  daily_rate.csv、daily_topwords.csv、daily_topic_share.csv、daily_engagement.csv、
  按天_命中率与发帖量.png、按天_热词top10.png、按天_主题份额.png、按天_虚伪vs非虚伪互动.png
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAD_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
ANALYSIS = os.path.normpath(os.path.join(CAD_ROOT, "..", "analysis"))
WIDE_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果",
                         "merged_wide_v2.csv")
CAD_PATH = os.path.join(CAD_ROOT, "分词与命中", "结果", "CAD命中_明细.csv")
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果",
                        "分词", "weibo关键词_分词结果.pickle")
STOP_PATH = os.path.join(ANALYSIS, "词典", "stopwords.txt")
NMF_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果",
                        "主题聚类", "weibo关键词_nmf_nva_assignments.csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "描述性统计结果", "按天舆情")
os.makedirs(OUT_DIR, exist_ok=True)

CATS = ["虚伪", "愤怒", "厌恶", "鄙视"]
EMO_CATS = ["愤怒", "厌恶", "鄙视"]
CAT_COLS = {"虚伪": "hyp_hit_cad", "愤怒": "anger_hit_cad",
            "厌恶": "disgust_hit_cad", "鄙视": "contempt_hit_cad"}
EMO_COLS = {"愤怒": "anger_hit_cad", "厌恶": "disgust_hit_cad",
            "鄙视": "contempt_hit_cad"}
EXTRA_STOP = ["智搜", "卡片", "秒懂", "热点", "看看", "分享", "微博", "内容", "相关",
              "明白", "链接", "详情", "点击", "查看", "全文", "网页", "客户端", "转发",
              "评论", "视频", "文章", "发布", "账号", "新闻", "报道", "原标题"]
# 主题 id -> 名称（依据 NMF top 词与汇报文档表格对应）
TOPIC_NAMES = {0: "餐饮行业预制菜质疑", 1: "平台资讯聚合", 2: "道歉与致歉信",
               3: "贾国龙回应", 4: "门店后厨与配方", 5: "罗永浩相关争论",
               6: "隔夜菜指控", 7: "动员大会事件", 8: "公关危机评论",
               9: "致歉信文本讨论"}
DAY_LABELS = ["09-10", "09-11", "09-12", "09-13", "09-14", "09-15", "09-16", "09-17"]


def save_fig(name):
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def to_csv(df, name):
    df.to_csv(os.path.join(OUT_DIR, name), index=False, encoding="utf-8-sig")


# ---------- 数据加载 ----------
wide = pd.read_csv(WIDE_PATH, encoding="utf-8-sig", dtype={"ID": str})
cad = pd.read_csv(CAD_PATH, encoding="utf-8-sig", dtype={"ID": str})
d = wide.merge(cad, on="ID", how="inner")
d["day"] = d["days_since_start"].astype(int)
print(f"样本: {len(d)} 帖; 天数: {sorted(d['day'].unique())}")

# ---------- ① 每日发帖量 + 命中率 ----------
daily = d.groupby("day").agg(
    发帖量=("ID", "size"),
    **{f"{cat}命中率": (CAT_COLS[cat], lambda s: 100 * (s > 0).mean()) for cat in CATS},
).reset_index()
daily.insert(0, "日期", daily["day"].map(lambda i: DAY_LABELS[i] if i < len(DAY_LABELS) else f"day{i}"))
to_csv(daily, "daily_rate.csv")
print("\n=== ① 每日发帖量与命中率 ===")
print(daily.to_string(index=False))

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(daily.index, daily["发帖量"], color="#DDDDDD", label="发帖量")
ax1.set_ylabel("发帖量")
ax1.set_xticks(daily.index)
ax1.set_xticklabels(daily["日期"], rotation=0)
ax1.set_xlabel("日期（2025-09-10 16:55 起，首尾两日各约 7 小时）")
ax2 = ax1.twinx()
colors = {"虚伪": "#333333", "愤怒": "#C44E52", "厌恶": "#55A868", "鄙视": "#8172B2"}
for cat in CATS:
    ax2.plot(daily.index, daily[f"{cat}命中率"], marker="o", ms=4,
             color=colors[cat], label=f"{cat}命中率")
ax2.set_ylabel("命中率 %")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper center", ncol=5, fontsize=9)
ax1.set_title("按天：发帖量与四类词命中率（首尾两日各约 7h）")
save_fig("按天_命中率与发帖量.png")

# ---------- ② 每日热词 top20 ----------
stopwords = set(s.strip("\n") for s in open(STOP_PATH, encoding="utf-8")) | set(EXTRA_STOP)
seg = pd.read_pickle(SEG_PATH)[["ID", "名动形"]]
seg["ID"] = seg["ID"].astype(str).str.strip()
seg = seg.merge(d[["ID", "day"]], on="ID", how="inner")

rows = []
for day, sub in seg.groupby("day"):
    counter = Counter()
    for wl in sub["名动形"]:
        for tok in wl:
            w = str(tok[0]).strip()
            if w and w not in stopwords and len(w) >= 2:
                counter[w] += 1
    total = sum(counter.values())
    for rank, (w, c) in enumerate(counter.most_common(20), 1):
        rows.append({"day": day, "日期": DAY_LABELS[day] if day < len(DAY_LABELS) else f"day{day}",
                     "rank": rank, "词": w, "词频": c,
                     "占比%": round(100 * c / total, 2)})
hot = pd.DataFrame(rows)
to_csv(hot, "daily_topwords.csv")
print("\n=== ② 每日热词 top8 ===")
for day in sorted(hot["day"].unique()):
    ws = hot[hot["day"] == day].head(8)
    print(DAY_LABELS[day], ": ", "、".join(f"{r['词']}({r['词频']})" for _, r in ws.iterrows()))

fig, axes = plt.subplots(2, 4, figsize=(14, 8))
for i, day in enumerate(sorted(hot["day"].unique())):
    ax = axes[i // 4][i % 4]
    sub = hot[hot["day"] == day].head(10)
    ax.barh(np.arange(len(sub))[::-1], sub["词频"], color="#4C72B0")
    ax.set_yticks(np.arange(len(sub))[::-1])
    ax.set_yticklabels(sub["词"], fontsize=8)
    ax.set_title(f"{DAY_LABELS[day]}（{int(daily.loc[daily['day'] == day, '发帖量'].iloc[0])} 帖）",
                 fontsize=10)
    ax.tick_params(axis="x", labelsize=8)
fig.suptitle("按天热词 top10（名动形词频，去停用词）", fontsize=13)
save_fig("按天_热词top10.png")

# ---------- ③ 每日主题份额 ----------
nmf = pd.read_csv(NMF_PATH, encoding="utf-8-sig", dtype={"ID": str})
nmf = nmf.merge(d[["ID", "day"]], on="ID", how="inner")
share = nmf.groupby(["day", "dominant_topic"]).size().reset_index(name="posts")
tot = share.groupby("day")["posts"].transform("sum")
share["份额%"] = 100 * share["posts"] / tot
share["主题"] = share["dominant_topic"].map(TOPIC_NAMES)
to_csv(share[["day", "dominant_topic", "主题", "posts", "份额%"]], "daily_topic_share.csv")
print("\n=== ③ 每日主题份额（%）===")
piv = share.pivot(index="主题", columns="day", values="份额%")
piv.columns = [DAY_LABELS[c] if c < len(DAY_LABELS) else f"day{c}" for c in piv.columns]
print(piv.round(1).to_string())

cmap = plt.get_cmap("tab20")
fig, ax = plt.subplots(figsize=(11, 5.5))
days = sorted(share["day"].unique())
bottom = np.zeros(len(days))
for t in range(10):
    vals = [share[(share["day"] == d) & (share["dominant_topic"] == t)]["份额%"].sum()
            for d in days]
    ax.bar(days, vals, bottom=bottom, label=TOPIC_NAMES[t], color=cmap(t))
    bottom += np.array(vals)
ax.set_xticks(days)
ax.set_xticklabels([DAY_LABELS[d] if d < len(DAY_LABELS) else f"day{d}" for d in days])
ax.set_ylabel("主题份额 %")
ax.set_xlabel("日期（首尾两日各约 7h）")
ax.set_title("按天：十大主题份额演化（全局 NMF 主题分配）")
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8)
save_fig("按天_主题份额.png")

# ---------- ④ 每日虚伪 vs 非虚伪互动 ----------
d["is_hyp"] = d["hyp_hit_binary_cad"] == 1
eng = d.groupby(["day", "is_hyp"]).agg(
    帖数=("ID", "size"),
    互动均值=("total_engagement", "mean"),
    互动中位=("total_engagement", "median"),
).reset_index()
eng["组"] = np.where(eng["is_hyp"], "虚伪帖", "非虚伪帖")
eng.insert(0, "日期", eng["day"].map(lambda i: DAY_LABELS[i] if i < len(DAY_LABELS) else f"day{i}"))
to_csv(eng[["日期", "day", "组", "帖数", "互动均值", "互动中位"]], "daily_engagement.csv")
print("\n=== ④ 每日互动均值 ===")
print(eng[["日期", "组", "帖数", "互动均值"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 4.5))
for grp, color, mk in [("虚伪帖", "#C44E52", "o"), ("非虚伪帖", "#888888", "s")]:
    sub = eng[eng["组"] == grp]
    ax.plot(sub["day"], sub["互动均值"], marker=mk, ms=5, color=color, label=grp)
ax.set_xticks(days)
ax.set_xticklabels([DAY_LABELS[d] if d < len(DAY_LABELS) else f"day{d}" for d in days])
ax.set_ylabel("平均总互动")
ax.set_xlabel("日期（首尾两日各约 7h）")
ax.set_title("按天：虚伪帖 vs 非虚伪帖平均互动量")
ax.legend()
save_fig("按天_虚伪vs非虚伪互动.png")

print(f"\n已写入: {OUT_DIR}")
