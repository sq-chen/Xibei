# -*- coding: utf-8 -*-
"""
11_主题情绪互动三维.py
======================
W-2 主题 × 情绪 × 互动三维画像（表现层，纯描述）：
  - 十大 NMF 主题（全局标签）× 四类词典命中率 × 分项互动均值的三维剖面
  - 热力图：主题 × 情绪命中率；主题 × 分项互动（log1p 均值）
  - 亮点扫描：高情绪×高互动 / 高伪善×低互动的主题组合（标准化打分排序）
输出：描述性统计结果/主题聚类/主题情绪互动三维.csv + 主题情绪热力图.png + 主题互动热力图.png
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import load_data, save_fig, to_csv, OUT_DIR, CATS, CAT_COLS, EMO_CATS

ASSIGN_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis",
    "分词与情感分析", "分词与情感分析结果", "主题聚类",
    "weibo关键词_nmf_nva_assignments.csv"))

TOPIC_LABELS = {
    0: "餐饮行业预制菜质疑", 1: "平台资讯聚合", 2: "道歉与致歉信",
    3: "贾国龙回应", 4: "门店后厨与配方", 5: "罗永浩相关争论",
    6: "隔夜菜指控", 7: "动员大会事件", 8: "公关危机评论", 9: "致歉信文本讨论",
}
ENGAGE = {"转发": "reposts_count", "评论": "comments_count", "点赞": "attitudes_count"}

d = load_data()
asg = pd.read_csv(ASSIGN_PATH, encoding="utf-8-sig", dtype={"ID": str})
asg = asg[["ID", "dominant_topic"]].rename(columns={"dominant_topic": "topic"})
d = d.merge(asg, on="ID", how="left")
print("未匹配主题的帖子:", int(d["topic"].isna().sum()))
d = d.dropna(subset=["topic"]).copy()
d["topic"] = d["topic"].astype(int)

# ---------- 1. 剖面表 ----------
rows = []
for t in sorted(d["topic"].unique()):
    sub = d[d["topic"] == t]
    row = {"topic": t, "主题": TOPIC_LABELS.get(t, t), "N": len(sub),
           "占比%": round(len(sub) / len(d) * 100, 1)}
    for c, col in CAT_COLS.items():
        row[f"{c}命中率%"] = round((sub[col] > 0).mean() * 100, 1)
        row[f"{c}命中强度"] = round(sub[col].mean(), 3)
    for k, col in ENGAGE.items():
        row[f"{k}均值"] = round(sub[col].mean(), 1)
        row[f"{k}零率%"] = round((sub[col] == 0).mean() * 100, 1)
    row["总互动均值"] = round(sub["total_engagement"].mean(), 1)
    row["总互动零率%"] = round((sub["total_engagement"] == 0).mean() * 100, 1)
    rows.append(row)
tab = pd.DataFrame(rows)
to_csv(tab, os.path.join("主题聚类", "主题情绪互动三维.csv"))
print(tab[["主题", "N", "占比%", "伪善命中率%", "愤怒命中率%", "厌恶命中率%", "鄙视命中率%",
          "转发均值", "评论均值", "点赞均值", "总互动均值"]].to_string(index=False))

# ---------- 2. 热力图 1：主题 × 情绪命中率 ----------
mat = tab[[f"{c}命中率%" for c in CATS]].values
fig, ax = plt.subplots(figsize=(7, 6.5))
im = ax.imshow(mat, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(4)); ax.set_xticklabels(CATS)
ax.set_yticks(range(10)); ax.set_yticklabels(tab["主题"])
for i in range(10):
    for j in range(4):
        ax.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center", fontsize=9)
plt.colorbar(im, label="命中率 (%)")
ax.set_title("十大主题 × 四类词典命中率（%）")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "主题聚类", "主题情绪热力图.png"), dpi=150); plt.close()

# ---------- 3. 热力图 2：主题 × 分项互动（log1p 均值） ----------
mat2 = tab[[f"{k}均值" for k in ENGAGE]].values
fig, ax = plt.subplots(figsize=(6.5, 6.5))
im = ax.imshow(np.log1p(mat2), cmap="YlGnBu", aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(list(ENGAGE))
ax.set_yticks(range(10)); ax.set_yticklabels(tab["主题"])
for i in range(10):
    for j in range(3):
        ax.text(j, i, f"{mat2[i, j]:.1f}", ha="center", va="center", fontsize=9)
plt.colorbar(im, label="log(1+均值)")
ax.set_title("十大主题 × 分项互动均值（log1p 色阶）")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "主题聚类", "主题互动热力图.png"), dpi=150); plt.close()

# ---------- 4. 亮点扫描（标准化打分排序，纯描述） ----------
z = tab.copy()
for c in CATS:
    z[f"z_{c}"] = (z[f"{c}命中率%"] - z[f"{c}命中率%"].mean()) / z[f"{c}命中率%"].std()
for k in ENGAGE:
    z[f"z_{k}"] = (np.log1p(z[f"{k}均值"]) - np.log1p(z[f"{k}均值"]).mean()) / np.log1p(z[f"{k}均值"]).std()
z["情绪z"] = z[["z_愤怒", "z_厌恶", "z_鄙视"]].mean(axis=1)
z["互动z"] = z[["z_转发", "z_评论", "z_点赞"]].mean(axis=1)
z["伪善z"] = z["z_伪善"]
z["情绪互动z"] = z["情绪z"] + z["互动z"]
z["伪善减互动z"] = z["伪善z"] - z["互动z"]
print("\n=== 亮点：高情绪 × 高互动 主题（情绪z+互动z 排序） ===")
print(z.sort_values("情绪互动z", ascending=False)[["主题", "情绪z", "互动z"]].head(5).to_string(index=False))
print("\n=== 高伪善 × 低互动 主题（伪善z − 互动z 排序） ===")
print(z.sort_values("伪善减互动z", ascending=False)[["主题", "伪善z", "互动z"]].head(5).to_string(index=False))

# ---------- 5. 三维画像主图：主题散点（情绪 z × 互动 z；右图 伪善 z × 互动 z） ----------
cmap20 = plt.cm.tab20.colors
fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))

# 左：情绪 × 互动（点的身份 = 主题 → 主题×情绪×互动 三维联合呈现）
ax = axes[0]
for i, r in z.iterrows():
    ax.scatter(r["情绪z"], r["互动z"], s=180, color=cmap20[int(r["topic"]) % 20],
               edgecolor="white", zorder=3)
    ax.annotate(r["主题"], (r["情绪z"], r["互动z"]),
                xytext=(r["情绪z"] + .03, r["互动z"] + .07), fontsize=9, color="#333")
ax.axhline(0, color="gray", ls="--", lw=.8)
ax.axvline(0, color="gray", ls="--", lw=.8)
ax.set_xlabel("情绪强度（三情绪命中率 z，越高越情绪化）")
ax.set_ylabel("互动水平（三分项互动 log 均值 z）")
ax.set_title("主题落在情绪 × 互动平面上的位置", fontsize=12)
ax.text(1.35, 1.15, "高情绪 × 高互动", fontsize=10, color="#c0392b", ha="right")
ax.text(-1.35, -1.25, "低情绪 × 低互动", fontsize=10, color="#7f8c8d", ha="left")

# 右：伪善 × 互动
ax = axes[1]
for i, r in z.iterrows():
    ax.scatter(r["伪善z"], r["互动z"], s=180, color=cmap20[int(r["topic"]) % 20],
               edgecolor="white", zorder=3)
    ax.annotate(r["主题"], (r["伪善z"], r["互动z"]),
                xytext=(r["伪善z"] + .03, r["互动z"] + .07), fontsize=9, color="#333")
ax.axhline(0, color="gray", ls="--", lw=.8)
ax.axvline(0, color="gray", ls="--", lw=.8)
ax.set_xlabel("伪善话语强度（伪善命中率 z）")
ax.set_ylabel("互动水平（三分项互动 log 均值 z）")
ax.set_title("主题落在伪善 × 互动平面上的位置", fontsize=12)
ax.text(1.35, 1.15, "高伪善 × 高互动", fontsize=10, color="#c0392b", ha="right")
ax.text(1.35, -1.25, "高伪善 × 低互动", fontsize=10, color="#8e44ad", ha="right")

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "主题聚类", "主题情绪互动散点.png"), dpi=150)
plt.close()
print("已导出：主题聚类/主题情绪互动散点.png")

print("\n已导出：描述性统计结果/主题聚类/ 主题情绪互动三维.csv + 2 张热力图 + 1 张联合散点图")
