# 实验2_调节分析.R
# =====================
# 2-4 调节与有调节的中介（全部样本 N=373；组别 grp：1=实验组/负性不一致，0=对照组/中性不一致）。
#   ① b 段被组别调节：情绪→传播意愿的斜率是否随道德性质不同；
#   ② a 段被组别调节：HP→情绪的斜率是否随道德性质不同；
#   ③ a 段被 CSR 关注度调节：关注 CSR 的人被背离伤得更重？
#   ④ b 段被个体差异调节：转发频率 / 互动倾向 / 社媒时长 / 性别 / 年龄——
#      什么条件下"情绪→传播"转化更强（为实验三提供边界条件线索）。
# 实现：lavaan 显变量乘积项，bootstrap 2000（BOOT_N 可调），条件间接效应与有调节中介指数。
# 输出：结果_调节分析_汇总.csv

library(readxl)
library(lavaan)
set.seed(20260903)
N_BOOT <- as.numeric(Sys.getenv("BOOT_N", "2000"))

# ---------- 1. 读取与计分（同既有脚本） ----------
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
  data.frame(
    HP = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))]),
    negemo = CAD(1:9),
    si3 = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))]),
    grp = grp,
    female = as.numeric(dat$性别 == "女"), age = as.numeric(dat$年龄),
    sm_time = as.numeric(c("少于30分钟"=1, "30分钟–1小时"=2, "1–2小时"=3,
                           "2–4小时"=4, "4–6小时"=5, "超过6小时"=6)[dat$社媒时长]),
    sm_inter = as.numeric(c("主要浏览，较少发帖和互动"=1, "偶尔点赞、发帖或评论"=2,
                            "经常主动发帖、转发、表达观点"=3)[dat$互动倾向]),
    freq_fwd = as.numeric(dat$转发频率),
    CSR = rowMeans(dat[c("Q23_1", "Q23_2", "Q23_3")])
  )
}
d <- rbind(prep(read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp), 1),
           prep(read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl), 0))
cat("全部样本 N =", nrow(d), "\n")
stopifnot(nrow(d) == 373)
# 连续调节变量中心化
for (v in c("CSR", "freq_fwd", "sm_inter", "sm_time", "age")) {
  d[[paste0(v, "_c")]] <- d[[v]] - mean(d[[v]])
}
# 乘积项
d$negemo_grp <- d$negemo * d$grp
d$HP_grp    <- d$HP * d$grp
d$HP_CSR    <- d$HP * d$CSR_c
for (v in c("freq_fwd", "sm_inter", "sm_time", "age")) {
  d[[paste0("negemo_", v)]] <- d$negemo * d[[paste0(v, "_c")]]
}

# ---------- 2. 模型与输出 ----------
sd_of <- function(x) sd(d[[x]])
report_mod <- function(fit, label, focus_vars) {
  pe <- parameterEstimates(fit, ci = TRUE)
  out <- pe[pe$lhs %in% focus_vars & pe$op %in% c("~", ":="),
            c("lhs", "op", "rhs", "est", "se", "z", "pvalue", "ci.lower", "ci.upper")]
  cat("==========", label, "==========\n")
  show <- data.frame(路径 = paste(out$lhs, out$op, out$rhs),
                     round(out[c("est", "se", "z", "pvalue", "ci.lower", "ci.upper")], 3))
  print(show, row.names = FALSE)
  invisible(out)
}

rows_all <- list()
add_rows <- function(fit, label) {
  pe <- parameterEstimates(fit, ci = TRUE)
  ind <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  r <- data.frame(模型 = label, 效应 = ind$lhs, est = round(ind$est, 3),
                  ci.lower = round(ind$ci.lower, 3), ci.upper = round(ind$ci.upper, 3))
  rows_all[[length(rows_all) + 1]] <<- r
}

# ① b 段被组别调节
m_bgrp <- '
  negemo ~ a*HP
  si3 ~ b1*negemo + cp*HP + b2*grp + b3*negemo_grp
  ind_ctrl := a*b1
  ind_exp  := a*(b1+b3)
  diff_ind := a*b3
'
fit1 <- sem(m_bgrp, data = d, se = "bootstrap", bootstrap = N_BOOT)
report_mod(fit1, "① b 段 × 组别", c("ind_ctrl", "ind_exp", "diff_ind", "negemo_grp"))
add_rows(fit1, "① b段×组别")

# ② a 段被组别调节
m_agrp <- '
  negemo ~ a1*HP + a2*grp + a3*HP_grp
  si3 ~ b*negemo + cp*HP
  ind_ctrl := a1*b
  ind_exp  := (a1+a3)*b
  diff_ind := a3*b
'
fit2 <- sem(m_agrp, data = d, se = "bootstrap", bootstrap = N_BOOT)
report_mod(fit2, "② a 段 × 组别", c("ind_ctrl", "ind_exp", "diff_ind", "HP_grp"))
add_rows(fit2, "② a段×组别")

# ③ a 段被 CSR 关注度调节
sdCSR <- sd_of("CSR_c")
m_acsr <- sprintf('
  negemo ~ a1*HP + a2*CSR_c + a3*HP_CSR
  si3 ~ b*negemo + cp*HP
  ind_low  := (a1 + a3*(%f))*b
  ind_high := (a1 + a3*(%f))*b
  diff_ind := a3*b*%f
', -sdCSR, sdCSR, 2 * sdCSR)
fit3 <- sem(m_acsr, data = d, se = "bootstrap", bootstrap = N_BOOT)
report_mod(fit3, "③ a 段 × CSR关注度", c("ind_low", "ind_high", "diff_ind", "HP_CSR"))
add_rows(fit3, "③ a段×CSR")

# ④ b 段被个体差异调节（连续变量：±1SD；分类：性别 0/1）
for (v in c("freq_fwd", "sm_inter", "sm_time", "age")) {
  sdV <- sd_of(paste0(v, "_c"))
  prod <- paste0("negemo_", v)
  m_v <- sprintf('
    negemo ~ a*HP
    si3 ~ b1*negemo + cp*HP + b2*%s_c + b3*%s
    ind_low  := a*(b1 + b3*(%f))
    ind_high := a*(b1 + b3*(%f))
    diff_ind := a*b3*%f
  ', v, prod, -sdV, sdV, 2 * sdV)
  fit_v <- sem(m_v, data = d, se = "bootstrap", bootstrap = N_BOOT)
  report_mod(fit_v, paste("④ b 段 ×", v), c("ind_low", "ind_high", "diff_ind", prod))
  add_rows(fit_v, paste0("④ b段×", v))
}
m_sex <- '
  negemo ~ a*HP
  si3 ~ b1*negemo + cp*HP + b2*female + b3*negemo_female
  ind_male   := a*b1
  ind_female := a*(b1+b3)
  diff_ind   := a*b3
'
d$negemo_female <- d$negemo * d$female
fit_sex <- sem(m_sex, data = d, se = "bootstrap", bootstrap = N_BOOT)
report_mod(fit_sex, "④ b 段 × 性别", c("ind_male", "ind_female", "diff_ind", "negemo_female"))
add_rows(fit_sex, "④ b段×性别")

# ---------- 3. 导出 ----------
out <- do.call(rbind, rows_all)
write.csv(out, "结果_调节分析_汇总.csv", row.names = FALSE)
cat("\n===== 有调节的中介汇总（bootstrap 95% CI） =====\n")
print(out, row.names = FALSE)
cat("\n已导出：结果_调节分析_汇总.csv\n完成时间：", format(Sys.time()), "\n")
