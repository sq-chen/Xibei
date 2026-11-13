# -*- coding: utf-8 -*-
"""
09_原始词典稳健性对比.py
========================
稳健性检查：v4 词典（清洗版）vs 原始词典（全保留版）的核心描述结果对比。
回答"词典清洗是否改变结论"。

对比内容：
① 总体命中率（四类，两版词数并列）；
② 虚伪帖内三情绪命中率（各版按自己的虚伪二分类）；
③ 虚伪 vs 非虚伪：三情绪命中率 + 比例 z 检验 + **命中率倍数**（主口径）；
④ 全样本 Spearman 相关（四类命中次数 × 总互动）；
⑤ 图：总体命中率对比、倍数对比。

输出：描述性统计结果/原始词典稳健性/
  命中率对比.csv、虚伪帖情绪面貌对比.csv、虚伪vs非虚伪_对比.csv、
  相关对比.csv、命中率对比.png、增益倍数对比.png
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAD_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
WIDE_PATH = os.path.join(CAD_ROOT, "..", "analysis", "分词与情感分析",
                         "分词与情感分析结果", "merged_wide_v2.csv")
V4_PATH = os.path.join(CAD_ROOT, "分词与命中", "结果", "CAD命中_明细.csv")
RAW_PATH = os.path.join(CAD_ROOT, "分词与命中", "结果_原始词典", "CAD命中_明细.csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "描述性统计结果", "原始词典稳健性")
os.makedirs(OUT_DIR, exist_ok=True)

CATS = ["虚伪", "愤怒", "厌恶", "鄙视"]
EMO_CATS = ["愤怒", "厌恶", "鄙视"]
EN = {"虚伪": "hyp", "愤怒": "anger", "厌恶": "disgust", "鄙视": "contempt"}
DICT_N = {"v4": {"虚伪": 245, "愤怒": 261, "厌恶": 137, "鄙视": 172},
          "原始": {"虚伪": 285, "愤怒": 265, "厌恶": 247, "鄙视": 231}}


def prop_z(p1, n1, p2, n2):
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p <= 0 or p >= 1:
        return np.nan, np.nan
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    return z, 2 * (1 - stats.norm.cdf(abs(z)))


def to_csv(df, name):
    df.to_csv(os.path.join(OUT_DIR, name), index=False, encoding="utf-8-sig")


def save_fig(name):
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path


wide = pd.read_csv(WIDE_PATH, encoding="utf-8-sig", dtype={"ID": str})
v4 = pd.read_csv(V4_PATH, encoding="utf-8-sig", dtype={"ID": str})
raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig", dtype={"ID": str})
d = wide.merge(v4, on="ID", how="inner").merge(raw, on="ID", how="inner")
print(f"合并样本: {len(d)} 帖")

# ---------- ① 总体命中率对比 ----------
rows = []
for cat in CATS:
    for ver, suf in [("v4", "cad"), ("原始", "raw")]:
        col = f"{EN[cat]}_hit_{suf}"
        rows.append({
            "类别": cat, "词典": ver, "词数": DICT_N[ver][cat],
            "命中帖": int((d[col] > 0).sum()),
            "命中率%": round(100 * (d[col] > 0).mean(), 1),
            "命中次数均值": round(d[col].mean(), 3),
        })
rate_cmp = pd.DataFrame(rows)
to_csv(rate_cmp, "命中率对比.csv")
print("\n=== ① 总体命中率对比 ===")
print(rate_cmp.to_string(index=False))

# ---------- ② 虚伪帖内三情绪命中率 ----------
rows = []
for ver, suf, bcol in [("v4", "cad", "hyp_hit_binary_cad"),
                       ("原始", "raw", "hyp_hit_binary_raw")]:
    sub = d[d[bcol] == 1]
    rows.append({"词典": ver, "虚伪帖数": len(sub),
                 "虚伪帖占比%": round(100 * len(sub) / len(d), 1)})
    for cat in EMO_CATS:
        rows[-1][f"{cat}命中率%"] = round(100 * (sub[f"{EN[cat]}_hit_{suf}"] > 0).mean(), 1)
hyp_face = pd.DataFrame(rows)
to_csv(hyp_face, "虚伪帖情绪面貌对比.csv")
print("\n=== ② 虚伪帖内三情绪命中率 ===")
print(hyp_face.to_string(index=False))

# ---------- ③ 虚伪 vs 非虚伪：z 检验 + 倍数 ----------
rows = []
for cat in EMO_CATS:
    for ver, suf, bcol in [("v4", "cad", "hyp_hit_binary_cad"),
                           ("原始", "raw", "hyp_hit_binary_raw")]:
        col = f"{EN[cat]}_hit_{suf}"
        h, nh = d[d[bcol] == 1], d[d[bcol] == 0]
        r1, r2 = (h[col] > 0).mean(), (nh[col] > 0).mean()
        z, p = prop_z(r1, len(h), r2, len(nh))
        rows.append({
            "情绪": cat, "词典": ver,
            "虚伪帖命中率%": round(100 * r1, 1),
            "非虚伪帖命中率%": round(100 * r2, 1),
            "倍数": round(r1 / r2, 2) if r2 > 0 else np.nan,
            "z": round(z, 2), "p": round(p, 4),
        })
cmp = pd.DataFrame(rows)
to_csv(cmp, "虚伪vs非虚伪_对比.csv")
print("\n=== ③ 虚伪 vs 非虚伪（z 检验 + 倍数）===")
print(cmp.to_string(index=False))

# ---------- ④ Spearman 相关（全样本，四类 × 总互动）----------
rows = []
for ver, suf in [("v4", "cad"), ("原始", "raw")]:
    for cat in CATS:
        r, p = stats.spearmanr(d[f"{EN[cat]}_hit_{suf}"], d["total_engagement"])
        rows.append({"词典": ver, "类别": cat, "总互动Spearman": round(r, 3),
                     "p": round(p, 4)})
corr_cmp = pd.DataFrame(rows)
to_csv(corr_cmp, "相关对比.csv")
print("\n=== ④ 全样本 Spearman（四类 × 总互动）===")
print(corr_cmp.to_string(index=False))

# ---------- ⑤ 图 ----------
piv = rate_cmp.pivot(index="类别", columns="词典", values="命中率%")[["v4", "原始"]]
fig, ax = plt.subplots(figsize=(6.5, 4.5))
x = np.arange(len(piv)); w = 0.36
ax.bar(x - w / 2, piv["v4"], w, label="v4 清洗版", color="#4C72B0")
ax.bar(x + w / 2, piv["原始"], w, label="原始全保留版", color="#DD8452")
for i, cat in enumerate(piv.index):
    ax.text(i - w / 2, piv["v4"][i] + 0.3, f"{piv['v4'][i]:.1f}", ha="center", fontsize=9)
    ax.text(i + w / 2, piv["原始"][i] + 0.3, f"{piv['原始'][i]:.1f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(piv.index)
ax.set_ylabel("命中率 %")
ax.set_title("词典清洗 vs 全保留：总体命中率对比")
ax.legend()
save_fig("命中率对比.png")

piv2 = cmp.pivot(index="情绪", columns="词典", values="倍数")[["v4", "原始"]]
fig, ax = plt.subplots(figsize=(6.5, 4.5))
x3 = np.arange(len(piv2))
ax.bar(x3 - w / 2, piv2["v4"], w, label="v4 清洗版", color="#4C72B0")
ax.bar(x3 + w / 2, piv2["原始"], w, label="原始全保留版", color="#DD8452")
for i, cat in enumerate(piv2.index):
    ax.text(i - w / 2, piv2["v4"].iloc[i] + 0.05, f"{piv2['v4'].iloc[i]:.2f}", ha="center", fontsize=9)
    ax.text(i + w / 2, piv2["原始"].iloc[i] + 0.05, f"{piv2['原始'].iloc[i]:.2f}", ha="center", fontsize=9)
ax.set_xticks(x3); ax.set_xticklabels(piv2.index)
ax.set_ylabel("命中率倍数（虚伪帖 / 非虚伪帖）")
ax.set_title("情绪增益倍数对比（主口径，不受词表规模影响）")
ax.legend()
save_fig("增益倍数对比.png")

print(f"\n已写入: {OUT_DIR}")
