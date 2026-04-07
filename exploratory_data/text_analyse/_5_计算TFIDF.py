import pandas as pd
from collections import Counter
import numpy as np

def compute_idf(df, column, preprocess=None, min_df=2):
    # 参数min_df用于过滤不常用单词的长尾
    def tran(lt):
        if len(lt) > 0:
            return [t[0] for t in lt]
        else:
            return lt

    def update(doc):
        tokens = doc if preprocess is None else preprocess(doc)
        counter.update(set(tokens))

    # 计算tokens
    counter = Counter()
    df[column] = df[column].map(tran)
    df[column].map(update)
    # 创建DataFrame并计算idf
    idf_df = pd.DataFrame.from_dict(counter, orient='index', columns=['df'])
    idf_df = idf_df.query('df>=@min_df')
    idf_df['idf'] = np.log(len(df) / idf_df['df']) + 0.1
    idf_df.index.name = 'token'
    # 返回DataFrame
    return idf_df

def word_tfidf(input_pickle,input_freq,input_nva,output):
    # input_pickle:包含分词结果的pickle文件
    # input_freq：统计词频中的所有词的词频xlsx文件
    # input_nva：统计词频中的实词的词频xlsx文件
    # output：输出的文件名
    try:
        tokens_df = pd.read_pickle(input_pickle)
    except:
        tokens_df = input_pickle
    # IDF值需要为整个语料库计算一次(这里不要使用子集!)，然后可以在各种分析中使用
    idf_df = compute_idf(tokens_df, column='中文分词')
    nva_idf_df = compute_idf(tokens_df, column='名动形')

    # 生成两个文件，分别是对所有词、所有实词的tf-idf计算
    file_name1 = output + ".xlsx"
    writer1 = pd.ExcelWriter(file_name1, engine="openpyxl")
    freq_df = pd.ExcelFile(input_freq)
    file_name2 = output + "-名动形.xlsx"
    writer2 = pd.ExcelWriter(file_name2, engine="openpyxl")
    nva_df = pd.ExcelFile(input_nva)
    for sheet1,sheet2 in zip(freq_df.sheet_names,nva_df.sheet_names):
        # 读取词频
        freq_t_df = pd.read_excel(input_freq, sheet_name=sheet1)
        freq_t_df.set_index('token', inplace=True)
        # 读取实词的词频
        nva_t_df = pd.read_excel(input_nva, sheet_name=sheet2)
        nva_t_df.set_index('token', inplace=True)
        # 计算词语的tfidf
        freq_t_df['tfidf'] = freq_t_df['freq'] * idf_df['idf']
        freq_t_df = freq_t_df.sort_values('tfidf', ascending=False)
        # 计算实词的tfidf
        nva_t_df['tfidf'] = nva_t_df['freq'] * nva_idf_df['idf']
        nva_t_df = nva_t_df.sort_values('tfidf', ascending=False)
        # 保存结果
        freq_t_df.to_excel(writer1, sheet_name=sheet1)
        nva_t_df.to_excel(writer2, sheet_name=sheet2)
    writer1.close()
    writer2.close()
