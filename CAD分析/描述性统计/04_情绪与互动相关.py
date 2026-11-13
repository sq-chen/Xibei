# -*- coding: utf-8 -*-
"""
04_情绪与互动相关.py
==================
分析内容（对应论文"情绪与传播的描述关联"）：
① Spearman 秩相关矩阵：四类词命中次数 × 转发/评论/点赞/总互动
   （全样本与虚伪帖子样本各一份热图；互动量零膨胀，用秩相关）；
② 认证类型剖面：蓝V/黄V/红V/金V/普通用户的四类命中率与互动量分布
   （用户属性混杂的描述证据）。

输出：描述性统计结果/emotion_vs_engagement_spearman.csv、
     emotion_vs_engagement_spearman_hit.csv、verification_type_emotion.csv、
     verification_type_engagement.csv、相关热图_全样本.png、相关热图_虚伪帖.png、
     认证类型情绪.png、认证类型互动.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from _common import (CATS, CAT_COLS, ENGAGE_COLS, load_data, save_fig, to_csv)

d = load_data()
d["any_engagement"] = (d["total_engagement"] > 0).astype(int)   # 宽表无此列，现场计算
d["verification_type"] = d["verification_type"].fillna("普通用户")
d.loc[d["verification_type"] == "", "verification_type"] = "普通用户"
VER_ORDER = ["普通用户", "蓝V", "黄V", "红V", "金V"]

# ---------- ① Spearman 相关矩阵 ----------
def spearman_matrix(sub: pd.DataFrame, label: str) -> pd.DataFrame:
    cat_cols = [CAT_COLS[c] for c in CATS]
    eng_cols = list(ENGAGE_COLS.values())
    mat = sub[cat_cols + eng_cols].corr(method="spearman")
    out = mat.loc[cat_cols, eng_cols].round(3)
    out.index = CATS; out.columns = ENGAGE_COLS.keys()
    return out

m_full = spearman_matrix(d, "全样本")
m_hit = spearman_matrix(d[d["hyp_hit_binary_cad"] == 1], "虚伪帖")
# 剔除零命中帖：任一 CAD 情绪命中的帖子内（零命中帖占比高，检验其是否稀释了相关）
any_emo = (d["anger_hit_cad"] + d["disgust_hit_cad"] + d["contempt_hit_cad"]) > 0
m_any = spearman_matrix(d[any_emo], "任一情绪命中帖")
to_csv(m_full.reset_index().rename(columns={"index": "类别"}), "emotion_vs_engagement_spearman.csv")
to_csv(m_hit.reset_index().rename(columns={"index": "类别"}), "emotion_vs_engagement_spearman_hit.csv")
to_csv(m_any.reset_index().rename(columns={"index": "类别"}), "emotion_vs_engagement_spearman_任一情绪命中.csv")
print("=== Spearman（全样本）===")
print(m_full.to_string())
print("\n=== Spearman（虚伪帖样本）===")
print(m_hit.to_string())
print(f"\n=== Spearman（任一情绪命中帖，n={int(any_emo.sum())}）===")
print(m_any.to_string())

for mat, name in [(m_full, "相关热图_全样本"), (m_hit, "相关热图_虚伪帖"),
                  (m_any, "相关热图_任一情绪命中帖")]:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    im = ax.imshow(mat.values, cmap="RdYlBu_r", vmin=-0.1, vmax=0.4)
    ax.set_xticks(range(len(mat.columns))); ax.set_xticklabels(mat.columns)
    ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im)
    ax.set_title(name.replace("相关热图_", "情绪命中次数与互动量 Spearman（") + "）")
    save_fig(f"{name}.png")

# ---------- ② 认证类型剖面 ----------
rows = []
for vt in VER_ORDER:
    sub = d[d["verification_type"] == vt]
    if len(sub) == 0:
        continue
    row = {"认证类型": vt, "帖数": len(sub)}
    for cat in CATS:
        row[f"{cat}命中率%"] = round(100 * (sub[CAT_COLS[cat]] > 0).mean(), 1)
    rows.append(row)
vt_emo = pd.DataFrame(rows)
to_csv(vt_emo, "verification_type_emotion.csv")
print("\n=== 认证类型 × 四类命中率 ===")
print(vt_emo.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(vt_emo)); w = 0.2
for i, cat in enumerate(CATS):
    ax.bar(x + (i - 1.5) * w, vt_emo[f"{cat}命中率%"], w, label=cat)
ax.set_xticks(x); ax.set_xticklabels(vt_emo["认证类型"])
ax.set_ylabel("命中率 %"); ax.set_title("认证类型 × 四类词命中率")
ax.legend()
save_fig("认证类型情绪.png")

# 互动量分布（log10(总互动+1) 箱线图）
fig, ax = plt.subplots(figsize=(8, 5))
data = [np.log10(d.loc[d["verification_type"] == vt, "total_engagement"] + 1)
        for vt in VER_ORDER if (d["verification_type"] == vt).any()]
ax.boxplot(data, labels=[vt for vt in VER_ORDER if (d["verification_type"] == vt).any()],
           showfliers=False)
ax.set_ylabel("log10(总互动+1)")
ax.set_title("认证类型 × 互动量分布")
save_fig("认证类型互动.png")

vt_eng = d.groupby("verification_type").agg(
    帖数=("ID", "size"),
    互动均值=("total_engagement", "mean"),
    互动中位=("total_engagement", "median"),
    零互动率=("any_engagement", lambda s: 100 * (1 - s.mean())),
).reindex([vt for vt in VER_ORDER if vt in d["verification_type"].unique()]).reset_index()
vt_eng["零互动率"] = vt_eng["零互动率"].round(1)
to_csv(vt_eng.rename(columns={"verification_type": "认证类型"}), "verification_type_engagement.csv")
print("\n=== 认证类型 × 互动量 ===")
print(vt_eng.to_string(index=False))
print("\n已写入")
