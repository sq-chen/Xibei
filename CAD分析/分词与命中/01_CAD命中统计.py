# -*- coding: utf-8 -*-
"""
11_CAD命中统计.py
==================
用 CAD词典_v4_终版.xlsx（虚伪 / 愤怒 / 厌恶 / 鄙视）对 01 分词结果做
精确 token 命中计数，产出每帖 4 类命中次数与词总数归一比例，并做词典覆盖率核查。

依赖：01 产出 weibo关键词_分词结果.pickle（中文分词 列为 [(词, 词性), ...]）；
      词典 词典/CAD词典_v4_终版.xlsx（4 个 sheet，sheet 名 = 类别）。

输出目录：分词与情感分析结果/CAD命中/
  - CAD命中_明细.csv        每帖一行：ID + 4 类命中次数 + /词总数 比例 + 虚伪二分类
  - CAD命中_覆盖率.csv       每个词典词在整个语料的命中帖数（0 命中 = 可能分词漏切）
  - CAD命中_汇总.txt         总体命中率摘要

列名带 _cad 后缀，与旧宽表（大连理工 21 情绪）区分；机制分析按 ID 左连接使用。
"""
from __future__ import annotations

import os
import sys

import openpyxl
import pandas as pd

# ---------- 路径（CAD分析 独立流程） ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))        # CAD分析/分词与命中
CAD_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))  # CAD分析/
DICT_PATH  = os.path.join(CAD_ROOT, "词典", "CAD词典_v4_终版.xlsx")
# 上游依赖：分词 pickle 由 analysis/01_数据预处理与分词.py 产出
# （jieba_user_dict.txt 已并入 CAD 短语；旧版备份为 分词结果_旧词典备份.pickle）
SEG_PATH = os.path.join(CAD_ROOT, "..", "analysis", "分词与情感分析",
                        "分词与情感分析结果", "分词", "weibo关键词_分词结果.pickle")
OUT_DIR = os.path.join(SCRIPT_DIR, "结果")
os.makedirs(OUT_DIR, exist_ok=True)

CATS = ["虚伪", "愤怒", "厌恶", "鄙视"]
CAT_EN = {"虚伪": "hyp", "愤怒": "anger", "厌恶": "disgust", "鄙视": "contempt"}


def load_dict() -> dict[str, set[str]]:
    wb = openpyxl.load_workbook(DICT_PATH, read_only=True)
    out = {}
    for cat in CATS:
        ws = wb[cat]
        out[cat] = {str(r[0].value).strip() for r in ws.iter_rows(min_row=1)
                    if r[0].value and str(r[0].value).strip()}
    wb.close()
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("加载词典 ...")
    d = load_dict()
    for c in CATS:
        print(f"  {c}: {len(d[c])} 词")

    print("加载分词结果 ...")
    df = pd.read_pickle(SEG_PATH)
    n = len(df)

    # 词序列：[(词, 词性), ...] -> [词, ...]
    words = df["中文分词"].map(
        lambda wl: [w for w, _ in wl] if isinstance(wl, list) else []
    )
    n_words = words.map(len).clip(lower=1)  # 词总数（分母，防除零）

    print("命中计数 ...")
    for cat in CATS:
        s = d[cat]
        df[f"{CAT_EN[cat]}_hit_cad"] = words.map(lambda wl: sum(1 for w in wl if w in s))
    df["hyp_hit_binary_cad"] = (df["hyp_hit_cad"] > 0).astype(int)
    for cat in CATS:
        en = CAT_EN[cat]
        df[f"{en}_hit_cad_pct"] = df[f"{en}_hit_cad"] / n_words  # /词总数

    # ---------- 明细 ----------
    out_cols = ["ID"] + [f"{CAT_EN[c]}_hit_cad" for c in CATS] \
        + [f"{CAT_EN[c]}_hit_cad_pct" for c in CATS] + ["hyp_hit_binary_cad"]
    df[out_cols].to_csv(os.path.join(OUT_DIR, "CAD命中_明细.csv"),
                        index=False, encoding="utf-8-sig")

    # ---------- 覆盖率核查：每个词典词的命中帖数 ----------
    token_sets = []
    for wl in words:
        token_sets.append(set(wl))
    cover_rows = []
    for cat in CATS:
        for w in sorted(d[cat], key=lambda x: (len(x), x)):
            cover_rows.append({"类别": cat, "词": w,
                               "命中帖数": sum(1 for ts in token_sets if w in ts)})
    cover = pd.DataFrame(cover_rows)
    cover.to_csv(os.path.join(OUT_DIR, "CAD命中_覆盖率.csv"),
                 index=False, encoding="utf-8-sig")

    # ---------- 汇总 ----------
    lines = [f"总帖数: {n}"]
    for cat in CATS:
        en = CAT_EN[cat]
        hit_n = int((df[f"{en}_hit_cad"] > 0).sum())
        lines.append(f"{cat}: 命中帖 {hit_n} ({hit_n/n*100:.1f}%), "
                     f"命中次数均值 {df[f'{en}_hit_cad'].mean():.3f}, "
                     f"/词总数均值 {df[f'{en}_hit_cad_pct'].mean():.4f}")
    lines.append(f"虚伪帖占比: {df['hyp_hit_binary_cad'].mean()*100:.1f}%")
    zero_cov = cover[cover["命中帖数"] == 0]
    lines.append(f"\n0 命中词（共 {len(zero_cov)} 个，需人工核查分词）:")
    for _, r in zero_cov.iterrows():
        lines.append(f"  [{r['类别']}] {r['词']}")
    with open(os.path.join(OUT_DIR, "CAD命中_汇总.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\n已写入: {OUT_DIR}")


if __name__ == "__main__":
    main()
