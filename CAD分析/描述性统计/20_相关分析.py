# -*- coding: utf-8 -*-
"""
20_相关分析.py
==============
微博帖子层面相关分析（表现层描述）：
  1. 伪善命中 × 三情绪命中 的 φ 相关（2×2 χ²）
  2. 四类词典命中数两两 Spearman
  3. 四类命中数 × 总互动/转评赞 Spearman
数据：_common.load_data()（84,032 帖）。结果直接打印，供汇报"相关分析"小节引用。
"""
import pandas as pd
from scipy import stats

from _common import load_data

d = load_data()
cols = {"伪善": "hyp_hit_cad", "愤怒": "anger_hit_cad",
        "厌恶": "disgust_hit_cad", "鄙视": "contempt_hit_cad"}

print("=== 1. 伪善命中 × 情绪命中（φ） ===")
for k in ["愤怒", "厌恶", "鄙视"]:
    t = pd.crosstab(d["hyp_hit_cad"] > 0, d[cols[k]] > 0)
    a, b = t.iloc[0, 0], t.iloc[0, 1]
    c, dd = t.iloc[1, 0], t.iloc[1, 1]
    phi = (a * dd - b * c) / ((a + b) * (c + dd) * (a + c) * (b + dd)) ** 0.5
    chi2, p, _, _ = stats.chi2_contingency(t)
    print(f"伪善×{k}: φ={phi:.3f}, χ²={chi2:.0f}, p={p:.2e}")

print("\n=== 2. 四类两两 Spearman ===")
keys = list(cols)
mat = pd.DataFrame(index=keys, columns=keys)
for i in keys:
    for j in keys:
        mat.loc[i, j] = round(stats.spearmanr(d[cols[i]], d[cols[j]])[0], 3)
print(mat)

print("\n=== 3. 命中数 × 互动 Spearman ===")
for k in keys:
    line = []
    for eng in ["total_engagement", "reposts_count", "comments_count", "attitudes_count"]:
        rho, p = stats.spearmanr(d[cols[k]], d[eng])
        line.append(f"{eng}={rho:.3f}")
    print(k, "|", "  ".join(line))
