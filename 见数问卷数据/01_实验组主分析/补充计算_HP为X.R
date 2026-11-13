# 补充计算：以 HP（虚伪感知全量表）为 X 的模型（N=189 主分析）
# 依据：Wagner 量表不拆分，全量表 HP 作为唯一虚伪感知构念。
# 运行：Rscript 补充计算_HP为X.R
suppressPackageStartupMessages({library(lavaan)})

BASE <- "E:/文档/毕设研/见数问卷数据/"
d <- read.csv(paste0(BASE, "结果_被试水平计分数据.csv"), fileEncoding = "UTF-8-BOM",
              check.names = FALSE)
d <- d[d$keep, ]   # N=189（keep 已为记忆+质检）

med <- function(fit, name) {
  pe <- lavaan::parameterEstimates(fit, ci = TRUE, standardized = TRUE)
  paths <- pe[pe$op == "~", c("lhs", "rhs", "est", "pvalue", "std.all")]
  ind <- pe[pe$op == ":=", c("lhs", "est", "ci.lower", "ci.upper")]
  cat("\n===", name, "===\n")
  print(cbind(paths[c("lhs", "rhs")], round(paths[c("est", "pvalue", "std.all")], 3)),
        row.names = FALSE)
  print(cbind(效应 = ind$lhs, round(ind[c("est", "ci.lower", "ci.upper")], 3)),
        row.names = FALSE)
  invisible(ind)
}

# 1) 简单中介：HP → negemo → si3
m1 <- 'negemo ~ a*X
       si3    ~ b*negemo + cp*X
       ind := a*b
       total := cp + a*b'
med(lavaan::sem(gsub("X", "HP", m1), data = d, se = "bootstrap", bootstrap = 2000), "H3可检验部分：HP→negemo→si3")

# 2) 三情绪平行中介
m2 <- 'anger ~ a1*X; disgust ~ a2*X; contempt ~ a3*X
       si3 ~ b1*anger + b2*disgust + b3*contempt + cp*X
       ind_anger := a1*b1; ind_disgust := a2*b2; ind_contempt := a3*b3
       total := cp + a1*b1 + a2*b2 + a3*b3
       diff_a_d := a1*b1 - a2*b2; diff_a_c := a1*b1 - a3*b3; diff_d_c := a2*b2 - a3*b3'
med(lavaan::sem(gsub("X", "HP", m2), data = d, se = "bootstrap", bootstrap = 2000), "H3三情绪平行中介")

# 3) 分组：行动 vs 退缩
m3 <- 'm_action ~ a1*X; m_withdraw ~ a2*X
       si3 ~ b1*m_action + b2*m_withdraw + cp*X
       ind_action := a1*b1; ind_withdraw := a2*b2; diff := a1*b1 - a2*b2'
med(lavaan::sem(gsub("X", "HP", m3), data = d, se = "bootstrap", bootstrap = 2000), "H2分组：行动vs退缩")

# 4) 分组：行动 vs 悲伤（旧唤醒度对照）
m4 <- 'm_action ~ a1*X; sadness ~ a2*X
       si3 ~ b1*m_action + b2*sadness + cp*X
       ind_action := a1*b1; ind_sadness := a2*b2; diff := a1*b1 - a2*b2'
med(lavaan::sem(gsub("X", "HP", m4), data = d, se = "bootstrap", bootstrap = 2000), "额外：行动vs悲伤")

# 5) 因变量 si2
med(lavaan::sem(gsub("si3", "si2", gsub("X", "HP", m1)), data = d, se = "bootstrap", bootstrap = 2000),
    "稳健：si2 因变量")

# 6) 协变量版
m1c <- 'negemo ~ a*X + g1*female + g2*age + g3*sm_time + g4*freq_fwd + g5*CSR
        si3    ~ b*negemo + cp*X + h1*female + h2*age + h3*sm_time + h4*freq_fwd + h5*CSR
        ind := a*b; total := cp + a*b'
med(lavaan::sem(gsub("X", "HP", m1c), data = d, se = "bootstrap", bootstrap = 2000), "稳健：加协变量")

# 7) 敏感性：不同剔除标准
cat("\n=== 敏感性（bootstrap 1000）===\n")
dall <- read.csv(paste0(BASE, "结果_被试水平计分数据.csv"), fileEncoding = "UTF-8-BOM",
                 check.names = FALSE)
for (nm in c("全部N197", "仅记忆N193", "主分析N189")) {
  dd <- if (nm == "全部N197") dall else if (nm == "仅记忆N193") dall[dall$keep_mem, ] else dall[dall$keep, ]
  f <- lavaan::sem(gsub("X", "HP", m1), data = dd, se = "bootstrap", bootstrap = 1000)
  pe <- lavaan::parameterEstimates(f, ci = TRUE)
  ind <- pe[pe$op == ":=" & pe$lhs == "ind", c("est", "ci.lower", "ci.upper")]
  cat(nm, ": "); print(round(ind, 3), row.names = FALSE)
}

# 8) 零阶回归 HP → si3
m0 <- lm(scale(si3) ~ scale(HP), d)
cat("\n=== 零阶回归 si3 ~ HP ===\n")
print(round(summary(m0)$coefficients, 4))
cat("R2 =", round(summary(m0)$r.squared, 3), "\n")
