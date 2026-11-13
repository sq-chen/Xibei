# -*- coding: utf-8 -*-
"""
构建原始词典_稳健性.py
======================
用途：稳健性检查用词典（v4 的对照版）。
口径（已与用户确认）：**切分 + 去编号 + 错别字修正，全部词条保留**——
不执行 v4 的任何删除规则（整句感叹句、谐音歧义词、形容词/动词变体、
错类情绪词、不足 2 字条目等一律保留）。

构成：
  虚伪 = 既有虚伪相关词表（analysis/词典/虚伪相关词.txt，89 词）
        + Q9 全部开放词条（切分/去编号/修正，全保留）
  愤怒 = LIWC 简中 anger 类目全量（265 词；v4 实际删了 4 词：
        气急败坏 / 仇 / 他妈的 / 性骚扰，本版加回）
  厌恶 = Q10 全部开放词条（同虚伪规则）
  鄙视 = Q11 全部开放词条（同虚伪规则）

错别字修正映射（来自 词典筛选逻辑说明.md 第 3 条，共 10 组）：
  隔应→膈应、做呕→作呕、小巧→小瞧、看清→看轻、方案→反感、
  雎不起→瞧不起、顾不了一屑→不屑一顾、不惜一顾→不屑一顾、
  明名不副实→名不副实、令人不是→令人不适、自欺其人→自欺欺人

输出：CAD词典_原始_稳健性.xlsx（虚伪/愤怒/厌恶/鄙视 + 构成报告 sheet）。
注意：本版不做 jieba 短语文件——按用户决定不重跑分词，直接复用 v4 分词
结果做 token 匹配；≥4 字长短语（整句类）在现有分词下会被切碎而漏命中，
稳健性检查方向偏保守（若有差异结论反而更强）。
"""
from __future__ import annotations

import os
import re
import sys

import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # CAD分析/词典
CAD_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))        # CAD分析/
RAW_PATH = os.path.join(SCRIPT_DIR, "词典原数据_全部被试.xlsx")
OLD_DICT_DIR = os.path.join(CAD_ROOT, "..", "analysis", "词典")
HYPO_TXT = os.path.join(OLD_DICT_DIR, "虚伪相关词.txt")
LIWC_DIC = os.path.join(OLD_DICT_DIR, "sc_liwc.dic")
OUT_PATH = os.path.join(SCRIPT_DIR, "CAD词典_原始_稳健性.xlsx")

# ---------- 参数 ----------
# 开放题 sheet 名 -> 词典类别
SHEET2CAT = {"Q9_虚伪": "虚伪", "Q10_厌恶": "厌恶", "Q11_鄙视": "鄙视"}
# 切分标点（中文+英文+空白）
SPLIT_RE = re.compile(r"[，、；。！？,;.!?／/ 　\t\n\r～~|]+")
# 错别字修正映射（词条级精确匹配；第 11 组"视如蔽履"在 v4 中被修正但
# 未记入说明文档，由 v4 差集核查补上，保证两版修正口径一致）
FIX_MAP = {
    "隔应": "膈应", "做呕": "作呕", "小巧": "小瞧", "看清": "看轻",
    "方案": "反感", "雎不起": "瞧不起", "顾不了一屑": "不屑一顾",
    "不惜一顾": "不屑一顾", "明名不副实": "名不副实",
    "令人不是": "令人不适", "自欺其人": "自欺欺人",
    "视如蔽履": "视如敝屣",
}


def split_answer(text: str) -> list[str]:
    """切分 + 编号剥离 + 错别字修正，返回词条列表（全部保留）。"""
    if not text:
        return []
    parts = [p for p in SPLIT_RE.split(str(text)) if p]
    out = []
    for p in parts:
        p = p.strip()
        # 词中数字按分隔处理（"膈应5反胃" -> 膈应 / 反胃）
        subs = re.split(r"\d+", p)
        subs = [s for s in subs if s]
        for s in subs:
            # 词尾编号（上一步已按数字切掉，这里兜底）
            s = re.sub(r"[\d。.、．]+$", "", s).strip()
            # 行首序号（"1.可恶" -> 可恶；数字已在上面切开，处理"一、"类）
            s = re.sub(r"^[一二三四五六七八九十]+[、.．]+", "", s).strip()
            if not s:
                continue
            s = FIX_MAP.get(s, s)  # 错别字修正
            out.append(s)
    return out


def load_liwc_anger() -> tuple[set[str], int]:
    """解析 sc_liwc.dic：每行 `词 类目编号...`；类目编号 129 = anger。"""
    words, def_lines = set(), 0
    for line in open(LIWC_DIC, encoding="utf-8", errors="ignore"):
        parts = line.split()
        if len(parts) < 2:
            continue
        if not any("一" <= ch <= "鿿" for ch in parts[0]):
            def_lines += 1  # 类目定义行（如 "129 anger"）
            continue
        if "129" in parts[1:]:
            words.add(parts[0])
    return words, def_lines


def load_hypo_base() -> tuple[set[str], int]:
    words, skipped = set(), 0
    for line in open(HYPO_TXT, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            skipped += 1
            continue
        words.add(line)
    return words, skipped


def main():
    # ---- 开放词：切分/去编号/修正，全保留 ----
    wb = openpyxl.load_workbook(RAW_PATH, read_only=True)
    open_words: dict[str, set[str]] = {c: set() for c in SHEET2CAT.values()}
    n_fixed = {c: 0 for c in SHEET2CAT.values()}
    n_ans = {c: 0 for c in SHEET2CAT.values()}
    for sheet, cat in SHEET2CAT.items():
        ws = wb[sheet]
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for row in rows:
            if not row or not row[2]:
                continue
            n_ans[cat] += 1
            raw = str(row[2])
            for tok in split_answer(raw):
                if FIX_MAP.get(tok) is not None:
                    n_fixed[cat] += 1
                open_words[cat].add(tok)
    wb.close()

    # ---- 愤怒 = LIWC anger 全量 ----
    anger, _ = load_liwc_anger()
    open_words["愤怒"] = set(anger)

    # ---- 虚伪 += 既有词表（合并前先记录开放词数）----
    n_open_only = {c: len(open_words[c]) for c in SHEET2CAT.values()}
    hypo_base, n_comment = load_hypo_base()
    open_words["虚伪"] |= hypo_base

    # ---- 写入 xlsx ----
    report_rows = [
        ["部分", "来源", "词数", "说明"],
        ["虚伪-既有词表", "analysis/词典/虚伪相关词.txt", len(hypo_base),
         f"跳过注释行 {n_comment}，实际 {len(hypo_base)} 词"],
        ["虚伪-开放词", "Q9 全部作答（切分/去编号/修正，全保留）",
         n_open_only["虚伪"],
         f"作答 {n_ans['虚伪']} 份，应用错别字修正 {n_fixed['虚伪']} 次"],
        ["愤怒", "LIWC sc_liwc.dic anger 类目全量", len(anger),
         "v4 曾删 4 词（气急败坏/仇/他妈的/性骚扰），本版加回"],
        ["厌恶-开放词", "Q10 全部作答（全保留）", len(open_words["厌恶"]),
         f"作答 {n_ans['厌恶']} 份，应用错别字修正 {n_fixed['厌恶']} 次"],
        ["鄙视-开放词", "Q11 全部作答（全保留）", len(open_words["鄙视"]),
         f"作答 {n_ans['鄙视']} 份，应用错别字修正 {n_fixed['鄙视']} 次"],
    ]

    with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as xw:
        for cat in ["虚伪", "愤怒", "厌恶", "鄙视"]:
            df = pd.DataFrame({"词": sorted(open_words[cat]), "来源": "原始_全保留"})
            df.to_excel(xw, sheet_name=cat, index=False)
        pd.DataFrame(report_rows).to_excel(
            xw, sheet_name="构成报告", index=False, header=False)

    print("=== 原始词典（稳健性版）构成 ===")
    for r in report_rows:
        print("  ", r[0], "=", r[2], "词")
    total = len(open_words["虚伪"]) + len(anger) + \
        len(open_words["厌恶"]) + len(open_words["鄙视"])
    print(f"合计（跨类重叠词重复计入）: {total}")
    # 与 v4 差异速览
    v4wb = openpyxl.load_workbook(
        os.path.join(SCRIPT_DIR, "CAD词典_v4_终版.xlsx"), read_only=True)
    v4 = {}
    for cat in ["虚伪", "愤怒", "厌恶", "鄙视"]:
        v4[cat] = {r[0].value for r in v4wb[cat].iter_rows(min_row=2)
                   if r[0].value}
    v4wb.close()
    print("\n=== 与 v4 对比 ===")
    for cat in ["虚伪", "愤怒", "厌恶", "鄙视"]:
        added = open_words[cat] - v4[cat]
        removed = v4[cat] - open_words[cat]
        print(f"{cat}: v4={len(v4[cat])} → 原始={len(open_words[cat])}"
              f"（新增 {len(added)}，减少 {len(removed)}）")
    print(f"\n已写入: {OUT_PATH}")


if __name__ == "__main__":
    main()
