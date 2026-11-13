# 补充计算_情绪分行为.R
# =====================
# 分化检验（理论驱动）：三种道德情绪各自预测哪种传播行为。
# 理论预期：愤怒→攻击型（公开回复/转发）；厌恶→回避型（不做）；蔑视→低成本围观（点赞）。
# 数据：品牌层长格式（373 人 × 3 品牌 = 1119 行），行为 1-5 序次。
# 模型：
#   ① clmm（序次）：act ~ 情绪_b + (1|id)，各情绪单独 + 三情绪联合；
#   ② glmer（二分类，随机截距）：攻击型（公开回复/转发=1）~ 情绪_b；
#       不做（=1）~ 情绪_b；点赞（=1）~ 情绪_b。
# 输出：结果_情绪分行为.csv

library(readxl)
library(ordinal)
library(lme4)
library(lmerTest)

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
  V118="记忆1", V119="记忆2", V120="记忆3"
)
cmap_ctrl <- c(
  V1="作答ID", V18="质检结果",
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
  V115="记忆1", V116="记忆2", V117="记忆3"
)
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
to_num <- function(x) as.numeric(c(lk, lkw)[as.character(x)])
act_map <- c("公开回复，发表自己的看法"=5, "转发这条微博（可附加公开评论）"=4,
             "点赞"=3, "发送私信（其他用户不可见）"=2, "不做任何操作"=1)

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
  id <- rep(dat$作答ID, each = 3)
  mk <- function(q) {
    as.vector(rbind(rowMeans(dat[paste0("Q2_", q)]),
                    rowMeans(dat[paste0("Q6_", q)]),
                    rowMeans(dat[paste0("Q13_", q)])))
  }
  hp_b <- as.vector(rbind(rowMeans(dat[paste0("Q1_", 1:3)]),
                          rowMeans(dat[paste0("Q5_", 1:3)]),
                          rowMeans(dat[paste0("Q12_", 1:3)])))
  act <- as.vector(rbind(unname(act_map[dat$Q3]),
                         unname(act_map[dat$Q7]),
                         unname(act_map[dat$Q14])))
  data.frame(id = factor(id), grp = grp,
             act = factor(act, levels = 1:5, ordered = TRUE),
             attack = as.numeric(act >= 4),   # 公开回复/转发
             like  = as.numeric(act == 3),
             none  = as.numeric(act == 1),
             hp_b = hp_b,
             anger = mk(1:3), disgust = mk(4:6), contempt = mk(7:9))
}
d_e <- build("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp, 1)
d_c <- build("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl, 0)
stopifnot(nrow(d_e) == 567, nrow(d_c) == 552)
d_all <- rbind(d_e, d_c)

rows <- list()
for (lab in c("实验组", "对照组", "全部样本")) {
  dd <- switch(lab, 实验组 = d_e, 对照组 = d_c, 全部样本 = d_all)
  cat("\n==========", lab, "（品牌行 N =", nrow(dd), "） ==========\n")
  # ① 序次 clmm（各情绪单独）
  for (emo in c("anger", "disgust", "contempt")) {
    f <- clm(act ~ dd[[emo]], data = dd)
    co <- summary(f)$coefficients
    z <- co[nrow(co), "z value"]; p <- co[nrow(co), "Pr(>|z|)"]
    cat(sprintf("clmm act ~ %-8s: b = %.3f, OR = %.3f, p = %.4f\n",
                emo, co[nrow(co), 1], exp(co[nrow(co), 1]), p))
    rows[[length(rows) + 1]] <- data.frame(样本 = lab, 模型 = "序次行为", 情绪 = emo,
        b = round(co[nrow(co), 1], 3), OR = round(exp(co[nrow(co), 1]), 3), p = round(p, 4))
  }
  # ② 二分类 glmer（攻击型 / 点赞 / 不做）
  for (out in c("attack", "like", "none")) {
    for (emo in c("anger", "disgust", "contempt")) {
      f <- glmer(as.formula(paste(out, "~", emo, "+ (1|id)")),
                 data = dd, family = binomial)
      co <- summary(f)$coefficients
      b <- co[emo, "Estimate"]; p <- co[emo, "Pr(>|z|)"]
      cat(sprintf("%-6s ~ %-8s: b = %.3f, OR = %.3f, p = %.4f\n",
                  out, emo, b, exp(b), p))
      rows[[length(rows) + 1]] <- data.frame(样本 = lab, 模型 = out, 情绪 = emo,
          b = round(b, 3), OR = round(exp(b), 3), p = round(p, 4))
    }
  }
}
out <- do.call(rbind, rows)
write.csv(out, "结果_情绪分行为.csv", row.names = FALSE)
cat("\n已导出：结果_情绪分行为.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
