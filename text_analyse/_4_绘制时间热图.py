from collections import Counter
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from pylab import mpl

mpl.rcParams["font.sans-serif"] = ["SimHei"]


def _parse_weibo_style_date(v):
    """按微博常见格式解析日期，避免 pd.to_datetime 把 '26-9-12' 猜成 2012-09-26 等。

    约定：日期在字符串最前，为 **年-月-日**；年为两位则 **2000+YY**（如 26 → 2026），
    与爬虫里 '25-9-13 07:59' 一致。支持 '2026-9-18' 四位年。
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return pd.NaT
    if isinstance(v, pd.Timestamp):
        return v.normalize()
    if hasattr(v, "year") and hasattr(v, "month") and not isinstance(v, str):
        try:
            return pd.Timestamp(v).normalize()
        except (ValueError, TypeError):
            return pd.NaT
    head = str(v).strip().split()[0].replace("/", "-")
    parts = head.split("-")
    if len(parts) < 3:
        return pd.NaT
    try:
        a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return pd.NaT
    if a >= 1000:
        y, m, d = a, b, c
    elif 0 <= a <= 99:
        y, m, d = 2000 + a, b, c
    else:
        return pd.NaT
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return pd.NaT
    try:
        return pd.Timestamp(year=y, month=m, day=d)
    except ValueError:
        return pd.NaT


def _to_calendar_day(series):
    """统一为自然日（去掉时分），便于按「天」聚合热图列数。"""
    s = series.copy()
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, errors="coerce").dt.normalize()
    # 字符串/对象：优先显式微博格式，绝不先用模糊 to_datetime（会错乱年份）
    parsed = s.map(_parse_weibo_style_date)
    nat = parsed.isna()
    if nat.any():
        parsed.loc[nat] = pd.to_datetime(s.loc[nat], errors="coerce", yearfirst=True)
    return pd.to_datetime(parsed, errors="coerce").dt.normalize()

def count_keywods(tokens,keywords):
    tokens=[t[0] for t in tokens if t[0] in keywords]
    counter=Counter(tokens)
    #查找counter中key为i的values值，若找不到则返回0
    return [counter.get(k,0) for k in keywords]

def count_keywords_by(df,by,keywords,column):
    #对每一个document对进行count_keywords操作，得到一个矩阵
    freq_matrix=df[column].apply(count_keywods,keywords=keywords)
    #print(isinstance(freq_matrix.iloc[0], list))
    #print(pd.DataFrame(freq_matrix).head(5))
    try:
        #DataFrame.from_records构建器支持元组列表或结构数据类型（dtype）的多维数组
        freq_df=pd.DataFrame.from_records(freq_matrix,columns=keywords)
    except:
        freq_df = pd.DataFrame(freq_matrix.tolist(), columns=keywords)
    #将原始数据中的year列复制给freq_df，然后在freq_df中可以按year列聚合和排序
    freq_df[by] = df[by]
    return freq_df.groupby(by=by).sum().sort_index()

def draw_heatmap(input_pickle,input_keyword,output):
    # input_pickle:包含分词结果的pickle文件
    # input_keyword：统计词频中输出的高频词xlsx文件，用于绘制关键词（如前50个高频词）的热图
    # output：保存的文件名称
    try:
        df = pd.read_pickle(input_pickle)
    except:
        df = input_pickle
    keywords = pd.read_excel(input_keyword)['token'].to_list()[:20]
    df = df.copy()
    df["_heatmap_day"] = _to_calendar_day(df["date"])
    df = df.dropna(subset=["_heatmap_day"])
    # 按自然日聚合（同一天多条帖合并为一列）
    freq_df = count_keywords_by(df, by="_heatmap_day", keywords=keywords, column="名动形")
    denom = df.groupby("_heatmap_day")["名动形数目"].sum()
    freq_df = freq_df.div(denom, axis=0)
    #应用平方根作为次线性滤波器以获得更好的对比度
    freq_df = freq_df.apply(np.sqrt)
    n_dates, n_kw = freq_df.shape[0], len(keywords)
    xlabels = [pd.Timestamp(x).strftime("%Y-%m-%d") for x in freq_df.index]
    # 按天列数通常远少于按条数；仍按列数控制画布与标注
    w = max(14.0, min(36.0, 0.42 * n_dates))
    h = max(8.0, min(16.0, 0.42 * n_kw))
    plt.figure(figsize=(w, h))
    show_annot = n_dates <= 14 and n_kw <= 14
    ax = sns.heatmap(
        data=freq_df.T,
        xticklabels=xlabels,
        yticklabels=True,
        cbar=False,
        annot=show_annot,
        annot_kws={"fontsize": 9},
        linewidth=0.5,
        cmap="YlOrRd",
    )
    ax.xaxis.tick_top()
    plt.yticks(fontsize=min(18, max(10, 220 // max(n_kw, 1))))
    plt.xticks(rotation=55, ha="left", fontsize=min(11, max(7, 180 // max(n_dates, 1))))
    plt.tight_layout()
    plt.savefig(output + ".png", dpi=150, bbox_inches="tight")

