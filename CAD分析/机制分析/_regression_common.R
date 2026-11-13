# -*- coding: utf-8 -*-
# 机制分析回归：lme4 HLM / GLMM 共用工具

suppressPackageStartupMessages({
  library(lme4)
  library(lmerTest)
  library(readr)
  library(dplyr)
  library(MuMIn)
})

CONTINUOUS_CONTROLS <- c(
  "log_text_len",
  "has_pic",
  "has_video",
  "posts_per_hour",
  "user_post_count"
)

TIME_CONTROLS <- c("is_weekend")

resolve_emotion_mode <- function(hit = FALSE) {
  if (hit) {
    list(
      hit = TRUE,
      mode_label = "命中计数",
      out_suffix = "_hit",
      moral_col = "moral_hit_score",
      high_arousal_col = "high_arousal_hit_score",
      low_arousal_col = "low_arousal_hit_score",
      arousal_group_col = "arousal_group_hit",
      neg_col = "neg_hit_score",
      pos_col = "pos_hit_score"
    )
  } else {
    list(
      hit = FALSE,
      mode_label = "强度加权",
      out_suffix = "",
      moral_col = "moral_score",
      high_arousal_col = "high_arousal_score",
      low_arousal_col = "low_arousal_score",
      arousal_group_col = "arousal_group",
      neg_col = "neg_score",
      pos_col = "pos_score"
    )
  }
}

prepare_regression_df <- function(df) {
  df <- df %>%
    mutate(
      verification_type = factor(
        ifelse(is.na(verification_type) | verification_type == "", "普通用户", verification_type),
        levels = c("普通用户", "蓝V", "黄V", "红V", "金V")
      ),
      phase = factor(phase, levels = c("P1", "P2", "P3")),
      hour_of_day = factor(hour_of_day, levels = 0:23),
      user_id = factor(user_id)
    )
  df
}

build_formula <- function(y_col, main_vars) {
  rhs <- c(main_vars, CONTINUOUS_CONTROLS, TIME_CONTROLS,
           "verification_type", "phase", "hour_of_day", "(1 | user_id)")
  as.formula(paste(y_col, "~", paste(rhs, collapse = " + ")))
}

run_hlm <- function(df, y_col, main_vars) {
  f <- build_formula(y_col, main_vars)
  lmer(f, data = df, REML = FALSE, control = lmerControl(check.conv.singular = "ignore"))
}

run_glmm_logit <- function(df, y_col, main_vars) {
  f <- build_formula(y_col, main_vars)
  glmer(
    f,
    data = df,
    family = binomial(link = "logit"),
    control = glmerControl(
      optimizer = "bobyqa",
      optCtrl = list(maxfun = 2e5),
      check.conv.singular = "ignore"
    )
  )
}

.fixed_coef_table <- function(model) {
  sm <- summary(model)$coefficients
  vars <- rownames(sm)
  stat_col <- intersect(colnames(sm), c("t value", "z value"))[1]
  p_col <- intersect(colnames(sm), c("Pr(>|t|)", "Pr(>|z|)"))[1]
  ci <- tryCatch(
    confint(model, method = "Wald", parm = "beta_"),
    error = function(e) matrix(NA_real_, nrow = length(vars), ncol = 2, dimnames = list(vars, c("2.5 %", "97.5 %")))
  )
  data.frame(
    variable = vars,
    coef = sm[, "Estimate"],
    se = sm[, "Std. Error"],
    t_stat = if (!is.na(stat_col)) sm[, stat_col] else NA_real_,
    p_value = if (!is.na(p_col)) sm[, p_col] else NA_real_,
    ci_lower = ci[, 1],
    ci_upper = ci[, 2],
    row.names = NULL,
    check.names = FALSE
  )
}

coef_pvalue <- function(model, var) {
  sm <- summary(model)$coefficients
  if (!var %in% rownames(sm)) return(NA_real_)
  p_col <- intersect(colnames(sm), c("Pr(>|t|)", "Pr(>|z|)"))[1]
  sm[var, p_col]
}

model_to_table <- function(model) {
  .fixed_coef_table(model)
}

glmm_to_table <- function(model) {
  tb <- .fixed_coef_table(model)
  tb$OR <- exp(tb$coef)
  tb[, c("variable", "coef", "OR", "se", "p_value")]
}

standardize_coefs <- function(model, df, y_col, x_vars) {
  y_sd <- sd(df[[y_col]], na.rm = TRUE)
  if (is.na(y_sd) || y_sd == 0) {
    return(setNames(rep(NA_real_, length(x_vars)), x_vars))
  }
  beta <- numeric(length(x_vars))
  names(beta) <- x_vars
  for (v in x_vars) {
    x_sd <- sd(df[[v]], na.rm = TRUE)
    coef_v <- fixef(model)[v]
    if (!is.na(x_sd) && x_sd > 0 && !is.na(coef_v)) {
      beta[v] <- unname(coef_v) * x_sd / y_sd
    } else {
      beta[v] <- NA_real_
    }
  }
  beta
}

model_r2 <- function(model, data = NULL) {
  mat <- tryCatch(
    if (!is.null(data)) {
      MuMIn::r.squaredGLMM(model, datab = data)
    } else {
      MuMIn::r.squaredGLMM(model)
    },
    error = function(e) NULL
  )
  if (!is.null(mat)) {
    marginal <- unname(mat[1, "R2m"])
    conditional <- unname(mat[1, "R2c"])
    if (!is.na(marginal)) {
      return(list(marginal = marginal, conditional = conditional))
    }
  }
  if (requireNamespace("performance", quietly = TRUE)) {
    perf <- tryCatch(performance::r2(model), error = function(e) NULL)
    if (!is.null(perf)) {
      marginal <- unname(perf$R2_marginal)
      conditional <- unname(perf$R2_conditional)
      if (!is.na(marginal)) {
        return(list(marginal = marginal, conditional = conditional))
      }
    }
  }
  list(marginal = NA_real_, conditional = NA_real_)
}

append_summary_rows <- function(rows, model_name, model, df, y_col, key_vars) {
  beta_std <- standardize_coefs(model, df, y_col, key_vars)
  sm <- summary(model)$coefficients
  p_col <- intersect(colnames(sm), c("Pr(>|t|)", "Pr(>|z|)"))[1]
  r2 <- model_r2(model)
  for (var in key_vars) {
    if (!var %in% names(fixef(model))) next
    rows[[length(rows) + 1]] <- list(
      model = model_name,
      variable = var,
      coef = unname(fixef(model)[var]),
      se = unname(sm[var, "Std. Error"]),
      beta_std = beta_std[var],
      p_value = unname(sm[var, p_col]),
      r_squared_marginal = r2$marginal,
      r_squared_conditional = r2$conditional,
      n_obs = nobs(model)
    )
  }
  rows
}

write_model_fit_csv <- function(models, path) {
  rows <- lapply(names(models), function(name) {
    m <- models[[name]]
    r2 <- model_r2(m)
    data.frame(
      model = name,
      n_obs = nobs(m),
      r_squared_marginal = r2$marginal,
      r_squared_conditional = r2$conditional,
      stringsAsFactors = FALSE
    )
  })
  write_csv_utf8(bind_rows(rows), path)
}

run_wald_equal_coef <- function(model, var_a, var_b) {
  coefs <- fixef(model)
  vc <- as.matrix(vcov(model))
  if (!all(c(var_a, var_b) %in% names(coefs))) {
    stop("Wald 检验变量不在模型中: ", var_a, ", ", var_b)
  }
  idx <- match(c(var_a, var_b), names(coefs))
  diff_est <- coefs[idx[1]] - coefs[idx[2]]
  diff_var <- vc[idx[1], idx[1]] + vc[idx[2], idx[2]] - 2 * vc[idx[1], idx[2]]
  stat <- (diff_est^2) / diff_var
  p <- pchisq(stat, df = 1, lower.tail = FALSE)
  list(
    test = paste0("H0: beta_", var_a, " = beta_", var_b),
    statistic = unname(stat),
    p_value = p,
    df_num = 1,
    df_denom = NA_real_
  )
}

write_csv_utf8 <- function(x, path) {
  write_excel_csv(x, path, na = "")
}

script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg)) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/")))
  }
  normalizePath(".", winslash = "/")
}

merged_wide_default <- function() {
  normalizePath(
    file.path(script_dir(), "..", "分词与情感分析", "分词与情感分析结果", "merged_wide_v2.csv"),
    winslash = "/",
    mustWork = FALSE
  )
}

mechanism_result_root <- function() {
  normalizePath(file.path(script_dir(), "机制分析结果"), winslash = "/")
}
