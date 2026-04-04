import re
import pandas as pd

rule = re.compile("[\w\u4e00-\u9fa5]+")
nva = ["a","ad","an","d","l","s",
       "n","nr","nrfg","nrt","ns","nt","nw","nz",
       "v","vd","vi","vn","vq"]

def count_word(input_pickle,column,output='', min_freq=2):
    # input_pickle:包含分词结果的pickle文件
    # column：“中文分词”或“名动形”，分别对不同的词的类别进行计数
    # output：输出文件
    try:
        tokens_df = pd.read_pickle(input_pickle)
    except:
        tokens_df = input_pickle
    # 对每个词进行计数
    def word_dict(tokens):
        for word, flag in tokens:
            if len(word) > 1 and len(rule.findall(word)) != 0:
                result[word] = result.get(word, 0) + 1
                pos[word] = flag

    result = {}
    pos = {}
    tokens_df[column].apply(word_dict)
    for key, value in result.items():
        result[key] = [value, pos[key]]
    # 将计数器转为DataFrame
    freq_df = pd.DataFrame.from_dict(result, orient='index', columns=['freq', 'pos'])
    # 去掉出现频次小于2的词
    freq_df = freq_df.query('freq>=@min_freq')
    freq_df.index.name = 'token'
    # 统计出现的频次百分比
    total = sum(freq_df['freq'].tolist())
    freq_df['percentile'] = freq_df['freq'].map(lambda x: '{}({:.1%})'.format(x, x / total))
    freq_df = freq_df.sort_values(by='freq', ascending=False)
    # 保存文件
    if output == '':
        return freq_df
    else:
        freq_df.to_excel(output + '.xlsx')
    #print(freq_df.head(5))