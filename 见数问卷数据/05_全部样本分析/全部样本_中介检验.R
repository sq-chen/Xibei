# 全部样本_中介检验.R
# =====================
# 实验组（负性不一致，N=189）+ 对照组（中性不一致，N=184）= 全部样本 N=373 的中介检验。
# 与两组单独分析完全同口径：
#   - X = HP（不一致感知全量表，9 条），Y = si3（传播意愿，9 条），稳健性 Y = si2
#   - 筛查：指令题全对 + 记忆题全对 + 质检正常
#   - 计分逻辑与 实验2_数据分析.Rmd / 对照组_中介检验.R 完全一致
#   - lavaan 估计，bootstrap 5000（主模型）/ 2000（si2 与协变量稳健性），随机种子 20260903
# 模型：① 简单中介（消极情绪复合）；② 三情绪平行中介；③ 五情绪单独中介（含恐惧/悲伤）；
#       ④ 行动组 vs 退缩组；⑤ si2 稳健性（简单中介）；⑥ 组别协变量稳健性（简单中介，控制 grp）。
# 输出：结果_全部样本中介效应汇总.csv

library(readxl)
library(lavaan)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "5000"))

# ---------- 1. 读取与列名映射（同 操纵检验_组间对比.R） ----------
read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}
cmap_exp <- c(
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
  V75="Q12_1", V76="Q12_2", V77="Q12_3",
  V78="Q13_1", V79="Q13_2", V80="Q13_3", V81="Q13_4", V82="Q13_5", V83="Q13_6",
  V84="Q13_7", V85="Q13_8", V86="Q13_9", V87="Q13_10", V88="Q13_11", V89="Q13_12",
  V90="Q13_13", V91="Q13_14", V92="Q13_15", V93="Q13_16",
  V94="Q14", V95="Q15_1", V96="Q15_2", V97="Q15_3",
  V98="性别", V99="年龄", V102="社媒时长",
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
  V95="性别", V96="年龄", V99="社媒时长",
  V109="互动倾向", V110="转发频率",
  V111="Q23_1", V112="Q23_2", V113="Q23_3",
  V115="记忆1", V116="记忆2", V117="记忆3"
)
dat_e <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_c <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)

# ---------- 2. 严格筛查（两组同口径：指令+记忆+质检） ----------
chk_e <- dat_e$Q2_16 == "比较不同意" & dat_e$Q6_16 == "比较同意" & dat_e$Q13_16 == "完全不同意"
mem_e <- dat_e$记忆1 == "后厨大量使用冷冻食材" &
         dat_e$记忆2 == "全流程甲醛管控，检测达标后出租" &
         dat_e$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
qua_e <- dat_e$质检结果 == "正常"
keep_e <- chk_e & mem_e & qua_e

chk_c <- dat_c$Q2_16 == "比较不同意" & dat_c$Q6_16 == "比较同意" & dat_c$Q13_16 == "完全不同意"
mem_c <- dat_c$记忆1 == "智能电动汽车制造" &
         dat_c$记忆2 == "在港交所挂牌上市" &
         dat_c$记忆3 == "外卖业务"
qua_c <- dat_c$质检结果 == "正常"
keep_c <- chk_c & mem_c & qua_c

cat("=== 筛查计数（严格口径：指令+记忆+质检） ===\n")
cat("实验组：总", nrow(dat_e), "| 纳入分析", sum(keep_e), "\n")
cat("对照组：总", nrow(dat_c), "| 纳入分析", sum(keep_c), "\n")
cat("全部样本 N =", sum(keep_e) + sum(keep_c), "\n")
stopifnot(sum(keep_e) == 189, sum(keep_c) == 184)

# ---------- 3. 计分（与两组脚本完全一致） ----------
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
         "比较符合"=5, "符合"=6, "完全符合"=7)
to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])

score_one <- function(dat) {
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
  data.frame(
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
    CSR         = rowMeans(dat[c("Q23_1", "Q23_2", "Q23_3")], na.rm = TRUE)
  )
}
sc_e <- score_one(dat_e)[keep_e, ]
sc_c <- score_one(dat_c)[keep_c, ]
sc_e$grp <- 1   # 实验组（负性不一致）
sc_c$grp <- 0   # 对照组（中性不一致）
d <- rbind(sc_e, sc_c)
cat("合并后样本 N =", nrow(d), "（实验组", sum(d$grp == 1), "/ 对照组", sum(d$grp == 0), "）\n\n")

# ---------- 4. 模型语法（与两组脚本相同） ----------
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
m_grp <- '
  m_action   ~ a1*X
  m_withdraw ~ a2*X
  si3 ~ b1*m_action + b2*m_withdraw + cp*X
  ind_action   := a1*b1
  ind_withdraw := a2*b2
  diff := a1*b1 - a2*b2
'
m_cov <- '
  negemo ~ a*X + g1*grp
  si3    ~ b*negemo + cp*X + h1*grp
  ind := a*b
  total := cp + a*b
'

med_report <- function(fit, label) {
  cat("==========", label, "==========\n")
  pe <- lavaan::parameterEstimates(fit, ci = TRUE, standardized = TRUE)
  paths <- pe[pe$op == "~",
              c("lhs", "rhs", "est", "se", "z", "pvalue", "std.all")]
  ind   <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cat("--- 路径系数 ---\n")
  print(cbind(paths[c("lhs", "rhs")],
              round(paths[c("est", "se", "z", "pvalue", "std.all")], 3)),
        row.names = FALSE)
  cat("--- 间接效应（bootstrap 95% CI）---\n")
  print(cbind(效应 = ind$lhs, round(ind[c("est", "ci.lower", "ci.upper")], 3)),
        row.names = FALSE)
  invisible(ind)
}

ind_rows <- function(fit, model) {
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  out <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cbind(模型 = model, 效应 = out$lhs, out[, -1])
}

# ---------- 5. 依次运行（主模型 bootstrap 5000；si2 与协变量 2000） ----------
cat(">>> ① 简单中介（消极情绪复合）bootstrap", N_BOOT, "\n")
fit_h2 <- lavaan::sem(gsub("X", "HP", m_h2), data = d,
                      se = "bootstrap", bootstrap = N_BOOT)
med_report(fit_h2, "全部样本 ① X→消极情绪→SI")

cat(">>> ② 三情绪平行中介 bootstrap", N_BOOT, "\n")
fit_h3 <- lavaan::sem(gsub("X", "HP", m_h3), data = d,
                      se = "bootstrap", bootstrap = N_BOOT)
med_report(fit_h3, "全部样本 ② 三情绪平行中介")

fit_singles <- list()
for (emo in c("anger", "disgust", "contempt", "fear", "sadness")) {
  cat(">>> ③ 单独中介：", emo, "bootstrap", N_BOOT, "\n")
  fit_single <- lavaan::sem(gsub("M", emo, gsub("X", "HP", m_single)),
                            data = d, se = "bootstrap", bootstrap = N_BOOT)
  med_report(fit_single, paste("全部样本 ③ 单独中介 -", emo))
  fit_singles[[emo]] <- fit_single
}

cat(">>> ④ 行动组 vs 退缩组 bootstrap", N_BOOT, "\n")
fit_grp <- lavaan::sem(gsub("X", "HP", m_grp), data = d,
                       se = "bootstrap", bootstrap = N_BOOT)
med_report(fit_grp, "全部样本 ④ 行动组vs退缩组")

cat(">>> ⑤ si2 稳健性 bootstrap", min(N_BOOT, 2000), "\n")
fit_h2_si2 <- lavaan::sem(gsub("si3", "si2", gsub("X", "HP", m_h2)),
                          data = d, se = "bootstrap", bootstrap = min(N_BOOT, 2000))
med_report(fit_h2_si2, "全部样本 ⑤ 因变量 si2")

cat(">>> ⑥ 组别协变量稳健性 bootstrap", min(N_BOOT, 2000), "\n")
fit_h2_cov <- lavaan::sem(gsub("X", "HP", m_cov), data = d,
                          se = "bootstrap", bootstrap = min(N_BOOT, 2000))
med_report(fit_h2_cov, "全部样本 ⑥ 控制组别 grp")

# ---------- 6. 导出 ----------
medi_summary <- rbind(
  ind_rows(fit_h2, "全部样本 简单中介: X→消极情绪→SI"),
  ind_rows(fit_h3, "全部样本 三情绪平行中介"),
  ind_rows(fit_singles[["anger"]],    "全部样本 单独中介-愤怒"),
  ind_rows(fit_singles[["disgust"]],  "全部样本 单独中介-厌恶"),
  ind_rows(fit_singles[["contempt"]], "全部样本 单独中介-蔑视"),
  ind_rows(fit_singles[["fear"]],     "全部样本 单独中介-恐惧"),
  ind_rows(fit_singles[["sadness"]],  "全部样本 单独中介-悲伤"),
  ind_rows(fit_grp, "全部样本 行动组vs退缩组"),
  ind_rows(fit_h2_si2, "全部样本 稳健性: si2"),
  ind_rows(fit_h2_cov, "全部样本 稳健性: 组别协变量")
)
write.csv(medi_summary, "结果_全部样本中介效应汇总.csv", row.names = FALSE)
cat("\n已导出：结果_全部样本中介效应汇总.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
