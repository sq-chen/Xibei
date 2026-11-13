# 补充计算：合并数据（N=193）下解读所需的辅助模型数字
# 运行方式：Rscript 补充计算_辅助模型.R
suppressPackageStartupMessages({library(readxl); library(lavaan)})

BASE <- "E:/文档/毕设研/见数问卷数据/"
d <- read.csv(paste0(BASE, "结果_被试水平计分数据.csv"), fileEncoding = "UTF-8-BOM",
              check.names = FALSE)
d <- d[d$keep, ]

med <- function(fit, name) {
  pe <- lavaan::parameterEstimates(fit, ci = TRUE)
  ind <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cat("\n===", name, "===\n")
  print(cbind(效应 = ind$lhs, round(ind[c("est", "ci.lower", "ci.upper")], 3)),
        row.names = FALSE)
  invisible(ind)
}

# ---- 1) 因变量换 si2 ----
m_h2 <- 'negemo ~ a*X
          si3    ~ b*negemo + cp*X
          ind := a*b'
fit <- lavaan::sem(gsub("si3", "si2", gsub("X", "x_inc", m_h2)), data = d,
                   se = "bootstrap", bootstrap = 2000)
med(fit, "H2 因变量 si2")

m_h4 <- 'm_hyp  ~ a1*X
         negemo ~ a2*X + d21*m_hyp
         si3    ~ b1*m_hyp + b2*negemo + cp*X
         ind_chain := a1*d21*b2
         ind_hyp   := a1*b1
         ind_emo   := a2*b2'
fit <- lavaan::sem(gsub("si3", "si2", gsub("X", "x_inc", m_h4)), data = d,
                   se = "bootstrap", bootstrap = 2000)
med(fit, "H4 链式因变量 si2")

# ---- 2) 加协变量 ----
m_h2_cov <- 'negemo ~ a*X + g1*female + g2*age + g3*sm_time + g4*freq_fwd + g5*CSR
             si3    ~ b*negemo + cp*X + h1*female + h2*age + h3*sm_time + h4*freq_fwd + h5*CSR
             ind := a*b'
fit <- lavaan::sem(gsub("X", "x_inc", m_h2_cov), data = d,
                   se = "bootstrap", bootstrap = 2000)
med(fit, "H2 加协变量")

# ---- 3) 分品牌 H2（需要条目级，重新计分）----
dat <- as.data.frame(read_excel(paste0(BASE, "../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx"), skip = 1))
names(dat) <- paste0("V", seq_len(ncol(dat)))
colmap <- c(V22="Q1_1", V23="Q1_2", V24="Q1_3", V25="Q2_1", V26="Q2_2", V27="Q2_3",
  V28="Q2_4", V29="Q2_5", V30="Q2_6", V31="Q2_7", V32="Q2_8", V33="Q2_9",
  V34="Q2_10", V35="Q2_11", V36="Q2_12", V37="Q2_13", V38="Q2_14", V39="Q2_15",
  V42="Q4_1", V43="Q4_2", V44="Q4_3",
  V47="Q5_1", V48="Q5_2", V49="Q5_3", V50="Q6_1", V51="Q6_2", V52="Q6_3",
  V53="Q6_4", V54="Q6_5", V55="Q6_6", V56="Q6_7", V57="Q6_8", V58="Q6_9",
  V59="Q6_10", V60="Q6_11", V61="Q6_12", V62="Q6_13", V63="Q6_14", V64="Q6_15",
  V67="Q8_1", V68="Q8_2", V69="Q8_3",
  V75="Q12_1", V76="Q12_2", V77="Q12_3", V78="Q13_1", V79="Q13_2", V80="Q13_3",
  V81="Q13_4", V82="Q13_5", V83="Q13_6", V84="Q13_7", V85="Q13_8", V86="Q13_9",
  V87="Q13_10", V88="Q13_11", V89="Q13_12", V90="Q13_13", V91="Q13_14", V92="Q13_15",
  V95="Q15_1", V96="Q15_2", V97="Q15_3",
  V118="记忆1", V119="记忆2", V120="记忆3")
names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)

lk <- c("完全不同意"=1, "不同意"=2, "比较不同意"=3, "一般"=4,
        "比较同意"=5, "同意"=6, "完全同意"=7)
lkw <- c("完全不愿意"=1, "不愿意"=2, "比较不愿意"=3, "一般"=4,
         "比较愿意"=5, "愿意"=6, "非常愿意"=7)
to_num <- function(x) as.numeric(c(lk, lkw)[as.character(x)])
items <- c(paste0("Q1_", 1:3), paste0("Q5_", 1:3), paste0("Q12_", 1:3),
           paste0("Q2_", 1:15), paste0("Q6_", 1:15), paste0("Q13_", 1:15),
           paste0("Q4_", 1:3), paste0("Q8_", 1:3), paste0("Q15_", 1:3))
dat[items] <- lapply(dat[items], to_num)
rev_items <- c("Q1_1", "Q1_2", "Q5_1", "Q5_2", "Q12_1", "Q12_2")
dat[rev_items] <- lapply(dat[rev_items], function(x) 8 - x)

mem_all <- dat$记忆1 == "后厨大量使用冷冻食材" &
           dat$记忆2 == "全流程甲醛管控，检测达标后出租" &
           dat$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀"
ii <- mem_all
m_brand <- 'negemo ~ a*X
            si3    ~ b*negemo + cp*X
            ind := a*b'
brands <- list(西贝 = list(x = "Q1_2", emo = paste0("Q2_", 1:9), si = paste0("Q4_", 1:3)),
               自如 = list(x = "Q5_2", emo = paste0("Q6_", 1:9), si = paste0("Q8_", 1:3)),
               始祖鸟 = list(x = "Q12_2", emo = paste0("Q13_", 1:9), si = paste0("Q15_", 1:3)))
cat("\n=== 分品牌 H2（bootstrap 1000）===\n")
for (b in names(brands)) {
  bd <- data.frame(X = dat[ii, brands[[b]]$x],
                   negemo = rowMeans(dat[ii, brands[[b]]$emo], na.rm = TRUE),
                   si3 = rowMeans(dat[ii, brands[[b]]$si], na.rm = TRUE))
  f <- lavaan::sem(m_brand, data = bd, se = "bootstrap", bootstrap = 1000)
  pe <- lavaan::parameterEstimates(f, ci = TRUE)
  ind <- pe[pe$op == ":=" & pe$lhs == "ind", c("est", "ci.lower", "ci.upper")]
  cat(b, ": "); print(round(ind, 3), row.names = FALSE)
}

# ---- 4) 偏相关 ----
controls <- c("female", "age", "sm_time", "freq_fwd", "CSR")
partial_r <- function(x, y, controls, data) {
  d2 <- na.omit(data[c(x, y, controls)])
  rx <- residuals(lm(as.formula(paste(x, "~", paste(controls, collapse = "+"))), d2))
  ry <- residuals(lm(as.formula(paste(y, "~", paste(controls, collapse = "+"))), d2))
  ct <- cor.test(rx, ry)
  c(r = unname(ct$estimate), p = ct$p.value)
}
cat("\n=== 偏相关（控制性别/年龄/社媒时长/转发频率/CSR）===\n")
for (pr in list(c("HP","anger"), c("HP","disgust"), c("HP","contempt"),
                c("HP","negemo"), c("negemo","si3"), c("HP","si3"))) {
  res <- partial_r(pr[1], pr[2], controls, d)
  cat(sprintf("%s ~ %s: r = %.3f, p = %.3f\n", pr[1], pr[2], res["r"], res["p"]))
}

# ---- 5) 相对权重 ----
rel_weights <- function(y, xdf) {
  X <- as.matrix(xdf)
  e <- eigen(cor(X))
  Z <- X %*% e$vectors %*% diag(1 / sqrt(e$values))
  bz <- coef(lm(y ~ Z - 1))
  rw <- as.numeric(e$vectors^2 %*% (e$values * bz^2))
  names(rw) <- colnames(xdf)
  rw
}
rw <- rel_weights(d$si3, d[c("anger", "disgust", "contempt")])
cat("\n=== 相对权重（占 R2 百分比）===\n")
print(round(rw / sum(rw) * 100, 1))
