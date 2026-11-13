# 实验2_多层中介_续跑.R
# =====================
# 原脚本（实验2_多层中介.R）在"全部样本"bootstrap 前中断：
#   实验组/对照组 的簇 bootstrap 已完成（结果见 10_运行日志/日志_多层中介.Rout 06:03 版），
#   全部样本 的 bootstrap、三情绪组内附报、CSV 写出 未执行。
# 本脚本续跑：点估计全部重算（秒级）；实验组/对照组的 bootstrap CI 沿用已完成值
#   （引自日志：实验组 组内 .225 [.125,.344] 组间 .256 [.074,.501]；
#     对照组 组内 -.123 [-.261,.045] 组间 .226 [.066,.402]）；
#   全部样本 重新 bootstrap（单次抽样同时取组内/组间，比原脚本省一半时间）。
# 输出覆盖：结果_多层中介_汇总.csv / 结果_多层中介_三情绪组内.csv

library(readxl)
library(lme4)
library(lmerTest)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "2000"))

# ---------- 1. 读取、筛查、构建品牌长格式（与原脚本一致） ----------
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
  data.frame(
    id = factor(id),
    brand = rep(1:3, each = nrow(dat)),
    grp = grp,
    HP = hp_b,
    anger = mk(1:3), disgust = mk(4:6), contempt = mk(7:9),
    negemo = mk(1:9),
    si3 = si_b
  )
}
long_e <- build_long(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
long_c <- build_long(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)
stopifnot(length(unique(long_e$id)) == 189, length(unique(long_c$id)) == 184)
long_all <- rbind(long_e, long_c)

# ---------- 2. 两阶段 2-1-1 中介 ----------
add_cwc <- function(dlong) {
  dlong$X_b <- ave(dlong$HP, dlong$id, FUN = mean)
  dlong$X_w <- dlong$HP - dlong$X_b
  dlong$M_b <- ave(dlong$negemo, dlong$id, FUN = mean)
  dlong$M_w <- dlong$negemo - dlong$M_b
  dlong
}
two_stage <- function(dlong) {
  m1 <- lmer(negemo ~ X_w + X_b + (1|id), data = dlong)
  m2 <- lmer(si3 ~ M_w + M_b + X_w + X_b + (1|id), data = dlong)
  c(ind_w = unname(fixef(m1)["X_w"]) * unname(fixef(m2)["M_w"]),
    ind_b = unname(fixef(m1)["X_b"]) * unname(fixef(m2)["M_b"]))
}
print_coef <- function(dlong, label) {
  dlong <- add_cwc(dlong)
  m1 <- lmer(negemo ~ X_w + X_b + (1|id), data = dlong)
  m2 <- lmer(si3 ~ M_w + M_b + X_w + X_b + (1|id), data = dlong)
  cat("\n==========", label, "（N =", length(unique(dlong$id)), "人） ==========\n")
  for (nm in c("m1 (negemo ~ X_w + X_b)", "m2 (si3 ~ M_w + M_b + X_w + X_b)")) {
    m <- if (startsWith(nm, "m1")) m1 else m2
    sm <- summary(m)$coefficients
    keep_rows <- rownames(sm) %in% c("X_w", "X_b", "M_w", "M_b")
    print(round(sm[keep_rows, c(1, 2, 4, 5)], 4))
  }
}
clust_boot <- function(dlong) {
  dlong <- add_cwc(dlong)
  ids <- unique(dlong$id)
  draws <- replicate(N_BOOT, {
    s <- sample(ids, replace = TRUE)
    idx <- unlist(lapply(s, function(i) which(dlong$id == i)))
    ts <- tryCatch(two_stage(dlong[idx, ]), error = function(e) c(ind_w = NA, ind_b = NA))
    ts[c("ind_w", "ind_b")]
  })
  data.frame(ind_w_lo = unname(quantile(draws["ind_w", ], .025, na.rm = TRUE)),
             ind_w_hi = unname(quantile(draws["ind_w", ], .975, na.rm = TRUE)),
             ind_b_lo = unname(quantile(draws["ind_b", ], .025, na.rm = TRUE)),
             ind_b_hi = unname(quantile(draws["ind_b", ], .975, na.rm = TRUE)))
}

# ---------- 3. 实验组/对照组：点估计重算 + 沿用已完成 bootstrap CI ----------
print_coef(long_e, "实验组"); print_coef(long_c, "对照组")
pt_e <- two_stage(add_cwc(long_e)); pt_c <- two_stage(add_cwc(long_c))
cat(sprintf("实验组点估计: 组内 %.3f | 组间 %.3f\n", pt_e["ind_w"], pt_e["ind_b"]))
cat(sprintf("对照组点估计: 组内 %.3f | 组间 %.3f\n", pt_c["ind_w"], pt_c["ind_b"]))
# 已完成 bootstrap（引自 日志_多层中介.Rout 06:03 版，同种子 20260903）：
ci_e <- c(ind_w_lo = .125, ind_w_hi = .344, ind_b_lo = .074, ind_b_hi = .501)
ci_c <- c(ind_w_lo = -.261, ind_w_hi = .045, ind_b_lo = .066, ind_b_hi = .402)

# ---------- 4. 全部样本：完整 bootstrap ----------
print_coef(long_all, "全部样本")
pt_a <- two_stage(add_cwc(long_all))
cat(sprintf("全部样本点估计: 组内 %.3f | 组间 %.3f\n", pt_a["ind_w"], pt_a["ind_b"]))
cat("全部样本 bootstrap 运行中（B =", N_BOOT, "）...\n")
t0 <- Sys.time()
ci_a <- clust_boot(long_all)
cat("bootstrap 完成，用时", round(difftime(Sys.time(), t0, units = "mins"), 1), "分钟\n")

mlm_tab <- rbind(
  data.frame(样本 = "实验组", 路径 = "组内", a = NA, b = NA, ind = pt_e["ind_w"],
             ci_lower = ci_e["ind_w_lo"], ci_upper = ci_e["ind_w_hi"]),
  data.frame(样本 = "对照组", 路径 = "组内", a = NA, b = NA, ind = pt_c["ind_w"],
             ci_lower = ci_c["ind_w_lo"], ci_upper = ci_c["ind_w_hi"]),
  data.frame(样本 = "全部样本", 路径 = "组内", a = NA, b = NA, ind = pt_a["ind_w"],
             ci_lower = ci_a["ind_w_lo"], ci_upper = ci_a["ind_w_hi"]),
  data.frame(样本 = "实验组", 路径 = "组间", a = NA, b = NA, ind = pt_e["ind_b"],
             ci_lower = ci_e["ind_b_lo"], ci_upper = ci_e["ind_b_hi"]),
  data.frame(样本 = "对照组", 路径 = "组间", a = NA, b = NA, ind = pt_c["ind_b"],
             ci_lower = ci_c["ind_b_lo"], ci_upper = ci_c["ind_b_hi"]),
  data.frame(样本 = "全部样本", 路径 = "组间", a = NA, b = NA, ind = pt_a["ind_b"],
             ci_lower = ci_a["ind_b_lo"], ci_upper = ci_a["ind_b_hi"])
)

# a/b 路径系数（lmer 固定效应）
path_row <- function(dlong) {
  dlong <- add_cwc(dlong)
  m1 <- lmer(negemo ~ X_w + X_b + (1|id), data = dlong)
  m2 <- lmer(si3 ~ M_w + M_b + X_w + X_b + (1|id), data = dlong)
  sm1 <- summary(m1)$coefficients; sm2 <- summary(m2)$coefficients
  list(a_w = unname(sm1["X_w", 1]), a_b = unname(sm1["X_b", 1]),
       b_w = unname(sm2["M_w", 1]), b_b = unname(sm2["M_b", 1]),
       cp_w = unname(sm2["X_w", 1]), cp_b = unname(sm2["X_b", 1]),
       a_w_p = unname(sm1["X_w", 5]), a_b_p = unname(sm1["X_b", 5]),
       b_w_p = unname(sm2["M_w", 5]), b_b_p = unname(sm2["M_b", 5]),
       cp_w_p = unname(sm2["X_w", 5]), cp_b_p = unname(sm2["X_b", 5]))
}
pe <- path_row(long_e); pc <- path_row(long_c); pa <- path_row(long_all)
fill <- function(rows, i, p) {
  rows$a[i] <- if (rows$路径[i] == "组内") p$a_w else p$a_b
  rows$b[i] <- if (rows$路径[i] == "组内") p$b_w else p$b_b
  rows
}
mlm_tab <- fill(mlm_tab, 1, pe); mlm_tab <- fill(mlm_tab, 2, pc); mlm_tab <- fill(mlm_tab, 3, pa)
mlm_tab <- fill(mlm_tab, 4, pe); mlm_tab <- fill(mlm_tab, 5, pc); mlm_tab <- fill(mlm_tab, 6, pa)
write.csv(mlm_tab, "结果_多层中介_汇总.csv", row.names = FALSE)
print(mlm_tab, row.names = FALSE)
cat("\n路径 p 值（组内/组间 的 a、b、c'）:\n")
for (lab in c("实验组", "对照组", "全部样本")) {
  p <- switch(lab, 实验组 = pe, 对照组 = pc, 全部样本 = pa)
  cat(sprintf("%s: a_w %.3f (p=%.4f) | a_b %.3f (p=%.4f) | b_w %.3f (p=%.4f) | b_b %.3f (p=%.4f) | cp_w %.3f (p=%.4f) | cp_b %.3f (p=%.4f)\n",
              lab, p$a_w, p$a_w_p, p$a_b, p$a_b_p, p$b_w, p$b_w_p, p$b_b, p$b_b_p, p$cp_w, p$cp_w_p, p$cp_b, p$cp_b_p))
}

# ---------- 5. 附报：三道德情绪各自的被试内中介（点估计 + p，不做 bootstrap） ----------
cat("\n=== 附报：三道德情绪被试内中介（X_w→情绪_w→si3，lmer 两阶段点估计） ===\n")
emo_rows <- list()
for (lab in c("实验组", "对照组", "全部样本")) {
  dl <- switch(lab, 实验组 = long_e, 对照组 = long_c, 全部样本 = long_all)
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
