# -*- coding: utf-8 -*-
"""
06_主题与CAD交叉.py
==================
【内容】把 NMF 主题聚类结果接上 CAD 变量：每个主题的帖子规模、虚伪命中率、
        三类情绪命中率、互动量——回答"大家在讨论什么、哪些讨论最情绪化/最虚伪/传播最广"。
【方法】NMF_assignments（含互动量与阶段）左连接 CAD命中_明细，按 dominant_topic 聚合。
【输出】描述性统计结果/主题聚类/
  topic_names.csv        主题命名与描述（人工命名初版）
  topic_profile.csv      主题×帖子数/占比/虚伪率/三情绪率/互动量
  topic_phase_share.png  主题×阶段占比堆叠图
  topic_profile.png      主题规模 + 虚伪/情绪命中率组合图
  topic_engagement.png   主题×互动量（log 刻度箱线或均值柱）
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import OUT_DIR as DESC_OUT, save_fig, to_csv

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "analysis"))
TOPIC_DIR = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "主题聚类")
CAD_PATH = os.path.join(SCRIPT_DIR, "..", "分词与命中", "结果", "CAD命中_明细.csv")

# ---------- 主题命名（依据现行 weibo关键词_nmf_nva_topic_words.csv 校准） ----------
TOPIC_NAMES = {
    0: ("餐饮行业预制菜质疑", "对预制菜行业本身的质疑与讨论"),
    1: ("平台资讯聚合", "智搜/热点/卡片等机器聚合资讯"),
    2: ("道歉与致歉信", "西贝发布道歉信、整改承诺（华与华操刀）"),
    3: ("贾国龙回应", "创始人回应与“网络黑社会”言论争议"),
    4: ("门店后厨与配方", "后厨调整、转基因大豆油、冷冻预制、儿童餐等细节"),
    5: ("罗永浩相关争论", "罗永浩吐槽馒头/菜单/账单，起诉与放弃追究等交锋"),
    6: ("隔夜菜指控", "对隔夜菜、赏味期与具体菜品的指控与核实"),
    7: ("动员大会事件", "内部作战/动员大会相关讨论"),
    8: ("公关危机评论", "对公关策略的灾难级评价与危机复盘"),
    9: ("致歉信文本讨论", "对致歉信文本（“初恋”等表述）的逐句讨论"),
}


def main():
    assign = pd.read_csv(os.path.join(TOPIC_DIR, "weibo关键词_nmf_nva_assignments.csv"),
                         encoding="utf-8-sig", dtype={"ID": str})
    cad = pd.read_csv(CAD_PATH, encoding="utf-8-sig", dtype={"ID": str})
    d = assign.merge(cad, on="ID", how="inner")

    d["topic_name"] = d["dominant_topic"].map(
        lambda t: TOPIC_NAMES[t][0] if t in TOPIC_NAMES else f"主题{t}")

    # ---- 主题画像表 ----
    rows = []
    for t, sub in d.groupby("dominant_topic"):
        n = len(sub)
        rows.append({
            "topic_id": t,
            "主题": TOPIC_NAMES.get(t, (f"主题{t}", ""))[0],
            "说明": TOPIC_NAMES.get(t, ("", ""))[1],
            "帖子数": n,
            "占比%": round(n / len(d) * 100, 1),
            "虚伪命中率%": round((sub["hyp_hit_cad"] > 0).mean() * 100, 1),
            "愤怒命中率%": round((sub["anger_hit_cad"] > 0).mean() * 100, 1),
            "厌恶命中率%": round((sub["disgust_hit_cad"] > 0).mean() * 100, 1),
            "鄙视命中率%": round((sub["contempt_hit_cad"] > 0).mean() * 100, 1),
            "互动均值": round(sub["total_engagement"].mean(), 1),
            "互动中位": sub["total_engagement"].median(),
            "零互动率%": round((sub["total_engagement"] == 0).mean() * 100, 1),
        })
    prof = pd.DataFrame(rows).sort_values("帖子数", ascending=False)
    to_csv(prof, os.path.join("主题聚类", "topic_profile.csv"))
    to_csv(pd.DataFrame([{"topic_id": k, "主题": v[0], "说明": v[1]}
                         for k, v in sorted(TOPIC_NAMES.items())]),
           os.path.join("主题聚类", "topic_names.csv"))

    print("=== 主题画像（按帖子数排序）===")
    print(prof.to_string(index=False, max_colwidth=30))

    # ---- 图 1：主题规模 + 虚伪/情绪命中率 ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    prof_s = prof.sort_values("帖子数")
    ax.barh(prof_s["主题"], prof_s["帖子数"], color="#4C72B0")
    for i, v in enumerate(prof_s["帖子数"]):
        ax.text(v, i, f" {v/1000:.1f}k", va="center", fontsize=8)
    ax.set_xlabel("帖子数"); ax.set_title("各主题帖子规模")
    ax = axes[1]
    emo_cols = ["虚伪命中率%", "愤怒命中率%", "厌恶命中率%", "鄙视命中率%"]
    x = np.arange(len(prof_s)); w = 0.2
    for j, c in enumerate(emo_cols):
        ax.bar(x + (j - 1.5) * w, prof_s[c], w, label=c.replace("命中率%", ""))
    ax.set_xticks(x); ax.set_xticklabels(prof_s["主题"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("命中率 %"); ax.set_title("各主题 CAD 词汇命中率")
    ax.legend(fontsize=8)
    fig.tight_layout()
    save_fig(os.path.join("主题聚类", "topic_profile.png"))

    # ---- 图 2：主题×阶段占比堆叠 ----
    ps = pd.read_csv(os.path.join(TOPIC_DIR, "NMF_phase_share.csv"), encoding="utf-8-sig")
    ps["topic_name"] = ps["dominant_topic"].map(lambda t: TOPIC_NAMES.get(t, (f"主题{t}", ""))[0])
    pv = ps.pivot_table(index="phase", columns="topic_name",
                        values="share_within_phase", aggfunc="sum")
    pv = pv[[c for c in prof.sort_values("帖子数")["主题"] if c in pv.columns]]
    fig, ax = plt.subplots(figsize=(10, 5))
    pv.T.plot(kind="bar", stacked=True, ax=ax,
              color=["#4C72B0", "#DD8452", "#55A868"])
    ax.set_ylabel("阶段内占比"); ax.set_xlabel("主题")
    ax.legend(title="阶段")
    ax.set_title("主题×阶段：讨论焦点如何演变")
    fig.tight_layout()
    save_fig(os.path.join("主题聚类", "topic_phase_share.png"))

    # ---- 图 3：主题×互动量（log 箱线） ----
    fig, ax = plt.subplots(figsize=(10, 5))
    d["log_eng"] = np.log1p(d["total_engagement"])
    order = prof.sort_values("互动中位")["主题"].tolist()
    data = [d[d["topic_name"] == t]["log_eng"].values for t in order]
    ax.boxplot(data, vert=False, labels=[f"{t}" for t in order], showfliers=False)
    ax.set_xlabel("log(总互动+1)"); ax.set_title("各主题互动量分布（剔异常值）")
    fig.tight_layout()
    save_fig(os.path.join("主题聚类", "topic_engagement.png"))

    print(f"\n已写入: {TOPIC_DIR}")


if __name__ == "__main__":
    main()
