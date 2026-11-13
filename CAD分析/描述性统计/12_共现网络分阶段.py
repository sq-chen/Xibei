# -*- coding: utf-8 -*-
"""
12_共现网络分阶段.py
====================
W-4 共现网络分阶段对比（P1/P2/P3，表现层）：
  - 每期：高频词（名动形，剔停用词与品牌词）top150 → 帖内共现边 → Louvain 社区
  - 对比：三期社区数、模块度、中心词、社区构成；相邻期 top 词重叠（Jaccard）与新词/退场词
输出：描述性统计结果/主题聚类/cooccur_phase_edges_*.csv、cooccur_phase_communities_*.csv、
      cooccur_phase_network.png（三期并排）、cooccur_phase_summary.csv
"""
import os
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from _common import OUT_DIR, to_csv

ANALYSIS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "analysis"))
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "分词",
                        "weibo关键词_分词结果.pickle")
STOP_PATH = os.path.join(ANALYSIS, "词典", "stopwords.txt")
ASSIGN_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "主题聚类",
                           "weibo关键词_nmf_nva_assignments.csv")

TOP_N = 150
MIN_EDGE = {"P1": 15, "P2": 20, "P3": 20}   # 三期帖量不同，阈值按规模调
RANDOM_STATE = 42

EXTRA_STOP = ["智搜", "卡片", "秒懂", "热点", "看看", "分享", "微博", "内容", "相关",
              "明白", "链接", "详情", "点击", "查看", "全文", "网页", "客户端", "转发",
              "评论", "视频", "文章", "发布", "账号", "新闻", "报道", "原标题",
              "西贝", "莜面村"]

stopwords = set(s.strip("\n") for s in open(STOP_PATH, encoding="utf-8"))
stopwords |= set(EXTRA_STOP)

df = pd.read_pickle(SEG_PATH)
asg = pd.read_csv(ASSIGN_PATH, encoding="utf-8-sig", dtype={"ID": str})[["ID", "phase"]]
df = df.merge(asg, on="ID", how="left")

PHASES = ["P1", "P2", "P3"]


def build_network(docs):
    freq = Counter()
    for ws in docs:
        freq.update(ws)
    top = [w for w, _ in freq.most_common(TOP_N)]
    top_set = set(top)
    pair_cnt = Counter()
    for ws in docs:
        uniq = [w for w in set(ws) if w in top_set]
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                pair_cnt[(uniq[i], uniq[j])] += 1
    return freq, top, pair_cnt


summ_rows = []
phase_data = {}
for ph in PHASES:
    sub = df[df["phase"] == ph]
    docs = []
    for tl in sub["名动形"]:
        docs.append([str(t[0]).strip() for t in tl
                     if t and str(t[0]).strip() not in stopwords
                     and len(str(t[0]).strip()) >= 2])
    freq, top, pair_cnt = build_network(docs)
    edges = [(a, b, c) for (a, b), c in pair_cnt.items() if c >= MIN_EDGE[ph]]
    G = nx.Graph()
    for w in top:
        G.add_node(w, freq=freq[w])
    for a, b, c in edges:
        G.add_edge(a, b, weight=c)
    comms = list(nx.community.louvain_communities(
        G, weight="weight", resolution=1.3, seed=RANDOM_STATE))
    comms.sort(key=len, reverse=True)
    mod = nx.community.modularity(G, comms, weight="weight")
    # 社区词表
    comm_rows = []
    for ci, comm in enumerate(comms):
        for w in sorted(comm, key=lambda x: G.nodes[x]["freq"], reverse=True):
            comm_rows.append({"phase": ph, "community": ci, "word": w,
                              "freq": G.nodes[w]["freq"]})
    to_csv(pd.DataFrame(comm_rows),
           os.path.join("主题聚类", f"cooccur_phase_communities_{ph}.csv"))
    to_csv(pd.DataFrame(edges, columns=["source", "target", "weight"]),
           os.path.join("主题聚类", f"cooccur_phase_edges_{ph}.csv"))
    # 每社区 top5 中心词
    comm_top = "; ".join(
        f"C{ci}:{'/'.join(sorted(c, key=lambda x: G.nodes[x]['freq'], reverse=True)[:5])}"
        for ci, c in enumerate(comms[:6]))
    summ_rows.append({"phase": ph, "N帖": len(docs), "节点数": G.number_of_nodes(),
                      "边数": G.number_of_edges(), "社区数": len(comms),
                      "模块度": round(mod, 3), "前6社区top5词": comm_top})
    phase_data[ph] = dict(freq=freq, top=top, G=G, comms=comms)
    print(f"[{ph}] 帖 {len(docs)} | 节点 {G.number_of_nodes()} | 边 {G.number_of_edges()} | "
          f"社区 {len(comms)} | 模块度 {mod:.3f}")

summ = pd.DataFrame(summ_rows)
to_csv(summ, os.path.join("主题聚类", "cooccur_phase_summary.csv"))
print("\n=== 三期网络概要 ===\n" + summ[["phase", "N帖", "节点数", "边数", "社区数", "模块度"]].to_string(index=False))
print("\n=== 三期社区 top5 词 ===\n" + summ[["phase", "前6社区top5词"]].to_string(index=False))

# ---------- 相邻期词重叠 ----------
for a, b in [("P1", "P2"), ("P2", "P3")]:
    ta, tb = set(phase_data[a]["top"]), set(phase_data[b]["top"])
    jac = len(ta & tb) / len(ta | tb)
    new = sorted(tb - ta, key=lambda w: -phase_data[b]["freq"][w])[:15]
    gone = sorted(ta - tb, key=lambda w: -phase_data[a]["freq"][w])[:15]
    print(f"\n[{a}→{b}] top150 Jaccard = {jac:.3f}")
    print(f"  新进高频词: {' '.join(new)}")
    print(f"  退场高频词: {' '.join(gone)}")

# ---------- 三期并排网络图 ----------
fig, axes = plt.subplots(1, 3, figsize=(21, 7))
for ai, ph in enumerate(PHASES):
    G = phase_data[ph]["G"]
    comms = phase_data[ph]["comms"]
    cmap = {}
    for ci, c in enumerate(comms):
        for w in c:
            cmap[w] = ci
    sub = G.subgraph([n for n in G.nodes if n in cmap]).copy()
    pos = nx.spring_layout(sub, seed=RANDOM_STATE, k=.6)
    node_colors = [cmap[n] for n in sub.nodes]
    sizes = [np.log1p(sub.nodes[n]["freq"]) * 55 for n in sub.nodes]
    top5 = set()
    for c in comms[:6]:
        top5 |= set(sorted(c, key=lambda x: G.nodes[x]["freq"], reverse=True)[:4])
    labels = {n: n for n in sub.nodes if n in top5}
    nx.draw_networkx_edges(sub, pos, alpha=.12, width=.5)
    nx.draw_networkx_nodes(sub, pos, node_color=node_colors, node_size=sizes,
                           cmap=plt.cm.tab20, alpha=.85)
    nx.draw_networkx_labels(sub, pos, labels, font_size=8)
    axes[ai].set_title(f"{ph}（{len(sub)} 节点 / {len(comms)} 社区 / 模块度 {nx.community.modularity(G, comms, weight='weight'):.3f}）")
    axes[ai].axis("off")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "主题聚类", "cooccur_phase_network.png"), dpi=150)
plt.close()
print("\n已导出：描述性统计结果/主题聚类/cooccur_phase_*（边表/社区词表/概要/三期并排网络图）")
