# 补充计算_品牌调节.R
# =====================
# 品牌作为调节变量（实验组内，品牌嵌套被试）：
#   m1: negemo ~ HP × 品牌 + (1|id)   —— a 段是否随品牌变化
#   m2: si3 ~ negemo × 品牌 + HP + (1|id) —— b 段是否随品牌变化
# 条件间接效应：各品牌 a×b；差异指数：三品牌两两差异。
# 簇 bootstrap 2000（按被试重抽），输出 CIs。
library(readxl)
library(lme4)
library(lmerTest)
set.seed(20260903)
N_BOOT <- 2000

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
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
to_num <- function(x) as.numeric(c(lk, lkw)[as.character(x)])

dat <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
scale_items <- c(
  paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
  paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
  paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3)
)
dat[scale_items] <- lapply(dat[scale_items], to_num)
rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)
chk <- dat$Q2_16 == "比较不同意" & dat$Q6_16 == "比较同意" & dat$Q13_16 == "完全不同意"
mem <- dat$记忆1 == "后厨大量使用冷冻食材" &
       dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
       dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
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
neg_b <- rowMeans(cbind(mk(1:3), mk(4:6), mk(7:9)))
d <- data.frame(id = factor(id),
                brand = factor(rep(c("西贝", "自如", "始祖鸟"), each = nrow(dat))),
                HP = hp_b, negemo = neg_b, si3 = si_b)
stopifnot(nrow(d) == 567)

# ---------- 点估计与交互检验 ----------
m1 <- lmer(negemo ~ HP * brand + (1|id), data = d)
m2 <- lmer(si3 ~ negemo * brand + HP + (1|id), data = d)
cat("=== 交互项检验（lmerTest，Type III） ===\n")
print(anova(m1, type = 3)[c("HP:brand"), ])
print(anova(m2, type = 3)[c("negemo:brand"), ])

# ---------- 条件间接效应（点估计） ----------
fit_two <- function(dd) {
  mm1 <- lmer(negemo ~ HP * brand + (1|id), data = dd)
  mm2 <- lmer(si3 ~ negemo * brand + HP + (1|id), data = dd)
  f1 <- fixef(mm1); f2 <- fixef(mm2)
  # 位置索引（避免中文交互项名匹配问题）：顺序固定为 (Intercept), HP, brand2, brand3, HP:brand2, HP:brand3
  a <- c(西贝 = unname(f1[2]),
         自如 = unname(f1[2] + f1[5]),
         始祖鸟 = unname(f1[2] + f1[6]))
  b <- c(西贝 = unname(f2[2]),
         自如 = unname(f2[2] + f2[5]),
         始祖鸟 = unname(f2[2] + f2[6]))
  ind <- a * b
  c(ind, d_自如_西贝 = ind["自如"] - ind["西贝"],
    d_始祖鸟_西贝 = ind["始祖鸟"] - ind["西贝"],
    d_始祖鸟_自如 = ind["始祖鸟"] - ind["自如"])
}
pt <- fit_two(d)
cat("\n=== 条件间接效应（点估计） ===\n")
print(round(pt, 3))

# ---------- 簇 bootstrap ----------
cat("\nbootstrap", N_BOOT, "运行中 ...\n")
t0 <- Sys.time()
ids <- unique(d$id)
D <- matrix(NA_real_, nrow = 6, ncol = N_BOOT,
            dimnames = list(names(pt), NULL))
for (b in seq_len(N_BOOT)) {
  s <- sample(ids, replace = TRUE)
  idx <- unlist(lapply(s, function(i) which(d$id == i)))
  v <- tryCatch(fit_two(d[idx, ]), error = function(e) rep(NA_real_, 6))
  if (length(v) == 6) D[, b] <- v
}
cat("bootstrap 完成，用时", round(difftime(Sys.time(), t0, units = "mins"), 1), "分钟\n")
cat("\n=== 条件间接效应与差异（bootstrap 95% CI） ===\n")
for (k in rownames(D)) {
  ci <- quantile(D[k, ], c(.025, .975), na.rm = TRUE)
  cat(sprintf("%-14s: %.3f [%.3f, %.3f]\n", k, pt[k], ci[1], ci[2]))
}
out <- data.frame(量 = rownames(D), est = round(pt, 3),
                  ci_lower = round(apply(D, 1, function(x) quantile(x, .025, na.rm = TRUE)), 3),
                  ci_upper = round(apply(D, 1, function(x) quantile(x, .975, na.rm = TRUE)), 3))
write.csv(out, "结果_品牌调节.csv", row.names = FALSE)
cat("\n已导出：结果_品牌调节.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
