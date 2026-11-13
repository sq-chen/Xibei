# -*- coding: utf-8 -*-
"""描述性统计公共模块：数据加载、绘图设置、比例检验工具。
供 01~04 脚本 import；输出目录统一为 描述性统计结果/。"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")          # 无界面保存图片
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ---------- 中文字体（与旧流水线 HEATMAP_FONT=SimHei 一致） ----------
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # CAD分析/描述性统计
CAD_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))    # CAD分析/
WIDE_PATH  = os.path.join(CAD_ROOT, "..", "analysis", "分词与情感分析",
                          "分词与情感分析结果", "merged_wide_v2.csv")
CAD_PATH   = os.path.join(CAD_ROOT, "分词与命中", "结果", "CAD命中_明细.csv")
OUT_DIR    = os.path.join(SCRIPT_DIR, "描述性统计结果")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 类别与列名 ----------
CATS = ["伪善", "愤怒", "厌恶", "鄙视"]
CAT_COLS = {"伪善": "hyp_hit_cad", "愤怒": "anger_hit_cad",
            "厌恶": "disgust_hit_cad", "鄙视": "contempt_hit_cad"}
EMO_CATS = ["愤怒", "厌恶", "鄙视"]
EMO_COLS = {"愤怒": "anger_hit_cad", "厌恶": "disgust_hit_cad", "鄙视": "contempt_hit_cad"}
ENGAGE_COLS = {"转发": "reposts_count", "评论": "comments_count",
               "点赞": "attitudes_count", "总互动": "total_engagement"}
PHASE_ORDER = ["P1", "P2", "P3"]


def load_data() -> pd.DataFrame:
    """宽表（互动量/认证/阶段等元数据）左连接 CAD 命中明细（4 类命中计数）。"""
    wide = pd.read_csv(WIDE_PATH, encoding="utf-8-sig", dtype={"ID": str})
    cad = pd.read_csv(CAD_PATH, encoding="utf-8-sig", dtype={"ID": str})
    d = wide.merge(cad, on="ID", how="inner")
    d["created_at"] = pd.to_datetime(d["created_at"], errors="coerce")
    return d


def prop_z(p1: float, n1: int, p2: float, n2: int):
    """两独立样本比例 z 检验：返回 (z, p)。"""
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p <= 0 or p >= 1:
        return np.nan, np.nan
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    return z, 2 * (1 - stats.norm.cdf(abs(z)))


def save_fig(name: str) -> str:
    """保存当前图到 描述性统计结果/ 并关闭。"""
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def to_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(os.path.join(OUT_DIR, name), index=False, encoding="utf-8-sig")
