# 实验2_多组SEM.R
# =====================
# 2-1 多组结构方程模型与测量不变性（实验组 N=189 vs 对照组 N=184）。
# 目的：
#   ① 测量不变性：三因子（不一致感知 HP / 消极情绪 NEG / 传播意愿 SI，各 3 个品牌包裹）
#      跨组 configural → metric → scalar 逐步加约束，判断两组量表是否同构（合并 N=373 合法性的前提）；
#   ② 多组中介：在标量不变性约束下估计两组 a/b/cp 路径，并用 χ² 差异检验逐条比较——
#      "道德性质改变水平而非机制"的正式证据。
# 包裹构造（每构念 3 个品牌包裹，组间同构）：
#   HP:  西贝 Q1_1-3 均值 / 自如 Q5_1-3 / 始祖鸟 Q12_1-3
#   NEG: 西贝 Q2_1-9 / 自如 Q6_1-9 / 始祖鸟 Q13_1-9（愤怒+厌恶+蔑视 9 条）
#   SI:  西贝 Q4_1-3 / 自如 Q8_1-3 / 始祖鸟 Q15_1-3
# 输出：结果_多组SEM_测量不变性.csv / 结果_多组SEM_路径系数.csv / 结果_多组SEM_等值检验.csv

library(readxl)
library(lavaan)

# ---------- 1. 读取与筛查计分（与既有脚本完全同口径） ----------
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
dat_e <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_c <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)

lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
         "比较符合"=5, "符合"=6, "完全符合"=7)
to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])

prep <- function(dat, grp_label) {
  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3)
  )
  dat[scale_items] <- lapply(dat[scale_items], to_num)
  rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
  dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)
  chk <- dat$Q2_16 == "比较不同意" & dat$Q6_16 == "比较同意" & dat$Q13_16 == "完全不同意"
  if (grp_label == "exp") {
    mem <- dat$记忆1 == "后厨大量使用冷冻食材" &
           dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
           dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
  } else {
    mem <- dat$记忆1 == "智能电动汽车制造" &
           dat$记忆2 == "在港交所挂牌上市" &
           dat$记忆3 == "外卖业务"
  }
  keep <- chk & mem & (dat$质检结果 == "正常")
  out <- data.frame(
    grp = grp_label,
    hp1 = rowMeans(dat[paste0("Q1_", 1:3)], na.rm = TRUE),
    hp2 = rowMeans(dat[paste0("Q5_", 1:3)], na.rm = TRUE),
    hp3 = rowMeans(dat[paste0("Q12_", 1:3)], na.rm = TRUE),
    neg1 = rowMeans(dat[paste0("Q2_", 1:9)],  na.rm = TRUE),
    neg2 = rowMeans(dat[paste0("Q6_", 1:9)],  na.rm = TRUE),
    neg3 = rowMeans(dat[paste0("Q13_", 1:9)], na.rm = TRUE),
    si1  = rowMeans(dat[paste0("Q4_", 1:3)],  na.rm = TRUE),
    si2  = rowMeans(dat[paste0("Q8_", 1:3)],  na.rm = TRUE),
    si3  = rowMeans(dat[paste0("Q15_", 1:3)], na.rm = TRUE),
    keep = keep
  )
  out <- out[out$keep, ]
  out$keep <- NULL
  out
}
d_e <- prep(dat_e, "exp")
d_c <- prep(dat_c, "ctrl")
d <- rbind(d_e, d_c)
cat("实验组 N =", nrow(d_e), "| 对照组 N =", nrow(d_c), "| 合计 =", nrow(d), "\n")
stopifnot(nrow(d_e) == 189, nrow(d_c) == 184)

# ---------- 2. 测量模型与不变性检验 ----------
m_meas <- '
  HP  =~ hp1 + hp2 + hp3
  NEG =~ neg1 + neg2 + neg3
  SI  =~ si1 + si2 + si3
  # 同一品牌的三个包裹共享品牌情境方差（MTMM 风格的相关残差）
  hp1 ~~ neg1 + si1
  neg1 ~~ si1
  hp2 ~~ neg2 + si2
  neg2 ~~ si2
  hp3 ~~ neg3 + si3
  neg3 ~~ si3
'
fit_cfg <- cfa(m_meas, data = d, group = "grp")
fit_met <- cfa(m_meas, data = d, group = "grp", group.equal = "loadings")
fit_sca <- cfa(m_meas, data = d, group = "grp", group.equal = c("loadings", "intercepts"))

fit_tab <- function(fit, step) {
  fm <- fitMeasures(fit, c("chisq", "df", "pvalue", "cfi", "rmsea", "srmr"))
  data.frame(步骤 = step, 模型 = if (step == "configural") "形态等值" else
              if (step == "metric") "载荷等值" else "截距等值",
             chisq = round(fm["chisq"], 2), df = fm["df"], p = round(fm["pvalue"], 4),
             CFI = round(fm["cfi"], 3), RMSEA = round(fm["rmsea"], 3),
             SRMR = round(fm["srmr"], 3))
}
inv_tab <- rbind(fit_tab(fit_cfg, "configural"),
                 fit_tab(fit_met, "metric"),
                 fit_tab(fit_sca, "scalar"))
cat("\n=== 测量不变性 ===\n"); print(inv_tab, row.names = FALSE)

lrt_met <- anova(fit_cfg, fit_met)   # 形态 vs 载荷
lrt_sca <- anova(fit_met, fit_sca)   # 载荷 vs 截距
cat("\n形态 vs 载荷等值: chi2 =", round(lrt_met[2, "Chisq diff"], 2),
    "df =", lrt_met[2, "Df diff"], "p =", round(lrt_met[2, "Pr(>Chisq)"], 4), "\n")
cat("载荷 vs 截距等值: chi2 =", round(lrt_sca[2, "Chisq diff"], 2),
    "df =", lrt_sca[2, "Df diff"], "p =", round(lrt_sca[2, "Pr(>Chisq)"], 4), "\n")
inv_tab$delta_CFI <- c(NA, diff(inv_tab$CFI))
write.csv(inv_tab, "结果_多组SEM_测量不变性.csv", row.names = FALSE)

# ---------- 3. 多组中介（显变量主口径：复合分数，尺度与既有单组分析一致） ----------
# 注：潜变量版结构系数受组间测量尺度差异扭曲（SI 潜变量尺度随组变化），
# 故路径系数比较以显变量模型为准；潜变量模型仅用于测量不变性并附报标准化系数。
m_med_mf <- '
  negemo ~ c(a1, a2)*HP
  si3    ~ c(b1, b2)*negemo + c(cp1, cp2)*HP
  ind_1   := a1*b1
  ind_2   := a2*b2
  total_1 := cp1 + a1*b1
  total_2 := cp2 + a2*b2
'
d$negemo <- rowMeans(d[, c("neg1", "neg2", "neg3")])
d$HP     <- rowMeans(d[, c("hp1", "hp2", "hp3")])
d$si3    <- rowMeans(d[, c("si1", "si2", "si3")])
fit_free <- sem(m_med_mf, data = d, group = "grp")
cat("\n=== 多组中介路径系数（显变量主口径；lavaan 按组名排序：ctrl=对照组 在前，exp=实验组 在后） ===\n")
pe <- parameterEstimates(fit_free, standardized = FALSE)
print(pe[pe$op %in% c("~", ":="), c("lhs", "op", "rhs", "group", "est", "se", "z", "pvalue")],
      row.names = FALSE)
write.csv(pe[pe$op %in% c("~", ":="), c("lhs", "op", "rhs", "group", "est", "se", "z", "pvalue")],
          "结果_多组SEM_路径系数.csv", row.names = FALSE)

# ---------- 4. 路径等值检验（逐条约束 + χ² 差异，显变量） ----------
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
eq_rows <- list()
for (nm in names(eq_tests)) {
  fit_eq <- sem(eq_tests[[nm]], data = d, group = "grp")
  lr <- anova(fit_eq, fit_free)
  eq_rows[[length(eq_rows) + 1]] <- data.frame(
    约束 = nm, chisq_diff = round(lr[2, "Chisq diff"], 2), df_diff = lr[2, "Df diff"],
    p = round(lr[2, "Pr(>Chisq)"], 4),
    结论 = ifelse(lr[2, "Pr(>Chisq)"] < .05, "两组有显著差异", "两组无显著差异"))
}
eq_tab <- do.call(rbind, eq_rows)
cat("\n=== 路径等值检验（显变量；H0: 两组路径相等） ===\n")
print(eq_tab, row.names = FALSE)
write.csv(eq_tab, "结果_多组SEM_等值检验.csv", row.names = FALSE)

# ---------- 5. 附报：潜变量多组中介（标量不变性约束下的标准化系数） ----------
m_med_lv <- paste(m_meas, '
  NEG ~ c(a1, a2)*HP
  SI  ~ c(b1, b2)*NEG + c(cp1, cp2)*HP
  ind_1 := a1*b1
  ind_2 := a2*b2
')
fit_lv <- sem(m_med_lv, data = d, group = "grp",
              group.equal = c("loadings", "intercepts"))
pe_lv <- parameterEstimates(fit_lv, standardized = TRUE)
cat("\n=== 附报：潜变量多组中介（标准化系数 std.all；组1=对照组，组2=实验组） ===\n")
print(pe_lv[pe_lv$op %in% c("~", ":="),
            c("lhs", "op", "rhs", "group", "est", "std.all", "se", "pvalue")],
      row.names = FALSE)
write.csv(pe_lv[pe_lv$op %in% c("~", ":="),
                c("lhs", "op", "rhs", "group", "est", "std.all", "se", "pvalue")],
          "结果_多组SEM_潜变量附报.csv", row.names = FALSE)

cat("\n已导出：结果_多组SEM_测量不变性.csv / 结果_多组SEM_路径系数.csv / 结果_多组SEM_等值检验.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
