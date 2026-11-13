# -*- coding: utf-8 -*-
"""
13_KWIC摘录.py
==============
W-6 典型帖子定性摘录（KWIC，表现层定性材料）：
  - 对四类词典（虚伪/愤怒/厌恶/鄙视）命中的帖子，按总互动与转发数各取高互动代表帖；
    另取同时命中 ≥3 类的"高情绪复合帖"。
  - 上下文窗口：定位正文中第一个命中的词典词（长词优先），前后各 30 字符摘录。
  - 输出：描述性统计结果/KWIC摘录.csv（类别/主题/互动/命中词/上下文/全文）+ 控制台打印每类 top8。
"""
import os

import pandas as pd

from _common import OUT_DIR, to_csv, CATS, load_data

ANALYSIS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "..", "analysis"))
SEG_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "分词",
                        "weibo关键词_分词结果.pickle")
ASSIGN_PATH = os.path.join(ANALYSIS, "分词与情感分析", "分词与情感分析结果", "主题聚类",
                           "weibo关键词_nmf_nva_assignments.csv")
DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "词典",
                         "CAD词典_v4_终版.xlsx")

TOPIC_LABELS = {
    0: "预制菜行业质疑", 1: "平台资讯聚合", 2: "道歉与致歉信",
    3: "贾国龙回应", 4: "门店后厨与配方", 5: "罗永浩交锋与起诉",
    6: "隔夜菜指控", 7: "动员大会事件", 8: "公关危机评论", 9: "致歉信文本讨论",
}
WINDOW = 30

# ---------- 1. 数据 ----------
d = load_data()
seg = pd.read_pickle(SEG_PATH)[["ID", "post", "date"]]
asg = pd.read_csv(ASSIGN_PATH, encoding="utf-8-sig", dtype={"ID": str})[["ID", "dominant_topic"]]
seg["ID"] = seg["ID"].astype(str)
asg["ID"] = asg["ID"].astype(str)
d = d.merge(seg, on="ID", how="left").merge(asg, on="ID", how="left")

dict_words = {}
xl = pd.ExcelFile(DICT_PATH)
for c in CATS:
    ws = [str(w).strip() for w in xl.parse(c)["词"].tolist()
          if len(str(w).strip()) >= 2]          # KWIC 只用 ≥2 字词，避免单字噪音
    dict_words[c] = sorted(ws, key=len, reverse=True)   # 长词优先匹配

CAT_COLS = {"虚伪": "hyp_hit_cad", "愤怒": "anger_hit_cad",
            "厌恶": "disgust_hit_cad", "鄙视": "contempt_hit_cad"}


def first_match(text, words):
    """返回 (命中词, 位置) 或 (None, -1)。"""
    best = None
    best_i = len(text) + 1
    for w in words:
        i = text.find(w)
        if 0 <= i < best_i:
            best, best_i = w, i
    return best, best_i


rows = []
for c in CATS:
    hit = d[d[CAT_COLS[c]] > 0].copy()
    cand = pd.concat([
        hit.sort_values("total_engagement", ascending=False).head(10),
        hit.sort_values("reposts_count", ascending=False).head(5),
    ]).drop_duplicates("ID")
    for _, r in cand.iterrows():
        text = str(r.get("post", ""))
        w, i = first_match(text, dict_words[c])
        if w is None or i < 0:
            continue
        lo = max(0, i - WINDOW)
        rows.append({
            "类别": c, "ID": r["ID"], "日期": str(r.get("date", ""))[:10],
            "主题": TOPIC_LABELS.get(int(r["dominant_topic"]), "?")
                    if pd.notna(r.get("dominant_topic")) else "?",
            "转发": int(r["reposts_count"]), "评论": int(r["comments_count"]),
            "点赞": int(r["attitudes_count"]), "总互动": int(r["total_engagement"]),
            "命中词": w,
            "上下文": text[lo:i + WINDOW + len(w)].replace("\n", " "),
            "全文": text.replace("\n", " ")[:200],
        })

# 多类复合帖：命中 ≥3 类
multi = d[(d["hyp_hit_cad"] > 0) & (d["anger_hit_cad"] > 0)
          & ((d["disgust_hit_cad"] > 0) | (d["contempt_hit_cad"] > 0))].copy()
for _, r in multi.sort_values("total_engagement", ascending=False).head(8).iterrows():
    text = str(r.get("post", ""))
    hits = []
    earliest = len(text) + 1
    for c in CATS:
        w, i = first_match(text, dict_words[c])
        if w:
            hits.append(f"{c}·{w}")
            earliest = min(earliest, i)
    if not hits:
        continue
    lo = max(0, earliest - WINDOW)
    rows.append({
        "类别": "多类复合", "ID": r["ID"], "日期": str(r.get("date", ""))[:10],
        "主题": TOPIC_LABELS.get(int(r["dominant_topic"]), "?")
                if pd.notna(r.get("dominant_topic")) else "?",
        "转发": int(r["reposts_count"]), "评论": int(r["comments_count"]),
        "点赞": int(r["attitudes_count"]), "总互动": int(r["total_engagement"]),
        "命中词": " + ".join(hits),
        "上下文": text[lo:lo + 2 * WINDOW + 20].replace("\n", " "),
        "全文": text.replace("\n", " ")[:200],
    })

out = pd.DataFrame(rows)
to_csv(out, os.path.join("KWIC摘录.csv"))
print(f"共摘录 {len(out)} 条\n")
for c in CATS + ["多类复合"]:
    sub = out[out["类别"] == c].head(8)
    print(f"\n========== {c}（top8 摘录） ==========")
    for _, r in sub.iterrows():
        print(f"[{r['日期']} | {r['主题']} | 转{r['转发']} 评{r['评论']} 赞{r['点赞']}] "
              f"命中<{r['命中词']}> …{r['上下文']}…")
print("\n已导出：描述性统计结果/KWIC摘录.csv")
