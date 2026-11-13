# -*- coding: utf-8 -*-
"""
05_主题聚类_NMF.py
==================
【内容】用 v4 短语重跑后的分词结果重跑 NMF 主题聚类（回答"大众在讨论什么"）。
【方法】名动形分词 → 伪文档 → TfidfVectorizer（min_df=10，max_features=8000）
       → sklearn NMF（K=10，nndsvda）→ 帖-主题分配 / 主题 top 词 / 主题×阶段占比。
【与原流水线 07 的差异】① 使用 v4 短语重跑后的新分词；
                       ② 停用词补充微博自动文本噪声词（智搜/卡片/秒懂等），消除噪声主题。
【输出】描述性统计结果/主题聚类/
  NMF_assignments.csv（帖×主题混合比例 + dominant_topic + phase）
  NMF_topic_words.csv（各主题 top15 词）
  NMF_phase_share.csv（主题×阶段帖子占比）
  NMF_model_info.txt（参数与重构误差）
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "描述性统计结果", "主题聚类")
os.makedirs(OUT_DIR, exist_ok=True)

ANALYSIS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "analysis"))
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "分词",
                        "weibo关键词_分词结果.pickle")
STOP_PATH = os.path.join(ANALYSIS, "词典", "stopwords.txt")
WIDE_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "merged_wide_v2.csv")

N_TOPICS = 10
MIN_DF = 10
MAX_FEATURES = 8000
MAX_ITER = 200
RANDOM_STATE = 42
TOP_WORDS = 15

# 微博自动文本/通用噪声词（原停用词表未覆盖，导致旧结果出现"智搜"噪声主题）
EXTRA_STOP = ["智搜", "卡片", "秒懂", "热点", "看看", "分享", "微博", "内容", "相关",
              "明白", "链接", "详情", "点击", "查看", "全文", "网页", "客户端", "转发",
              "评论", "视频", "文章", "发布", "账号", "新闻", "报道", "原标题"]

TOKEN_RULE = r"([一-鿕\U00010000-\U0010ffffa-zA-Z0-9+#&:\._\-% ]{2,})￥"


def tokens_to_doc(token_list):
    if not isinstance(token_list, list) or not token_list:
        return ""
    parts = [str(t[0]).strip() for t in token_list if t]
    return "￥".join(p for p in parts if p) + "￥"


def main():
    stopwords = [s.strip("\n") for s in open(STOP_PATH, encoding="utf-8")]
    stopwords = stopwords + EXTRA_STOP

    df = pd.read_pickle(SEG_PATH)
    df["__doc__"] = df["名动形"].map(tokens_to_doc)
    df = df[df["__doc__"].str.len() > 0].reset_index(drop=True)
    print(f"文档数: {len(df)}")

    vec = TfidfVectorizer(stop_words=stopwords, token_pattern=TOKEN_RULE,
                          min_df=MIN_DF, max_features=MAX_FEATURES)
    dt = vec.fit_transform(df["__doc__"])
    vocab = vec.get_feature_names_out()
    print(f"词表: {dt.shape[1]} 词")

    nmf = NMF(n_components=N_TOPICS, init="nndsvda", random_state=RANDOM_STATE,
              max_iter=MAX_ITER, alpha_W=0.0, alpha_H=0.0, l1_ratio=0.0)
    doc_topic = nmf.fit_transform(dt)
    topic_word = nmf.components_

    row_sums = doc_topic.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    doc_topic_norm = doc_topic / row_sums

    assign = pd.DataFrame(doc_topic_norm,
                          columns=[f"topic_{i}" for i in range(N_TOPICS)])
    assign.insert(0, "dominant_topic", doc_topic_norm.argmax(axis=1))
    assign.insert(0, "ID", df["ID"].astype(str).str.strip())

    # 阶段来自宽表（与原流水线一致）
    wide = pd.read_csv(WIDE_PATH, encoding="utf-8-sig", dtype={"ID": str},
                       usecols=["ID", "phase", "total_engagement",
                                "reposts_count", "comments_count", "attitudes_count"])
    assign = assign.merge(wide, on="ID", how="left")

    assign.to_csv(os.path.join(OUT_DIR, "NMF_assignments.csv"),
                  index=False, encoding="utf-8-sig")

    rows = []
    for k in range(N_TOPICS):
        order = np.argsort(topic_word[k])[::-1][:TOP_WORDS]
        for rank, idx in enumerate(order, 1):
            rows.append({"topic_id": k, "rank": rank, "word": vocab[idx],
                         "weight": float(topic_word[k, idx])})
    pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, "NMF_topic_words.csv"),
                              index=False, encoding="utf-8-sig")

    phase_share = (assign.groupby(["phase", "dominant_topic"], dropna=False)
                   .size().reset_index(name="posts"))
    totals = phase_share.groupby("phase")["posts"].transform("sum")
    phase_share["share_within_phase"] = phase_share["posts"] / totals
    phase_share.to_csv(os.path.join(OUT_DIR, "NMF_phase_share.csv"),
                       index=False, encoding="utf-8-sig")

    with open(os.path.join(OUT_DIR, "NMF_model_info.txt"), "w", encoding="utf-8") as f:
        f.write(f"n_docs\t{len(df)}\n")
        f.write(f"n_features\t{dt.shape[1]}\n")
        f.write(f"n_topics\t{N_TOPICS}\n")
        f.write(f"reconstruction_error\t{nmf.reconstruction_err_:.4f}\n")
        f.write(f"extra_stopwords\t{len(EXTRA_STOP)}\n")

    print("\n=== 各主题 top10 词 ===")
    tw = pd.DataFrame(rows)
    for t in range(N_TOPICS):
        ws = tw[tw.topic_id == t].sort_values("weight", ascending=False)["word"].head(10)
        print(f"主题{t}: {'、'.join(ws)}")
    print(f"\n重构误差: {nmf.reconstruction_err_:.4f}")
    print(f"已写入: {OUT_DIR}")


if __name__ == "__main__":
    main()
