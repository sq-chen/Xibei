# 全部样本_行为与学科表.R —— 修正列位置后补提行为选择分布与学科分布
library(readxl)

read_one <- function(path, colmap) {
  dat <- as.data.frame(readxl::read_excel(path, skip = 1))
  names(dat) <- paste0("V", seq_len(ncol(dat)))
  names(dat)[as.integer(sub("V", "", names(colmap)))] <- unname(colmap)
  dat
}
# 实验组：Q2_16=V40、Q6_16=V65、Q13_16=V93；学科=V100
cmap_exp <- c(V1="作答ID", V18="质检结果", V40="Q2_16", V41="Q3",
              V65="Q6_16", V66="Q7", V93="Q13_16", V94="Q14", V100="学科",
              V118="记忆1", V119="记忆2", V120="记忆3")
# 对照组：Q2_16=V40、Q6_16=V65、Q13_16=V90；学科=V97
cmap_ctrl <- c(V1="作答ID", V18="质检结果", V40="Q2_16", V41="Q3",
               V65="Q6_16", V66="Q7", V90="Q13_16", V91="Q14", V97="学科",
               V115="记忆1", V116="记忆2", V117="记忆3")

dat_exp  <- read_one("../00_原始与整理数据/已采纳_原始数据_合并_实验组.xlsx", cmap_exp)
dat_ctrl <- read_one("../00_原始与整理数据/已采纳_原始数据_对照组.xlsx", cmap_ctrl)

keep_exp <- dat_exp$Q2_16 == "比较不同意" & dat_exp$Q6_16 == "比较同意" &
            dat_exp$Q13_16 == "完全不同意" &
            dat_exp$记忆1 == "后厨大量使用冷冻食材" &
            dat_exp$记忆2 == "全流程甲醛管控，检测达标后出租" &
            dat_exp$记忆3 == "赞助在喜马拉雅山脉举办的烟花秀" &
            dat_exp$质检结果 == "正常"
keep_ctrl <- dat_ctrl$Q2_16 == "比较不同意" & dat_ctrl$Q6_16 == "比较同意" &
             dat_ctrl$Q13_16 == "完全不同意" &
             dat_ctrl$记忆1 == "智能电动汽车制造" &
             dat_ctrl$记忆2 == "在港交所挂牌上市" &
             dat_ctrl$记忆3 == "外卖业务" &
             dat_ctrl$质检结果 == "正常"
cat("实验组纳入:", sum(keep_exp), "| 对照组纳入:", sum(keep_ctrl), "\n")
stopifnot(sum(keep_exp) == 189, sum(keep_ctrl) == 184)

beh_all <- c(unlist(dat_exp[keep_exp, c("Q3", "Q7", "Q14")]),
             unlist(dat_ctrl[keep_ctrl, c("Q3", "Q7", "Q14")]))
cat("\n=== 行为选择分布（三题 × 全部被试 N=373） ===\n")
print(table(行为 = beh_all))
act_map <- c("公开回复，发表自己的看法"=5, "转发这条微博（可附加公开评论）"=4,
             "点赞"=3, "发送私信（其他用户不可见）"=2, "不做任何操作"=1)
act <- act_map[beh_all]
cat(sprintf("\n总行为选择数: %d\n", length(act)))
cat(sprintf("主动传播（公开回复/转发）: %.1f%%\n", mean(act >= 4) * 100))
cat(sprintf("不做任何操作: %.1f%%\n", mean(act == 1) * 100))

cat("\n=== 学科分布（合并） ===\n")
cat("实验组:\n"); print(table(学科 = dat_exp$学科[keep_exp]))
cat("对照组:\n"); print(table(学科 = dat_ctrl$学科[keep_ctrl]))
cat("\n合并合计:\n")
t_exp <- table(dat_exp$学科[keep_exp])
t_ctrl <- table(dat_ctrl$学科[keep_ctrl])
print(merge(as.data.frame(t_exp), as.data.frame(t_ctrl), by = "Var1", all = TRUE))
