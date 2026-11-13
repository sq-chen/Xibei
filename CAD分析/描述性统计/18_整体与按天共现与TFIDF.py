# -*- coding: utf-8 -*-
"""
18_整体与按天共现与TFIDF.py
===========================
按新口径（不分阶段）重做词语层面分析：
  1. 整体共现网络（8 天全部帖子，top150 名动形词，Louvain 社区）→ 微博_共现网络_整体.png
  2. 按天共现网络（8 面板小图，每天 top30 词）→ 微博_共现网络_按天.png
  3. 按天 top 共现词对表 → 按天共现_词对.csv
  4. 按天 TF-IDF top5 表 → 按天_tfidf_top5.csv（idf 按 8 天计算）
输出图片直接写入 vault media；表格写入 描述性统计结果/主题聚类/。
"""
import os
import math
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from _common import to_csv

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

ANALYSIS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "analysis"))
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "分词",
                        "weibo关键词_分词结果.pickle")
STOP_PATH = os.path.join(ANALYSIS, "词典", "stopwords.txt")
MEDIA = r"E:\文档\obsidian\毕设\汇报\media"
RANDOM_STATE = 42

EXTRA_STOP = ["智搜", "卡片", "秒懂", "热点", "看看", "分享", "微博", "内容", "相关",
              "明白", "链接", "详情", "点击", "查看", "全文", "网页", "客户端", "转发",
              "评论", "视频", "文章", "发布", "账号", "新闻", "报道", "原标题",
              "西贝", "莜面村"]
stopwords = set(s.strip("\n") for s in open(STOP_PATH, encoding="utf-8"))
stopwords |= set(EXTRA_STOP)

df = pd.read_pickle(SEG_PATH)
df["day"] = pd.to_datetime(df["date"]).dt.floor("D")
days = sorted(df["day"].unique())


def docs_of(sub):
    return [[str(t[0]).strip() for t in tl
             if t and str(t[0]).strip() not in stopwords
             and len(str(t[0]).strip()) >= 2] for tl in sub["名动形"]]


def build_net(docs, top_n):
    freq = Counter()
    for ws in docs:
        freq.update(ws)
    top = [w for w, _ in freq.most_common(top_n)]
    top_set = set(top)
    pair_cnt = Counter()
    for ws in docs:
        uniq = [w for w in set(ws) if w in top_set]
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                pair_cnt[(uniq[i], uniq[j])] += 1
    return freq, top, pair_cnt


def to_graph(top, pair_cnt, min_edge):
    G = nx.Graph()
    for w in top:
        G.add_node(w)
    for (a, b), c in pair_cnt.items():
        if c >= min_edge:
            G.add_edge(a, b, weight=c)
    return G


# ---------- 1. 整体共现网络 ----------
docs_all = docs_of(df)
freq_all, top_all, pair_all = build_net(docs_all, 150)
# 只保留共现强度最高的 500 条边（否则 1 万+ 条边不可读）
weights = sorted(pair_all.values(), reverse=True)
min_edge = weights[min(500, len(weights) - 1)]
G_all = to_graph(top_all, pair_all, min_edge=min_edge)
print("整体网络 min_edge =", min_edge)
comms = list(nx.community.louvain_communities(G_all, weight="weight",
                                              resolution=1.3, seed=RANDOM_STATE))
comms.sort(key=len, reverse=True)
mod = nx.community.modularity(G_all, comms, weight="weight")
print(f"整体网络: 节点 {G_all.number_of_nodes()} / 边 {G_all.number_of_edges()} / "
      f"社区 {len(comms)} / 模块度 {mod:.3f}")
comm_rows = []
for ci, comm in enumerate(comms):
    for w in sorted(comm, key=lambda x: -freq_all[x]):
        comm_rows.append({"community": ci, "word": w, "freq": freq_all[w],
                          "top12": "、".join(sorted(comm, key=lambda x: -freq_all[x])[:12])})
to_csv(pd.DataFrame(comm_rows), os.path.join("主题聚类", "整体共现_社区.csv"))
for ci, comm in enumerate(comms[:5]):
    print(f"  C{ci} (n={len(comm)}):", "、".join(sorted(comm, key=lambda x: -freq_all[x])[:12]))

node_color = {}
palette = plt.cm.tab10.colors
for ci, comm in enumerate(comms):
    for w in comm:
        node_color[w] = palette[ci % 10]

fig, ax = plt.subplots(figsize=(13, 9))
pos = nx.spring_layout(G_all, seed=RANDOM_STATE, k=0.55, weight="weight")
nx.draw_networkx_edges(G_all, pos, ax=ax, alpha=0.14, width=0.6)
sizes = [150 + 26 * math.log1p(freq_all[n]) for n in G_all.nodes]
nx.draw_networkx_nodes(G_all, pos, ax=ax, node_size=sizes,
                       node_color=[node_color[n] for n in G_all.nodes], alpha=0.9)
nx.draw_networkx_labels(G_all, pos, ax=ax, font_size=8.5,
                        font_family="SimHei")
ax.set_title("全部帖子的词共现网络（8 天合计，top150 高频词，Louvain 社区）", fontsize=12)
ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(MEDIA, "微博_共现网络_整体.png"), dpi=150)
plt.close()

# ---------- 2. 按天共现网络（8 面板） ----------
fig, axes = plt.subplots(2, 4, figsize=(16, 9))
daily_pairs_rows = []
for k, (day, ax) in enumerate(zip(days, axes.ravel())):
    sub = df[df["day"] == day]
    docs = docs_of(sub)
    freq, top, pair_cnt = build_net(docs, 30)
    min_edge = max(2, round(len(docs) * 0.0003))
    G = to_graph(top, pair_cnt, min_edge=min_edge)
    if G.number_of_edges() == 0:
        G = to_graph(top, pair_cnt, min_edge=1)
    p = nx.spring_layout(G, seed=RANDOM_STATE, k=0.45, weight="weight")
    nx.draw_networkx_edges(G, p, ax=ax, alpha=0.3, width=0.7)
    s = [60 + 6 * math.log1p(freq[n]) for n in G.nodes]
    nx.draw_networkx_nodes(G, p, ax=ax, node_size=s, node_color="#4C72B0", alpha=0.9)
    nx.draw_networkx_labels(G, p, ax=ax, font_size=6.5, font_family="SimHei")
    ax.set_title(f"{day.strftime('%m-%d')}（{len(docs):,} 帖）", fontsize=9)
    ax.axis("off")
    # 当日 top5 共现词对
    for (a, b), c in pair_cnt.most_common(5):
        daily_pairs_rows.append({"日期": day.strftime("%m-%d"), "词对": f"{a}-{b}",
                                 "共现次数": c})
fig.suptitle("词共现网络按天变化（每天 top30 高频词）", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(os.path.join(MEDIA, "微博_共现网络_按天.png"), dpi=150)
plt.close()
to_csv(pd.DataFrame(daily_pairs_rows), os.path.join("主题聚类", "按天共现_词对.csv"))
print("\n按天 top5 共现词对:")
for day, grp in pd.DataFrame(daily_pairs_rows).groupby("日期"):
    print(f"  {day}: " + "；".join(f"{r['词对']}({r['共现次数']})" for _, r in grp.iterrows()))

# ---------- 3. 按天 TF-IDF top5（与流水线口径一致：以单条帖子为文档，idf=log(N/df)+0.1） ----------
tfidf_rows = []
for day in days:
    sub = df[df["day"] == day]
    docs = docs_of(sub)
    n_docs = len(docs)
    tf = Counter()
    df_post = Counter()
    for ws in docs:
        uniq = set(ws)
        tf.update(ws)
        df_post.update(uniq)
    scored = [(w, f * (math.log(n_docs / df_post[w]) + 0.1))
              for w, f in tf.items() if df_post[w] >= 10]
    scored.sort(key=lambda t: -t[1])
    tfidf_rows.append({"日期": day.strftime("%m-%d"),
                       "top5_tfidf": "、".join(w for w, _ in scored[:5])})
to_csv(pd.DataFrame(tfidf_rows), os.path.join("主题聚类", "按天_tfidf_top5.csv"))
print("\n按天 TF-IDF top5（帖内 df 口径）:")
print(pd.DataFrame(tfidf_rows).to_string(index=False))

print("\n已输出：微博_共现网络_整体.png / 微博_共现网络_按天.png + 3 个 CSV")
