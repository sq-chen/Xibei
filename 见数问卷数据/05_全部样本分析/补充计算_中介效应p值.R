# 补充计算_中介效应p值.R
# =====================
# 快速重拟合各中介模型（不做 bootstrap，秒级），输出 a/b 路径系数（se、p）
# 与间接效应 Sobel（delta 法）z / p——供汇报表格取数。
# 覆盖：实验组 / 对照组 / 全部样本 ×（三情绪平行中介、五情绪单独中介、行动组vs退缩组）。
# 输出：结果_中介效应p值.csv

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
    anger = CAD(1:3), disgust = CAD(4:6), contempt = CAD(7:9),
    fear = CAD(10:12), sadness = CAD(13:15), negemo = CAD(1:9),
    m_action = rowMeans(dat[c(paste0("Q2_", 1:6), paste0("Q6_", 1:6), paste0("Q13_", 1:6))]),
    m_withdraw = CAD(7:9),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))])
  )
}
d_e <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
d_c <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)
d_all <- rbind(d_e, d_c)

m_par <- '
  anger    ~ a1*HP
  disgust  ~ a2*HP
  contempt ~ a3*HP
  si3 ~ b1*anger + b2*disgust + b3*contempt + cp*HP
'
m_single <- 'M ~ a*HP
             si3 ~ b*M + cp*HP'
m_grp <- 'm_action   ~ a1*HP
          m_withdraw ~ a2*HP
          si3 ~ b1*m_action + b2*m_withdraw + cp*HP'

sobel <- function(a, sea, b, seb) {
  ind <- a * b
  se_ind <- sqrt(b^2 * sea^2 + a^2 * seb^2)
  z <- ind / se_ind
  p <- 2 * (1 - pnorm(abs(z)))
  c(ind = ind, z = z, p = p)
}

rows <- list()
add_single <- function(dat, sample, emo) {
  m <- gsub("M", emo, m_single)
  fit <- sem(m, data = dat)
  pe <- parameterEstimates(fit)
  a <- pe$est[pe$lhs == emo & pe$rhs == "HP"]
  b <- pe$est[pe$lhs == "si3" & pe$rhs == emo]
  sea <- pe$se[pe$lhs == emo & pe$rhs == "HP"]
  seb <- pe$se[pe$lhs == "si3" & pe$rhs == emo]
  pa <- pe$pvalue[pe$lhs == emo & pe$rhs == "HP"]
  pb <- pe$pvalue[pe$lhs == "si3" & pe$rhs == emo]
  sb <- sobel(a, sea, b, seb)
  rows[[length(rows) + 1]] <<- data.frame(
    样本 = sample, 模型 = "单独中介", 情绪 = emo,
    a = round(a, 3), a_p = round(pa, 4), b = round(b, 3), b_p = round(pb, 4),
    ind = round(sb["ind"], 3), sobel_z = round(sb["z"], 2), sobel_p = round(sb["p"], 4))
}
add_par <- function(dat, sample) {
  fit <- sem(m_par, data = dat)
  pe <- parameterEstimates(fit)
  for (i in 1:3) {
    emo <- c("anger", "disgust", "contempt")[i]
    a <- pe$est[pe$lhs == emo & pe$rhs == "HP"]
    b <- pe$est[pe$lhs == "si3" & pe$rhs == emo]
    sea <- pe$se[pe$lhs == emo & pe$rhs == "HP"]
    seb <- pe$se[pe$lhs == "si3" & pe$rhs == emo]
    pa <- pe$pvalue[pe$lhs == emo & pe$rhs == "HP"]
    pb <- pe$pvalue[pe$lhs == "si3" & pe$rhs == emo]
    sb <- sobel(a, sea, b, seb)
    rows[[length(rows) + 1]] <<- data.frame(
      样本 = sample, 模型 = "平行中介", 情绪 = emo,
      a = round(a, 3), a_p = round(pa, 4), b = round(b, 3), b_p = round(pb, 4),
      ind = round(sb["ind"], 3), sobel_z = round(sb["z"], 2), sobel_p = round(sb["p"], 4))
  }
}
add_grp <- function(dat, sample) {
  fit <- sem(m_grp, data = dat)
  pe <- parameterEstimates(fit)
  for (i in 1:2) {
    mm <- c("m_action", "m_withdraw")[i]
    lab <- c("行动组", "退缩组")[i]
    a <- pe$est[pe$lhs == mm & pe$rhs == "HP"]
    b <- pe$est[pe$lhs == "si3" & pe$rhs == mm]
    sea <- pe$se[pe$lhs == mm & pe$rhs == "HP"]
    seb <- pe$se[pe$lhs == "si3" & pe$rhs == mm]
    pa <- pe$pvalue[pe$lhs == mm & pe$rhs == "HP"]
    pb <- pe$pvalue[pe$lhs == "si3" & pe$rhs == mm]
    sb <- sobel(a, sea, b, seb)
    rows[[length(rows) + 1]] <<- data.frame(
      样本 = sample, 模型 = "分组中介", 情绪 = lab,
      a = round(a, 3), a_p = round(pa, 4), b = round(b, 3), b_p = round(pb, 4),
      ind = round(sb["ind"], 3), sobel_z = round(sb["z"], 2), sobel_p = round(sb["p"], 4))
  }
}

for (sample in c("实验组", "对照组", "全部样本")) {
  dat <- switch(sample, 实验组 = d_e, 对照组 = d_c, 全部样本 = d_all)
  add_par(dat, sample)
  add_grp(dat, sample)
  for (emo in c("anger", "disgust", "contempt", "fear", "sadness")) {
    add_single(dat, sample, emo)
  }
}
out <- do.call(rbind, rows)
write.csv(out, "结果_中介效应p值.csv", row.names = FALSE)
print(out, row.names = FALSE)
cat("\n已导出：结果_中介效应p值.csv\n")
