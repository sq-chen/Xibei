# %% 标签添加按 ctrl+f11 或者直接 f11
# 读入函数
import pandas as pd
from _1_数据预处理与分词 import process_data
from _2_统计词频 import count_word
from _4_绘制时间热图 import draw_heatmap
from _5_计算TFIDF import word_tfidf
from _6_计算热词贡献率 import keyword_contriution
from _7_计算高频词的相关词 import calculate_co_currence
from _8_画相关词的树图 import draw_tree
from _9_情感分析 import sentiment_analysis
# %%
# 创建文件夹
import os

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(path, ": Folder created")
    else:
        print(path, ": Folder already exists")

# %%
# *************************************************************************
# ***                              对整体文档进行处理                      ***
# *************************************************************************
# %%
# 分词
# process_data(input,output):
# input：输入的原始数据集
# output：输出的文件名，会生成xlsx和pickle两种形式的文件，xlsx方便查看，pickle则方便之后其他的操作
create_folder("./result")
create_folder("./result/分词结果")
process_data("./data/五月天超话-12.3-12.9-帖子.xlsx", "./result/分词结果/超话-中文分词")
process_data("./data/五月天假唱话题-12.3-12.9.xlsx", "./result/分词结果/社区外-中文分词")
# %%
# count_word(input_pickle,column,output):
# input_pickle:包含分词结果的pickle文件
# column：“中文分词”或“名动形”，分别对不同的词的类别进行计数
# output：输出文件xlsx
# 统计所有词的词频
create_folder("./result/整体文档")
create_folder("./result/整体文档/统计词频")
count_word(input_pickle='./result/分词结果/超话-中文分词.pickle', column='中文分词',
           output='./result/整体文档/统计词频/超话-整体词频')
count_word(input_pickle="./result/分词结果/社区外-中文分词.pickle", column='中文分词',
           output='./result/整体文档/统计词频/社区外-整体词频')
# 统计实词的词频
count_word(input_pickle='./result/分词结果/超话-中文分词.pickle', column='名动形',
           output='./result/整体文档/统计词频/超话-整体词频-名动形')
count_word(input_pickle="./result/分词结果/社区外-中文分词.pickle", column='名动形',
           output='./result/整体文档/统计词频/社区外-整体词频-名动形')
# %%
# 计算tf-idf
create_folder("./result/整体文档/计算tf-idf")
word_tfidf(input_pickle='./result/分词结果/超话-中文分词.pickle',
           input_freq='./result/整体文档/统计词频/超话-整体词频.xlsx',
           input_nva='./result/整体文档/统计词频/超话-整体词频-名动形.xlsx',
           output="./result/整体文档/计算tf-idf/超话-整体词频-tf-idf")
word_tfidf(input_pickle='./result/分词结果/社区外-中文分词.pickle',
           input_freq='./result/整体文档/统计词频/社区外-整体词频.xlsx',
           input_nva='./result/整体文档/统计词频/社区外-整体词频-名动形.xlsx',
           output="./result/整体文档/计算tf-idf/社区外-整体词频-tf-idf")
# %%
# 绘制热图
# draw_heatmap(input_pickle,input_keyword,output):
# input_pickle:包含分词结果的pickle文件
# input_keyword：统计词频中输出的高频词xlsx文件，用于绘制关键词（如前50个高频词）的热图
# output：保存的文件名称
# 超话内的实词热图
create_folder("./result/整体文档/时间词频热图")
draw_heatmap(input_pickle='./result/分词结果/超话-中文分词.pickle',
             input_keyword='./result/整体文档/计算tf-idf/超话-整体词频-tf-idf-名动形.xlsx',
             output='./result/整体文档/时间词频热图/超话-名动形-tf-idf')
# 超话外的实词热图
draw_heatmap(input_pickle='./result/分词结果/社区外-中文分词.pickle',
             input_keyword='./result/整体文档/计算tf-idf/社区外-整体词频-tf-idf-名动形.xlsx',
             output='./result/整体文档/时间词频热图/社区外-名动形-tf-idf')
# %%
# 计算热词贡献率
create_folder("result/整体文档/热词贡献统计")
create_folder("result/整体文档/热词贡献统计/社区内")
create_folder("result/整体文档/热词贡献统计/社区外")
# 社区内：简单词频的贡献率
keyword_contriution(input_pickle="./result/分词结果/超话-中文分词.pickle",
                    read_token='./result/整体文档/统计词频/超话-整体词频.xlsx',
                    nva='',
                    token_col='freq',
                    output="result/整体文档/热词贡献统计/社区内/")
keyword_contriution(input_pickle="./result/分词结果/超话-中文分词.pickle",
                    read_token='./result/整体文档/统计词频/超话-整体词频-名动形.xlsx',
                    nva='名动形',
                    token_col='freq',
                    output="result/整体文档/热词贡献统计/社区内/")
# 社区外：简单词频的贡献率
keyword_contriution(input_pickle='./result/分词结果/社区外-中文分词.pickle',
                    read_token='./result/整体文档/统计词频/社区外-整体词频.xlsx',
                    nva='',
                    token_col='freq',
                    output="result/整体文档/热词贡献统计/社区外/")
keyword_contriution(input_pickle='./result/分词结果/社区外-中文分词.pickle',
                    read_token='./result/整体文档/统计词频/社区外-整体词频-名动形.xlsx',
                    nva='名动形',
                    token_col='freq',
                    output="result/整体文档/热词贡献统计/社区外/")
# %%
# tfidf的贡献率
keyword_contriution(input_pickle="./result/分词结果/超话-中文分词.pickle",
                    read_token='./result/整体文档/计算tf-idf/超话-整体词频-tf-idf.xlsx',
                    nva='',
                    token_col='tfidf',
                    output="result/整体文档/热词贡献统计/社区内/")
keyword_contriution(input_pickle="./result/分词结果/超话-中文分词.pickle",
                    read_token='./result/整体文档/计算tf-idf/超话-整体词频-tf-idf-名动形.xlsx',
                    nva='名动形',
                    token_col='tfidf',
                    output="result/整体文档/热词贡献统计/社区内/")
# 社区外：tfidf的贡献率
keyword_contriution(input_pickle='./result/分词结果/社区外-中文分词.pickle',
                    read_token='./result/整体文档/计算tf-idf/社区外-整体词频-tf-idf.xlsx',
                    nva='',
                    token_col='tfidf',
                    output="result/整体文档/热词贡献统计/社区外/")
keyword_contriution(input_pickle='./result/分词结果/社区外-中文分词.pickle',
                    read_token='./result/整体文档/计算tf-idf/社区外-整体词频-tf-idf-名动形.xlsx',
                    nva='名动形',
                    token_col='tfidf',
                    output="result/整体文档/热词贡献统计/社区外/")
# %%
# 计算相关词
create_folder("./result/整体文档/相关词")
calculate_co_currence(input_pickle="./result/分词结果/超话-中文分词.pickle",
                      keywords="./result/整体文档/热词贡献统计/社区内/中文热词_freq__0.05.xlsx",
                      output="./result/整体文档/相关词/超话-0.05高频词的相关词-关键词")
calculate_co_currence(input_pickle="./result/分词结果/超话-中文分词.pickle",
                      keywords="result/整体文档/热词贡献统计/社区内/中文热词_freq_名动形_0.05.xlsx",
                      output="./result/整体文档/相关词/超话-0.05高频词的相关词-关键词-名动形",
                      column='名动形')
#%%
calculate_co_currence(input_pickle="./result/分词结果/社区外-中文分词.pickle",
                      keywords="./result/整体文档/热词贡献统计/社区外/中文热词_freq__0.05.xlsx",
                      output="./result/整体文档/相关词/社区外-0.05高频词的相关词-关键词")
calculate_co_currence(input_pickle="./result/分词结果/社区外-中文分词.pickle",
                      keywords="result/整体文档/热词贡献统计/社区外/中文热词_freq_名动形_0.05.xlsx",
                      output="./result/整体文档/相关词/社区外-0.05高频词的相关词-关键词-名动形",
                      column='名动形')
# %% 情感分析
create_folder("./result/整体文档/情感分析")
sentiment_analysis(input="./result/分词结果/超话-中文分词.pickle",
                   output="./result/整体文档/情感分析/超话-情感分析")
sentiment_analysis(input="./result/分词结果/社区外-中文分词.pickle",
                   output="./result/整体文档/情感分析/社区外-情感分析")
# %%
# *************************************************************************
# ***                       每日分析                                     ***
# *************************************************************************
# %%
# 统计词频
create_folder("./result/每日分析")
create_folder("./result/每日分析/统计词频")
community_tokens = pd.read_pickle("./result/分词结果/超话-中文分词.pickle")
tags_tokens = pd.read_pickle("./result/分词结果/社区外-中文分词.pickle")
dates_com = sorted(list(set(community_tokens['date'].tolist())))
dates_tag = sorted(list(set(tags_tokens['date'].tolist())))
for d1,d2 in zip(dates_com, dates_tag):
    temp_date_community = community_tokens[community_tokens['date'] == d1]
    # 超话内——所有词
    freq_date_community = count_word(input_pickle=temp_date_community, column='中文分词',
                                     output='./result/每日分析/统计词频/超话-每日词频-' + d1)
    # 超话内——所有实词
    nva_date_community = count_word(input_pickle=temp_date_community, column='名动形',
                                    output='./result/每日分析/统计词频/超话-每日词频-名动形-' + d1)
    temp_date_tags = tags_tokens[tags_tokens['date'] == d2]
    # 超话外——所有词
    freq_date_tags = count_word(input_pickle=temp_date_tags, column='中文分词',
                                output='./result/每日分析/统计词频/社区外-每日词频-' + d2)
    # 超话外——所有实词
    nva_date_tags = count_word(input_pickle=temp_date_tags, column='名动形',
                               output='./result/每日分析/统计词频/社区外-每日词频-名动形-' + d2)
# %%
# 计算tf-idf
# word_tfidf(input_pickle,input_freq,input_nva,output):
# input_pickle:包含分词结果的pickle文件
# input_freq：统计词频中的所有词的词频xlsx文件
# input_nva：统计词频中的实词的词频xlsx文件
# output：输出的文件名
create_folder("./result/每日分析/计算tf-idf")
community_tokens = pd.read_pickle("./result/分词结果/超话-中文分词.pickle")
tags_tokens = pd.read_pickle("./result/分词结果/社区外-中文分词.pickle")
dates_com = sorted(list(set(community_tokens['date'].tolist())))
dates_tag = sorted(list(set(tags_tokens['date'].tolist())))
for d1,d2 in zip(dates_com, dates_tag):
    temp_date_community = community_tokens[community_tokens['date'] == d1]
    word_tfidf(input_pickle=temp_date_community,
               input_freq='./result/每日分析/统计词频/超话-每日词频-' + d1 + '.xlsx',
               input_nva='./result/每日分析/统计词频/超话-每日词频-名动形-' + d1 + '.xlsx',
               output="./result/每日分析/计算tf-idf/超话-" + d1 + "-tf-idf")
    temp_date_tags = tags_tokens[tags_tokens['date'] == d2]
    word_tfidf(input_pickle=temp_date_tags,
               input_freq='./result/每日分析/统计词频/社区外-每日词频-' + d2 + '.xlsx',
               input_nva='./result/每日分析/统计词频/社区外-每日词频-名动形-' + d2 + '.xlsx',
               output="./result/每日分析/计算tf-idf/社区外-" + d2 + "-tf-idf")
# %%
# 计算热词贡献率
# keyword_contriution(input_pickle,read_token,nva,token_col,output):
# input_pickle:包含分词结果的pickle文件
# read_token:统计词频的xlsx文件
# "freq"——所有词的高频词；"nva"——所有实词的高频词；"tfidf"——所有词中tfidf中较高；"nva_tfidf"——所有实词中tfidf中较高；
# nva:''——所有词；"nva"——实词的高频词
# token_col:"freq"——简单词频；'tfidf'——权重
# threshold：选择前threshold（百分比）的词语
# output：保存的文件名称
create_folder("./result/每日分析/热词贡献统计")
create_folder("./result/每日分析/热词贡献统计/社区内")
create_folder("./result/每日分析/热词贡献统计/社区外")
community_tokens = pd.read_pickle("./result/分词结果/超话-中文分词.pickle")
tags_tokens = pd.read_pickle("./result/分词结果/社区外-中文分词.pickle")
dates_com = sorted(list(set(community_tokens['date'].tolist())))
dates_tag = sorted(list(set(tags_tokens['date'].tolist())))
for d1,d2 in zip(dates_com, dates_tag):
    temp_date_community = community_tokens[community_tokens['date'] == d1]
    # 社区内：简单词频的贡献率
    keyword_contriution(input_pickle=temp_date_community,
                        read_token='./result/每日分析/统计词频/超话-每日词频-' + d1 + '.xlsx',
                        nva='',
                        token_col='freq',
                        output="result/每日分析/热词贡献统计/社区内/" + d1 + "-")
    keyword_contriution(input_pickle=temp_date_community,
                        read_token='./result/每日分析/统计词频/超话-每日词频-名动形-' + d1 + '.xlsx',
                        nva='名动形',
                        token_col='freq',
                        output="result/每日分析/热词贡献统计/社区内/" + d1 + "-")
    # 社区外：简单词频的贡献率
    temp_date_tags = tags_tokens[tags_tokens['date'] == d2]
    keyword_contriution(input_pickle=temp_date_tags,
                        read_token='./result/每日分析/统计词频/社区外-每日词频-' + d2 + '.xlsx',
                        nva='',
                        token_col='freq',
                        output="result/每日分析/热词贡献统计/社区外/" + d2 + "-")
    keyword_contriution(input_pickle=temp_date_tags,
                        read_token='./result/每日分析/统计词频/社区外-每日词频-名动形-' + d2 + '.xlsx',
                        nva='名动形',
                        token_col='freq',
                        output="result/每日分析/热词贡献统计/社区外/" + d2 + "-")
# %%
for d1,d2 in zip(dates_com, dates_tag):
    temp_date_community = community_tokens[community_tokens['date'] == d1]
    #  社区内：tfidf的贡献率 
    keyword_contriution(input_pickle=temp_date_community,
                        read_token="./result/每日分析/计算tf-idf/超话-" + d1 + "-tf-idf.xlsx",
                        nva='',
                        token_col='tfidf',
                        output="result/每日分析/热词贡献统计/社区内/" + d1 + "-")
    keyword_contriution(input_pickle=temp_date_community,
                        read_token="./result/每日分析/计算tf-idf/超话-" + d1 + "-tf-idf-名动形.xlsx",
                        nva='名动形',
                        token_col='tfidf',
                        output="result/每日分析/热词贡献统计/社区内/" + d1 + "-")
    #  社区外：tfidf的贡献率
    temp_date_tags = tags_tokens[tags_tokens['date'] == d2]
    keyword_contriution(input_pickle=temp_date_tags,
                        read_token="./result/每日分析/计算tf-idf/社区外-" + d2 + "-tf-idf.xlsx",
                        nva='',
                        token_col='tfidf',
                        output="result/每日分析/热词贡献统计/社区外/" + d2 + "-")
    keyword_contriution(input_pickle=temp_date_tags,
                        read_token="./result/每日分析/计算tf-idf/社区外-" + d2 + "-tf-idf-名动形.xlsx",
                        nva='名动形',
                        token_col='tfidf',
                        output="result/每日分析/热词贡献统计/社区外/" + d2 + "-")
# %%
# 计算相关词
# calculate_co_currence(input_pickle,keywords, output, column="中文分词", keywords_num=20,min_df=10, cos=0.15):
# input_pickle:包含分词结果的pickle文件
# keywords:想要查看的高频词；输入的是统计词频中的xlsx文件
# output：保存的文件名称，输出两种文件：txt文件用于存储所有词的相关性；xlsx文件只包含高频词的相关性
create_folder("./result/每日分析/相关词")
community_tokens = pd.read_pickle("./result/分词结果/超话-中文分词.pickle")
tags_tokens = pd.read_pickle("./result/分词结果/社区外-中文分词.pickle")
dates_com = sorted(list(set(community_tokens['date'].tolist())))
dates_tag = sorted(list(set(tags_tokens['date'].tolist())))
for d1,d2 in zip(dates_com, dates_tag):
    create_folder("./result/每日分析/相关词/" + d1)
    temp_date_community = community_tokens[community_tokens['date'] == d1]
    calculate_co_currence(input_pickle=temp_date_community,
                          keywords="result/每日分析/热词贡献统计/社区内/" + d1 + "-" + "中文热词_freq__0.05.xlsx",
                          output="./result/每日分析/相关词/" + d1 + "/超话-0.05高频词的相关词-" + d1)
    calculate_co_currence(input_pickle=temp_date_community,
                          keywords="result/每日分析/热词贡献统计/社区内/" + d1 + "-" + "中文热词_freq_名动形_0.05.xlsx",
                          output="./result/每日分析/相关词/" + d1 + "/超话-0.05高频词的相关词-名动形-" + d1,
                          column='名动形')

    temp_date_tags = tags_tokens[tags_tokens['date'] == d2]
    calculate_co_currence(input_pickle=temp_date_tags,
                          keywords="result/每日分析/热词贡献统计/社区外/" + d2 + "-" + "中文热词_freq__0.05.xlsx",
                          output="./result/每日分析/相关词/" + d1 + "/社区外-0.05高频词的相关词-" + d2)
    calculate_co_currence(input_pickle=temp_date_tags,
                          keywords="result/每日分析/热词贡献统计/社区外/" + d2 + "-" + "中文热词_freq_名动形_0.05.xlsx",
                          output="./result/每日分析/相关词/" + d1 + "/社区外-0.05高频词的相关词-名动形-" + d2,
                          column='名动形')
# %%
# *************************************************************************
# ***                  含有假唱关键词及其相关词的分析                       ***
# *************************************************************************
# %% 建立结果文件夹
base_path_lip_syncing = "./result/假唱关键词的分析"
create_folder(base_path_lip_syncing)
wordfreq_path_lip_syncing = os.path.join(base_path_lip_syncing,"统计词频")
create_folder(wordfreq_path_lip_syncing)
heatmap_path_lip_syncing = os.path.join(base_path_lip_syncing,"时间词频热图")
create_folder(heatmap_path_lip_syncing)
tfidf_path_lip_syncing = os.path.join(base_path_lip_syncing,"计算tf-idf")
create_folder(tfidf_path_lip_syncing)
# %% 筛选出含有假唱关键词的帖子
# 筛选出只含有关键词的帖子
def contain_keyword(df, kw, column='中文分词'):
    try:
        df = pd.read_pickle(df)
    except:
        df = df

    def is_contain_keyword(ls):
        for k in kw:
            if k in ls:
                return True
        return False

    # print("previous:",df.shape)
    df['中文分词-list'] = df[column].map(lambda lt: [word[0] for word in lt])
    df['contain_keyword'] = df['中文分词-list'].map(is_contain_keyword)
    df = df[df['contain_keyword'] == True]
    # print("now:",df.shape)
    return df

community_kw = ['假唱','真唱','垫音']
community_df = contain_keyword("result/分词结果/超话-中文分词.pickle",community_kw)
# 社区外-名动形
tags_kw = ['假唱','五月天','演唱会','真唱','质疑','没有','真的','歌手','现场','演出','鉴定','行为']
tags_df = contain_keyword("result/分词结果/社区外-中文分词.pickle",tags_kw)
# %% 统计词频
count_word(input_pickle=community_df, column='中文分词',
           output=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-整体词频'))
count_word(input_pickle=community_df, column='名动形', output=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-名动形'))
count_word(input_pickle=tags_df, column='中文分词', output=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-整体词频'))
count_word(input_pickle=tags_df, column='名动形', output=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-名动形'))
# %% 绘制热图
draw_heatmap(community_df,
             os.path.join(wordfreq_path_lip_syncing,'超话-关键词-名动形.xlsx'),
             os.path.join(heatmap_path_lip_syncing,'超话-关键词-名动形'))
draw_heatmap(tags_df,
             os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-名动形.xlsx'),
             os.path.join(heatmap_path_lip_syncing,'社区外-关键词-名动形'))
# %% 计算tf-idf
word_tfidf(input_pickle=community_df,
           input_freq=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_lip_syncing,"超话-关键词-tfidf"))
word_tfidf(input_pickle=tags_df,
           input_freq=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_lip_syncing,"社区外-关键词-tfidf"))
# %% 计算热词贡献率
wordcontribution_lip_syncing = os.path.join(base_path_lip_syncing,"热词贡献统计")
com_wordcontribution_lip_syncing = os.path.join(wordcontribution_lip_syncing,"社区内")
tags_wordcontribution_lip_syncing = os.path.join(wordcontribution_lip_syncing,"社区外")
create_folder(wordcontribution_lip_syncing)
create_folder(com_wordcontribution_lip_syncing)
create_folder(tags_wordcontribution_lip_syncing)
# %% 社区内：简单词频的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=com_wordcontribution_lip_syncing+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_lip_syncing,'超话-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=com_wordcontribution_lip_syncing+"/")
# %% 社区外：简单词频的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=tags_wordcontribution_lip_syncing+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_lip_syncing,'社区外-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=tags_wordcontribution_lip_syncing+"/")
# %% 社区内：tfidf的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_lip_syncing,'超话-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=com_wordcontribution_lip_syncing+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_lip_syncing,'超话-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=com_wordcontribution_lip_syncing+"/")
# %% 社区外：tfidf的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_lip_syncing,'社区外-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=tags_wordcontribution_lip_syncing+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_lip_syncing,'社区外-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=tags_wordcontribution_lip_syncing+"/")
# %% 计算相关词
coword_lip_syncing = os.path.join(base_path_lip_syncing,"相关词")
create_folder(coword_lip_syncing)
# %%
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_lip_syncing,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_lip_syncing,"超话-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_lip_syncing,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_lip_syncing,"超话-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
# %%
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_lip_syncing,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_lip_syncing,"社区外-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_lip_syncing,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_lip_syncing,"社区外-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
# %%画相关词的树图
tree_lip_syncing = os.path.join(base_path_lip_syncing,"树图")
create_folder(tree_lip_syncing)
draw_tree(edge_file="result/假唱关键词的分析/相关词/超话-0.05高频词的相关词-关键词-名动形.txt",
          word='假唱', max_dist=3,n_top=5,
          output=tree_lip_syncing+'/'+"超话-假唱关键词-名动形-1")
draw_tree(edge_file="result/假唱关键词的分析/相关词/社区外-0.05高频词的相关词-关键词-名动形.txt",
          word='假唱', max_dist=3,n_top=5,
          output=tree_lip_syncing+'/'+"社区外-假唱关键词-名动形-1")
# %%
# *************************************************************************
# ***                  含有五月天关键词及其相关词的分析                     ***
# *************************************************************************
# %% 建立结果文件夹
base_path_mayday = "./result/五月天关键词的分析"
create_folder(base_path_mayday)
wordfreq_path_mayday = os.path.join(base_path_mayday,"统计词频")
create_folder(wordfreq_path_mayday)
heatmap_path_mayday = os.path.join(base_path_mayday,"时间词频热图")
create_folder(heatmap_path_mayday)
tfidf_path_mayday = os.path.join(base_path_mayday,"计算tf-idf")
create_folder(tfidf_path_mayday)
# %% 筛选出含有五月天关键词的帖子
# 筛选出只含有关键词的帖子
def contain_keyword(df, kw, column='中文分词'):
    try:
        df = pd.read_pickle(df)
    except:
        df = df

    def is_contain_keyword(ls):
        for k in kw:
            if k in ls:
                return True
        return False

    # print("previous:",df.shape)
    df['中文分词-list'] = df[column].map(lambda lt: [word[0] for word in lt])
    df['contain_keyword'] = df['中文分词-list'].map(is_contain_keyword)
    df = df[df['contain_keyword'] == True]
    # print("now:",df.shape)
    return df

community_kw = ['五月天','身边', '站在', '全世界', '没有', '永远', '80岁', '唱到', '记得', '一起', '演唱会']
community_df = contain_keyword("result/分词结果/超话-中文分词.pickle",community_kw)
# 社区外-名动形
tags_kw = ['五月天','假唱', '演唱会', '质疑', '近日', '进行', '风波', '上海', '网友', '现场']
tags_df = contain_keyword("result/分词结果/社区外-中文分词.pickle",tags_kw)
# %% 统计词频
count_word(input_pickle=community_df, column='中文分词',
           output=os.path.join(wordfreq_path_mayday,'超话-关键词-整体词频'))
count_word(input_pickle=community_df, column='名动形', output=os.path.join(wordfreq_path_mayday,'超话-关键词-名动形'))
count_word(input_pickle=tags_df, column='中文分词', output=os.path.join(wordfreq_path_mayday,'社区外-关键词-整体词频'))
count_word(input_pickle=tags_df, column='名动形', output=os.path.join(wordfreq_path_mayday,'社区外-关键词-名动形'))
# %% 绘制热图
draw_heatmap(community_df,
             os.path.join(wordfreq_path_mayday,'超话-关键词-名动形.xlsx'),
             os.path.join(heatmap_path_mayday,'超话-关键词-名动形'))
draw_heatmap(tags_df,
             os.path.join(wordfreq_path_mayday,'社区外-关键词-名动形.xlsx'),
             os.path.join(heatmap_path_mayday,'社区外-关键词-名动形'))
# %% 计算tf-idf
word_tfidf(input_pickle=community_df,
           input_freq=os.path.join(wordfreq_path_mayday,'超话-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_mayday,'超话-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_mayday,"超话-关键词-tfidf"))
word_tfidf(input_pickle=tags_df,
           input_freq=os.path.join(wordfreq_path_mayday,'社区外-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_mayday,'社区外-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_mayday,"社区外-关键词-tfidf"))
# %% 计算热词贡献率
wordcontribution_mayday = os.path.join(base_path_mayday,"热词贡献统计")
com_wordcontribution_mayday = os.path.join(wordcontribution_mayday,"社区内")
tags_wordcontribution_mayday = os.path.join(wordcontribution_mayday,"社区外")
create_folder(wordcontribution_mayday)
create_folder(com_wordcontribution_mayday)
create_folder(tags_wordcontribution_mayday)
# %% 社区内：简单词频的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_mayday,'超话-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=com_wordcontribution_mayday+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_mayday,'超话-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=com_wordcontribution_mayday+"/")
# %% 社区外：简单词频的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_mayday,'社区外-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=tags_wordcontribution_mayday+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_mayday,'社区外-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=tags_wordcontribution_mayday+"/")
# %% 社区内：tfidf的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_mayday,'超话-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=com_wordcontribution_mayday+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_mayday,'超话-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=com_wordcontribution_mayday+"/")
# %% 社区外：tfidf的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_mayday,'社区外-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=tags_wordcontribution_mayday+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_mayday,'社区外-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=tags_wordcontribution_mayday+"/")
# %% 计算相关词
coword_mayday = os.path.join(base_path_mayday,"相关词")
create_folder(coword_mayday)
# %%
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_mayday,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_mayday,"超话-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_mayday,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_mayday,"超话-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
# %%
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_mayday,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_mayday,"社区外-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_mayday,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_mayday,"社区外-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
#%% 画树图
tree_mayday = os.path.join(base_path_mayday,"树图")
create_folder(tree_mayday)
draw_tree(edge_file=os.path.join(coword_mayday,"超话-0.05高频词的相关词-关键词.txt"),word='五月天',max_dist=3,n_top=10,output=os.path.join(tree_mayday,"超话-0.05高频词的相关词-关键词"))
draw_tree(edge_file=os.path.join(coword_mayday,"社区外-0.05高频词的相关词-关键词.txt"),word='五月天',max_dist=3,n_top=5,output=os.path.join(tree_mayday,"社区外-0.05高频词的相关词-关键词"))
# %%
# *************************************************************************
# ***                   含有真唱关键词及其相关词的分析                      ***
# *************************************************************************
# %% 建立结果文件夹
base_path_real = "./result/真唱关键词的分析"
create_folder(base_path_real)
wordfreq_path_real = os.path.join(base_path_real,"统计词频")
create_folder(wordfreq_path_real)
heatmap_path_real = os.path.join(base_path_real,"时间词频热图")
create_folder(heatmap_path_real)
tfidf_path_real = os.path.join(base_path_real,"计算tf-idf")
create_folder(tfidf_path_real)
# %% 筛选出含有真唱关键词的帖子
# 筛选出只含有关键词的帖子
def contain_keyword(df, kw, column='中文分词'):
    try:
        df = pd.read_pickle(df)
    except:
        df = df

    def is_contain_keyword(ls):
        for k in kw:
            if k in ls:
                return True
        return False

    # print("previous:",df.shape)
    df['中文分词-list'] = df[column].map(lambda lt: [word[0] for word in lt])
    df['contain_keyword'] = df['中文分词-list'].map(is_contain_keyword)
    df = df[df['contain_keyword'] == True]
    # print("now:",df.shape)
    return df

community_kw = ['真唱','假唱']
community_df = contain_keyword("result/分词结果/超话-中文分词.pickle",community_kw)
# 社区外-名动形
tags_kw = ['真唱','假唱', '演唱会']
tags_df = contain_keyword("result/分词结果/社区外-中文分词.pickle",tags_kw)
# %% 统计词频
count_word(input_pickle=community_df, column='中文分词',
           output=os.path.join(wordfreq_path_real,'超话-关键词-整体词频'))
count_word(input_pickle=community_df, column='名动形', output=os.path.join(wordfreq_path_real,'超话-关键词-名动形'))
count_word(input_pickle=tags_df, column='中文分词', output=os.path.join(wordfreq_path_real,'社区外-关键词-整体词频'))
count_word(input_pickle=tags_df, column='名动形', output=os.path.join(wordfreq_path_real,'社区外-关键词-名动形'))
# %% 计算tf-idf
word_tfidf(input_pickle=community_df,
           input_freq=os.path.join(wordfreq_path_real,'超话-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_real,'超话-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_real,"超话-关键词-tfidf"))
word_tfidf(input_pickle=tags_df,
           input_freq=os.path.join(wordfreq_path_real,'社区外-关键词-整体词频.xlsx'),
           input_nva=os.path.join(wordfreq_path_real,'社区外-关键词-名动形.xlsx'),
           output=os.path.join(tfidf_path_real,"社区外-关键词-tfidf"))
# %% 绘制热图
draw_heatmap(community_df,
             os.path.join(tfidf_path_real,'超话-关键词-tfidf-名动形.xlsx'),
             os.path.join(heatmap_path_real,'超话-关键词-tfidf-名动形'))
draw_heatmap(tags_df,
             os.path.join(tfidf_path_real,'社区外-关键词-tfidf-名动形.xlsx'),
             os.path.join(heatmap_path_real,'社区外-关键词-tfidf-名动形'))
# %% 计算热词贡献率
wordcontribution_real = os.path.join(base_path_real,"热词贡献统计")
com_wordcontribution_real = os.path.join(wordcontribution_real,"社区内")
tags_wordcontribution_real = os.path.join(wordcontribution_real,"社区外")
create_folder(wordcontribution_real)
create_folder(com_wordcontribution_real)
create_folder(tags_wordcontribution_real)
# %% 社区内：简单词频的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_real,'超话-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=com_wordcontribution_real+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(wordfreq_path_real,'超话-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=com_wordcontribution_real+"/")
# %% 社区外：简单词频的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_real,'社区外-关键词-整体词频.xlsx'),
                    nva='',
                    token_col='freq',
                    output=tags_wordcontribution_real+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(wordfreq_path_real,'社区外-关键词-名动形.xlsx'),
                    nva='名动形',
                    token_col='freq',
                    output=tags_wordcontribution_real+"/")
# %% 社区内：tfidf的贡献率
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_real,'超话-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=com_wordcontribution_real+"/")
keyword_contriution(input_pickle=community_df,
                    read_token=os.path.join(tfidf_path_real,'超话-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=com_wordcontribution_real+"/")
# %% 社区外：tfidf的贡献率
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_real,'社区外-关键词-tfidf.xlsx'),
                    nva='',
                    token_col='tfidf',
                    output=tags_wordcontribution_real+"/")
keyword_contriution(input_pickle=tags_df,
                    read_token=os.path.join(tfidf_path_real,'社区外-关键词-tfidf-名动形.xlsx'),
                    nva='名动形',
                    token_col='tfidf',
                    output=tags_wordcontribution_real+"/")
# %% 计算相关词
coword_real = os.path.join(base_path_real,"相关词")
create_folder(coword_real)
# %%
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_real,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_real,"超话-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=community_df,
                      keywords=os.path.join(com_wordcontribution_real,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_real,"超话-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
# %%
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_real,"中文热词_freq__0.05.xlsx"),
                      output=os.path.join(coword_real,"社区外-0.05高频词的相关词-关键词"))
calculate_co_currence(input_pickle=tags_df,
                      keywords=os.path.join(tags_wordcontribution_real,"中文热词_freq_名动形_0.05.xlsx"),
                      output=os.path.join(coword_real,"社区外-0.05高频词的相关词-关键词-名动形"),
                      column='名动形')
#%% 画树图
tree_real = os.path.join(base_path_real,"树图")
create_folder(tree_real)
draw_tree(edge_file=os.path.join(coword_real,"超话-0.05高频词的相关词-关键词.txt"),
          word='真唱',max_dist=3,n_top=5,
          output=os.path.join(tree_real,"超话-0.05高频词的相关词-关键词-1"))
draw_tree(edge_file=os.path.join(coword_real,"社区外-0.05高频词的相关词-关键词.txt"),
          word='真唱',max_dist=3,n_top=5,
          output=os.path.join(tree_real,"社区外-0.05高频词的相关词-关键词-1"))