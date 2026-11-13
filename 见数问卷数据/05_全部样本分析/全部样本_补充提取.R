# 全部样本_补充提取.R
# =====================
# 从 结果_全部样本_被试水平计分.csv 快速重拟合各中介模型（标准误 = 常规，
# 不做 bootstrap——间接效应的 bootstrap CI 已由 全部样本_总体分析.R 导出），
# 提取 a/b/c' 路径系数（点估计与 p），并补出行为分布、相关 p 值、学科表。
# 供写入进展笔记取数。

library(lavaan)
library(psych)

sc <- read.csv("结果_全部样本_被试水平计分.csv", stringsAsFactors = FALSE,
               fileEncoding = "UTF-8")
d <- sc[sc$keep, ]
cat("N =", nrow(d), "（实验组", sum(d$group == 1), "+ 对照组", sum(d$group == 0), "）\n")

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

show_paths <- function(fit, label) {
  cat("\n==========", label, "==========\n")
  pe <- lavaan::parameterEstimates(fit, standardized = TRUE)
  paths <- pe[pe$op == "~", c("lhs", "rhs", "est", "se", "z", "pvalue", "std.all")]
  print(cbind(paths[c("lhs", "rhs")],
              round(paths[c("est", "se", "z", "pvalue", "std.all")], 3)),
        row.names = FALSE)
  ind <- pe[pe$op == ":=", c("lhs", "est")]
  print(cbind(效应 = ind$lhs, est = round(ind$est, 3)), row.names = FALSE)
  invisible(fit)
}

fit_h2  <- show_paths(lavaan::sem(gsub("X", "HP", m_h2), data = d), "① 简单中介")
fit_h3  <- show_paths(lavaan::sem(gsub("X", "HP", m_h3), data = d), "② 三情绪平行中介")
for (emo in c("anger", "disgust", "contempt", "fear", "sadness")) {
  show_paths(lavaan::sem(gsub("M", emo, gsub("X", "HP", m_single)), data = d),
             paste("单独中介 -", emo))
}
fit_si2 <- show_paths(lavaan::sem(gsub("si3", "si2", gsub("X", "HP", m_h2)), data = d),
                      "⑤ 因变量 si2")
fit_grp <- show_paths(lavaan::sem(gsub("X", "HP", m_h2_groupcov), data = d),
                      "⑥ 简单中介 + 组别协变量")

cat("\n========== 相关矩阵 p 值（全部样本） ==========\n")
cvars <- c("HP", "anger", "disgust", "contempt", "fear", "sadness",
           "negemo", "m_action", "m_withdraw", "si3", "si2", "act_mean")
ct <- psych::corr.test(d[cvars], adjust = "none")
cat("--- r ---\n"); print(round(ct$r, 3))
cat("--- p ---\n"); print(round(ct$p, 3))

cat("\n========== 行为选择分布（三题 × 全部被试） ==========\n")
library(readxl)
read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}
cmap_exp <- c(V41="Q3", V66="Q7", V94="Q14", V1="作答ID",
              V25="Q2_16", V62="Q6_16", V90="Q13_16",
              V118="记忆1", V119="记忆2", V120="记忆3", V18="质检结果")
cmap_ctrl <- c(V41="Q3", V66="Q7", V91="Q14", V1="作答ID",
               V25="Q2_16", V62="Q6_16", V90="Q13_16",
               V115="记忆1", V116="记忆2", V117="记忆3", V18="质检结果")
dat_exp  <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_ctrl <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)
keep_exp  <- dat_exp$Q2_16 == "比较不同意" & dat_exp$Q6_16 == "比较同意" &
             dat_exp$Q13_16 == "完全不同意" &
             dat_exp$记忆1 == "后厨大量使用冷冻食材" &
             dat_exp$记忆2 == "全流程甲醛管控，检测达标后出租" &
             dat_exp$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀" &
             dat_exp$质检结果 == "正常"
keep_ctrl <- dat_ctrl$Q2_16 == "比较不同意" & dat_ctrl$Q6_16 == "比较同意" &
             dat_ctrl$Q13_16 == "完全不同意" &
             dat_ctrl$记忆1 == "智能电动汽车制造" &
             dat_ctrl$记忆2 == "在港交所挂牌上市" &
             dat_ctrl$记忆3 == "外卖业务" &
             dat_ctrl$质检结果 == "正常"
beh_all <- c(unlist(dat_exp[keep_exp, c("Q3", "Q7", "Q14")]),
             unlist(dat_ctrl[keep_ctrl, c("Q3", "Q7", "Q14")]))
print(table(行为 = beh_all))
cat("总行为选择数:", length(beh_all), "\n")

cat("\n========== 学科分布 ==========\n")
print(table(学科 = dat_exp$学科[keep_exp]))
print(table(学科 = dat_ctrl$学科[keep_ctrl]))

cat("\n========== 组间对比补充（恐惧/悲伤/HP/si3，Welch t） ==========\n")
for (v in c("HP", "fear", "sadness", "negemo", "si3", "si2", "act_mean")) {
  x1 <- d[[v]][d$group == 1]; x0 <- d[[v]][d$group == 0]
  tt <- t.test(x1, x0)
  cat(sprintf("%-8s 实验组 M=%.2f(SD=%.2f) vs 对照组 M=%.2f(SD=%.2f), d=%.2f, p=%.3g\n",
              v, mean(x1), sd(x1), mean(x0), sd(x0),
              (mean(x1) - mean(x0)) / sqrt((sd(x1)^2 + sd(x0)^2) / 2),
              tt$p.value))
}
