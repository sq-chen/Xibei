# 补充计算_多组SEM标准化.R
# =====================
# 汇报口径：多组比较只报告标准化系数（β）。
# 做法：HP/negemo/si3 在各组内 z 标准化（β = b × SDx/SDy），
#       再拟合显变量多组模型与等值检验——此时系数即标准化 β，
#       等值检验的 χ² 差异直接针对 β 是否组间相等。
# 输出：结果_多组SEM_标准化路径与等值检验.csv

library(readxl)
library(lavaan)

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

prep <- function(dat, grp) {
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
  CAD <- function(items) {
    rowMeans(dat[c(paste0("Q2_", items), paste0("Q6_", items), paste0("Q13_", items))])
  }
  data.frame(
    HP = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))]),
    negemo = CAD(1:9),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))]),
    grp = grp
  )
}
d_e <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
d_c <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)

# 组内 z 标准化 → 系数即标准化 β
z_within <- function(dd) {
  for (v in c("HP", "negemo", "si3")) {
    dd[[v]] <- as.numeric(scale(dd[[v]]))
  }
  dd
}
d <- rbind(z_within(d_e), z_within(d_c))
cat("实验组 N =", nrow(d_e), "| 对照组 N =", nrow(d_c), "| 合计 =", nrow(d), "\n")

m_free <- '
  negemo ~ c(a1, a2)*HP
  si3    ~ c(b1, b2)*negemo + c(cp1, cp2)*HP
  ind_1 := a1*b1
  ind_2 := a2*b2
'
fit_free <- sem(m_free, data = d, group = "grp")
pe <- parameterEstimates(fit_free, ci = TRUE)
print(pe[pe$op %in% c("~", ":="),
         c("lhs", "op", "rhs", "group", "est", "se", "z", "pvalue")],
      row.names = FALSE)

eq_tests <- list(
  a  = 'negemo ~ c(a, a)*HP
        si3    ~ c(b1, b2)*negemo + c(cp1, cp2)*HP',
  b  = 'negemo ~ c(a1, a2)*HP
        si3    ~ c(b, b)*negemo + c(cp1, cp2)*HP',
  cp = 'negemo ~ c(a1, a2)*HP
        si3    ~ c(b1, b2)*negemo + c(cp, cp)*HP',
  all = 'negemo ~ c(a, a)*HP
         si3    ~ c(b, b)*negemo + c(cp, cp)*HP'
)
rows <- list()
for (nm in names(eq_tests)) {
  fit_eq <- sem(eq_tests[[nm]], data = d, group = "grp")
  lr <- anova(fit_eq, fit_free)
  rows[[length(rows) + 1]] <- data.frame(
    约束 = nm, chisq_diff = round(lr[2, "Chisq diff"], 2), df_diff = lr[2, "Df diff"],
    p = round(lr[2, "Pr(>Chisq)"], 4))
}
eq_tab <- do.call(rbind, rows)
cat("\n=== 标准化尺度上的等值检验（H0: 两组 β 相等） ===\n")
print(eq_tab, row.names = FALSE)
write.csv(eq_tab, "结果_多组SEM_标准化路径与等值检验.csv", row.names = FALSE)
cat("\n已导出：结果_多组SEM_标准化路径与等值检验.csv\n")
