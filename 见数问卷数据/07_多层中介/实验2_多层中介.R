# 实验2_多层中介.R
# =====================
# 2-2 多层中介（brand-level 2-1-1）：利用每位被试 × 3 品牌的嵌套结构，
# 把"不一致感知→情绪→传播意愿"分解为 组内（品牌间）与 组间（被试间）两条中介路径。
#   - 组内效应（X_w → M_w → Y）：同一个人内，HP 更高的品牌是否引发更强情绪与传播意愿——
#     控制全部稳定个体差异，因果推断力强于被试间分析；
#   - 组间效应（X_b → M_b → Y）：被试水平复现现有结论；
#   - ICC：品牌方差占比，量化"压均值损失的信息"。
# 实现：lme4 两阶段 + 按被试簇 bootstrap（B=2000）估计组内/组间间接效应百分位 CI。
# 样本：实验组 N=189、对照组 N=184、全部样本 N=373 分别跑；另附三道德情绪各自的组内中介。
# 输出：结果_多层中介_汇总.csv / 结果_多层中介_三情绪组内.csv

library(readxl)
library(lme4)
library(lmerTest)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "2000"))

# ---------- 1. 读取、筛查、构建品牌长格式 ----------
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

build_long <- function(dat, grp) {
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
  id <- rep(dat$作答ID, each = 3)
  # 注意：品牌值必须按人交错拼接（每人 3 个品牌相邻），与 id 的 each=3 顺序一致
  hp_b <- as.vector(rbind(rowMeans(dat[paste0("Q1_", 1:3)]),
                          rowMeans(dat[paste0("Q5_", 1:3)]),
                          rowMeans(dat[paste0("Q12_", 1:3)])))
  mk <- function(q) {
    as.vector(rbind(rowMeans(dat[paste0("Q2_", q)]),
                    rowMeans(dat[paste0("Q6_", q)]),
                    rowMeans(dat[paste0("Q13_", q)])))
  }
  si_b <- as.vector(rbind(rowMeans(dat[paste0("Q4_", 1:3)]),
                          rowMeans(dat[paste0("Q8_", 1:3)]),
                          rowMeans(dat[paste0("Q15_", 1:3)])))
  long <- data.frame(
    id = factor(id),
    brand = rep(1:3, each = nrow(dat)),
    grp = grp,
    HP = hp_b,
    anger = mk(1:3), disgust = mk(4:6), contempt = mk(7:9),
    negemo = mk(1:9),
    si3 = si_b
  )
  long
}
long_e <- build_long(dat_e <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
long_c <- build_long(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)
cat("实验组长格式:", nrow(long_e), "行 /", length(unique(long_e$id)), "人\n")
cat("对照组长格式:", nrow(long_c), "行 /", length(unique(long_c$id)), "人\n")
stopifnot(length(unique(long_e$id)) == 189, length(unique(long_c$id)) == 184)

# ---------- 2. ICC ----------
icc_of <- function(dlong, v) {
  m0 <- lmer(as.formula(paste(v, "~ 1 + (1|id)")), data = dlong)
  vc <- as.data.frame(VarCorr(m0))
  vc$vcov[1] / sum(vc$vcov)
}
cat("\n=== ICC（品牌方差占比） ===\n")
for (lab in c("实验组", "对照组", "全部")) {
  dl <- switch(lab, 实验组 = long_e, 对照组 = long_c,
               全部 = rbind(long_e, long_c))
  cat(lab, ": HP =", round(icc_of(dl, "HP"), 3),
      "| negemo =", round(icc_of(dl, "negemo"), 3),
      "| si3 =", round(icc_of(dl, "si3"), 3), "\n")
}

# ---------- 3. 两阶段 2-1-1 中介（lme4）与簇 bootstrap ----------
add_cwc <- function(dlong) {
  # 组间 = 个人均值；组内 = 品牌对个人均值的偏离（person-mean centering）
  dlong$X_b <- ave(dlong$HP, dlong$id, FUN = mean)
  dlong$X_w <- dlong$HP - dlong$X_b
  dlong$M_b <- ave(dlong$negemo, dlong$id, FUN = mean)
  dlong$M_w <- dlong$negemo - dlong$M_b
  dlong
}
two_stage <- function(dlong) {
  m1 <- lmer(negemo ~ X_w + X_b + (1|id), data = dlong)
  m2 <- lmer(si3 ~ M_w + M_b + X_w + X_b + (1|id), data = dlong)
  a_w <- unname(fixef(m1)["X_w"]); a_b <- unname(fixef(m1)["X_b"])
  b_w <- unname(fixef(m2)["M_w"]); b_b <- unname(fixef(m2)["M_b"])
  cp_w <- unname(fixef(m2)["X_w"]); cp_b <- unname(fixef(m2)["X_b"])
  c(ind_w = a_w * b_w, ind_b = a_b * b_b,
    a_w = a_w, a_b = a_b, b_w = b_w, b_b = b_b, cp_w = cp_w, cp_b = cp_b)
}

run_mlm_med <- function(dlong, label, boot = TRUE) {
  dlong <- add_cwc(dlong)
  pt <- two_stage(dlong)
  cat("\n==========", label, "（N =", length(unique(dlong$id)), "人） ==========\n")
  # 两阶段模型的系数显著性（lmerTest）
  m1 <- lmer(negemo ~ X_w + X_b + (1|id), data = dlong)
  m2 <- lmer(si3 ~ M_w + M_b + X_w + X_b + (1|id), data = dlong)
  for (m in list(m1, m2)) {
    sm <- summary(m)$coefficients
    print(round(sm[rownames(sm) %in% c("X_w", "X_b", "M_w", "M_b"), c(1, 2, 4, 5)], 3))
  }
  cat(sprintf("点估计: 组内 ind = %.3f | 组间 ind = %.3f\n", pt["ind_w"], pt["ind_b"]))
  if (boot) {
    ids <- unique(dlong$id)
    draws <- replicate(N_BOOT, {
      s <- sample(ids, replace = TRUE)
      idx <- unlist(lapply(s, function(i) which(dlong$id == i)))
      ts <- tryCatch(two_stage(dlong[idx, ]), error = function(e) rep(NA_real_, 8))
      ts[c("ind_w", "ind_b")]
    })
    ci_w <- quantile(draws["ind_w", ], c(.025, .975), na.rm = TRUE)
    ci_b <- quantile(draws["ind_b", ], c(.025, .975), na.rm = TRUE)
    cat(sprintf("bootstrap %d: 组内 ind %.3f [%.3f, %.3f] | 组间 ind %.3f [%.3f, %.3f]\n",
                N_BOOT, pt["ind_w"], ci_w[1], ci_w[2], pt["ind_b"], ci_b[1], ci_b[2]))
    return(data.frame(样本 = label, 路径 = "组内", a = pt["a_w"], b = pt["b_w"],
                      ind = pt["ind_w"], ci_lower = unname(ci_w[1]), ci_upper = unname(ci_w[2])))
  }
  NULL
}

rows <- list()
rows[[1]] <- run_mlm_med(long_e, "实验组")
rows[[2]] <- run_mlm_med(long_c, "对照组")
rows[[3]] <- run_mlm_med(rbind(long_e, long_c), "全部样本")

# 组间路径补充行（bootstrap 只对间接效应做，组间间接也用同样抽样补充）
add_between_row <- function(dlong, label) {
  dlong <- add_cwc(dlong)
  pt <- two_stage(dlong)
  ids <- unique(dlong$id)
  draws <- replicate(N_BOOT, {
    s <- sample(ids, replace = TRUE)
    idx <- unlist(lapply(s, function(i) which(dlong$id == i)))
    ts <- tryCatch(two_stage(dlong[idx, ]), error = function(e) rep(NA_real_, 8))
    ts[c("ind_w", "ind_b")]
  })
  ci_b <- quantile(draws["ind_b", ], c(.025, .975), na.rm = TRUE)
  data.frame(样本 = label, 路径 = "组间", a = pt["a_b"], b = pt["b_b"],
             ind = pt["ind_b"], ci_lower = unname(ci_b[1]), ci_upper = unname(ci_b[2]))
}
rows[[4]] <- add_between_row(long_e, "实验组")
rows[[5]] <- add_between_row(long_c, "对照组")
rows[[6]] <- add_between_row(rbind(long_e, long_c), "全部样本")
mlm_tab <- do.call(rbind, rows)
write.csv(mlm_tab, "结果_多层中介_汇总.csv", row.names = FALSE)
print(mlm_tab, row.names = FALSE)

# ---------- 4. 附报：三道德情绪各自的组内中介（点估计 + lmerTest p，不做 bootstrap） ----------
cat("\n=== 附报：三道德情绪组内中介（X_w→情绪_w→si3，lmer 两阶段点估计） ===\n")
emo_rows <- list()
for (lab in c("实验组", "对照组", "全部")) {
  dl <- switch(lab, 实验组 = long_e, 对照组 = long_c, 全部 = rbind(long_e, long_c))
  dl <- add_cwc(dl)
  for (emo in c("anger", "disgust", "contempt")) {
    dl$E_w <- dl[[emo]] - ave(dl[[emo]], dl$id, FUN = mean)
    dl$E_b <- ave(dl[[emo]], dl$id, FUN = mean)
    m1 <- lmer(as.formula(paste(emo, "~ X_w + X_b + (1|id)")), data = dl)
    m2 <- lmer(si3 ~ E_w + E_b + X_w + X_b + (1|id), data = dl)
    a_w <- unname(fixef(m1)["X_w"]); b_w <- unname(fixef(m2)["E_w"])
    p_a <- summary(m1)$coefficients["X_w", "Pr(>|t|)"]
    p_b <- summary(m2)$coefficients["E_w", "Pr(>|t|)"]
    emo_rows[[length(emo_rows) + 1]] <- data.frame(
      样本 = lab, 情绪 = emo, a_w = round(a_w, 3), a_p = round(p_a, 4),
      b_w = round(b_w, 3), b_p = round(p_b, 4), ind_w = round(a_w * b_w, 3))
  }
}
emo_tab <- do.call(rbind, emo_rows)
print(emo_tab, row.names = FALSE)
write.csv(emo_tab, "结果_多层中介_三情绪组内.csv", row.names = FALSE)

cat("\n已导出：结果_多层中介_汇总.csv / 结果_多层中介_三情绪组内.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
