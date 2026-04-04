import pandas as pd
import re
from collections import Counter
from collections import defaultdict

def find_threshold(freq,threshold):
    num = int(len(freq)*threshold)
    #print(num)
    min = freq[num]
    indices = [i for i, val in enumerate(freq) if val == min]
    index = indices[-1]
    return index

#count = -1
def token_filter(tokens,tokens_overall):
    user_tokens = []
    for t in tokens:
        if t in tokens_overall:
            user_tokens.append(t)
    count_tokens = Counter(user_tokens)
    ss = ""
    check_num = 0
    for token,num in count_tokens.items():
        ss = ss + token + ">>" + str(num) + "//"
        check_num += num
    return ss

def token_calculate(ss):
    regex = re.compile(r">>(\d+)//")
    num = regex.findall(ss)
    user_freq = 0
    for t in num:
        user_freq += float(t)
    return user_freq

def relative_freq(user_freq,freq_overall):
    return user_freq / sum(freq_overall) * 100

def calculate_contribution(temp_df,column,sta_tokens,token_col,threshold,):
    # temp_df:包含分词结果的pickle文件
    # column:'中文分词'；"名动形"
    # sta_tokens：统计词频的xlsx文件
    # token_col："freq"——简单词频；'tfidf'——权重
    # 获取所有词语列表
    tokens = sta_tokens['token'].tolist()
    # 获取所有词语的简单频次或tfidf
    freq = sta_tokens[token_col].tolist()
    # 根据阈值得到相应的被认为是高频词的数目
    num = find_threshold(freq, threshold)
    # 保存相应的高频词
    df_sta_new = sta_tokens[['token', token_col]][:num + 1]
    # 获取前threshold个词与频次/tfidf
    freq_overall = freq[:num + 1]
    tokens_overall = tokens[:num + 1]
    # print(tokens_overall)
    # 统计用户提及目标高频词
    temp_df[column+'_mention'] = temp_df[column].apply(token_filter, tokens_overall=tokens_overall)
    # 统计用户提及目标高频词的次数
    temp_df[column+'_mention_num'] = temp_df[column+'_mention'].map(token_calculate)
    if token_col == 'tfidf':
        df_copy = temp_df[['name', 'ID', 'url', 'date', column + '_mention', column + '_mention_num']]
    else:
        # 统计用户提及目标高频词的百分比
        temp_df[column+'_mention_per'] = temp_df[column+'_mention_num'].apply(relative_freq, freq_overall=freq_overall)
        df_copy = temp_df[['name', 'ID','url', 'date', column+'_mention', column+'_mention_num', column+'_mention_per']]
    return df_sta_new,df_copy

def keyword_contriution(input_pickle,read_token,nva,token_col,output,thresholds=[0.01,0.03,0.05,0.1,0.2,0.3]):
    # input_pickle:包含分词结果的pickle文件
    # read_token:统计词频的xlsx文件
        # "freq"——所有词的高频词；"nva"——所有实词的高频词；"tfidf"——所有词中tfidf中较高；"nva_tfidf"——所有实词中tfidf中较高；
    # nva:''——所有词；"nva"——实词的高频词
    # token_col:"freq"——简单词频；'tfidf'——权重
    # threshold：选择前threshold（百分比）的词语
    # output：保存的文件名称
    # 读入分词的结果
    try:
        df = pd.read_pickle(input_pickle)
    except:
        df = input_pickle
    # 去掉词性标注
    column = ''
    if nva == '':
        column = "中文分词"
    else:
        column = '名动形'
    df[column] = df[column].map(lambda lt: [t[0] for t in lt])
    sta_tokens = pd.read_excel(read_token)
    for threshold in thresholds:
        df_sta_old, df_old = calculate_contribution(temp_df=df,
                                                    column=column,
                                                    sta_tokens=sta_tokens,
                                                    token_col=token_col,
                                                    threshold=threshold)
        df_sta_old.to_excel(output + "中文热词_" + token_col + "_" + nva + "_" + str(threshold) + ".xlsx")
        df_old.to_excel(output + "中文热词用户贡献率_" + token_col + "_" + nva + "_" + str(threshold) + ".xlsx")
