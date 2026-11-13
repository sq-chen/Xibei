# 操纵检验_组间对比.R
# =====================
# 实验组（负性不一致：西贝/自如/始祖鸟）vs 对照组（中性不一致：小米/农夫山泉/抖音）。
# 口径（与用户确认）：
#   - 两组同口径严格筛查：指令题全对 + 记忆题全对 + 质检正常
#     （实验组 N=189；对照组 N=184）
#   - 计分逻辑与 实验2_数据分析.Rmd 完全一致：不一致感知 = 9 条（前 2 条反向 + 第 3 条原向，3 品牌均值）
#   - 主检验：不一致感知组间差异（Welch t + Cohen's d）
#   - 附报：愤怒/厌恶/蔑视、传播意愿的组间差异；人口学平衡（性别 chi2、年龄/社媒时长 Welch t）
# 输出：结果_操纵检验.csv（与 Rmd 同文件夹）

library(readxl)

# ---------- 1. 读取与列名映射 ----------
read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}

# 实验组列映射（与 Rmd 一致）
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

# 对照组列映射（无 Q9/10/11 开放词与批次列；第 70 列起整体比实验组前移 3 列）
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

# ---------- 2. 严格筛查（两组同口径） ----------
# 指令题：小米/西贝应选"比较不同意"，农夫山泉/自如应选"比较同意"，抖音/始祖鸟应选"完全不同意"
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

cat("=== 筛查计数（严格口径：指令+记忆+质检） ===\n")
cat("实验组：总", nrow(dat_e), "| 指令题全对", sum(chk_e), "| 记忆题全对", sum(mem_e),
    "| 质检正常", sum(qua_e), "| 纳入分析", sum(keep_e), "\n")
cat("对照组：总", nrow(dat_c), "| 指令题全对", sum(chk_c), "| 记忆题全对", sum(mem_c),
    "| 质检正常", sum(qua_c), "| 纳入分析", sum(keep_c), "\n")

# ---------- 3. 计分（与 Rmd 一致的逻辑） ----------
score_one <- function(dat) {
  lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
          "比较同意"=5, "同意"=6, "完全同意"=7)
  lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
           "比较愿意"=5, "愿意"=6, "非常愿意"=7)
  lkf <- c("完全不符合"=1, "不符合"=2, "比较不符合"=3, "一般"=4,
           "比较符合"=5, "符合"=6, "完全符合"=7)
  to_num <- function(x) as.numeric(c(lk, lkw, lkf)[as.character(x)])

  scale_items <- c(
    paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),   # 不一致感知
    paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15), # 情绪（不含指令题）
    paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3)     # 传播意愿
  )
  dat[scale_items] <- lapply(dat[scale_items], to_num)

  # 反向计分（不一致感知前 2 条正向措辞）
  rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
  dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)

  CAD <- function(items) {
    rowMeans(dat[c(paste0("Q2_", items), paste0("Q6_", items), paste0("Q13_", items))],
             na.rm = TRUE)
  }
  data.frame(
    HP       = rowMeans(dat[c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3))],
                        na.rm = TRUE),                                      # 不一致感知（9条）
    anger    = CAD(1:3),
    disgust  = CAD(4:6),
    contempt = CAD(7:9),
    si3      = rowMeans(dat[c(paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))],
                        na.rm = TRUE),                                      # 传播意愿（9条）
    female   = as.integer(dat$性别 == "女"),
    age      = as.numeric(dat$年龄),
    sm_time  = as.numeric(c("少于30分钟"=1, "30分钟–1小时"=2, "1–2小时"=3,
                            "2–4小时"=4, "4–6小时"=5, "超过6小时"=6)[dat$社媒时长])
  )
}

sc_e <- score_one(dat_e)[keep_e, ]
sc_c <- score_one(dat_c)[keep_c, ]

# ---------- 4. 组间对比 ----------
# Welch t + Cohen's d（合并标准差）
cmp <- function(x, y) {
  x <- x[!is.na(x)]; y <- y[!is.na(y)]
  tt <- t.test(x, y)                       # Welch（默认）
  sp <- sqrt(((length(x) - 1) * var(x) + (length(y) - 1) * var(y)) /
             (length(x) + length(y) - 2))
  d <- (mean(x) - mean(y)) / sp
  c(N1 = length(x), M1 = mean(x), SD1 = sd(x),
    N2 = length(y), M2 = mean(y), SD2 = sd(y),
    t = tt$statistic, df = tt$parameter, p = tt$p.value, d = d)
}

res <- rbind(
  "不一致感知"     = cmp(sc_e$HP,       sc_c$HP),
  "愤怒"           = cmp(sc_e$anger,    sc_c$anger),
  "厌恶"           = cmp(sc_e$disgust,  sc_c$disgust),
  "蔑视"           = cmp(sc_e$contempt, sc_c$contempt),
  "传播意愿"       = cmp(sc_e$si3,      sc_c$si3),
  "年龄"           = cmp(sc_e$age,      sc_c$age),
  "社媒时长"       = cmp(sc_e$sm_time,  sc_c$sm_time)
)

cat("\n=== 组间对比（实验组 - 对照组；Welch t；d 为正 = 实验组更高） ===\n")
print(round(res, 3))

# 性别平衡（chi2）
sex_tab <- rbind(实验组 = table(sc_e$female), 对照组 = table(sc_c$female))
colnames(sex_tab) <- c("男", "女")
ch <- chisq.test(sex_tab)
cat("\n=== 性别平衡 ===\n")
print(sex_tab)
cat(sprintf("chi2(1) = %.2f, p = %.3f\n", ch$statistic, ch$p.value))

# ---------- 5. 导出 ----------
out <- data.frame(构念 = rownames(res), round(res, 3))
out$p <- format.pval(res[, "p"], digits = 3, eps = 0.001)
names(out) <- c("构念", "实验组N", "实验组M", "实验组SD",
                "对照组N", "对照组M", "对照组SD", "t", "df", "p", "d")
write.csv(out, "结果_操纵检验.csv", row.names = FALSE)
cat("\n已导出：结果_操纵检验.csv\n")
