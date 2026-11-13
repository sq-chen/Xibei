# 补充计算_五情绪复合中介.R
# =====================
# 简单中介：不一致感知(HP) → 消极情绪（五情绪复合：愤怒/厌恶/蔑视/恐惧/悲伤 共 45 条）→ 传播意愿(si3)
# 三个样本分别跑（实验组 N=189 / 对照组 N=184 / 全部样本 N=373）。
# 口径与既有中介脚本完全一致：筛查（指令+记忆+质检）、lavaan、bootstrap 5000、种子 20260903。
# 输出：结果_五情绪复合中介.csv（a/b/cp 路径系数与 p、间接/总效应与 bootstrap CI、Sobel p）

library(readxl)
library(lavaan)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "5000"))

read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}
cmap_exp <- c(
  V1="作答ID", V18="质检结果",
  V22="Q1_1", V23="Q1_2", V24="Q1_3",
  V25="Q2_1", V26="Q2_2", V27="Q2_3", V28="Q2_4", V29="Q2_5", V30="Q2_6",
  V31="Q2_7", V32="Q2_8", V33="Q2_9", V34="Q2_10", V35="Q2_11", V36="Q2_12",
  V37="Q2_13", V38="Q2_14", V39="Q2_15", V40="Q2_16",
  V42="Q4_1", V43="Q4_2", V44="Q4_3",
  V47="Q5_1", V48="Q5_2", V49="Q5_3",
  V50="Q6_1", V51="Q6_2", V52="Q6_3", V53="Q6_4", V54="Q6_5", V55="Q6_6",
  V56="Q6_7", V57="Q6_8", V58="Q6_9", V59="Q6_10", V60="Q6_11", V61="Q6_12",
  V62="Q6_13", V63="Q6_14", V64="Q6_15", V65="Q6_16",
  V67="Q8_1", V68="Q8_2", V69="Q8_3",
  V75="Q12_1", V76="Q12_2", V77="Q12_3",
  V78="Q13_1", V79="Q13_2", V80="Q13_3", V81="Q13_4", V82="Q13_5", V83="Q13_6",
  V84="Q13_7", V85="Q13_8", V86="Q13_9", V87="Q13_10", V88="Q13_11", V89="Q13_12",
  V90="Q13_13", V91="Q13_14", V92="Q13_15", V93="Q13_16",
  V95="Q15_1", V96="Q15_2", V97="Q15_3",
  V118="记忆1", V119="记忆2", V120="记忆3"
)
cmap_ctrl <- c(
  V1="作答ID", V18="质检结果",
  V22="Q1_1", V23="Q1_2", V24="Q1_3",
  V25="Q2_1", V26="Q2_2", V27="Q2_3", V28="Q2_4", V29="Q2_5", V30="Q2_6",
  V31="Q2_7", V32="Q2_8", V33="Q2_9", V34="Q2_10", V35="Q2_11", V36="Q2_12",
  V37="Q2_13", V38="Q2_14", V39="Q2_15", V40="Q2_16",
  V42="Q4_1", V43="Q4_2", V44="Q4_3",
  V47="Q5_1", V48="Q5_2", V49="Q5_3",
  V50="Q6_1", V51="Q6_2", V52="Q6_3", V53="Q6_4", V54="Q6_5", V55="Q6_6",
  V56="Q6_7", V57="Q6_8", V58="Q6_9", V59="Q6_10", V60="Q6_11", V61="Q6_12",
  V62="Q6_13", V63="Q6_14", V64="Q6_15", V65="Q6_16",
  V67="Q8_1", V68="Q8_2", V69="Q8_3",
  V72="Q12_1", V73="Q12_2", V74="Q12_3",
  V75="Q13_1", V76="Q13_2", V77="Q13_3", V78="Q13_4", V79="Q13_5", V80="Q13_6",
  V81="Q13_7", V82="Q13_8", V83="Q13_9", V84="Q13_10", V85="Q13_11", V86="Q13_12",
  V87="Q13_13", V88="Q13_14", V89="Q13_15", V90="Q13_16",
  V92="Q15_1", V93="Q15_2", V94="Q15_3",
  V115="记忆1", V116="记忆2", V117="记忆3"
)
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
to_num <- function(x) as.numeric(c(lk, lkw)[as.character(x)])

build <- function(path, cmap, grp) {
  dat <- read_one(path, cmap)
  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3)
  )
  dat[scale_items] <- lapply(dat[scale_items], to_num)
  rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
  dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)
  chk <- dat$Q2_16 == "比较不同意" & dat$Q6_16 == "比较同意" & dat$Q13_16 == "完全不同意"
  if (grp == 1) {
    mem <- dat$记忆1 == "后厨大量使用冷冻食材" &
           dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
           dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
  } else {
    mem <- dat$记忆1 == "智能电动汽车制造" &
           dat$记忆2 == "在港交所挂牌上市" &
           dat$记忆3 == "外卖业务"
  }
  keep <- chk & mem & (dat$质检结果 == "正常")
  dat <- dat[keep, ]
  data.frame(
    HP = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))]),
    negemo5 = rowMeans(dat[c(paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15))]),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))])
  )
}
d_e <- build("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp, 1)
d_c <- build("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl, 0)
stopifnot(nrow(d_e) == 189, nrow(d_c) == 184)
cat("实验组 N =", nrow(d_e), "| 对照组 N =", nrow(d_c), "\n")

m_single <- '
  negemo5 ~ a*HP
  si3     ~ b*negemo5 + cp*HP
  ind   := a*b
  total := cp + a*b
'
sobel_p <- function(a, b, se_a, se_b) {
  se_ab <- sqrt(b^2 * se_a^2 + a^2 * se_b^2)
  2 * (1 - pnorm(abs(a * b / se_ab)))
}

rows <- list()
for (lab in c("实验组", "对照组", "全部样本")) {
  dd <- switch(lab, 实验组 = d_e, 对照组 = d_c, 全部样本 = rbind(d_e, d_c))
  fit <- lavaan::sem(m_single, data = dd, se = "bootstrap", bootstrap = N_BOOT)
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  a <- pe$est[pe$lhs == "negemo5" & pe$op == "~" & pe$rhs == "HP"]
  b <- pe$est[pe$lhs == "si3" & pe$op == "~" & pe$rhs == "negemo5"]
  cp <- pe$est[pe$lhs == "si3" & pe$op == "~" & pe$rhs == "HP"]
  a_p <- pe$pvalue[pe$lhs == "negemo5" & pe$op == "~" & pe$rhs == "HP"]
  b_p <- pe$pvalue[pe$lhs == "si3" & pe$op == "~" & pe$rhs == "negemo5"]
  cp_p <- pe$pvalue[pe$lhs == "si3" & pe$op == "~" & pe$rhs == "HP"]
  se_a <- pe$se[pe$lhs == "negemo5" & pe$op == "~" & pe$rhs == "HP"]
  se_b <- pe$se[pe$lhs == "si3" & pe$op == "~" & pe$rhs == "negemo5"]
  ind <- pe[pe$lhs == "ind" & pe$op == ":=", ]
  tot <- pe[pe$lhs == "total" & pe$op == ":=", ]
  sp <- sobel_p(a, b, se_a, se_b)
  cat(sprintf("%s: a=%.3f(p=%.4f) b=%.3f(p=%.4f) cp=%.3f(p=%.4f) | ind=%.3f [%.3f, %.3f] Sobel p=%.4f | total=%.3f [%.3f, %.3f]\n",
              lab, a, a_p, b, b_p, cp, cp_p,
              ind$est, ind$ci.lower, ind$ci.upper, sp,
              tot$est, tot$ci.lower, tot$ci.upper))
  rows[[length(rows) + 1]] <- data.frame(
    样本 = lab, a = round(a, 3), a_p = round(a_p, 4),
    b = round(b, 3), b_p = round(b_p, 4), cp = round(cp, 3), cp_p = round(cp_p, 4),
    ind = round(ind$est, 3), ind_lo = round(ind$ci.lower, 3), ind_hi = round(ind$ci.upper, 3),
    sobel_p = round(sp, 4),
    total = round(tot$est, 3), total_lo = round(tot$ci.lower, 3), total_hi = round(tot$ci.upper, 3))
}
out <- do.call(rbind, rows)
write.csv(out, "结果_五情绪复合中介.csv", row.names = FALSE)
cat("\n已导出：结果_五情绪复合中介.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
