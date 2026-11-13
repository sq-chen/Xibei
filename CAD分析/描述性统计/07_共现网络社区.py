# -*- coding: utf-8 -*-
"""
07_共现网络社区.py
==================
【内容】高频词共现网络 + 社区检测：把"哪些词常在一起被讨论"画成网络，
        社区即自然的讨论簇（比主题词表更直观）。
【方法】① 名动形分词统计词频，取 top N 高频词（剔除停用词与微博噪声词）；
        ② 帖内两两共现计数得加权边（仅保留两端都在 top N 内的边）；
        ③ networkx 构图 → Louvain 社区检测（resolution=1.3）；
        ④ spring 布局出图（节点大小=词频，颜色=社区，边透明度=权重）。
【输出】描述性统计结果/主题聚类/
  cooccur_edges.csv        共现边表（source,target,weight；可导入 Gephi）
  cooccur_communities.csv  社区词表（社区 ID + 词 + 词频）
  cooccur_network.png      共现网络图
"""
import os
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx


from _common import OUT_DIR, save_fig, to_csv

ANALYSIS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "analysis"))
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "分词",
                        "weibo关键词_分词结果.pickle")
STOP_PATH = os.path.join(ANALYSIS, "词典", "stopwords.txt")

TOP_N = 180          # 进入网络的词数
MIN_EDGE = 30        # 边最低共现次数（低于此忽略）
RANDOM_STATE = 42

EXTRA_STOP = ["智搜", "卡片", "秒懂", "热点", "看看", "分享", "微博", "内容", "相关",
              "明白", "链接", "详情", "点击", "查看", "全文", "网页", "客户端", "转发",
              "评论", "视频", "文章", "发布", "账号", "新闻", "报道", "原标题",
              "西贝", "莜面村"]   # 品牌名几乎与所有主题共现，会拉全图，剔除


def main():
    stopwords = set(s.strip("\n") for s in open(STOP_PATH, encoding="utf-8"))
    stopwords |= set(EXTRA_STOP)

    df = pd.read_pickle(SEG_PATH)
    docs = []
    freq = Counter()
    for tl in df["名动形"]:
        words = [str(t[0]).strip() for t in tl
                 if t and str(t[0]).strip() not in stopwords and len(str(t[0]).strip()) >= 2]
        docs.append(words)
        freq.update(words)
    top_words = [w for w, _ in freq.most_common(TOP_N)]
    top_set = set(top_words)
    print(f"文档 {len(docs)}，top{TOP_N} 词中最高频: {top_words[:10]}")

    # 帖内共现计数
    pair_cnt = Counter()
    for words in docs:
        ws = [w for w in set(words) if w in top_set]
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                pair_cnt[(ws[i], ws[j])] += 1

    edges = [(a, b, c) for (a, b), c in pair_cnt.items() if c >= MIN_EDGE]
    print(f"边数（≥{MIN_EDGE}）: {len(edges)}")
    to_csv(pd.DataFrame(edges, columns=["source", "target", "weight"]),
           os.path.join("主题聚类", "cooccur_edges.csv"))

    # 构图 + 社区
    G = nx.Graph()
    for w in top_words:
        G.add_node(w, freq=freq[w])
    for a, b, c in edges:
        G.add_edge(a, b, weight=c)

    communities = list(nx.community.louvain_communities(
        G, weight="weight", resolution=1.3, seed=RANDOM_STATE))
    communities.sort(key=len, reverse=True)
    comm_map = {}
    comm_rows = []
    for ci, comm in enumerate(communities):
        for w in sorted(comm, key=lambda x: G.nodes[x]["freq"], reverse=True):
            comm_map[w] = ci
            comm_rows.append({"社区": ci, "词": w, "词频": G.nodes[w]["freq"],
                              "社区内词数": len(comm)})
    to_csv(pd.DataFrame(comm_rows), os.path.join("主题聚类", "cooccur_communities.csv"))
    print(f"\n社区数: {len(communities)}")
    for ci, comm in enumerate(communities[:8]):
        ws = sorted(comm, key=lambda x: G.nodes[x]["freq"], reverse=True)[:15]
        print(f"社区{ci}（{len(comm)}词）: {'、'.join(ws)}")

    # 出图：spring 布局，颜色=社区
    pos = nx.spring_layout(G, k=0.55, seed=RANDOM_STATE, weight="weight", iterations=80)
    node_colors = [comm_map.get(n, len(communities)) for n in G.nodes()]
    node_sizes = [80 + np.sqrt(G.nodes[n]["freq"]) * 18 for n in G.nodes()]
    ew = [G[u][v]["weight"] for u, v in G.edges()]

    fig, ax = plt.subplots(figsize=(14, 12))
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=G.edges(),
                           alpha=0.12, width=[0.3 + np.log1p(w) / 6 for w in ew])
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                           node_color=node_colors, cmap=plt.cm.tab20, alpha=0.85)
    labels = {n: n for n in G.nodes() if G.nodes[n]["freq"] >= freq.most_common(60)[-1][1]}
    nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=9)
    ax.set_title(f"西贝舆情高频词共现网络（top{TOP_N} 词，边≥{MIN_EDGE}，颜色=社区）")
    ax.axis("off")
    save_fig(os.path.join("主题聚类", "cooccur_network.png"))

    print(f"\n已写入: {os.path.join(OUT_DIR, '主题聚类')}")


if __name__ == "__main__":
    main()
