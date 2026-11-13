# 补充_交互项p值.R：快速提取调节分析各交互项的系数与 p（lm 等价形式）
suppressPackageStartupMessages({library(readxl)})
source("交叉验证_报告数字.R", local = FALSE, encoding = "UTF-8")
# 注意：source 会执行全部验证（无害），d/d_e/d_c 已就绪

pv <- function(m, term) {
  s <- summary(m)$coefficients
  r <- s[term, ]
  cat(sprintf("%-28s b = % .3f  se = %.3f  t = % .2f  p = %.4f\n", term, r[1], r[2], r[3], r[4]))
}
cat("== 调节分析交互项（person-level lm，与 lavaan 显变量模型等价） ==\n")
m1 <- lm(si3 ~ negemo + HP + grp + negemo:grp, d)
pv(m1, "negemo:grp")
m2 <- lm(negemo ~ HP + grp + HP:grp, d)
pv(m2, "HP:grp")
d$CSR_c <- d$CSR - mean(d$CSR)
m3 <- lm(negemo ~ HP + CSR_c + HP:CSR_c, d)
pv(m3, "HP:CSR_c")
for (w in c("freq_fwd", "sm_inter", "sm_time")) {
  d[[paste0(w, "_c")]] <- d[[w]] - mean(d[[w]])
  f <- as.formula(paste0("si3 ~ negemo + HP + ", w, "_c + negemo:", w, "_c"))
  pv(lm(f, d), paste0("negemo:", w, "_c"))
}
m7 <- lm(si3 ~ negemo + HP + age + negemo:age, d)
pv(m7, "negemo:age")
m8 <- lm(si3 ~ negemo + HP + female + negemo:female, d)
pv(m8, "negemo:female")
