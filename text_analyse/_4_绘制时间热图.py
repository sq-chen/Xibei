from collections import Counter
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

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
    freq_df[by]=df[by]
    return freq_df.groupby(by=by).sum().sort_values(by)

def draw_heatmap(input_pickle,input_keyword,output):
    # input_pickle:包含分词结果的pickle文件
    # input_keyword：统计词频中输出的高频词xlsx文件，用于绘制关键词（如前50个高频词）的热图
    # output：保存的文件名称
    try:
        df = pd.read_pickle(input_pickle)
    except:
        df = input_pickle
    keywords = pd.read_excel(input_keyword)['token'].to_list()[:20]
    # 计算每个关键词在每日中出现的次数
    freq_df = count_keywords_by(df,by='date',keywords=keywords,column='名动形')
    #根据每日的tokens总数计算相对频率
    freq_df = freq_df.div(df.groupby('date')['名动形数目'].sum(),axis=0)
    #应用平方根作为次线性滤波器以获得更好的对比度
    freq_df = freq_df.apply(np.sqrt)
    plt.figure(figsize=(10, 10))
    ax = sns.heatmap(data=freq_df.T,xticklabels=True,yticklabels=True,cbar=False,annot=True,annot_kws={'fontsize':12},linewidth=.5,cmap="YlOrRd")
    ax.xaxis.tick_top()
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=16)
    plt.tight_layout()
    plt.savefig(output + ".png")

