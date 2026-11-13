# 两两中介逐步进入.R
# =====================
# 全部样本 N=373（实验组 189 + 对照组 184），X = HP（不一致感知），Y = si3（传播意愿）。
# 计分与筛查逻辑与 05_全部样本分析/全部样本_中介检验.R 完全一致。
#
# A. 逐步进入（平行多中介，逐个加入情绪）：
#   M1 愤怒 → M2 +厌恶 → M3 +蔑视 → M4 +恐惧 → M5 五情绪全进
# B. 两两组合（关键组合）：
#   P1 愤怒+蔑视；P2 厌恶+蔑视（道德情绪内部两两）
#   P3 恐惧+悲伤（非道德情绪两两）
#   （愤怒+厌恶 即 M2，不重复跑）
#
# 每模型报告：各情绪 a/b 路径、特定间接效应（bootstrap 95% 百分位 CI）、
# 总间接效应、直接效应 c′，以及模型内中介两两对比（diff，服务 H2 差异检验）。
# lavaan 估计，se="bootstrap"，bootstrap 默认 5000（--boot 覆盖）。
#
# 用法：Rscript 两两中介逐步进入.R [--models M1,M2,...] [--boot 5000]
# 输出：结果_{key}_路径.csv / 结果_{key}_间接效应.csv

setwd("E:/文档/毕设研/数据/见数问卷数据/13_两两中介")
library(readxl)
library(lavaan)

# ---------- 0. 命令行参数 ----------
parse_cli <- function() {
  a <- commandArgs(trailingOnly = TRUE)
  get_flag <- function(flag, default) {
    i <- which(a == flag)
    if (length(i) && i[1] < length(a)) a[i[1] + 1] else default
  }
  mods <- get_flag("--models", "")
  boot <- as.numeric(get_flag("--boot", "5000"))
  sample <- get_flag("--sample", "all")
  list(models = if (mods == "") names(MODELS) else strsplit(mods, ",")[[1]],
       boot = boot,
       sample = sample)
}

MODELS <- list(
  M1 = "anger",
  M2 = "anger,disgust",
  M3 = "anger,disgust,contempt",
  M4 = "anger,disgust,contempt,fear",
  M5 = "anger,disgust,contempt,fear,sadness",
  P1 = "anger,contempt",
  P2 = "disgust,contempt",
  P3 = "fear,sadness"
)
MODEL_LABEL <- c(
  M1 = "逐步1: 愤怒",
  M2 = "逐步2: 愤怒+厌恶",
  M3 = "逐步3: 愤怒+厌恶+蔑视",
  M4 = "逐步4: +恐惧",
  M5 = "逐步5: 五情绪全进",
  P1 = "两两: 愤怒+蔑视",
  P2 = "两两: 厌恶+蔑视",
  P3 = "两两: 恐惧+悲伤"
)

cli <- parse_cli()
N_BOOT <- cli$boot
cat("模型：", paste(cli$models, collapse = ", "), "| bootstrap =", N_BOOT, "\n")

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
cat("样本：", sample_label, "N =", nrow(d), "\n")

# ---------- 4. 平行多中介模型语法 ----------
build_parallel_model <- function(emos) {
  lines <- c()
  for (i in seq_along(emos)) {
    lines <- c(lines, sprintf("%s ~ a%d*X", emos[i], i))
  }
  b_terms <- paste(sprintf("b%d*%s", seq_along(emos), emos), collapse = " + ")
  lines <- c(lines, sprintf("si3 ~ %s + cp*X", b_terms))
  if (length(emos) > 1) {
    prs <- combn(emos, 2)
    for (k in seq_len(ncol(prs))) {
      lines <- c(lines, sprintf("%s ~~ %s", prs[1, k], prs[2, k]))
    }
  }
  for (i in seq_along(emos)) {
    lines <- c(lines, sprintf("ind_%s := a%d*b%d", emos[i], i, i))
  }
  lines <- c(lines, sprintf("totind := %s",
                            paste(sprintf("a%d*b%d", seq_along(emos), seq_along(emos)),
                                  collapse = " + ")))
  lines <- c(lines, "total := cp + totind")
  if (length(emos) > 1) {
    prs <- combn(seq_along(emos), 2)
    for (k in seq_len(ncol(prs))) {
      i <- prs[1, k]; j <- prs[2, k]
      lines <- c(lines, sprintf("diff_%s_%s := a%d*b%d - a%d*b%d",
                                emos[i], emos[j], i, i, j, j))
    }
  }
  paste(lines, collapse = "\n")
}

# ---------- 5. 运行 ----------
run_model <- function(key, idx) {
  emos <- strsplit(MODELS[[key]], ",")[[1]]
  syn <- build_parallel_model(emos)
  set.seed(20260903 + idx)
  cat(">>>", key, MODEL_LABEL[[key]], "| 中介:", paste(emos, collapse = " + "),
      "| bootstrap =", N_BOOT, "\n")
  fit <- lavaan::sem(gsub("X", "HP", syn), data = d,
                     se = "bootstrap", bootstrap = N_BOOT)
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  paths <- pe[pe$op == "~", c("lhs", "rhs", "est", "se", "z", "pvalue",
                              "ci.lower", "ci.upper")]
  inds  <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  tag <- if (cli$sample == "all") "" else paste0("_", sample_label)
  write.csv(paths, sprintf("结果%s_%s_路径.csv", tag, key), row.names = FALSE)
  write.csv(inds,  sprintf("结果%s_%s_间接效应.csv", tag, key), row.names = FALSE)
  cat("--- 路径 ---\n")
  pr_num <- round(paths[sapply(paths, is.numeric)], 4)
  print(cbind(paths[c("lhs", "rhs")], pr_num), row.names = FALSE)
  cat("--- 间接效应与对比（bootstrap CI） ---\n")
  in_num <- round(inds[sapply(inds, is.numeric)], 4)
  print(cbind(效应 = inds$lhs, in_num), row.names = FALSE)
  invisible(list(paths = paths, inds = inds))
}

idx_map <- setNames(seq_along(names(MODELS)), names(MODELS))
for (key in cli$models) {
  if (!key %in% names(MODELS)) {
    cat("跳过未知模型：", key, "\n")
    next
  }
  tryCatch(run_model(key, idx_map[[key]]),
           error = function(e) cat("模型", key, "报错：", conditionMessage(e), "\n"))
}
cat("完成时间：", format(Sys.time()), "\n")
