# -*- coding: utf-8 -*-
"""
19_共现网络改版.py
==================
整体共现网络可读性改版（原 150 节点弹簧布局标签挤成一坨）：
  1. 环形布局网络：top60 词、保留共现最强 ~250 条边，节点沿圆周排布、标签朝外
  2. 共现热力图：top50 词 × top50 词（log 色阶，按社区排序，块状结构可见）
输出：毕设/汇报/media/微博_共现网络_整体.png（覆盖）+ 微博_共现热图.png
"""
import math
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

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
docs = [[str(t[0]).strip() for t in tl
         if t and str(t[0]).strip() not in stopwords
         and len(str(t[0]).strip()) >= 2] for tl in df["名动形"]]

freq = Counter()
for ws in docs:
    freq.update(ws)
top_all = [w for w, _ in freq.most_common(150)]
top_set = set(top_all)
pair_cnt = Counter()
for ws in docs:
    uniq = [w for w in set(ws) if w in top_set]
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            pair_cnt[(uniq[i], uniq[j])] += 1

# ---------- 1. 环形网络（top60 词） ----------
TOP_RING = 60
ring_words = top_all[:TOP_RING]
ring_set = set(ring_words)
G = nx.Graph()
for w in ring_words:
    G.add_node(w, freq=freq[w])
edges = sorted(((a, b, c) for (a, b), c in pair_cnt.items()
                if a in ring_set and b in ring_set), key=lambda t: -t[2])[:250]
G.add_weighted_edges_from([(a, b, c) for a, b, c in edges])

comms = list(nx.community.louvain_communities(G, weight="weight",
                                              resolution=1.2, seed=RANDOM_STATE))
comms.sort(key=len, reverse=True)
palette = plt.cm.tab10.colors
node_color = {}
for ci, comm in enumerate(comms):
    for w in comm:
        node_color[w] = palette[ci % 10]
for w in G.nodes:
    if w not in node_color:
        node_color[w] = "#999999"

fig, ax = plt.subplots(figsize=(12.5, 12.5))
pos = nx.circular_layout(G)
nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.10, width=0.5)
sizes = [120 + 20 * math.log1p(G.nodes[n]["freq"]) for n in G.nodes]
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes,
                       node_color=[node_color[n] for n in G.nodes], alpha=0.9)
# 标签沿圆周朝外
for n, (x, y) in pos.items():
    ang = math.degrees(math.atan2(y, x))
    ha = "left" if x >= 0 else "right"
    rot = ang if x >= 0 else ang + 180
    ax.annotate(n, (x, y), xytext=(0, 0), textcoords="offset points",
                fontsize=10, color="#222222", ha=ha, va="center",
                rotation=rot, rotation_mode="anchor")
ax.set_xlim(-1.28, 1.28)
ax.set_ylim(-1.28, 1.28)
ax.set_title("全部帖子的词共现网络（环形布局，top60 高频词，颜色=社区）", fontsize=13)
ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(MEDIA, "微博_共现网络_整体.png"), dpi=150)
plt.close()
print(f"环形网络: 节点 {G.number_of_nodes()} / 边 {G.number_of_edges()} / 社区 {len(comms)}")
for ci, comm in enumerate(comms[:5]):
    print(f"  C{ci} (n={len(comm)}):", "、".join(sorted(comm, key=lambda x: -freq[x])[:10]))

# ---------- 2. 共现热力图（top50 × top50，按社区排序） ----------
TOP_HM = 50
hm_words = top_all[:TOP_HM]
# 用全量 Louvain 社区给 top50 排序（保持与报告社区表一致）
G_full = nx.Graph()
G_full.add_nodes_from(top_all)
edges_full = [(a, b, c) for (a, b), c in pair_cnt.items()
              if c >= max(1, int(sorted(pair_cnt.values(), reverse=True)[499]))]
G_full.add_weighted_edges_from(edges_full)
comms_full = list(nx.community.louvain_communities(
    G_full, weight="weight", resolution=1.3, seed=RANDOM_STATE))
comms_full.sort(key=len, reverse=True)
comm_of = {}
for ci, comm in enumerate(comms_full):
    for w in comm:
        comm_of[w] = ci
# 未进社区的词排最后
order = sorted(hm_words, key=lambda w: comm_of.get(w, 99))
idx = {w: i for i, w in enumerate(order)}
M = np.zeros((TOP_HM, TOP_HM))
for (a, b), c in pair_cnt.items():
    if a in idx and b in idx:
        M[idx[a], idx[b]] = c
        M[idx[b], idx[a]] = c

fig, ax = plt.subplots(figsize=(11, 9.5))
im = ax.imshow(np.log1p(M), cmap="YlOrRd", aspect="equal")
# 社区分块线
boundaries = []
prev = None
for i, w in enumerate(order):
    c = comm_of.get(w, 99)
    if c != prev:
        boundaries.append(i - 0.5)
        prev = c
boundaries.append(TOP_HM - 0.5)
for b in boundaries[1:-1]:
    ax.axhline(b, color="white", lw=1.6)
    ax.axvline(b, color="white", lw=1.6)
ax.set_xticks(range(TOP_HM))
ax.set_xticklabels(order, rotation=90, fontsize=8)
ax.set_yticks(range(TOP_HM))
ax.set_yticklabels(order, fontsize=8)
ax.set_title("top50 高频词共现热力图（色阶=共现次数取对数；白线=社区分界）", fontsize=12)
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label="log(共现次数+1)")
fig.tight_layout()
fig.savefig(os.path.join(MEDIA, "微博_共现热图.png"), dpi=150)
plt.close()
print("\n已输出：微博_共现网络_整体.png（环形版）/ 微博_共现热图.png")
