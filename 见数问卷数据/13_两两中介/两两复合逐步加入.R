# 两两复合逐步加入.R
# =====================
# 情绪两两（或更多）取均值合成「单一中介」，逐步加入情绪（简单中介模型）：
#   S2  = 愤怒+厌恶；S4 = 愤怒+厌恶+蔑视+恐惧
#   两两组合：PAC = 愤怒+蔑视；PDC = 厌恶+蔑视；PFS = 恐惧+悲伤
#   （S1=愤怒 见平行版 M1；S3=三情绪复合、S5=五情绪复合 见 10.9 简单中介）
# X = HP（不一致感知），Y = si3（传播意愿），bootstrap 默认 5000。
# 计分与筛查逻辑与 全部样本_中介检验.R 完全一致。
#
# 用法：Rscript 两两复合逐步加入.R --sample all|exp|ctrl [--boot 5000]
# 输出：结果_{样本}_复合中介汇总.csv

setwd("E:/文档/毕设研/数据/见数问卷数据/13_两两中介")
library(readxl)
library(lavaan)

parse_cli <- function() {
  a <- commandArgs(trailingOnly = TRUE)
  get_flag <- function(flag, default) {
    i <- which(a == flag)
    if (length(i) && i[1] < length(a)) a[i[1] + 1] else default
  }
  boot <- as.numeric(get_flag("--boot", "5000"))
  sample <- get_flag("--sample", "all")
  list(boot = boot, sample = sample)
}
cli <- parse_cli()

COMPOSITES <- list(
  S2  = c(anger = "愤怒", disgust = "厌恶"),
  S4  = c(anger = "愤怒", disgust = "厌恶", contempt = "蔑视", fear = "恐惧"),
  PAC = c(anger = "愤怒", contempt = "蔑视"),
  PDC = c(disgust = "厌恶", contempt = "蔑视"),
  PFS = c(fear = "恐惧", sadness = "悲伤")
)
COMP_LABEL <- c(
  S2  = "逐步2: 愤怒+厌恶",
  S4  = "逐步4: +恐惧（四情绪）",
  PAC = "两两: 愤怒+蔑视",
  PDC = "两两: 厌恶+蔑视",
  PFS = "两两: 恐惧+悲伤"
)

# ---------- 1. 读取与列名映射（同 全部样本_中介检验.R） ----------
read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}
cmap_exp <- c(
  V1="作答ID", V5="作答总时长", V18="质检结果",
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
  V118="记忆1", V119="记忆2", V120="记忆3",
  V121="批次"
)
cmap_ctrl <- c(
  V1="作答ID", V5="作答总时长", V18="质检结果",
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
dat_e <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_c <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)

# ---------- 2. 严格筛查（两组同口径：指令+记忆+质检） ----------
chk_e <- dat_e$Q2_16 == "比较不同意" & dat_e$Q6_16 == "比较同意" & dat_e$Q13_16 == "完全不同意"
mem_e <- dat_e$记忆1 == "后厨大量使用冷冻食材" &
         dat_e$记忆2 == "全流程甲醛管控，检测达标后出租" &
         dat_e$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
qua_e <- dat_e$质检结果 == "正常"
keep_e <- chk_e & mem_e & qua_e

chk_c <- dat_c$Q2_16 == "比较不同意" & dat_c$Q6_16 == "比较同意" & dat_c$Q13_16 == "完全不同意"
mem_c <- dat_c$记忆1 == "智能电动汽车制造" &
         dat_c$记忆2 == "在港交所挂牌上市" &
         dat_c$记忆3 == "外卖业务"
qua_c <- dat_c$质检结果 == "正常"
keep_c <- chk_c & mem_c & qua_c

stopifnot(sum(keep_e) == 189, sum(keep_c) == 184)

# ---------- 3. 计分（与既有脚本完全一致） ----------
lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
         "比较符合"=5, "符合"=6, "完全符合"=7)
to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])

score_one <- function(dat) {
  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3),
    paste0("Q23_", 1:3)
  )
  dat[scale_items] <- lapply(dat[scale_items], to_num)
  rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
  dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)
  CAD <- function(items) {
    rowMeans(dat[c(paste0("Q2_", items), paste0("Q6_", items), paste0("Q13_", items))],
             na.rm = TRUE)
  }
  data.frame(
    HP       = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))],
                        na.rm = TRUE),
    anger    = CAD(1:3),
    disgust  = CAD(4:6),
    contempt = CAD(7:9),
    fear     = CAD(10:12),
    sadness  = CAD(13:15),
    si3      = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))],
                        na.rm = TRUE)
  )
}
sc_e <- score_one(dat_e)[keep_e, ]
sc_c <- score_one(dat_c)[keep_c, ]
if (cli$sample == "exp") {
  d <- sc_e
} else if (cli$sample == "ctrl") {
  d <- sc_c
} else {
  d <- rbind(sc_e, sc_c)
}
sample_label <- c(exp = "实验组", ctrl = "对照组", all = "全部样本")[[cli$sample]]
tag <- if (cli$sample == "all") "" else paste0("_", sample_label)
cat("样本：", sample_label, "N =", nrow(d), "| bootstrap =", cli$boot, "\n")

# ---------- 4. 复合变量与简单中介 ----------
m_simple <- '
  M ~ a*X
  si3 ~ b*M + cp*X
  ind := a*b
  total := cp + a*b
'

sum_rows <- list()
idx <- 0
for (key in names(COMPOSITES)) {
  emos <- names(COMPOSITES[[key]])
  d$M <- rowMeans(d[emos], na.rm = TRUE)
  set.seed(20260903 + (idx <- idx + 1))
  cat(">>>", key, COMP_LABEL[[key]], "| 复合：", paste(COMPOSITES[[key]], collapse = "+"),
      "\n")
  fit <- lavaan::sem(gsub("X", "HP", m_simple), data = d,
                     se = "bootstrap", bootstrap = cli$boot)
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  a_r  <- pe[pe$lhs == "M" & pe$rhs == "HP", ]
  b_r  <- pe[pe$lhs == "si3" & pe$rhs == "M", ]
  cp_r <- pe[pe$lhs == "si3" & pe$rhs == "HP", ]
  ind_r <- pe[pe$lhs == "ind", ]
  tot_r <- pe[pe$lhs == "total", ]
  sum_rows[[key]] <- data.frame(
    模型 = key,
    复合 = paste(COMPOSITES[[key]], collapse = "+"),
    a_est = a_r$est, a_p = a_r$pvalue, a_cil = a_r$ci.lower, a_ciu = a_r$ci.upper,
    b_est = b_r$est, b_p = b_r$pvalue, b_cil = b_r$ci.lower, b_ciu = b_r$ci.upper,
    cp_est = cp_r$est, cp_p = cp_r$pvalue,
    ind_est = ind_r$est, ind_cil = ind_r$ci.lower, ind_ciu = ind_r$ci.upper,
    total_est = tot_r$est, total_cil = tot_r$ci.lower, total_ciu = tot_r$ci.upper
  )
  cat(sprintf("a=%.3f p=%.3f | b=%.3f p=%.3f | c'=%.3f p=%.3f | 间接 %.3f [%.3f, %.3f] | 总 %.3f [%.3f, %.3f]\n",
              a_r$est, a_r$pvalue, b_r$est, b_r$pvalue, cp_r$est, cp_r$pvalue,
              ind_r$est, ind_r$ci.lower, ind_r$ci.upper,
              tot_r$est, tot_r$ci.lower, tot_r$ci.upper))
}
out <- do.call(rbind, sum_rows)
write.csv(out, sprintf("结果%s_复合中介汇总.csv", tag), row.names = FALSE)
cat("已导出：", sprintf("结果%s_复合中介汇总.csv", tag), "\n")
cat("完成时间：", format(Sys.time()), "\n")
