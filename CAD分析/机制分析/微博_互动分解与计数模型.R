# 微博_互动分解与计数模型.R
# =====================
# 实验一（西贝微博 84,032 帖）两项补充：
#   1-1 互动类型分解：情绪（愤怒/厌恶/鄙视 pct）→ 转发 / 评论 / 点赞 三种互动分别建模
#       （既有 hobs1 已做"虚伪→分项互动"、hobs3 只做"情绪→总互动"；本脚本补上"情绪→分项互动"）
#   1-2 计数模型升级：glmmTMB 负二项 / 零膨胀负二项，替代 log 线性近似
#       （分项计数 reposts/comments/attitudes 全样本建模，含零帖；破零子模型正式检验虚伪的作用）
# 口径与 微博CAD机制分析.Rmd 一致：
#   - 数据 = merged_wide_v2.csv 左连接 CAD命中_明细.csv（v4 词典）
#   - 控制变量沿用 _regression_common.R 全套（含 (1|user_id) 随机截距）
# 输出：机制分析结果/hobs1补充_情绪分项互动.csv、hobs1补充_计数模型_虚伪.csv、
#        hobs1补充_计数模型_情绪.csv
suppressPackageStartupMessages({
  library(lme4); library(lmerTest); library(glmmTMB)
  library(readr); library(dplyr)
})
source("_regression_common.R", encoding = "UTF-8")

WIDE_PATH <- file.path("..", "..", "analysis", "分词与情感分析", "分词与情感分析结果", "merged_wide_v2.csv")
CAD_PATH  <- file.path("..", "分词与命中", "结果", "CAD命中_明细.csv")
OUT_ROOT  <- "机制分析结果"

wide <- read_csv(WIDE_PATH, locale = locale(encoding = "UTF-8"), show_col_types = FALSE)
cad  <- read_csv(CAD_PATH,  locale = locale(encoding = "UTF-8"), show_col_types = FALSE)
d <- wide %>% left_join(cad, by = "ID") %>% prepare_regression_df()
cat("连接后:", nrow(d), "行；未匹配 CAD 命中:", sum(is.na(d$hyp_hit_binary_cad)), "\n")
d$hyp_hit_binary_cad[is.na(d$hyp_hit_binary_cad)] <- 0
d$anger_hit_cad_pct[is.na(d$anger_hit_cad_pct)] <- 0
d$disgust_hit_cad_pct[is.na(d$disgust_hit_cad_pct)] <- 0
d$contempt_hit_cad_pct[is.na(d$contempt_hit_cad_pct)] <- 0
# 复合情绪强度 = 三情绪 pct 之和（与 Rmd 的 neg_hit_cad_pct 口径一致）
d$neg_hit_cad_pct <- d$anger_hit_cad_pct + d$disgust_hit_cad_pct + d$contempt_hit_cad_pct

SPLIT_DVS <- c(log_reposts = "log_reposts", log_comments = "log_comments", log_likes = "log_likes")
EMO_VARS  <- c("anger_hit_cad_pct", "disgust_hit_cad_pct", "contempt_hit_cad_pct")
COUNT_DVS <- c(total = "total_engagement", reposts = "reposts_count",
               comments = "comments_count", likes = "attitudes_count")

# ============ Part A（1-1 核心）：情绪 → 分项互动（lmer，剔零帖，同 hobs3 口径） ============
cat("========== Part A: 三情绪 → 转发/评论/点赞（log，剔零帖） ==========\n")
rows_a <- list()
for (dv_name in names(SPLIT_DVS)) {
  y <- SPLIT_DVS[[dv_name]]
  d_pos <- d %>% filter(.data[[y]] > 0)
  f <- as.formula(paste(y, "~", paste(c(EMO_VARS, CONTINUOUS_CONTROLS, TIME_CONTROLS,
                                        "verification_type", "phase", "hour_of_day",
                                        "(1 | user_id)"), collapse = " + ")))
  m <- lmer(f, data = d_pos, REML = FALSE, control = lmerControl(check.conv.singular = "ignore"))
  cat("\n=== DV:", y, "（n =", nrow(d_pos), "） ===\n")
  tb <- model_to_table(m)
  print(tb[tb$variable %in% EMO_VARS, c("variable", "coef", "se", "p_value")])
  for (v in EMO_VARS) {
    rows_a[[length(rows_a) + 1]] <- list(DV = dv_name, variable = v,
      coef = unname(fixef(m)[v]),
      se = summary(m)$coefficients[v, "Std. Error"],
      p_value = coef_pvalue(m, v), n_obs = nrow(d_pos))
  }
  # 两两 Wald
  w1 <- run_wald_equal_coef(m, EMO_VARS[1], EMO_VARS[2])
  w2 <- run_wald_equal_coef(m, EMO_VARS[1], EMO_VARS[3])
  w3 <- run_wald_equal_coef(m, EMO_VARS[2], EMO_VARS[3])
  cat(sprintf("Wald 两两: 怒-厌 chi2=%.2f p=%.3f | 怒-鄙 chi2=%.2f p=%.3f | 厌-鄙 chi2=%.2f p=%.3f\n",
              w1$statistic, w1$p_value, w2$statistic, w2$p_value, w3$statistic, w3$p_value))
}
write_csv_utf8(bind_rows(rows_a), file.path(OUT_ROOT, "hobs1补充_情绪分项互动.csv"))

# ============ Part B（1-1 佐证）：虚伪 → 分项互动 复核（lmer 剔零帖，与既有 hobs1_* 对照） ============
cat("\n========== Part B: 虚伪 → 分项互动 复核 ==========\n")
rows_b <- list()
for (dv_name in names(SPLIT_DVS)) {
  y <- SPLIT_DVS[[dv_name]]
  d_pos <- d %>% filter(.data[[y]] > 0)
  f <- as.formula(paste(y, "~ hyp_hit_binary_cad +", paste(
    c(CONTINUOUS_CONTROLS, TIME_CONTROLS, "verification_type", "phase", "hour_of_day",
      "(1 | user_id)"), collapse = " + ")))
  m <- lmer(f, data = d_pos, REML = FALSE, control = lmerControl(check.conv.singular = "ignore"))
  cat(sprintf("%s: 虚伪 coef=%.4f p=%.4g\n", y, fixef(m)["hyp_hit_binary_cad"],
              coef_pvalue(m, "hyp_hit_binary_cad")))
  rows_b[[length(rows_b) + 1]] <- list(DV = dv_name, variable = "hyp_hit_binary_cad",
    coef = unname(fixef(m)["hyp_hit_binary_cad"]),
    se = summary(m)$coefficients["hyp_hit_binary_cad", "Std. Error"],
    p_value = coef_pvalue(m, "hyp_hit_binary_cad"), n_obs = nrow(d_pos))
}
write_csv_utf8(bind_rows(rows_b), file.path(OUT_ROOT, "hobs1补充_虚伪分项复核.csv"))

# ============ Part C（1-2）：计数模型——负二项 / 零膨胀负二项（全样本，含零帖） ============
cat("\n========== Part C: 计数模型（glmmTMB） ==========\n")
ctrl_rhs <- c("hyp_hit_binary_cad", CONTINUOUS_CONTROLS, TIME_CONTROLS,
              "verification_type", "phase", "hour_of_day", "(1 | user_id)")

fit_nb <- function(y, main_vars, ziformula = ~1, zi_char = NULL) {
  rhs <- c(main_vars, CONTINUOUS_CONTROLS, TIME_CONTROLS,
           "verification_type", "phase", "hour_of_day", "(1 | user_id)")
  f <- as.formula(paste(y, "~", paste(rhs, collapse = " + ")))
  tryCatch(
    glmmTMB(f, data = d, family = nbinom2, ziformula = ziformula),
    error = function(e) { cat("!! 模型失败:", y, conditionMessage(e), "\n"); NULL })
}

extract_nb <- function(m, var, label) {
  if (is.null(m)) return(NULL)
  sm <- summary(m)$coefficients$cond
  if (!var %in% rownames(sm)) return(NULL)
  list(label = label, variable = var,
       coef = sm[var, "Estimate"], se = sm[var, "Std. Error"],
       z = sm[var, "z value"], p = sm[var, "Pr(>|z|)"],
       IRR = exp(sm[var, "Estimate"]))
}

# 1) 虚伪 → 各互动计数：负二项（主）+ 零膨胀负二项（破零子模型 = 虚伪）
rows_nb <- list(); rows_zi <- list(); models_zi <- list()
for (dv_name in names(COUNT_DVS)) {
  y <- COUNT_DVS[[dv_name]]
  cat("\n=== 计数 DV:", dv_name, "===\n")
  m_nb <- fit_nb(y, "hyp_hit_binary_cad", ~1)
  if (!is.null(m_nb)) {
    r <- extract_nb(m_nb, "hyp_hit_binary_cad", paste0("NB-", dv_name))
    if (!is.null(r)) { print(as.data.frame(r)); rows_nb[[length(rows_nb)+1]] <- r }
  }
  m_zi <- tryCatch(
    glmmTMB(as.formula(paste(y, "~", paste(ctrl_rhs, collapse = " + "))),
            data = d, family = nbinom2,
            ziformula = ~ hyp_hit_binary_cad),
    error = function(e) { cat("!! zi 模型失败:", conditionMessage(e), "\n"); NULL })
  if (!is.null(m_zi)) {
    models_zi[[dv_name]] <- m_zi
    sm_c <- summary(m_zi)$coefficients$cond
    sm_z <- summary(m_zi)$coefficients$zi
    r1 <- list(label = paste0("ZINB-cond-", dv_name), variable = "hyp_hit_binary_cad",
               coef = sm_c["hyp_hit_binary_cad", "Estimate"],
               se = sm_c["hyp_hit_binary_cad", "Std. Error"],
               z = sm_c["hyp_hit_binary_cad", "z value"],
               p = sm_c["hyp_hit_binary_cad", "Pr(>|z|)"],
               IRR = exp(sm_c["hyp_hit_binary_cad", "Estimate"]))
    r2 <- list(label = paste0("ZINB-zi-", dv_name), variable = "hyp_hit_binary_cad",
               coef = sm_z["hyp_hit_binary_cad", "Estimate"],
               se = sm_z["hyp_hit_binary_cad", "Std. Error"],
               z = sm_z["hyp_hit_binary_cad", "z value"],
               p = sm_z["hyp_hit_binary_cad", "Pr(>|z|)"],
               IRR = exp(sm_z["hyp_hit_binary_cad", "Estimate"]))
    cat(sprintf("  cond: IRR=%.3f p=%.3g | zi: coef=%.3f p=%.3g（zi 系数为 logit，正=更易零）\n",
                r1$IRR, r1$p, r2$coef, r2$p))
    rows_zi[[length(rows_zi)+1]] <- r1; rows_zi[[length(rows_zi)+1]] <- r2
  }
}
write_csv_utf8(bind_rows(rows_nb), file.path(OUT_ROOT, "hobs1补充_计数模型_虚伪.csv"))
write_csv_utf8(bind_rows(rows_zi), file.path(OUT_ROOT, "hobs1补充_计数模型_虚伪_零膨胀.csv"))

# 2) 情绪 → 各互动计数（负二项，控制虚伪；情绪用 neg_hit_cad_pct 与三情绪分别两版）
rows_emo <- list()
for (dv_name in names(COUNT_DVS)) {
  y <- COUNT_DVS[[dv_name]]
  m1 <- fit_nb(y, c("neg_hit_cad_pct", "hyp_hit_binary_cad"), ~1)
  if (!is.null(m1)) {
    r <- extract_nb(m1, "neg_hit_cad_pct", paste0("NB-复合情绪-", dv_name))
    if (!is.null(r)) { print(as.data.frame(r)); rows_emo[[length(rows_emo)+1]] <- r }
  }
  m2 <- fit_nb(y, c("anger_hit_cad_pct", "disgust_hit_cad_pct", "contempt_hit_cad_pct",
                    "hyp_hit_binary_cad"), ~1)
  if (!is.null(m2)) {
    for (v in EMO_VARS) {
      r <- extract_nb(m2, v, paste0("NB-三情绪-", dv_name))
      if (!is.null(r)) rows_emo[[length(rows_emo)+1]] <- r
    }
  }
}
write_csv_utf8(bind_rows(rows_emo), file.path(OUT_ROOT, "hobs1补充_计数模型_情绪.csv"))

cat("\n已导出：hobs1补充_情绪分项互动.csv / hobs1补充_虚伪分项复核.csv /",
    "hobs1补充_计数模型_虚伪.csv / hobs1补充_计数模型_虚伪_零膨胀.csv /",
    "hobs1补充_计数模型_情绪.csv\n完成时间：", format(Sys.time()), "\n")
