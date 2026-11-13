# -*- coding: utf-8 -*-
"""
全部样本（实验组 N=189 + 对照组 N=184 = 373）描述性统计
======================================================
口径与 对照组_描述统计.py / 实验2_数据分析.Rmd / 操纵检验_组间对比.R 完全一致：
  - 筛查：指令题全对 + 记忆题全对 + 质检正常
  - 计分：不一致感知 = 9 条（前 2 条反向 + 第 3 条原向，3 品牌均值）；
          情绪 = 各 3 条 × 3 品牌均值；传播意愿 si3 = 9 条均值、si2 = 6 条均值
输出：
  - 结果_全部样本描述统计.csv     （各构念 M/SD/单样本t/Cohen's d）
  - 结果_全部样本被试水平计分.csv  （被试水平计分数据，含组别 grp）
  - 结果_全部样本描述统计.txt      （全部输出：筛查/人口学/描述/配对/行为/相关/信度/组间对比）
"""
import pandas as pd
import numpy as np
from scipy import stats

DATA_E = "../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx"
DATA_C = "../00_原始与整理数据/已采纳_原始数据_对照组.xlsx"
OUT_DESC = "结果_全部样本描述统计.csv"
OUT_SCORED = "结果_全部样本被试水平计分.csv"
OUT_LOG = "结果_全部样本描述统计.txt"

# ---------- 1. 读取与列名映射（同 操纵检验_组间对比.R / 对照组_描述统计.py） ----------
cmap_e = {
    1: "作答ID", 5: "作答总时长", 18: "质检结果",
    22: "Q1_1", 23: "Q1_2", 24: "Q1_3",
    25: "Q2_1", 26: "Q2_2", 27: "Q2_3", 28: "Q2_4", 29: "Q2_5", 30: "Q2_6",
    31: "Q2_7", 32: "Q2_8", 33: "Q2_9", 34: "Q2_10", 35: "Q2_11", 36: "Q2_12",
    37: "Q2_13", 38: "Q2_14", 39: "Q2_15", 40: "Q2_16",
    41: "Q3", 42: "Q4_1", 43: "Q4_2", 44: "Q4_3",
    47: "Q5_1", 48: "Q5_2", 49: "Q5_3",
    50: "Q6_1", 51: "Q6_2", 52: "Q6_3", 53: "Q6_4", 54: "Q6_5", 55: "Q6_6",
    56: "Q6_7", 57: "Q6_8", 58: "Q6_9", 59: "Q6_10", 60: "Q6_11", 61: "Q6_12",
    62: "Q6_13", 63: "Q6_14", 64: "Q6_15", 65: "Q6_16",
    66: "Q7", 67: "Q8_1", 68: "Q8_2", 69: "Q8_3",
    75: "Q12_1", 76: "Q12_2", 77: "Q12_3",
    78: "Q13_1", 79: "Q13_2", 80: "Q13_3", 81: "Q13_4", 82: "Q13_5", 83: "Q13_6",
    84: "Q13_7", 85: "Q13_8", 86: "Q13_9", 87: "Q13_10", 88: "Q13_11", 89: "Q13_12",
    90: "Q13_13", 91: "Q13_14", 92: "Q13_15", 93: "Q13_16",
    94: "Q14", 95: "Q15_1", 96: "Q15_2", 97: "Q15_3",
    98: "性别", 99: "年龄", 100: "学科", 102: "社媒时长",
    112: "互动倾向", 113: "转发频率",
    114: "Q23_1", 115: "Q23_2", 116: "Q23_3",
    118: "记忆1", 119: "记忆2", 120: "记忆3",
    121: "批次",
}
cmap_c = {
    1: "作答ID", 5: "作答总时长", 18: "质检结果",
    22: "Q1_1", 23: "Q1_2", 24: "Q1_3",
    25: "Q2_1", 26: "Q2_2", 27: "Q2_3", 28: "Q2_4", 29: "Q2_5", 30: "Q2_6",
    31: "Q2_7", 32: "Q2_8", 33: "Q2_9", 34: "Q2_10", 35: "Q2_11", 36: "Q2_12",
    37: "Q2_13", 38: "Q2_14", 39: "Q2_15", 40: "Q2_16",
    41: "Q3", 42: "Q4_1", 43: "Q4_2", 44: "Q4_3",
    47: "Q5_1", 48: "Q5_2", 49: "Q5_3",
    50: "Q6_1", 51: "Q6_2", 52: "Q6_3", 53: "Q6_4", 54: "Q6_5", 55: "Q6_6",
    56: "Q6_7", 57: "Q6_8", 58: "Q6_9", 59: "Q6_10", 60: "Q6_11", 61: "Q6_12",
    62: "Q6_13", 63: "Q6_14", 64: "Q6_15", 65: "Q6_16",
    66: "Q7", 67: "Q8_1", 68: "Q8_2", 69: "Q8_3",
    72: "Q12_1", 73: "Q12_2", 74: "Q12_3",
    75: "Q13_1", 76: "Q13_2", 77: "Q13_3", 78: "Q13_4", 79: "Q13_5", 80: "Q13_6",
    81: "Q13_7", 82: "Q13_8", 83: "Q13_9", 84: "Q13_10", 85: "Q13_11", 86: "Q13_12",
    87: "Q13_13", 88: "Q13_14", 89: "Q13_15", 90: "Q13_16",
    91: "Q14", 92: "Q15_1", 93: "Q15_2", 94: "Q15_3",
    95: "性别", 96: "年龄", 97: "学科", 99: "社媒时长",
    109: "互动倾向", 110: "转发频率",
    111: "Q23_1", 112: "Q23_2", 113: "Q23_3",
    115: "记忆1", 116: "记忆2", 117: "记忆3",
}


def load(path, cmap):
    dat = pd.read_excel(path, skiprows=1, header=0)
    dat.columns = [f"V{i}" for i in range(1, dat.shape[1] + 1)]
    dat.rename(columns={f"V{k}": v for k, v in cmap.items()}, inplace=True)
    return dat


dat_e = load(DATA_E, cmap_e)
dat_c = load(DATA_C, cmap_c)

log = []
log.append(f"导入数据：实验组 {dat_e.shape[0]} 行（西贝/自如/始祖鸟）、"
           f"对照组 {dat_c.shape[0]} 行（小米/农夫山泉/抖音）")

# ---------- 2. 严格筛查（两组同口径：指令题 + 记忆题 + 质检） ----------
chk_e = ((dat_e["Q2_16"] == "比较不同意") & (dat_e["Q6_16"] == "比较同意")
         & (dat_e["Q13_16"] == "完全不同意"))
mem_e = ((dat_e["记忆1"] == "后厨大量使用冷冻食材")
         & (dat_e["记忆2"] == "全流程甲醛管控，检测达标后出租")
         & (dat_e["记忆3"] == "赞助在喜马拉雅山脉举办的烟花秀"))
qua_e = dat_e["质检结果"] == "正常"
keep_e = chk_e & mem_e & qua_e

chk_c = ((dat_c["Q2_16"] == "比较不同意") & (dat_c["Q6_16"] == "比较同意")
         & (dat_c["Q13_16"] == "完全不同意"))
mem_c = ((dat_c["记忆1"] == "智能电动汽车制造")
         & (dat_c["记忆2"] == "在港交所挂牌上市")
         & (dat_c["记忆3"] == "外卖业务"))
qua_c = dat_c["质检结果"] == "正常"
keep_c = chk_c & mem_c & qua_c

log.append("=== 筛查计数（严格口径：指令+记忆+质检） ===")
log.append(f"实验组：总 {len(dat_e)} | 指令题全对 {int(chk_e.sum())} | 记忆题全对 {int(mem_e.sum())} "
           f"| 质检正常 {int(qua_e.sum())} | 纳入分析 {int(keep_e.sum())}")
log.append(f"对照组：总 {len(dat_c)} | 指令题全对 {int(chk_c.sum())} | 记忆题全对 {int(mem_c.sum())} "
           f"| 质检正常 {int(qua_c.sum())} | 纳入分析 {int(keep_c.sum())}")
log.append(f"全部样本 N = {int(keep_e.sum()) + int(keep_c.sum())}")

# ---------- 3. 计分（与 R 完全一致） ----------
lk = {"完全不同意": 1, "不同意": 2, "比较不同意": 3, "一般": 4,
      "比较同意": 5, "同意": 6, "完全同意": 7}
lkw = {"完全不愿意": 1, "不愿意": 2, "比较不愿意": 3, "一般": 4,
       "比较愿意": 5, "愿意": 6, "非常愿意": 7}
lkf = {"完全不符合": 1, "不符合": 2, "比较不符合": 3, "一般": 4,
       "比较符合": 5, "符合": 6, "完全符合": 7}
to_num = {**lk, **lkw, **lkf}

scale_items = ([f"Q1_{i}" for i in range(1, 4)] + [f"Q5_{i}" for i in range(1, 4)]
               + [f"Q12_{i}" for i in range(1, 4)]
               + [f"Q2_{i}" for i in range(1, 16)] + [f"Q6_{i}" for i in range(1, 16)]
               + [f"Q13_{i}" for i in range(1, 16)]
               + [f"Q4_{i}" for i in range(1, 4)] + [f"Q8_{i}" for i in range(1, 4)]
               + [f"Q15_{i}" for i in range(1, 4)]
               + [f"Q23_{i}" for i in range(1, 4)])
rev_items = ["Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2"]


def score(dat):
    for c in scale_items:
        dat[c] = dat[c].map(to_num)
    for c in rev_items:
        dat[c] = 8 - dat[c]

    def CAD(items):
        cols = [f"Q2_{i}" for i in items] + [f"Q6_{i}" for i in items] + [f"Q13_{i}" for i in items]
        return dat[cols].mean(axis=1)

    return pd.DataFrame({
        "id": dat["作答ID"],
        "HP": dat[[f"Q1_{i}" for i in range(1, 4)] + [f"Q5_{i}" for i in range(1, 4)]
                  + [f"Q12_{i}" for i in range(1, 4)]].mean(axis=1),
        "anger": CAD(range(1, 4)), "disgust": CAD(range(4, 7)), "contempt": CAD(range(7, 10)),
        "fear": CAD(range(10, 13)), "sadness": CAD(range(13, 16)),
        "negemo": CAD(range(1, 10)),
        "m_action": dat[[f"Q2_{i}" for i in range(1, 7)] + [f"Q6_{i}" for i in range(1, 7)]
                        + [f"Q13_{i}" for i in range(1, 7)]].mean(axis=1),
        "m_withdraw": CAD(range(7, 10)),
        "si3": dat[[f"Q4_{i}" for i in range(1, 4)] + [f"Q8_{i}" for i in range(1, 4)]
                   + [f"Q15_{i}" for i in range(1, 4)]].mean(axis=1),
        "si2": dat[["Q4_1", "Q4_2", "Q8_1", "Q8_2", "Q15_1", "Q15_2"]].mean(axis=1),
        "female": (dat["性别"] == "女").astype(int),
        "age": pd.to_numeric(dat["年龄"], errors="coerce"),
        "sm_time": dat["社媒时长"].map({"少于30分钟": 1, "30分钟–1小时": 2, "1–2小时": 3,
                                        "2–4小时": 4, "4–6小时": 5, "超过6小时": 6}),
        "freq_fwd": pd.to_numeric(dat["转发频率"], errors="coerce"),
        "CSR": dat[["Q23_1", "Q23_2", "Q23_3"]].mean(axis=1),
    })


sc_e = score(dat_e); sc_e["keep"] = keep_e
sc_c = score(dat_c); sc_c["keep"] = keep_c

# 行为单选：公开回复5 > 转发4 > 点赞3 > 私信2 > 不做1
act_map = {"公开回复，发表自己的看法": 5, "转发这条微博（可附加公开评论）": 4,
           "点赞": 3, "发送私信（其他用户不可见）": 2, "不做任何操作": 1}
for sc, dat in [(sc_e, dat_e), (sc_c, dat_c)]:
    beh = pd.DataFrame({c: dat[c].map(act_map) for c in ["Q3", "Q7", "Q14"]})
    sc["act_ord_mean"] = beh.mean(axis=1)
    sc["act_mean"] = (beh >= 4).astype(float).mean(axis=1)
    sc["dur"] = pd.to_numeric(dat["作答总时长"], errors="coerce")

d_e = sc_e[sc_e["keep"]].copy(); d_c = sc_c[sc_c["keep"]].copy()
d_e["grp"] = 1; d_c["grp"] = 0
d = pd.concat([d_e, d_c], ignore_index=True)
n = len(d)
log.append(f"全部样本主分析 N = {n}（实验组 {len(d_e)} / 对照组 {len(d_c)}）")

# ---------- 4. 人口学 ----------
log.append("\n=== 人口学（全部样本） ===")
log.append(f"性别: 女 {int(d['female'].sum())} / 男 {int(len(d) - d['female'].sum())}")
log.append(f"年龄: M = {d['age'].mean():.1f}, SD = {d['age'].std(ddof=1):.1f}, "
           f"范围 [{int(d['age'].min())}, {int(d['age'].max())}]")
subj_all = pd.concat([dat_e.loc[keep_e, "学科"], dat_c.loc[keep_c, "学科"]])
log.append(f"学科分布:\n{subj_all.value_counts().to_string()}")
log.append(f"社媒时长（1-6 有序）: M = {d['sm_time'].mean():.2f}, SD = {d['sm_time'].std(ddof=1):.2f}")
log.append(f"作答时长(秒): 中位数 = {d['dur'].median():.0f}, 最小值 = {d['dur'].min():.0f}")

# ---------- 5. 描述统计 + 单样本 t（vs 中点 4） ----------
vars_desc = ["HP", "anger", "disgust", "contempt", "fear", "sadness",
             "negemo", "m_action", "m_withdraw", "si3", "si2"]
labels = {"HP": "不一致感知", "anger": "愤怒", "disgust": "厌恶", "contempt": "蔑视",
          "fear": "恐惧", "sadness": "悲伤", "negemo": "消极情绪复合",
          "m_action": "行动组(愤怒+厌恶)", "m_withdraw": "退缩组(蔑视)",
          "si3": "传播意愿", "si2": "主动传播意愿"}
rows = []
log.append("\n=== 描述统计与单样本 t（vs 量表中点 4） ===")
for v in vars_desc:
    x = d[v].dropna()
    tt = stats.ttest_1samp(x, 4)
    dcohen = (x.mean() - 4) / x.std(ddof=1)
    rows.append([labels[v], round(x.mean(), 3), round(x.std(ddof=1), 3),
                 round(tt.statistic, 3), len(x) - 1, tt.pvalue, round(dcohen, 3)])
    log.append(f"{labels[v]}: M = {x.mean():.3f}, SD = {x.std(ddof=1):.3f}, "
               f"t({len(x)-1}) = {tt.statistic:.3f}, p = {tt.pvalue:.4f}, d = {dcohen:.3f}")
desc_df = pd.DataFrame(rows, columns=["构念", "M", "SD", "t", "df", "p", "d_vs4"])

# ---------- 6. 情绪配对比较 ----------
log.append("\n=== 三情绪强度两两配对比较 ===")
for a, b in [("anger", "disgust"), ("anger", "contempt"), ("disgust", "contempt")]:
    tt = stats.ttest_rel(d[a], d[b])
    log.append(f"{labels[a]} vs {labels[b]}: 差值 = {np.mean(d[a]-d[b]):.3f}, "
               f"t = {tt.statistic:.2f}, p = {tt.pvalue:.3f}")

log.append("--- 恐惧/悲伤与三情绪（配对） ---")
for emo in ["anger", "disgust", "contempt"]:
    for fb in ["fear", "sadness"]:
        tt = stats.ttest_rel(d[emo], d[fb])
        log.append(f"{labels[emo]} vs {labels[fb]}: 差值 = {np.mean(d[emo]-d[fb]):.3f}, "
                   f"t = {tt.statistic:.2f}, p = {tt.pvalue:.3f}")

# ---------- 7. 行为单选题（6 品牌汇总） ----------
log.append("\n=== 行为单选题分布（6 品牌汇总 = 6 道题） ===")
beh_all = pd.concat([dat_e.loc[keep_e, ["Q3", "Q7", "Q14"]],
                     dat_c.loc[keep_c, ["Q3", "Q7", "Q14"]]])
tab_all = beh_all.stack().value_counts()
log.append(tab_all.to_string())
pct_active = d["act_mean"].mean() * 100
log.append(f"主动传播比例（公开回复/转发，6 品牌平均）: {pct_active:.1f}%")
log.append(f"分组：实验组 {d_e['act_mean'].mean()*100:.1f}% / 对照组 {d_c['act_mean'].mean()*100:.1f}%")
log.append(f"行为强度 act_ord_mean: M = {d['act_ord_mean'].mean():.3f}, SD = {d['act_ord_mean'].std(ddof=1):.3f}")
r_pb, p_pb = stats.pearsonr(d["si3"], d["act_mean"])
log.append(f"si3 与主动传播 act_mean 点双列相关 r = {r_pb:.3f}, p = {p_pb:.4f}")

# ---------- 8. 相关矩阵（关键对） ----------
log.append("\n=== 核心相关（Pearson，全部样本） ===")
pairs = [("HP", "anger"), ("HP", "disgust"), ("HP", "contempt"),
         ("HP", "fear"), ("HP", "sadness"),
         ("anger", "si3"), ("disgust", "si3"), ("contempt", "si3"),
         ("fear", "si3"), ("sadness", "si3"),
         ("HP", "si3"), ("negemo", "si3")]
for a, b in pairs:
    r, p = stats.pearsonr(d[a], d[b])
    log.append(f"{labels.get(a, a)} ~ {labels.get(b, b)}: r = {r:.3f}, p = {p:.4f}")

# ---------- 9. 信度（Cronbach α，全部样本） ----------
def raw_alpha(df):
    k = df.shape[1]
    if k < 2 or df.shape[0] < 3:
        return np.nan
    var_items = df.var(ddof=1).sum()
    var_total = df.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - var_items / var_total)

item_sets = {
    "不一致感知 HP": [f"Q1_{i}" for i in range(1, 4)] + [f"Q5_{i}" for i in range(1, 4)]
                     + [f"Q12_{i}" for i in range(1, 4)],
    "愤怒": [f"Q2_{i}" for i in range(1, 4)] + [f"Q6_{i}" for i in range(1, 4)]
            + [f"Q13_{i}" for i in range(1, 4)],
    "厌恶": [f"Q2_{i}" for i in range(4, 7)] + [f"Q6_{i}" for i in range(4, 7)]
            + [f"Q13_{i}" for i in range(4, 7)],
    "蔑视": [f"Q2_{i}" for i in range(7, 10)] + [f"Q6_{i}" for i in range(7, 10)]
            + [f"Q13_{i}" for i in range(7, 10)],
    "恐惧": [f"Q2_{i}" for i in range(10, 13)] + [f"Q6_{i}" for i in range(10, 13)]
            + [f"Q13_{i}" for i in range(10, 13)],
    "悲伤": [f"Q2_{i}" for i in range(13, 16)] + [f"Q6_{i}" for i in range(13, 16)]
            + [f"Q13_{i}" for i in range(13, 16)],
    "消极情绪复合": [f"Q2_{i}" for i in range(1, 10)] + [f"Q6_{i}" for i in range(1, 10)]
                    + [f"Q13_{i}" for i in range(1, 10)],
    "传播意愿 si3": [f"Q4_{i}" for i in range(1, 4)] + [f"Q8_{i}" for i in range(1, 4)]
                    + [f"Q15_{i}" for i in range(1, 4)],
    "主动传播意愿 si2": ["Q4_1", "Q4_2", "Q8_1", "Q8_2", "Q15_1", "Q15_2"],
    "CSR关注度": ["Q23_1", "Q23_2", "Q23_3"],
}
items_all = pd.concat([dat_e.loc[keep_e, :], dat_c.loc[keep_c, :]], ignore_index=True)
log.append("\n=== 信度（Cronbach α，全部样本 N=%d） ===" % n)
for name, cols in item_sets.items():
    a = raw_alpha(items_all[cols])
    log.append(f"{name}: α = {a:.3f}")

# ---------- 10. 组间对比简表（实验组 vs 对照组，Welch t，供参考） ----------
log.append("\n=== 组间对比（实验组 - 对照组；Welch t；d 为正 = 实验组更高） ===")
for v in ["HP", "anger", "disgust", "contempt", "fear", "sadness",
          "negemo", "m_action", "m_withdraw", "si3", "si2", "age", "sm_time"]:
    x, y = d_e[v].dropna(), d_c[v].dropna()
    tt = stats.ttest_ind(x, y, equal_var=False)
    sp = np.sqrt(((len(x) - 1) * x.var(ddof=1) + (len(y) - 1) * y.var(ddof=1))
                 / (len(x) + len(y) - 2))
    dd = (x.mean() - y.mean()) / sp
    log.append(f"{labels.get(v, v)}: 实验组 {x.mean():.2f}({x.std(ddof=1):.2f}) vs "
               f"对照组 {y.mean():.2f}({y.std(ddof=1):.2f}), d = {dd:.2f}, p = {tt.pvalue:.4f}")

# ---------- 11. 导出 ----------
desc_df.to_csv(OUT_DESC, index=False, encoding="utf-8-sig")
sc_all = pd.concat([sc_e, sc_c], ignore_index=True)
sc_all.to_csv(OUT_SCORED, index=False, encoding="utf-8-sig")
with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log) + "\n")

print("\n".join(log))
print(f"\n已导出：{OUT_DESC} / {OUT_SCORED} / {OUT_LOG}")
