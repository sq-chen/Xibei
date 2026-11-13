# 恐惧悲伤_单独中介.R
# =====================
# 恐惧、悲伤单独中介检验（实验组 N=189 / 对照组 N=184），导师意见补充。
# 与既有分析完全同口径：
#   - X = HP（不一致感知全量表，9 条），Y = si3（传播意愿，9 条）
#   - 筛查：指令题全对 + 记忆题全对 + 质检正常
#   - lavaan 估计，bootstrap 5000，随机种子 20260903
#   - 单独中介模型语法与 三情绪单独中介 完全一致（仅把 M 换成 fear / sadness）
# 输出：结果_恐惧悲伤中介效应汇总.csv
#       结果_恐惧悲伤中介路径系数.txt（a/b/c'/间接/总效应 全部路径，供论文取数）

library(readxl)
library(lavaan)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "5000"))

# ---------- 1. 读取与列名映射 ----------
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

# ---------- 2. 筛查（两组同口径：指令+记忆+质检） ----------
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

# ---------- 3. 计分（与实验组 Rmd / 对照组中介检验.R 完全一致） ----------
score_data <- function(dat, keep) {
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
    keep        = keep
  )
}

# ---------- 4. 模型语法（与既有单独中介完全一致） ----------
m_single <- '
  M    ~ a*X
  si3  ~ b*M + cp*X
  ind := a*b
  total := cp + a*b
'

run_group <- function(path, colmap, group_label, exp_group, expected_n) {
  dat <- read_one(path, colmap)
  keep <- screen(dat, exp_group)
  cat("\n##########", group_label, "##########\n")
  cat("总", nrow(dat), "| 纳入分析", sum(keep), "\n")
  stopifnot(sum(keep) == expected_n)
  d <- score_data(dat, keep)
  d <- d[d$keep, ]
  cat("主分析样本 N =", nrow(d), "\n")

  fits <- list()
  for (emo in c("fear", "sadness")) {
    cat("\n>>>", group_label, "单独中介：", emo, "bootstrap", N_BOOT, "\n")
    fit <- lavaan::sem(gsub("M", emo, gsub("X", "HP", m_single)),
                       data = d, se = "bootstrap", bootstrap = N_BOOT)
    pe <- lavaan::parameterEstimates(fit, ci = TRUE, standardized = TRUE)
    paths <- pe[pe$op == "~", c("lhs", "rhs", "est", "se", "z", "pvalue", "std.all")]
    ind   <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
    cat("--- 路径系数 ---\n")
    print(cbind(paths[c("lhs", "rhs")],
                round(paths[c("est", "se", "z", "pvalue", "std.all")], 3)),
          row.names = FALSE)
    cat("--- 间接效应（bootstrap 95% CI）---\n")
    print(cbind(效应 = ind$lhs, round(ind[c("est", "ci.lower", "ci.upper")], 3)),
          row.names = FALSE)
    fits[[emo]] <- fit
  }
  fits
}

# ---------- 5. 运行两组 ----------
fits_exp  <- run_group("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp,
                       "实验组（N=189）", exp_group = TRUE,  expected_n = 189)
fits_ctrl <- run_group("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx",     cmap_ctrl,
                       "对照组（N=184）", exp_group = FALSE, expected_n = 184)

# ---------- 6. 导出 ----------
ind_rows <- function(fit, model) {
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  out <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cbind(模型 = model, 效应 = out$lhs, out[, -1])
}
medi_summary <- rbind(
  ind_rows(fits_exp[["fear"]],    "实验组 H2s: 单独中介-恐惧"),
  ind_rows(fits_exp[["sadness"]], "实验组 H2s: 单独中介-悲伤"),
  ind_rows(fits_ctrl[["fear"]],   "对照组 H2s: 单独中介-恐惧"),
  ind_rows(fits_ctrl[["sadness"]],"对照组 H2s: 单独中介-悲伤")
)
write.csv(medi_summary, "结果_恐惧悲伤中介效应汇总.csv", row.names = FALSE)
cat("\n已导出：结果_恐惧悲伤中介效应汇总.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
