# -*- coding: utf-8 -*-
"""
21_按主题典型话语.py
====================
为汇报 §7 摘录各主题代表帖：每个 NMF 主题取 2-3 条（优先含主题特征词、
按总互动降序、按文本前 40 字去重）。
输出：打印 + /tmp/kwic_topics.json（文本已截断至 150 字，供人工校订后进汇报）。
"""
import json

import pandas as pd

ANALYSIS = r"..\..\analysis"
SEG = ANALYSIS + r"\分词与情感分析\分词与情感分析结果\分词\weibo关键词_分词结果.pickle"
WIDE = ANALYSIS + r"\分词与情感分析\分词与情感分析结果\merged_wide_v2.csv"
ASG = ANALYSIS + r"\分词与情感分析\分词与情感分析结果\主题聚类\weibo关键词_nmf_nva_assignments.csv"
TW = ANALYSIS + r"\分词与情感分析\分词与情感分析结果\主题聚类\weibo关键词_nmf_nva_topic_words.csv"

NAMES = {0: "餐饮行业预制菜质疑", 1: "平台资讯聚合", 2: "道歉与致歉信",
         3: "贾国龙回应", 4: "门店后厨与配方", 5: "罗永浩相关争论",
         6: "隔夜菜指控", 7: "动员大会事件", 8: "公关危机评论", 9: "致歉信文本讨论"}

df = pd.read_pickle(SEG)
wide = pd.read_csv(WIDE, encoding="utf-8-sig", dtype={"ID": str})
asg = pd.read_csv(ASG, encoding="utf-8-sig", dtype={"ID": str})
tw = pd.read_csv(TW, encoding="utf-8-sig")
top_words = {t: tw[tw["topic_id"] == t].sort_values("weight", ascending=False)["word"].head(6).tolist()
             for t in range(10)}

d = df[["ID", "name", "date", "post"]].merge(asg[["ID", "dominant_topic"]], on="ID", how="inner")
d = d.merge(wide[["ID", "reposts_count", "comments_count", "attitudes_count",
                  "total_engagement"]], on="ID", how="inner")
d["date"] = pd.to_datetime(d["date"])

out = {}
for t in range(10):
    sub = d[d["dominant_topic"] == t].copy()
    has_kw = sub["post"].apply(lambda x: sum(k in str(x) for k in top_words[t]))
    cand = sub[has_kw >= 1].sort_values("total_engagement", ascending=False)
    if len(cand) < 2:
        cand = sub.sort_values("total_engagement", ascending=False)
    picks, seen = [], set()
    for _, r in cand.iterrows():
        key = str(r["post"])[:40]
        if key in seen:
            continue
        seen.add(key)
        picks.append({"date": r["date"].strftime("%m-%d"), "name": r["name"],
                      "rep": int(r["reposts_count"]), "com": int(r["comments_count"]),
                      "lik": int(r["attitudes_count"]),
                      "text": str(r["post"]).replace("\n", " ").strip()[:150]})
        if len(picks) >= 3:
            break
    out[NAMES[t]] = picks
    print(f"== {NAMES[t]} ==")
    for p in picks:
        print(f"  {p['date']} @{p['name']} 转{p['rep']} 评{p['com']} 赞{p['lik']}: {p['text'][:80]}")
    print()

json.dump(out, open("/tmp/kwic_topics.json", "w", encoding="utf-8"), ensure_ascii=False)
print("已导出 /tmp/kwic_topics.json")
