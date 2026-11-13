# 交叉验证_报告数字.R
# =====================
# 用最朴素的人级计算（lm/lm 交互/均值）独立重算汇报文档中的关键数字，
# 与已报告值逐一对照，排查数据拼接/口径类错误。
# 输出：结果_交叉验证对照表.csv

suppressPackageStartupMessages({library(readxl)})

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
  V98="性别", V99="年龄", V102="社媒时长", V112="互动倾向", V113="转发频率",
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
  V95="性别", V96="年龄", V99="社媒时长", V109="互动倾向", V110="转发频率",
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
    HP = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))]),
    anger = CAD(1:3), disgust = CAD(4:6), contempt = CAD(7:9),
    fear = CAD(10:12), sadness = CAD(13:15), negemo = CAD(1:9),
    m_action = rowMeans(dat[c(paste0("Q2_", 1:6), paste0("Q6_", 1:6), paste0("Q13_", 1:6))]),
    m_withdraw = CAD(7:9),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))]),
    act_ord_mean = rowMeans(beh),
    female = as.numeric(dat$性别 == "女"),
    age = as.numeric(dat$年龄),
    sm_time = as.numeric(c("少于30分钟"=1, "30分钟–1小时"=2, "1–2小时"=3,
                           "2–4小时"=4, "4–6小时"=5, "超过6小时"=6)[dat$社媒时长]),
    sm_inter = as.numeric(c("主要浏览，较少发帖和互动"=1, "偶尔点赞、发帖或评论"=2,
                            "经常主动发帖、转发、表达观点"=3)[dat$互动倾向]),
    freq_fwd = as.numeric(dat$转发频率),
    CSR = rowMeans(dat[c("Q23_1", "Q23_2", "Q23_3")]),
    grp = grp
  )
}
d_e <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1)
d_c <- prep(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0)
d <- rbind(d_e, d_c)

chk_rows <- list()
add_chk <- function(项目, 报告值, 重算值) {
  chk_rows[[length(chk_rows) + 1]] <<- data.frame(
    项目 = 项目, 报告值 = 报告值,
    重算值 = round(重算值, 3),
    一致 = abs(as.numeric(报告值) - as.numeric(重算值)) < 0.011)  # 容差=四舍五入粒度
}

cat("N: 实验组", nrow(d_e), "对照组", nrow(d_c), "\n")
stopifnot(nrow(d_e) == 189, nrow(d_c) == 184)

# 1. 操纵检验均值
add_chk("操纵-不一致感知-实验组M", 5.78, mean(d_e$HP))
add_chk("操纵-不一致感知-对照组M", 4.23, mean(d_c$HP))
add_chk("操纵-愤怒-实验组M", 5.81, mean(d_e$anger))
add_chk("操纵-愤怒-对照组M", 3.24, mean(d_c$anger))
add_chk("操纵-传播意愿-实验组M", 5.43, mean(d_e$si3))
add_chk("操纵-传播意愿-对照组M", 4.27, mean(d_c$si3))

# 2. 简单中介（person-level lm）
sm_med <- function(dd) {
  a <- unname(coef(lm(negemo ~ HP, dd))[2])
  b <- unname(coef(lm(si3 ~ negemo + HP, dd))[2])
  cp <- unname(coef(lm(si3 ~ negemo + HP, dd))[3])
  c(a = a, b = b, cp = cp)
}
r_e <- sm_med(d_e); r_c <- sm_med(d_c); r_a <- sm_med(d)
add_chk("简单中介-实验组a", .747, r_e["a"]); add_chk("简单中介-实验组b", .343, r_e["b"])
add_chk("简单中介-实验组cp", .184, r_e["cp"])
add_chk("简单中介-对照组a", 1.032, r_c["a"]); add_chk("简单中介-对照组b", .219, r_c["b"])
add_chk("简单中介-对照组cp", -.534, r_c["cp"])
add_chk("简单中介-全部a", 1.210, r_a["a"]); add_chk("简单中介-全部b", .399, r_a["b"])
add_chk("简单中介-全部cp", -.182, r_a["cp"])

# 3. 标准化多组路径（组内 z 标准化后 person-level lm）
z_w <- function(dd) { for (v in c("HP", "negemo", "si3")) dd[[v]] <- scale(dd[[v]]); dd }
ze <- z_w(d_e); zc <- z_w(d_c)
add_chk("标准化a-实验组", .758, coef(lm(negemo ~ HP, ze))[2])
add_chk("标准化a-对照组", .771, coef(lm(negemo ~ HP, zc))[2])
add_chk("标准化b-实验组", .269, coef(lm(si3 ~ negemo + HP, ze))[2])
add_chk("标准化b-对照组", .266, coef(lm(si3 ~ negemo + HP, zc))[2])
add_chk("标准化cp-实验组", .147, coef(lm(si3 ~ negemo + HP, ze))[3])
add_chk("标准化cp-对照组", -.485, coef(lm(si3 ~ negemo + HP, zc))[3])

# 4. 五情绪单独中介（全部样本）a/b
for (emo in c("anger", "disgust", "contempt", "fear", "sadness")) {
  a <- coef(lm(as.formula(paste(emo, "~ HP")), d))[2]
  b <- coef(lm(as.formula(paste("si3 ~", emo, "+ HP")), d))[2]
  rep <- switch(emo, anger = c(1.218, .380), disgust = c(1.211, .375),
                contempt = c(1.202, .320), fear = c(.856, .309), sadness = c(.862, .274))
  add_chk(paste0("五情绪单独-", emo, "-a"), rep[1], a)
  add_chk(paste0("五情绪单独-", emo, "-b"), rep[2], b)
}

# 5. 恐惧/悲伤（两组）
for (g in c("实验组", "对照组")) {
  dd <- if (g == "实验组") d_e else d_c
  rep <- if (g == "实验组") list(fear = c(.577, .111), sadness = c(.482, .096))
         else list(fear = c(.297, .165), sadness = c(.556, .213))
  for (emo in c("fear", "sadness")) {
    a <- coef(lm(as.formula(paste(emo, "~ HP")), dd))[2]
    b <- coef(lm(as.formula(paste("si3 ~", emo, "+ HP")), dd))[2]
    add_chk(paste0(g, "-", emo, "-a"), rep[[emo]][1], a)
    add_chk(paste0(g, "-", emo, "-b"), rep[[emo]][2], b)
  }
}

# 6. 行动组 vs 退缩组（全部样本）
a1 <- coef(lm(m_action ~ HP, d))[2]; a2 <- coef(lm(m_withdraw ~ HP, d))[2]
m <- lm(si3 ~ m_action + m_withdraw + HP, d)
add_chk("行动组ind(全部)", .654, a1 * coef(m)[2])
add_chk("退缩组ind(全部)", -.183, a2 * coef(m)[3])

# 7. 落差回归关键行（与行为建模脚本同公式：含 sm_time/female/age）
gap_f <- scale(d$si3) - scale(d$act_ord_mean)
m_gap <- lm(gap_f ~ negemo + fear + sadness + CSR + freq_fwd + sm_inter + sm_time + female + age + grp, d)
add_chk("落差回归grp系数", .504, coef(m_gap)["grp"])
add_chk("落差回归sm_inter系数", -.237, coef(m_gap)["sm_inter"])
add_chk("落差回归negemo系数", -.158, coef(m_gap)["negemo"])

# 8. 调节分析关键交互（person-level lm 交互）
m_int_b <- lm(si3 ~ negemo + HP + grp + negemo:grp, d)
cat("   [b段×组别交互 b3 =", round(coef(m_int_b)["negemo:grp"], 3), "（>0 即实验组 b 更强，与报告 diff=.757 同方向）]\n")
m_int_a <- lm(negemo ~ HP + grp + HP:grp, d)
cat("   [a段×组别交互 a3 =", round(coef(m_int_a)["HP:grp"], 3), "（<0 即实验组 a 更小，与报告 diff=−.114 同方向）]\n")

out <- do.call(rbind, chk_rows)
out <- out[!is.na(out$报告值), ]
print(out, row.names = FALSE)
cat("\n全部一致:", all(out$一致), "| 不一致项数:", sum(!out$一致), "\n")
write.csv(out, "结果_交叉验证对照表.csv", row.names = FALSE)
