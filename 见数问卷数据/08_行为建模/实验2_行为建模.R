# 实验2_行为建模.R
# =====================
# 2-3 行为选择完整建模：把 5 级行为单选题（公开回复5 > 转发4 > 点赞3 > 私信2 > 不做1）当真正的因变量。
#   ① 品牌层序次 logistic（clmm）：act ~ 品牌 HP_b + 品牌 negemo_b + (1|id)，实验组/对照组/合并分别跑；
#   ② 被试层序次 logistic（polr）：round(行为强度均值) ~ HP + negemo（+组别）；
#   ③ 意愿-行为落差：gap = scale(si3) − scale(行为强度)，单样本 t（H0: 落差=0）+ 落差回归
#      （什么预测"说而不做"：情绪、CSR 关注度、转发频率、互动倾向、性别、年龄、组别）。
# 输出：结果_行为建模_序次logistic.csv / 结果_行为建模_落差分析.csv

library(readxl)
library(MASS)
library(ordinal)

# ---------- 1. 读取与计分（与既有脚本同口径） ----------
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
  V98="性别", V99="年龄", V102="社媒时长",
  V112="互动倾向", V113="转发频率",
  V114="Q23_1", V115="Q23_2", V116="Q23_3",
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
  V95="性别", V96="年龄", V99="社媒时长",
  V109="互动倾向", V110="转发频率",
  V111="Q23_1", V112="Q23_2", V113="Q23_3",
  V115="记忆1", V116="记忆2", V117="记忆3"
)
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
         "比较符合"=5, "符合"=6, "完全符合"=7)
to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])
act_map <- c("公开回复，发表自己的看法"=5, "转发这条微博（可附加公开评论）"=4,
             "点赞"=3, "发送私信（其他用户不可见）"=2, "不做任何操作"=1)

prep <- function(dat, grp) {
  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3),
    paste0("Q23_", 1:3)
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
  beh <- data.frame(act_map[dat$Q3], act_map[dat$Q7], act_map[dat$Q14])
  data.frame(
    id = dat$作答ID, grp = grp,
    HP = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))]),
    anger = CAD(1:3), disgust = CAD(4:6), contempt = CAD(7:9),
    fear = CAD(10:12), sadness = CAD(13:15), negemo = CAD(1:9),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))]),
    act_ord_mean = rowMeans(beh),
    act_b1 = unname(act_map[dat$Q3]), act_b2 = unname(act_map[dat$Q7]),
    act_b3 = unname(act_map[dat$Q14]),
    female = as.numeric(dat$性别 == "女"), age = as.numeric(dat$年龄),
    sm_time = as.numeric(c("少于30分钟"=1, "30分钟–1小时"=2, "1–2小时"=3,
                           "2–4小时"=4, "4–6小时"=5, "超过6小时"=6)[dat$社媒时长]),
    sm_inter = as.numeric(c("主要浏览，较少发帖和互动"=1, "偶尔点赞、发帖或评论"=2,
                            "经常主动发帖、转发、表达观点"=3)[dat$互动倾向]),
    freq_fwd = as.numeric(dat$转发频率),
    CSR = rowMeans(dat[c("Q23_1", "Q23_2", "Q23_3")])
  )
}
d_e <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
d_c <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)
d <- rbind(d_e, d_c)
cat("实验组 N =", nrow(d_e), "| 对照组 N =", nrow(d_c), "| 全部 =", nrow(d), "\n")
stopifnot(nrow(d_e) == 189, nrow(d_c) == 184)

# ---------- 2. 品牌层序次 logistic（clmm，行为 1-5 ~ 品牌 HP + 品牌情绪 + (1|id)） ----------
# 品牌层 HP/情绪：直接从原始 dat 计算（Q1/Q5/Q12；Q2/Q6/Q13 1-9）
brand_vars <- function(dat, grp) {
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
    mem <- dat$记忆1 == "后厨大量使用冷冻食材" & dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
           dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
  } else {
    mem <- dat$记忆1 == "智能电动汽车制造" & dat$记忆2 == "在港交所挂牌上市" & dat$记忆3 == "外卖业务"
  }
  keep <- chk & mem & (dat$质检结果 == "正常")
  dat <- dat[keep, ]
  # 注意：品牌值按人交错拼接（每人 3 个品牌相邻），与 id 的 each=3 顺序一致
  list(
    hp_b = as.vector(rbind(rowMeans(dat[paste0("Q1_", 1:3)]),
                           rowMeans(dat[paste0("Q5_", 1:3)]),
                           rowMeans(dat[paste0("Q12_", 1:3)]))),
    neg_b = as.vector(rbind(rowMeans(dat[paste0("Q2_", 1:9)]),
                            rowMeans(dat[paste0("Q6_", 1:9)]),
                            rowMeans(dat[paste0("Q13_", 1:9)])))
  )
}
bv_e <- brand_vars(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
bv_c <- brand_vars(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)

df_e  <- data.frame(act = factor(as.vector(rbind(d_e$act_b1, d_e$act_b2, d_e$act_b3)),
                                 levels = 1:5, ordered = TRUE),
                    hp_b = bv_e$hp_b, neg_b = bv_e$neg_b, id = factor(rep(d_e$id, 3)))
df_c  <- data.frame(act = factor(as.vector(rbind(d_c$act_b1, d_c$act_b2, d_c$act_b3)),
                                 levels = 1:5, ordered = TRUE),
                    hp_b = bv_c$hp_b, neg_b = bv_c$neg_b, id = factor(rep(d_c$id, 3)))
df_all <- rbind(data.frame(df_e, grp = 1), data.frame(df_c, grp = 0))

clmm_rows <- function(m, label) {
  sm <- summary(m)$coefficients
  r <- data.frame(样本 = label, 变量 = rownames(sm),
                  coef = round(sm[, 1], 3), se = round(sm[, 2], 3),
                  z = round(sm[, 3], 2), p = round(sm[, 4], 4),
                  OR = round(exp(sm[, 1]), 3))
  rownames(r) <- NULL
  r[r$变量 %in% c("hp_b", "neg_b", "grp"), ]
}
m1 <- clmm(act ~ hp_b + neg_b + (1|id), data = df_e, link = "logit")
m2 <- clmm(act ~ hp_b + neg_b + (1|id), data = df_c, link = "logit")
m3 <- clmm(act ~ hp_b + neg_b + (1|id), data = df_all, link = "logit")
m4 <- clmm(act ~ hp_b + neg_b + grp + (1|id), data = df_all, link = "logit")
ord_out <- rbind(clmm_rows(m1, "实验组(品牌层)"), clmm_rows(m2, "对照组(品牌层)"),
                 clmm_rows(m3, "全部(品牌层)"), clmm_rows(m4, "全部(品牌层,含组别)"))
cat("\n=== 品牌层序次 logistic（OR：每升 1 分，选择更高一级行为的几率倍数） ===\n")
print(ord_out, row.names = FALSE)

# ---------- 3. 被试层序次 logistic（polr，round(行为强度)） ----------
d_e$act_r <- factor(round(d_e$act_ord_mean), levels = 1:5, ordered = TRUE)
d_c$act_r <- factor(round(d_c$act_ord_mean), levels = 1:5, ordered = TRUE)
d$act_r   <- factor(round(d$act_ord_mean), levels = 1:5, ordered = TRUE)
run_polr <- function(dd, label, with_grp = FALSE) {
  f <- if (with_grp) act_r ~ HP + negemo + grp else act_r ~ HP + negemo
  m <- polr(f, data = dd, Hess = TRUE)
  ct <- summary(m)$coefficients
  r <- data.frame(样本 = label, 变量 = rownames(ct),
                  coef = round(ct[, 1], 3), se = round(ct[, 2], 3),
                  z = round(ct[, 3], 2), p = round(pnorm(-abs(ct[, 3])) * 2, 4),
                  OR = round(exp(ct[, 1]), 3))
  rownames(r) <- NULL
  r[r$变量 %in% c("HP", "negemo", "grp"), ]
}
polr_out <- rbind(run_polr(d_e, "实验组"), run_polr(d_c, "对照组"),
                  run_polr(d, "全部"), run_polr(d, "全部,含组别", TRUE))
cat("\n=== 被试层序次 logistic（polr） ===\n")
print(polr_out, row.names = FALSE)
write.csv(rbind(ord_out, polr_out), "结果_行为建模_序次logistic.csv", row.names = FALSE)

# ---------- 4. 意愿-行为落差 ----------
# 落差 = 标准化传播意愿 − 标准化行为强度（均值恒 0，反映的是个体间"说多做少"的相对程度；
# 其 SD 描述落差离散度，回归回答"谁更倾向于说而不做"）
d_e$gap <- as.numeric(scale(d_e$si3)) - as.numeric(scale(d_e$act_ord_mean))
d_c$gap <- as.numeric(scale(d_c$si3)) - as.numeric(scale(d_c$act_ord_mean))
d$gap   <- as.numeric(scale(d$si3))   - as.numeric(scale(d$act_ord_mean))
cat("\n=== 意愿-行为落差（描述） ===\n")
for (lab in c("实验组", "对照组", "全部")) {
  dd <- switch(lab, 实验组 = d_e, 对照组 = d_c, 全部 = d)
  r <- cor(dd$si3, dd$act_ord_mean)
  cat(sprintf("%s: 落差 SD=%.3f | si3~行为强度相关 r=%.3f（意愿与行为对齐程度）\n",
              lab, sd(dd$gap), r))
}
gap_rows <- list()
for (lab in c("实验组", "对照组", "全部")) {
  dd <- switch(lab, 实验组 = d_e, 对照组 = d_c, 全部 = d)
  f <- if (lab == "全部") {
    gap ~ negemo + fear + sadness + CSR + freq_fwd + sm_inter + sm_time + female + age + grp
  } else {
    gap ~ negemo + fear + sadness + CSR + freq_fwd + sm_inter + sm_time + female + age
  }
  m <- lm(f, data = dd)
  sm <- summary(m)$coefficients
  r <- data.frame(样本 = lab, 变量 = rownames(sm),
                  coef = round(sm[, 1], 3), se = round(sm[, 2], 3),
                  t = round(sm[, 3], 2), p = round(sm[, 4], 4))
  rownames(r) <- NULL
  gap_rows[[length(gap_rows) + 1]] <- r[r$变量 != "(Intercept)", ]
}
gap_out <- do.call(rbind, gap_rows)
cat("\n=== 落差回归（正系数 = 意愿高于行为的程度更大，即更'说而不做'） ===\n")
print(gap_out, row.names = FALSE)
write.csv(gap_out, "结果_行为建模_落差分析.csv", row.names = FALSE)

cat("\n已导出：结果_行为建模_序次logistic.csv / 结果_行为建模_落差分析.csv\n")
cat("完成时间：", format(Sys.time()), "\n")
