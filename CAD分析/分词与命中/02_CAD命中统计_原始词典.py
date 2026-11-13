# -*- coding: utf-8 -*-
"""
02_CAD命中统计_原始词典.py
==========================
稳健性检查：用 **原始词典（全保留版）** 对同一份 v4 分词结果做精确 token
命中计数（不重跑分词——用户决定；长短语在现有分词下会切碎漏命中，
稳健性方向偏保守）。

与 01 的唯一差异：词典换为 词典/CAD词典_原始_稳健性.xlsx，
输出目录换为 结果_原始词典/。其余口径完全一致。

输出目录：分词与命中/结果_原始词典/
  - CAD命中_明细.csv / CAD命中_覆盖率.csv / CAD命中_汇总.txt
"""
from __future__ import annotations

import os
import sys

import openpyxl
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))        # CAD分析/分词与命中
CAD_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))  # CAD分析/
DICT_PATH  = os.path.join(CAD_ROOT, "词典", "CAD词典_原始_稳健性.xlsx")
SEG_PATH = os.path.join(CAD_ROOT, "..", "analysis", "分词与情感分析",
                        "分词与情感分析结果", "分词", "weibo关键词_分词结果.pickle")
OUT_DIR = os.path.join(SCRIPT_DIR, "结果_原始词典")
os.makedirs(OUT_DIR, exist_ok=True)

CATS = ["虚伪", "愤怒", "厌恶", "鄙视"]
CAT_EN = {"虚伪": "hyp", "愤怒": "anger", "厌恶": "disgust", "鄙视": "contempt"}


def load_dict() -> dict[str, set[str]]:
    wb = openpyxl.load_workbook(DICT_PATH, read_only=True)
    out = {}
    for cat in CATS:
        ws = wb[cat]
        out[cat] = {str(r[0].value).strip() for r in ws.iter_rows(min_row=2)
                    if r[0].value and str(r[0].value).strip()}
    wb.close()
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("加载词典（原始全保留版）...")
    d = load_dict()
    for c in CATS:
        print(f"  {c}: {len(d[c])} 词")

    print("加载分词结果（v4 分词 pickle，不重跑）...")
    df = pd.read_pickle(SEG_PATH)
    n = len(df)

    words = df["中文分词"].map(
        lambda wl: [w for w, _ in wl] if isinstance(wl, list) else []
    )
    n_words = words.map(len).clip(lower=1)

    print("命中计数 ...")
    for cat in CATS:
        s = d[cat]
        df[f"{CAT_EN[cat]}_hit_raw"] = words.map(lambda wl: sum(1 for w in wl if w in s))
    df["hyp_hit_binary_raw"] = (df["hyp_hit_raw"] > 0).astype(int)
    for cat in CATS:
        en = CAT_EN[cat]
        df[f"{en}_hit_raw_pct"] = df[f"{en}_hit_raw"] / n_words

    out_cols = ["ID"] + [f"{CAT_EN[c]}_hit_raw" for c in CATS] \
        + [f"{CAT_EN[c]}_hit_raw_pct" for c in CATS] + ["hyp_hit_binary_raw"]
    df[out_cols].to_csv(os.path.join(OUT_DIR, "CAD命中_明细.csv"),
                        index=False, encoding="utf-8-sig")

    token_sets = [set(wl) for wl in words]
    cover_rows = []
    for cat in CATS:
        for w in sorted(d[cat], key=lambda x: (len(x), x)):
            cover_rows.append({"类别": cat, "词": w,
                               "命中帖数": sum(1 for ts in token_sets if w in ts)})
    cover = pd.DataFrame(cover_rows)
    cover.to_csv(os.path.join(OUT_DIR, "CAD命中_覆盖率.csv"),
                 index=False, encoding="utf-8-sig")

    lines = [f"总帖数: {n}", "（词典：原始全保留版；分词：v4 pickle 未重跑）"]
    for cat in CATS:
        en = CAT_EN[cat]
        hit_n = int((df[f"{en}_hit_raw"] > 0).sum())
        lines.append(f"{cat}: 命中帖 {hit_n} ({hit_n/n*100:.1f}%), "
                     f"命中次数均值 {df[f'{en}_hit_raw'].mean():.3f}, "
                     f"/词总数均值 {df[f'{en}_hit_raw_pct'].mean():.4f}")
    lines.append(f"虚伪帖占比: {df['hyp_hit_binary_raw'].mean()*100:.1f}%")
    zero_cov = cover[cover["命中帖数"] == 0]
    lines.append(f"\n0 命中词（共 {len(zero_cov)} 个，长短语多为现有分词切碎所致）:")
    for _, r in zero_cov.iterrows():
        lines.append(f"  [{r['类别']}] {r['词']}")
    with open(os.path.join(OUT_DIR, "CAD命中_汇总.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\n已写入: {OUT_DIR}")


if __name__ == "__main__":
    main()
