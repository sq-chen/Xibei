# -*- coding: utf-8 -*-
"""
整理数据_替换与选取逻辑.py
=========================
从「已采纳_原始数据.xlsx」与「已整理数据.xlsx」逆向得到的整理规则，可复用于同一问卷
后续批次的数据整理，保证与第一批「已整理数据.xlsx」完全一致。

## 规则说明（与第一批已整理数据逐列比对验证）

### 1. 列选取（原始 120 列 → 整理 104 列）
- 删除原始第 3–18 列（开始/结束时间、作答时长、渠道、发布ID/名称、IP、
  经纬度、省份/城市、设备/操作系统/浏览器、屏幕分辨率、质检结果）
- 保留顺序：原始第 [1, 2] + [19..69] + [73..120] + [70, 71, 72]
  （即开放式词汇题 Q9/Q10/Q11 从原始第 70–72 列移到末尾）

### 2. 值替换（其余列保持原值，含文本与 0/1 多选）
- 同意类 7 点（Q1_*/Q2_*/Q5_*/Q6_*/Q12_*/Q13_*，含 Q2_16 等指令题）：
  完全不同意=1 不同意=2 比较不同意=3 一般=4 比较同意=5 同意=6 完全同意=7
- 愿意类 7 点（Q4_*/Q8_*/Q15_*）：
  完全不愿意=1 不愿意=2 比较不愿意=3 一般=4 比较愿意=5 愿意=6 非常愿意=7
- 符合类 7 点（Q23_1/2/3）：
  完全不符合=1 不符合=2 比较不符合=3 一般=4 比较符合=5 符合=6 完全符合=7
- 行为单选（Q3/Q7/Q14）：
  不做任何操作=1 发送私信（其他用户不可见）=2 点赞=3
  转发这条微博（可附加公开评论）=4 公开回复，发表自己的看法=5
- 性别 Q16：女=1 男=2
- 社媒时长 Q19：少于30分钟=1 30分钟–1小时=2 1–2小时=3 2–4小时=4
  4–6小时=5 超过6小时=6
- 互动倾向 Q21：主要浏览，较少发帖和互动=1 偶尔点赞、发帖或评论=2
  经常主动发帖、转发、表达观点=3

### 3. 表头与行
- 保留原两行表头（第 1 行题干、第 2 行题号），数据自第 3 行起
- 不删任何被试行

用法：
    python 整理数据_替换与选取逻辑.py <原始xlsx路径> <输出xlsx路径>
"""
import sys
import openpyxl

# ---------- 值替换映射 ----------
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

# 整理列顺序（原始列号）
COLS_KEEP = [1, 2] + list(range(19, 70)) + list(range(73, 121)) + [70, 71, 72]
assert len(COLS_KEEP) == 104

# 整理列号 -> 映射表（按整理后列位置标注；未列出者保持原值）
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

    unmapped = {}   # 整理列号 -> {值: 次数}
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
    print(f"  行数 {n_rows}（含 2 行表头，被试 {n_rows - 2} 人），列数 104")
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
    clean_file(sys.argv[1], sys.argv[2])
