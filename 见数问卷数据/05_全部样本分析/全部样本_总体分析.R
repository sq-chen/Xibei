# 全部样本_总体分析.R
# =====================
# 把实验组（负性不一致，N=189）与对照组（中性不一致，N=184）合并为全部样本 N=373，
# 做整体分析：
#   1. 样本构成（性别/年龄/学科/社媒时长/作答时长，两组合并）
#   2. 构念描述统计 + 单样本 t（vs 中点 4）+ 情绪配对比较
#   3. 行为选择分布（合并）+ 主动传播率 + 点双列相关
#   4. 核心相关矩阵（含恐惧/悲伤）
#   5. 信度（合并样本 Cronbach α）
#   6. 中介检验（以全部数据为样本）：
#      ① 简单中介（消极情绪复合）        bootstrap 5000
#      ② 三情绪平行中介                  bootstrap 5000
#      ③ 三情绪单独中介 ×3               bootstrap 5000
#      ④ 恐惧/悲伤单独中介 ×2            bootstrap 5000
#      ⑤ 因变量换 si2 稳健性             bootstrap 2000
#      ⑥ 控制组别的稳健性（组别协变量）    bootstrap 2000
# 全部与既有分析同口径：X = HP（9条）、Y = si3（9条）、lavaan、种子 20260903。
# 输出：
#   结果_全部样本_中介效应汇总.csv
#   结果_全部样本_描述统计.csv
#   结果_全部样本_相关矩阵.csv
#   结果_全部样本_信度表.csv
#   结果_全部样本_被试水平计分.csv
#   结果_全部样本_总体分析.txt（完整日志）

library(readxl)
library(lavaan)
library(psych)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "5000"))

logf <- file("结果_全部样本_总体分析.txt", "w", encoding = "UTF-8")
log <- function(...) {
  txt <- paste0(..., collapse = " ")
  cat(txt, "\n")
  cat(txt, "\n", file = logf)
}

# ---------- 1. 读取与列名映射（同 恐惧悲伤_单独中介.R / 既有脚本） ----------
read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}

cmap_exp <- c(
  V1="作答ID", V2="用户ID", V5="作答总时长", V18="质检结果",
  V22="Q1_1", V23="Q1_2", V24="Q1_3",
  V25="Q2_1", V26="Q2_2", V27="Q2_3", V28="Q2_4", V29="Q2_5", V30="Q2_6",
  V31="Q2_7", V32="Q2_8", V33="Q2_9", V34="Q2_10", V35="Q2_11", V36="Q2_12",
  V37="Q2_13", V38="Q2_14", V39="Q2_15", V40="Q2_16",
  V41="Q3", V42="Q4_1", V43="Q4_2", V44="Q4_3",
  V47="Q5_1", V48="Q5_2", V49="Q5_3",
  V50="Q6_1", V51="Q6_2", V52="Q6_3", V53="Q6_4", V54="Q6_5", V55="Q6_6",
  V56="Q6_7", V57="Q6_8", V58="Q6_9", V59="Q6_10", V60="Q6_11", V61="Q6_12",
  V62="Q6_13", V63="Q6_14", V64="Q6_15", V65="Q6_16",
  V66="Q7", V67="Q8_1", V68="Q8_2", V69="Q8_3",
  V75="Q12_1", V76="Q12_2", V77="Q12_3",
  V78="Q13_1", V79="Q13_2", V80="Q13_3", V81="Q13_4", V82="Q13_5", V83="Q13_6",
  V84="Q13_7", V85="Q13_8", V86="Q13_9", V87="Q13_10", V88="Q13_11", V89="Q13_12",
  V90="Q13_13", V91="Q13_14", V92="Q13_15", V93="Q13_16",
  V94="Q14", V95="Q15_1", V96="Q15_2", V97="Q15_3",
  V98="性别", V99="年龄", V100="学科", V102="社媒时长",
  V112="互动倾向", V113="转发频率",
  V114="Q23_1", V115="Q23_2", V116="Q23_3",
  V118="记忆1", V119="记忆2", V120="记忆3",
  V121="批次"
)

cmap_ctrl <- c(
  V1="作答ID", V5="作答总时长", V18="质检结果",
  V22="Q1_1", V23="Q1_2", V24="Q1_3",
  V25="Q2_1", V26="Q2_2", V27="Q2_3", V28="Q2_4", V29="Q2_5", V30="Q2_6",
  V31="Q2_7", V32="Q2_8", V33="Q2_9", V34="Q2_10", V35="Q2_11", V36="Q2_12",
  V37="Q2_13", V38="Q2_14", V39="Q2_15", V40="Q2_16",
  V41="Q3", V42="Q4_1", V43="Q4_2", V44="Q4_3",
  V47="Q5_1", V48="Q5_2", V49="Q5_3",
  V50="Q6_1", V51="Q6_2", V52="Q6_3", V53="Q6_4", V54="Q6_5", V55="Q6_6",
  V56="Q6_7", V57="Q6_8", V58="Q6_9", V59="Q6_10", V60="Q6_11", V61="Q6_12",
  V62="Q6_13", V63="Q6_14", V64="Q6_15", V65="Q6_16",
  V66="Q7", V67="Q8_1", V68="Q8_2", V69="Q8_3",
  V72="Q12_1", V73="Q12_2", V74="Q12_3",
  V75="Q13_1", V76="Q13_2", V77="Q13_3", V78="Q13_4", V79="Q13_5", V80="Q13_6",
  V81="Q13_7", V82="Q13_8", V83="Q13_9", V84="Q13_10", V85="Q13_11", V86="Q13_12",
  V87="Q13_13", V88="Q13_14", V89="Q13_15", V90="Q13_16",
  V91="Q14", V92="Q15_1", V93="Q15_2", V94="Q15_3",
  V95="性别", V96="年龄", V97="学科", V99="社媒时长",
  V109="互动倾向", V110="转发频率",
  V111="Q23_1", V112="Q23_2", V113="Q23_3",
  V115="记忆1", V116="记忆2", V117="记忆3"
)

# ---------- 2. 筛查与计分（两组同口径，见既有脚本） ----------
# 两组原始表列数不同（实验组多 用户ID/批次 等列），score_all 只把
# 两组共用的条目列拼进返回表，保证 rbind 对齐。
common_cols <- c(
  paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
  paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
  paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3),
  paste0("Q23_", 1:3),
  "性别", "年龄", "学科", "社媒时长", "转发频率", "互动倾向",
  "质检结果", "作答总时长"
)

screen <- function(dat, exp_group = TRUE) {
  chk <- dat$Q2_16 == "比较不同意" & dat$Q6_16 == "比较同意" & dat$Q13_16 == "完全不同意"
  if (exp_group) {
    mem <- dat$记忆1 == "后厨大量使用冷冻食材" &
           dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
           dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
  } else {
    mem <- dat$记忆1 == "智能电动汽车制造" &
           dat$记忆2 == "在港交所挂牌上市" &
           dat$记忆3 == "外卖业务"
  }
  qua <- dat$质检结果 == "正常"
  chk & mem & qua
}

score_all <- function(dat, keep) {
  lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
          "比较同意"=5, "同意"=6, "完全同意"=7)
  lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
           "比较愿意"=5, "愿意"=6, "非常愿意"=7)
  lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
           "比较符合"=5, "符合"=6, "完全符合"=7)
  to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])

  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3),
    paste0("Q23_", 1:3)
  )
  dat[scale_items] <- lapply(dat[scale_items], to_num)
  rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
  dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)

  CAD <- function(items) {
    rowMeans(dat[c(paste0("Q2_", items), paste0("Q6_", items), paste0("Q13_", items))],
             na.rm = TRUE)
  }
  # 行为单选题编码：有序版（公开回复5 > 转发4 > 点赞3 > 私信2 > 不做1）；
  # act_mean = 3 题中"主动传播（公开回复/转发）"的比例
  act_map <- c("公开回复，发表自己的看法"=5, "转发这条微博（可附加公开评论）"=4,
               "点赞"=3, "发送私信（其他用户不可见）"=2, "不做任何操作"=1)
  beh_ord <- data.frame(act_map[dat$Q3], act_map[dat$Q7], act_map[dat$Q14])
  data.frame(
    id          = dat$作答ID,
    HP          = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))],
                           na.rm = TRUE),
    anger       = CAD(1:3),
    disgust     = CAD(4:6),
    contempt    = CAD(7:9),
    fear        = CAD(10:12),
    sadness     = CAD(13:15),
    negemo      = CAD(1:9),
    m_action    = rowMeans(dat[c(paste0("Q2_", 1:6), paste0("Q6_", 1:6), paste0("Q13_", 1:6))],
                           na.rm = TRUE),
    m_withdraw  = CAD(7:9),
    si3         = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))],
                           na.rm = TRUE),
    si2         = rowMeans(dat[c("Q4_1", "Q4_2", "Q8_1", "Q8_2", "Q15_1", "Q15_2")],
                           na.rm = TRUE),
    female      = as.integer(dat$性别 == "女"),
    age         = as.numeric(dat$年龄),
    sm_time     = as.numeric(c("少于30分钟"=1, "30分钟–1小时"=2, "1–2小时"=3,
                               "2–4小时"=4, "4–6小时"=5, "超过6小时"=6)[dat$社媒时长]),
    freq_fwd    = as.numeric(dat$转发频率),
    CSR         = rowMeans(dat[c("Q23_1", "Q23_2", "Q23_3")], na.rm = TRUE),
    dur         = as.numeric(dat$作答总时长),
    act_ord_mean = rowMeans(beh_ord, na.rm = TRUE),
    act_mean     = rowMeans((beh_ord >= 4) * 1, na.rm = TRUE),
    keep        = keep,
    dat[common_cols]
  )
}

# ---------- 3. 合并 ----------
log("########## 数据合并 ##########")
dat_exp  <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_ctrl <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)
keep_exp  <- screen(dat_exp,  TRUE)
keep_ctrl <- screen(dat_ctrl, FALSE)
log("实验组：总", nrow(dat_exp), "| 纳入", sum(keep_exp))
log("对照组：总", nrow(dat_ctrl), "| 纳入", sum(keep_ctrl))
stopifnot(sum(keep_exp) == 189, sum(keep_ctrl) == 184)

sc_exp  <- score_all(dat_exp,  keep_exp)
sc_ctrl <- score_all(dat_ctrl, keep_ctrl)
sc_exp$group  <- 1L  # 1 = 负性不一致实验组
sc_ctrl$group <- 0L  # 0 = 中性不一致对照组
sc <- rbind(sc_exp, sc_ctrl)
d <- sc[sc$keep, ]
log("全部样本：实验组", sum(d$group == 1), "人 + 对照组", sum(d$group == 0),
    "人 = N =", nrow(d), "\n")

# ---------- 4. 样本构成 ----------
log("########## 4. 样本构成（全部样本） ##########")
log("性别：女", sum(d$female == 1), "人 / 男", sum(d$female == 0), "人")
log(sprintf("年龄：M = %.1f, SD = %.1f, 范围 [%d, %d]",
            mean(d$age, na.rm = TRUE), sd(d$age, na.rm = TRUE),
            min(d$age, na.rm = TRUE), max(d$age, na.rm = TRUE)))
log("学科分布（合并，实验组部分）：")
print(table(学科 = dat_exp$学科[keep_exp]), row.names = FALSE)
log("学科分布（合并，对照组部分）：")
print(table(学科 = dat_ctrl$学科[keep_ctrl]), row.names = FALSE)
log("")
log(sprintf("社媒时长（1-6 有序）：M = %.2f, SD = %.2f",
            mean(d$sm_time, na.rm = TRUE), sd(d$sm_time, na.rm = TRUE)))
log(sprintf("作答时长(秒)：中位数 = %.0f, 最小值 = %.0f",
            median(d$dur, na.rm = TRUE), min(d$dur, na.rm = TRUE)))

# ---------- 5. 构念描述统计 + 单样本 t（vs 中点 4） ----------
log("\n########## 5. 构念描述统计与单样本 t（vs 量表中点 4，N=373） ##########")
vars_desc <- c("HP", "anger", "disgust", "contempt", "fear", "sadness",
               "negemo", "m_action", "m_withdraw", "si3", "si2")
labels <- c(HP="不一致感知", anger="愤怒", disgust="厌恶", contempt="蔑视",
            fear="恐惧", sadness="悲伤", negemo="消极情绪复合",
            m_action="行动组(愤怒+厌恶)", m_withdraw="退缩组(蔑视)",
            si3="传播意愿", si2="主动传播意愿")
desc_rows <- lapply(vars_desc, function(v) {
  x <- d[[v]]
  tt <- t.test(x, mu = 4)
  r <- c(M = mean(x), SD = sd(x), t = unname(tt$statistic),
         df = unname(tt$parameter), p = tt$p.value,
         d = (mean(x) - 4) / sd(x))
  log(sprintf("%-14s M = %.3f, SD = %.3f, t(%d) = %.2f, p = %.4g, d = %.3f",
              labels[[v]], r["M"], r["SD"], r["df"], r["t"], r["p"], r["d"]))
  r
})
desc_df <- data.frame(构念 = unname(labels[vars_desc]), do.call(rbind, desc_rows))

log("\n--- 情绪两两配对比较（全部样本） ---")
emo5 <- c("anger", "disgust", "contempt", "fear", "sadness")
for (i in 1:4) for (j in (i + 1):5) {
  a <- emo5[i]; b <- emo5[j]
  tt <- t.test(d[[a]], d[[b]], paired = TRUE)
  log(sprintf("%s vs %s: 差值 = %.3f, t = %.2f, p = %.3f",
              labels[[a]], labels[[b]], mean(d[[a]] - d[[b]]),
              tt$statistic, tt$p.value))
}

# ---------- 6. 行为选择（合并分布） ----------
log("\n########## 6. 行为选择（三题 × 全部被试，合并分布） ##########")
beh_exp  <- unlist(dat_exp[keep_exp,  c("Q3", "Q7", "Q14")])
beh_ctrl <- unlist(dat_ctrl[keep_ctrl, c("Q3", "Q7", "Q14")])
beh_all  <- c(beh_exp, beh_ctrl)
print(table(行为 = beh_all), row.names = FALSE)
log("")
act_map <- c("公开回复，发表自己的看法"=5, "转发这条微博（可附加公开评论）"=4,
             "点赞"=3, "发送私信（其他用户不可见）"=2, "不做任何操作"=1)
act_all <- act_map[beh_all]
log(sprintf("主动传播率（公开回复/转发，三题合并）：%.1f%%", mean(act_all >= 4) * 100))
log(sprintf("行为强度（1-5 有序）合并均值：M = %.2f, SD = %.2f",
            mean(act_all), sd(act_all)))
r_pb <- cor.test(d$si3, d$act_mean)
log(sprintf("矩阵传播意愿 si3 与主动传播比例（被试水平）点双列相关 r = %.3f, p = %.4g",
            r_pb$estimate, r_pb$p.value))

# ---------- 7. 相关矩阵 ----------
log("\n########## 7. 核心相关矩阵（全部样本，Pearson） ##########")
cvars <- c("HP", "anger", "disgust", "contempt", "fear", "sadness",
           "negemo", "m_action", "m_withdraw", "si3", "si2", "act_mean")
ct <- psych::corr.test(d[cvars], adjust = "none")
print(round(ct$r, 3))
log("--- p 值矩阵 ---")
print(round(ct$p, 3))

# ---------- 8. 信度 ----------
log("\n########## 8. 信度（Cronbach α，全部样本 N=373） ##########")
alpha_of <- function(items) {
  psych::alpha(sc[sc$keep, items], check.keys = FALSE)$total$raw_alpha
}
item_sets <- list(
  不一致感知_HP = c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3)),
  愤怒 = c(paste0("Q2_", 1:3),  paste0("Q6_", 1:3),  paste0("Q13_", 1:3)),
  厌恶 = c(paste0("Q2_", 4:6),  paste0("Q6_", 4:6),  paste0("Q13_", 4:6)),
  蔑视 = c(paste0("Q2_", 7:9),  paste0("Q6_", 7:9),  paste0("Q13_", 7:9)),
  恐惧 = c(paste0("Q2_", 10:12),paste0("Q6_", 10:12),paste0("Q13_", 10:12)),
  悲伤 = c(paste0("Q2_", 13:15),paste0("Q6_", 13:15),paste0("Q13_", 13:15)),
  消极情绪复合 = c(paste0("Q2_", 1:9),  paste0("Q6_", 1:9),  paste0("Q13_", 1:9)),
  行动组 = c(paste0("Q2_", 1:6),  paste0("Q6_", 1:6),  paste0("Q13_", 1:6)),
  退缩组 = c(paste0("Q2_", 7:9),  paste0("Q6_", 7:9),  paste0("Q13_", 7:9)),
  传播意愿_si3 = c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3)),
  主动传播意愿_si2 = c("Q4_1", "Q4_2", "Q8_1", "Q8_2", "Q15_1", "Q15_2"),
  CSR关注度 = c("Q23_1", "Q23_2", "Q23_3")
)
alpha_rows <- lapply(names(item_sets), function(nm) {
  a <- alpha_of(item_sets[[nm]])
  log(sprintf("%-18s α = %.3f", nm, a))
  a
})
alpha_df <- data.frame(构念 = names(item_sets), alpha = unlist(alpha_rows))

# ---------- 9. 中介检验（以全部数据为样本） ----------
log("\n########## 9. 中介检验（全部样本 N=373，bootstrap，种子 20260903） ##########")

m_h2 <- '
  negemo ~ a*X
  si3    ~ b*negemo + cp*X
  ind := a*b
  total := cp + a*b
'
m_h3 <- '
  anger    ~ a1*X
  disgust  ~ a2*X
  contempt ~ a3*X
  si3 ~ b1*anger + b2*disgust + b3*contempt + cp*X
  ind_anger    := a1*b1
  ind_disgust  := a2*b2
  ind_contempt := a3*b3
  total := cp + a1*b1 + a2*b2 + a3*b3
  diff_a_d := a1*b1 - a2*b2
  diff_a_c := a1*b1 - a3*b3
  diff_d_c := a2*b2 - a3*b3
'
m_single <- '
  M    ~ a*X
  si3  ~ b*M + cp*X
  ind := a*b
  total := cp + a*b
'
m_h2_groupcov <- '
  negemo ~ a*X + g1*group
  si3    ~ b*negemo + cp*X + g2*group
  ind := a*b
  total := cp + a*b
'

med_report <- function(fit, label) {
  log("==========", label, "==========")
  pe <- lavaan::parameterEstimates(fit, ci = TRUE, standardized = TRUE)
  paths <- pe[pe$op == "~",
              c("lhs", "rhs", "est", "se", "z", "pvalue", "std.all")]
  ind   <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  log("--- 路径系数 ---")
  print(cbind(paths[c("lhs", "rhs")],
              round(paths[c("est", "se", "z", "pvalue", "std.all")], 3)),
        row.names = FALSE)
  log("--- 间接效应（bootstrap 95% CI）---")
  print(cbind(效应 = ind$lhs, round(ind[c("est", "ci.lower", "ci.upper")], 3)),
        row.names = FALSE)
  log("")
  invisible(ind)
}

ind_rows <- function(fit, model) {
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  out <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cbind(模型 = model, 效应 = out$lhs, out[, -1])
}

log(">>> ① 简单中介（消极情绪复合）bootstrap", N_BOOT)
fit_h2 <- lavaan::sem(gsub("X", "HP", m_h2), data = d,
                      se = "bootstrap", bootstrap = N_BOOT)
med_report(fit_h2, "全部样本 ① X→消极情绪→SI")

log(">>> ② 三情绪平行中介 bootstrap", N_BOOT)
fit_h3 <- lavaan::sem(gsub("X", "HP", m_h3), data = d,
                      se = "bootstrap", bootstrap = N_BOOT)
med_report(fit_h3, "全部样本 ② 三情绪平行中介")

fit_singles <- list()
for (emo in c("anger", "disgust", "contempt")) {
  log(">>> ③ 单独中介：", emo, "bootstrap", N_BOOT)
  fit_single <- lavaan::sem(gsub("M", emo, gsub("X", "HP", m_single)),
                            data = d, se = "bootstrap", bootstrap = N_BOOT)
  med_report(fit_single, paste("全部样本 ③ 单独中介 -", emo))
  fit_singles[[emo]] <- fit_single
}

for (emo in c("fear", "sadness")) {
  log(">>> ④ 单独中介：", emo, "bootstrap", N_BOOT)
  fit_single <- lavaan::sem(gsub("M", emo, gsub("X", "HP", m_single)),
                            data = d, se = "bootstrap", bootstrap = N_BOOT)
  med_report(fit_single, paste("全部样本 ④ 单独中介 -", emo))
  fit_singles[[emo]] <- fit_single
}

log(">>> ⑤ si2 稳健性 bootstrap", min(N_BOOT, 2000))
fit_h2_si2 <- lavaan::sem(gsub("si3", "si2", gsub("X", "HP", m_h2)),
                          data = d, se = "bootstrap", bootstrap = min(N_BOOT, 2000))
med_report(fit_h2_si2, "全部样本 ⑤ 因变量 si2")

log(">>> ⑥ 控制组别（group 协变量）bootstrap", min(N_BOOT, 2000))
fit_h2_grp <- lavaan::sem(gsub("X", "HP", m_h2_groupcov), data = d,
                          se = "bootstrap", bootstrap = min(N_BOOT, 2000))
med_report(fit_h2_grp, "全部样本 ⑥ 简单中介 + 组别协变量")

# ---------- 10. 导出 ----------
medi_summary <- rbind(
  ind_rows(fit_h2, "全部样本 H3: X→消极情绪→SI"),
  ind_rows(fit_h3, "全部样本 H2: 三情绪平行中介"),
  ind_rows(fit_singles[["anger"]],    "全部样本 H2s: 单独中介-愤怒"),
  ind_rows(fit_singles[["disgust"]],  "全部样本 H2s: 单独中介-厌恶"),
  ind_rows(fit_singles[["contempt"]], "全部样本 H2s: 单独中介-蔑视"),
  ind_rows(fit_singles[["fear"]],     "全部样本 H2s: 单独中介-恐惧"),
  ind_rows(fit_singles[["sadness"]],  "全部样本 H2s: 单独中介-悲伤"),
  ind_rows(fit_h2_si2, "全部样本 稳健性: si2"),
  ind_rows(fit_h2_grp, "全部样本 稳健性: 组别协变量")
)
write.csv(medi_summary, "结果_全部样本_中介效应汇总.csv", row.names = FALSE)
write.csv(desc_df, "结果_全部样本_描述统计.csv", row.names = FALSE)
write.csv(round(ct$r, 3), "结果_全部样本_相关矩阵.csv")
write.csv(alpha_df, "结果_全部样本_信度表.csv", row.names = FALSE)
write.csv(sc, "结果_全部样本_被试水平计分.csv", row.names = FALSE)

log("\n已导出：结果_全部样本_中介效应汇总.csv / 结果_全部样本_描述统计.csv /",
    "结果_全部样本_相关矩阵.csv / 结果_全部样本_信度表.csv / 结果_全部样本_被试水平计分.csv /",
    "结果_全部样本_总体分析.txt")
log("完成时间：", format(Sys.time()))
close(logf)
