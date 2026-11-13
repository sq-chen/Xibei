# -*- coding: utf-8 -*-
"""
问卷汇报图表.py
===============
从各分析结果 CSV 生成汇报用图表（输出到 vault media：E:\\文档\\obsidian\\毕设\\汇报\\media\\）：
  1. 问卷_简单中介森林图.png     三样本（实验组/对照组/全部）简单中介 间接/总效应 CI
  2. 问卷_五情绪单独中介.png     全部样本五情绪单独中介 CI 排序森林图
  3. 问卷_两组路径对比.png       多组 SEM：a/b/cp 两组路径系数对比
  4. 问卷_多层中介组内组间.png   三样本 组内/组间 中介效应（bootstrap CI）
  5. 问卷_调节简单斜率.png       组别 × b 段 有调节中介简单斜率（若有结果）
数据文件（相对本脚本上级目录）：
  01_实验组主分析/结果_中介效应汇总.csv
  03_对照组分析/结果_对照组中介效应汇总.csv
  05_全部样本分析/结果_全部样本中介效应汇总.csv
  06_多组SEM/结果_多组SEM_路径系数.csv
  07_多层中介/结果_多层中介_汇总.csv
  09_调节分析/结果_调节分析_汇总.csv
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DST = r"E:\文档\obsidian\毕设\汇报\media"
os.makedirs(DST, exist_ok=True)


def read_ind(path, model_kw, ret="ind"):
    """从汇总 CSV 里取 模型 包含 model_kw 且 效应==ret 的 (est, lo, hi)。"""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, encoding="utf-8-sig")
    sub = df[df["模型"].str.contains(model_kw) & (df["效应"] == ret)]
    if sub.empty:
        return None
    r = sub.iloc[0]
    return float(r["est"]), float(r["ci.lower"]), float(r["ci.upper"])


def forest(rows, path, title, xlabel="效应量（bootstrap 95% CI）", vline=0,
           xlim=None, colors=None):
    fig, ax = plt.subplots(figsize=(8, max(2.2, len(rows) * 0.55)))
    for i, (label, est, lo, hi, col) in enumerate(rows):
        ax.errorbar(est, i, xerr=[[est - lo], [hi - est]], fmt="o", ms=7,
                    color=col, ecolor=col, elinewidth=2, capsize=4, capthick=1.5)
        ax.text(est, i + 0.22, f"{est:.3f}", ha="center", fontsize=9)
    ax.axvline(vline, color="gray", ls="--", lw=1)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.invert_yaxis()
    if xlim:
        ax.set_xlim(xlim)
    plt.tight_layout()
    plt.savefig(os.path.join(DST, path), dpi=150)
    plt.close()
    print("saved:", path)


# ---------- 1. 简单中介森林图 ----------
C_RED, C_GRAY, C_BLUE = "#c0392b", "#7f8c8d", "#2471a3"
rows = []
r = read_ind(os.path.join(ROOT, "01_实验组主分析", "结果_中介效应汇总.csv"), "H3:", "ind")
if r: rows.append(("实验组 间接效应", r[0], r[1], r[2], C_RED))
r = read_ind(os.path.join(ROOT, "01_实验组主分析", "结果_中介效应汇总.csv"), "H3:", "total")
if r: rows.append(("实验组 总效应", r[0], r[1], r[2], C_RED))
r = read_ind(os.path.join(ROOT, "03_对照组分析", "结果_对照组中介效应汇总.csv"), "H3:", "ind")
if r: rows.append(("对照组 间接效应", r[0], r[1], r[2], C_GRAY))
r = read_ind(os.path.join(ROOT, "03_对照组分析", "结果_对照组中介效应汇总.csv"), "H3:", "total")
if r: rows.append(("对照组 总效应", r[0], r[1], r[2], C_GRAY))
r = read_ind(os.path.join(ROOT, "05_全部样本分析", "结果_全部样本中介效应汇总.csv"), "简单中介", "ind")
if r: rows.append(("全部样本 间接效应", r[0], r[1], r[2], C_BLUE))
r = read_ind(os.path.join(ROOT, "05_全部样本分析", "结果_全部样本中介效应汇总.csv"), "简单中介", "total")
if r: rows.append(("全部样本 总效应", r[0], r[1], r[2], C_BLUE))
forest(rows, "问卷_简单中介森林图.png",
       "不一致感知 → 消极情绪 → 传播意愿：间接效应与总效应（bootstrap 5000）",
       xlim=(-0.75, 0.85))

# ---------- 2. 五情绪单独中介森林图（全部样本） ----------
emo_cn = {"愤怒": "#c0392b", "厌恶": "#e67e22", "蔑视": "#8e44ad",
          "恐惧": "#7f8c8d", "悲伤": "#2471a3"}
rows = []
for emo in ["愤怒", "厌恶", "蔑视", "恐惧", "悲伤"]:
    r = read_ind(os.path.join(ROOT, "05_全部样本分析", "结果_全部样本中介效应汇总.csv"),
                 f"单独中介-{emo}", "ind")
    if r: rows.append((emo, r[0], r[1], r[2], emo_cn[emo]))
forest(rows, "问卷_五情绪单独中介.png",
       "全部样本（N=373）五种情绪单独中介：间接效应排序（bootstrap 5000）",
       xlim=(0, 0.75), vline=0)

# ---------- 3. 两组路径系数对比（多组 SEM） ----------
p = os.path.join(ROOT, "06_多组SEM", "结果_多组SEM_路径系数.csv")
if os.path.exists(p):
    pe = pd.read_csv(p, encoding="utf-8-sig")
    rows3 = []
    for lhs, rhs, label in [("negemo", "HP", "a：不一致感知→情绪"),
                            ("si3", "negemo", "b：情绪→传播意愿"),
                            ("si3", "HP", "c′：不一致感知→传播意愿（直接）")]:
        sub = pe[(pe["lhs"] == lhs) & (pe["rhs"] == rhs) & (pe["op"] == "~")]
        # 注：lavaan 分组顺序 = 数据出现顺序（rbind 实验组在前）→ group 1=实验组，2=对照组
        for g, lab, col in [(1, "实验组", C_RED), (2, "对照组", C_GRAY)]:
            rr = sub[sub["group"] == g]
            if not rr.empty:
                e, se = float(rr.iloc[0]["est"]), float(rr.iloc[0]["se"])
                rows3.append((f"{label}\n{lab}", e, se, col))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, (lab, e, se, col) in enumerate(rows3):
        ax.barh(i, e, xerr=se * 1.96, color=col, alpha=.9, height=.55, capsize=4)
        ax.text(e + (0.03 if e >= 0 else -0.03), i, f"{e:.3f}", va="center", fontsize=9)
    ax.axvline(0, color="k", lw=.8)
    ax.set_yticks(range(len(rows3)))
    ax.set_yticklabels([r[0] for r in rows3], fontsize=9)
    ax.set_title("多组 SEM：两组路径系数对比（显变量主口径，±1.96SE）", fontsize=12)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(DST, "问卷_两组路径对比.png"), dpi=150)
    plt.close()
    print("saved: 问卷_两组路径对比.png")

# ---------- 4. 多层中介 组内/组间 ----------
p4 = os.path.join(ROOT, "07_多层中介", "结果_多层中介_汇总.csv")
if os.path.exists(p4):
    mm = pd.read_csv(p4, encoding="utf-8-sig")
    rows4 = []
    for _, r in mm.iterrows():
        col = C_RED if r["样本"] == "实验组" else (C_GRAY if r["样本"] == "对照组" else C_BLUE)
        rows4.append((f"{r['样本']} {r['路径']}", float(r["ind"]),
                      float(r["ci_lower"]), float(r["ci_upper"]), col))
    forest(rows4, "问卷_多层中介组内组间.png",
           "多层中介（品牌嵌套被试）：组内与组间间接效应（簇 bootstrap 2000）",
           xlim=(-0.15, 0.7))

# ---------- 5. 调节分析简单斜率（组别 × b 段；若 b3 显著才画） ----------
p5 = os.path.join(ROOT, "09_调节分析", "结果_调节分析_汇总.csv")
if os.path.exists(p5):
    md = pd.read_csv(p5, encoding="utf-8-sig")
    sub = md[(md["模型"] == "① b段×组别") & (md["效应"].isin(["ind_ctrl", "ind_exp"]))]
    if len(sub) == 2:
        fig, ax = plt.subplots(figsize=(5.2, 4))
        drow = {r["效应"]: (r["est"], r["ci.lower"], r["ci.upper"]) for _, r in sub.iterrows()}
        xs = [0, 1]
        for xi, key in enumerate(["ind_ctrl", "ind_exp"]):
            e, lo, hi = drow[key]
            ax.errorbar(xi, e, yerr=[[e - lo], [hi - e]], fmt="o", ms=8,
                        color=[C_GRAY, C_RED][xi], capsize=6, elinewidth=2)
            ax.text(xi, e + 0.06, f"{e:.3f}", ha="center")
        ax.set_xticks(xs)
        ax.set_xticklabels(["中性不一致（对照组）", "负性不一致（实验组）"])
        ax.set_ylabel("经由消极情绪的间接效应")
        ax.set_title("组别 × b 段：条件间接效应", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(DST, "问卷_调节简单斜率.png"), dpi=150)
        plt.close()
        print("saved: 问卷_调节简单斜率.png")

print("\n图表生成完成，输出目录：", DST)
