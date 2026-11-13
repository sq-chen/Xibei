# -*- coding: utf-8 -*-
"""
整理数据_对照组.py
==================
对照组数据的整理脚本，规则与「整理数据_替换与选取逻辑.py」（实验组）完全一致，
仅列布局按对照组结构适配。

## 与实验组原始文件的差异
- 对照组 117 列，实验组（合并）121 列；
- 对照组没有 Q9/Q10/Q11 开放词汇题（实验组原始第 70–72 列），也没有末尾"批次"列；
- 其余列与实验组逐列对齐：对照组第 70 列起 = 实验组第 73 列起（整体前移 3 列）。
  因此整理后的列位置 1–101 与实验组整理文件的前 101 列完全对应，
  值替换映射（REPLACE_BY_CLEANED_COL）可原样复用（实验组整理文件多出的后 3 列是 Q9/10/11）。

## 列选取（原始 117 列 → 整理 101 列）
- 删除原始第 3–18 列（时间/渠道/IP/经纬度/省市/设备/浏览器/分辨率/质检结果）
- 保留顺序：原始第 [1, 2] + [19..117]（对照组无开放词题，无需像实验组那样把 70–72 移到末尾）

## 值替换（与实验组相同的字典映射，未列出者保持原值）
- 同意类 7 点（Q1_*/Q2_*/Q5_*/Q6_*/Q12_*/Q13_*，含指令题）/ 愿意类（Q4_*/Q8_*/Q15_*）
- 符合类（Q23_1/2/3）/ 行为单选（Q3/Q7/Q14）/ 性别 Q16 / 社媒时长 Q19 / 互动倾向 Q21

用法：
    python 整理数据_对照组.py <原始xlsx路径> <输出xlsx路径>
默认输入「已采纳_原始数据_对照组.xlsx」、输出「已整理数据_对照组.xlsx」。
"""
import sys
import openpyxl

# ---------- 值替换映射（与实验组脚本完全相同的字典） ----------
MAP_AGREE = {"完全不同意": 1, "不同意": 2, "比较不同意": 3, "一般": 4,
             "比较同意": 5, "同意": 6, "完全同意": 7}
MAP_WILL = {"完全不愿意": 1, "不愿意": 2, "比较不愿意": 3, "一般": 4,
            "比较愿意": 5, "愿意": 6, "非常愿意": 7}
MAP_CONFORM = {"完全不符合": 1, "不符合": 2, "比较不符合": 3, "一般": 4,
               "比较符合": 5, "符合": 6, "完全符合": 7}
MAP_ACT = {"不做任何操作": 1, "发送私信（其他用户不可见）": 2, "点赞": 3,
           "转发这条微博（可附加公开评论）": 4, "公开回复，发表自己的看法": 5}
MAP_SEX = {"女": 1, "男": 2}
MAP_Q19 = {"少于30分钟": 1, "30分钟–1小时": 2, "1–2小时": 3, "2–4小时": 4,
           "4–6小时": 5, "超过6小时": 6}
MAP_Q21 = {"主要浏览，较少发帖和互动": 1, "偶尔点赞、发帖或评论": 2,
           "经常主动发帖、转发、表达观点": 3}

# 整理列顺序（对照组原始列号：跳过 3–18 的元信息列，其余全保留）
COLS_KEEP = [1, 2] + list(range(19, 118))
assert len(COLS_KEEP) == 101

# 整理列号 -> 映射表（按整理后列位置标注；未列出者保持原值）。
# 与实验组脚本的 REPLACE_BY_CLEANED_COL 完全一致（两文件整理列 1–101 逐列对应）。
REPLACE_BY_CLEANED_COL = {}
REPLACE_BY_CLEANED_COL.update({j: MAP_AGREE for j in list(range(6, 25))})       # Q1_1..Q2_16
REPLACE_BY_CLEANED_COL[25] = MAP_ACT                                              # Q3
REPLACE_BY_CLEANED_COL.update({j: MAP_WILL for j in range(26, 29)})              # Q4_1-3
REPLACE_BY_CLEANED_COL.update({j: MAP_AGREE for j in list(range(31, 50))})       # Q5_1..Q6_16
REPLACE_BY_CLEANED_COL[50] = MAP_ACT                                             # Q7
REPLACE_BY_CLEANED_COL.update({j: MAP_WILL for j in range(51, 54)})              # Q8_1-3
REPLACE_BY_CLEANED_COL.update({j: MAP_AGREE for j in list(range(56, 75))})       # Q12_1..Q13_16
REPLACE_BY_CLEANED_COL[75] = MAP_ACT                                             # Q14
REPLACE_BY_CLEANED_COL.update({j: MAP_WILL for j in range(76, 79)})              # Q15_1-3
REPLACE_BY_CLEANED_COL[79] = MAP_SEX                                             # Q16
REPLACE_BY_CLEANED_COL[83] = MAP_Q19                                             # Q19
REPLACE_BY_CLEANED_COL[93] = MAP_Q21                                             # Q21
REPLACE_BY_CLEANED_COL.update({j: MAP_CONFORM for j in range(95, 98)})           # Q23_1-3


def clean_file(raw_path, out_path):
    wb = openpyxl.load_workbook(raw_path)
    ws = wb[wb.sheetnames[0]]
    n_rows = ws.max_row

    out_wb = openpyxl.Workbook()
    out_ws = out_wb.active
    out_ws.title = wb.sheetnames[0]

    unmapped = {}     # 整理列号 -> {值: 次数}
    empty_cells = {}  # 整理列号 -> 行号列表（原始为空的单元格）

    for i in range(1, n_rows + 1):
        for j, rc in enumerate(COLS_KEEP, 1):
            v = ws.cell(row=i, column=rc).value
            if i <= 2:
                # 两行表头原样保留
                out_ws.cell(row=i, column=j, value=v)
                continue
            mp = REPLACE_BY_CLEANED_COL.get(j)
            if mp is not None and v is not None:
                s = str(v).strip()
                if s in mp:
                    out_ws.cell(row=i, column=j, value=mp[s])
                elif s == "":
                    empty_cells.setdefault(j, []).append(i)
                    out_ws.cell(row=i, column=j, value=v)
                else:
                    unmapped.setdefault(j, {}).setdefault(s, 0)
                    unmapped[j][s] += 1
                    out_ws.cell(row=i, column=j, value=v)  # 原样保留，待人工处理
            else:
                out_ws.cell(row=i, column=j, value=v)

    out_wb.save(out_path)

    print(f"完成：{out_path}")
    print(f"  行数 {n_rows}（含 2 行表头，被试 {n_rows - 2} 人），列数 101")
    if unmapped:
        print("  [警告] 存在未匹配的原始取值（已原样保留，请人工检查）：")
        for j, cnt in sorted(unmapped.items()):
            print(f"    整理第{j}列: {cnt}")
    else:
        print("  [OK] 所有需替换列的值均成功映射")
    if empty_cells:
        print("  [注意] 存在空单元格的列:", empty_cells)
    return unmapped


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "已采纳_原始数据_对照组.xlsx"
    dst = sys.argv[2] if len(sys.argv) > 2 else "已整理数据_对照组.xlsx"
    clean_file(src, dst)
