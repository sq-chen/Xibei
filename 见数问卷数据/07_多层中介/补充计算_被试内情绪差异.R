# 补充计算_被试内情绪差异.R
# =====================
# 被试内（品牌内）三道德情绪间接效应的两两差异检验（簇 bootstrap 2000）。
# 被试内层面精度最高（每人自对照），是分化检验最后的精度空间。
library(readxl)
library(lme4)
set.seed(20260903)
N_BOOT <- 1000

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

build_long <- function(path, cmap, grp) {
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
  id <- rep(dat$作答ID, each = 3)
  mk <- function(q) {
    as.vector(rbind(rowMeans(dat[paste0("Q2_", q)]),
                    rowMeans(dat[paste0("Q6_", q)]),
                    rowMeans(dat[paste0("Q13_", q)])))
  }
  hp_b <- as.vector(rbind(rowMeans(dat[paste0("Q1_", 1:3)]),
                          rowMeans(dat[paste0("Q5_", 1:3)]),
                          rowMeans(dat[paste0("Q12_", 1:3)])))
  si_b <- as.vector(rbind(rowMeans(dat[paste0("Q4_", 1:3)]),
                          rowMeans(dat[paste0("Q8_", 1:3)]),
                          rowMeans(dat[paste0("Q15_", 1:3)])))
  data.frame(id = factor(id), brand = rep(1:3, each = nrow(dat)), grp = grp,
             HP = hp_b, anger = mk(1:3), disgust = mk(4:6), contempt = mk(7:9),
             si3 = si_b)
}
long_e <- build_long("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp, 1)
long_c <- build_long("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl, 0)

add_cwc <- function(dl) {
  dl$X_b <- ave(dl$HP, dl$id, FUN = mean)
  dl$X_w <- dl$HP - dl$X_b
  dl
}
# 一次两阶段拟合，输出三情绪被试内间接效应（用于差异）
ind3 <- function(dl) {
  dl <- add_cwc(dl)
  out <- c()
  for (emo in c("anger", "disgust", "contempt")) {
    dl$E_w <- dl[[emo]] - ave(dl[[emo]], dl$id, FUN = mean)
    dl$E_b <- ave(dl[[emo]], dl$id, FUN = mean)
    m1 <- lmer(as.formula(paste(emo, "~ X_w + X_b + (1|id)")), data = dl)
    m2 <- lmer(si3 ~ E_w + E_b + X_w + X_b + (1|id), data = dl)
    out[emo] <- unname(fixef(m1)["X_w"]) * unname(fixef(m2)["E_w"])
  }
  c(anger = out["anger"], disgust = out["disgust"], contempt = out["contempt"],
    a_minus_d = out["anger"] - out["disgust"],
    a_minus_c = out["anger"] - out["contempt"],
    d_minus_c = out["disgust"] - out["contempt"])
}

for (lab in c("实验组", "对照组", "全部样本")) {
  dl <- switch(lab, 实验组 = long_e, 对照组 = long_c, 全部样本 = rbind(long_e, long_c))
  dl <- add_cwc(dl)
  ids <- unique(dl$id)
  pt <- ind3(dl)
  D <- matrix(NA_real_, nrow = 6, ncol = N_BOOT,
              dimnames = list(c("anger", "disgust", "contempt", "a_minus_d", "a_minus_c", "d_minus_c"), NULL))
  for (b in seq_len(N_BOOT)) {
    s <- sample(ids, replace = TRUE)
    idx <- unlist(lapply(s, function(i) which(dl$id == i)))
    v <- tryCatch(ind3(dl[idx, ]), error = function(e) rep(NA_real_, 6))
    if (length(v) == 6) D[, b] <- v
  }
  cat("\n==========", lab, "==========\n")
  for (k in c("anger", "disgust", "contempt", "a_minus_d", "a_minus_c", "d_minus_c")) {
    ci <- quantile(D[k, ], c(.025, .975), na.rm = TRUE)
    cat(sprintf("%s: ind = %.3f [%.3f, %.3f]\n", k, pt[k], ci[1], ci[2]))
  }
  gc()
}
cat("\n完成时间：", format(Sys.time()), "\n")
