import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
#from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import pandas as pd

from paths_config import data_join

# 使用哈工大停止词表
f = open(data_join("stopwords.txt"), encoding="utf-8")
stopwords = f.readlines()
stopwords = [t.strip('\n') for t in stopwords] # 1661个词

rule = r"([\u4E00-\u9FD5\U00010000-\U0010ffffa-zA-Z0-9+#&:\._\-% ]{2,})￥"
def calculate_co_currence(input_pickle,keywords, output, column="中文分词", keywords_num=20,min_df=10, cos=0.15):
    # input_pickle:包含分词结果的pickle文件
    # keywords:想要查看的高频词；输入的是统计词频中的xlsx文件
    # output：保存的文件名称，输出两种文件：txt文件用于存储所有词的相关性；xlsx文件只包含高频词的相关性
    try:
        tokens_df = pd.read_pickle(input_pickle)
    except:
        tokens_df = input_pickle
    keywords = pd.read_excel(keywords)
    # 默认只看前20个高频词
    keywords = keywords['token'].to_list()[:keywords_num]
    # 将分词结果用￥连接起来，方便后面TfidfVectorizer()根据自定义的规则进行分词结果读取、计算相关性
    tokens_df[column] = tokens_df[column].map(lambda lt: '￥'.join([t[0].strip(' ') for t in lt]) + '￥')
    # 存储高频词的计算结果
    info = defaultdict(list)
    # 根据自定义的规则rule来读取分词结果，初始化TfidfVectorizer
    tfidf_word = TfidfVectorizer(stop_words=list(stopwords),token_pattern=rule, min_df=min_df)
    dt_word = tfidf_word.fit_transform(tokens_df[column])
    # 词汇量很小，可以直接计算余弦相似度。
    # 将行向量替换为列向量，我们\\只需对矩阵进行转置，使用NumPy.T
    r = cosine_similarity(dt_word.T, dt_word.T)
    np.fill_diagonal(r, 0)
    # 如果把它转换成一个一维数组，找到最大的元素是最容易的，通过np.argsort，得到排序元素的索引，并恢复词汇表查找的原始索引:
    # voc = tf_word.get_feature_names_out()
    voc = tfidf_word.get_feature_names_out()
    size = r.shape[0]
    file_txt = open(output+".txt", "a+", encoding='utf-8')
    file_txt.write("{} {} {}\n".format("word1", "word2", "cos"))
    _num = 0
    for index in np.argsort(r.flatten())[::-1]:
        if r.flatten()[index] < cos:
            _num += 1
            if _num == 1000:
                break
            continue
        a = int(index / size)
        b = index % size
        if a > b and r.flatten()[index] >= cos:
            file_txt.write("{} {} {}\n".format(voc[a], voc[b], r.flatten()[index]))
            if (voc[a] in keywords or voc[b] in keywords) and r.flatten()[index] >= cos:
                info['word1'].append(voc[a])
                info['word2'].append(voc[b])
                info['cos'].append(r.flatten()[index])
            # print('"%s" related to "%s", result is: %f' % (voc[a], voc[b],r.flatten()[index]))

    file_txt.close()
    info = pd.DataFrame(info)
    info.to_excel(output+"-边文件.xlsx")

    total = []
    total += keywords
    temp = defaultdict(list)
    for kw in keywords:
        related = []
        for index, row in info.iterrows():
            if kw == row['word1']:
                related.append(row['word2'])
                if row['word2'] not in total:
                    total.append(row['word2'])
            if kw == row['word2']:
                related.append(row['word1'])
                if row['word1'] not in total:
                    total.append(row['word1'])
        temp['token'].append(kw)
        temp['related'].append('、'.join(related))
    temp = pd.DataFrame(temp)
    total = pd.DataFrame(total,columns=['total'])
    res = pd.concat([temp, total[['total']]], axis=1)
    res.to_excel(output + ".xlsx")
