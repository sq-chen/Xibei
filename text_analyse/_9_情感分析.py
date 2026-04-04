# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description:
"""
import os
from codecs import open
import pandas as pd
from loguru import logger
import re
import emoji
#from pysenti import tokenizer
#from pysenti.compat import strdecode
#from pysenti.utils import split_sentence
from collections import defaultdict
import math

pwd_path = os.path.abspath(os.path.dirname(__file__))

# 情感词典
sentiment_dict_path = os.path.join(pwd_path, 'data/情感词典.xlsx')
# 连词词典
conjunction_dict_path = os.path.join(pwd_path, 'data/conjunction_dict.txt')
# 副词词典
adverb_dict_path = os.path.join(pwd_path, 'data/adverb_dict.txt')
# 否定词典
denial_dict_path = os.path.join(pwd_path, 'data/denial_dict.txt')
# 21种情感
emotion_tags =["快乐(PA)","安心(PE)","尊敬(PD)","赞扬(PH)","相信(PG)","喜爱(PB)","祝愿(PK)",
              "愤怒(NNA)","惊奇(PC)",
              "悲伤(NB)","失望(NJ)","疚(NH)","思(PF)",
              "慌(NI)","恐惧(NC)","羞(NG)",
              "烦闷(NE)","憎恶(ND)","贬责(NN)","妒忌(NK)","怀疑(NL)",]

class RuleClassifier:
    def __init__(self):
        self.name = "rule_classifier"
        self.sentiment_dict = pd.DataFrame()
        self.conjunction_dict = {}
        self.adverb_dict = {}
        self.denial_dict = {}
        self.user_sentiment_dict = {}
        self.inited = False

    def init(self, sentiment_dict_path=sentiment_dict_path):
        # 加载情感词典词典
        self.sentiment_dict = self._get_dict(sentiment_dict_path)
        self.conjunction_dict = self._get_dict(conjunction_dict_path)  # 连词
        self.adverb_dict = self._get_dict(adverb_dict_path)  # 副词
        self.denial_dict = self._get_dict(denial_dict_path) #否定词
        self.inited = True
    # 加载用户定义的词典
    def load_user_sentiment_dict(self, path):
        if not self.inited:
            self.init()
        self.user_sentiment_dict = self._get_dict(path)
        self.sentiment_dict = pd.concat([self.sentiment_dict,self.user_sentiment_dict])

    def classify(self, tokens):
        if not self.inited:
            self.init()
        # 情感分析整体数据结构
        result = defaultdict(list)
        #result["score"] = 0
        # 情感分析子句的数据结构
        word_of_bag = self._analyse_clause(tokens)
        # 将子句分析的数据结果添加到整体数据结构中
        #result["score"] += word_of_bag["score"]
        for emotion_tag in emotion_tags:
            result[emotion_tag] = result.get(emotion_tag,0) + word_of_bag[emotion_tag]
        return result

    def _analyse_clause(self, tokens):
        word_of_bag = defaultdict(list)
        #word_of_bag["score"] = 0
        word_of_bag["sentiment"] = []
        word_of_bag["conjunction"] = []
        for emotion_tag in emotion_tags:
            word_of_bag[emotion_tag] = 0
        seg_result = tokens
        # 逐个分析分词
        for word in seg_result:
            # 判断是否是连词
            r = self._is_word_conjunction(word)
            if r:
                word_of_bag["conjunction"].append(r)

            # 判断是否是情感词
            r = self._is_word_sentiment(word, seg_result)
            if r:
                word_of_bag["sentiment"].append(r)
                #word_of_bag["score"] += r["score"]
                for emotion_tag in emotion_tags:
                    word_of_bag[emotion_tag] += r[emotion_tag]
        # 综合连词的情感值
        for a_conjunction in word_of_bag["conjunction"]:
            #word_of_bag["score"] *= a_conjunction["value"]
            for emotion_tag in emotion_tags:
                word_of_bag[emotion_tag] *= a_conjunction["value"]

        return word_of_bag

    def _is_word_conjunction(self, the_word):
        r = defaultdict(list)
        if the_word in self.conjunction_dict:
            r["key"] = the_word
            r["value"] = self.conjunction_dict[the_word]
        return r

    def _is_word_sentiment(self, the_word, seg_result):
        r = defaultdict(list)
        # 判断分词是否在情感词典内
        if the_word in self.sentiment_dict['词语'].tolist():
            # 在情感词典内，则构建一个以情感词为中心的字典数据结构
            site = self.sentiment_dict['词语'].tolist().index(the_word)
            ploarity = self.sentiment_dict['极性'].tolist()[site]
            the_value = self.sentiment_dict['强度'].tolist()[site]
            the_emotion_tag = self.sentiment_dict['情感分类'].tolist()[site]
            index = seg_result.index(the_word)
            #print(the_word, the_value, the_emotion_tag)
            r = self._emotional_word_analysis(the_word, the_value, the_emotion_tag, seg_result, index)
        # 不在情感词典内，则返回空
        return r

    def _emotional_word_analysis(self, core_word, value, tag, segments, index):
        # 在情感词典内，则构建一个以情感词为中心的字典数据结构
        #print(core_word,value,tag)
        orientation = defaultdict(list)
        orientation["key"] = core_word
        orientation["adverb"] = []
        orientation["denial"] = []
        orientation["value"] = value
        orientation_score = value
        # 在三个前视窗内，判断是否有否定词、副词
        view_window = index - 1
        if view_window > -1:  # 无越界
            # 判断前一个词是否是情感词
            if segments[view_window] in self.sentiment_dict['词语'].tolist():
                #orientation["score"] = orientation_score
                for emotion_tag in emotion_tags:
                    if tag != emotion_tag:
                        orientation[emotion_tag] = 0
                    else:
                        orientation[emotion_tag] = orientation_score
                return orientation
            # 判断是否是副词
            if segments[view_window] in self.adverb_dict:
                # 构建副词字典数据结构
                adverb = {"key": segments[view_window], "sentiment": 1,
                          "value": self.adverb_dict[segments[view_window]]}
                orientation["adverb"].append(adverb)
                orientation_score *= self.adverb_dict[segments[view_window]]
            # 判断是否是否定词
            elif segments[view_window] in self.denial_dict:
                # 构建否定词字典数据结构
                denial = {"key": segments[view_window], "sentiment": 1,
                          "value": self.denial_dict[segments[view_window]]}
                orientation["denial"].append(denial)
                orientation_score *= -1
        view_window = index - 2
        if view_window > -1:
            # 判断前一个词是否是情感词
            if segments[view_window] in self.sentiment_dict['词语'].tolist():
                #orientation['score'] = orientation_score
                for emotion_tag in emotion_tags:
                    if tag != emotion_tag:
                        orientation[emotion_tag] = 0
                    else:
                        orientation[emotion_tag] = orientation_score
                return orientation
            if segments[view_window] in self.adverb_dict:
                adverb = {"key": segments[view_window], "sentiment": 2,
                          "value": self.adverb_dict[segments[view_window]]}
                orientation_score *= self.adverb_dict[segments[view_window]]
                orientation["adverb"].insert(0, adverb)
            elif segments[view_window] in self.denial_dict:
                denial = {"key": segments[view_window], "sentiment": 2,
                          "value": self.denial_dict[segments[view_window]]}
                orientation["denial"].insert(0, denial)
                orientation_score *= -1
                # 判断是否是“不是很好”的结构（区别于“很不好”）
                if len(orientation["adverb"]) > 0:
                    # 是，则引入调节阈值，0.3
                    orientation_score *= 0.3
        view_window = index - 3
        if view_window > -1:
            # 判断前一个词是否是情感词
            if segments[view_window] in self.sentiment_dict['词语'].tolist():
                #orientation["score"] = orientation_score
                for emotion_tag in emotion_tags:
                    if tag != emotion_tag:
                        orientation[emotion_tag] = 0
                    else:
                        orientation[emotion_tag] = orientation_score
                return orientation
            if segments[view_window] in self.adverb_dict:
                adverb = {"key": segments[view_window], "sentiment": 3,
                          "value": self.adverb_dict[segments[view_window]]}
                orientation_score *= self.adverb_dict[segments[view_window]]
                orientation["adverb"].insert(0, adverb)
            elif segments[view_window] in self.denial_dict:
                denial = {"key": segments[view_window], "sentiment": 3,
                          "value": self.denial_dict[segments[view_window]]}
                orientation["denial"].insert(0, denial)
                orientation_score *= -1
                # 判断是否是“不是很好”的结构（区别于“很不好”）
                if len(orientation["adverb"]) > 0 and len(orientation["denial"]) == 0:
                    orientation_score *= 0.3
        # 添加情感分析值
        orientation["score"] = orientation_score
        for emotion_tag in emotion_tags:
            if tag != emotion_tag:
                orientation[emotion_tag] = 0
            else:
                orientation[emotion_tag] = orientation_score
        # 返回的数据结构
        return orientation

    @staticmethod
    def _get_dict(path, encoding="utf-8"):
        """
        情感词典的构建
        :param path:
        :param encoding:
        :return:
        """
        if path.endswith(".txt"):
            sentiment_dict = {}
            with open(path, 'r', encoding=encoding) as f:
                c = 0
                for line in f:
                    parts = line.strip().split()
                    c += 1
                    if len(parts) == 2:
                        sentiment_dict[parts[0]] = float(parts[1])
                    else:
                        logger.error(f"num: {c}, {line}")
            return sentiment_dict
        else:
            f = pd.ExcelFile(path)
            sentiment_dict = pd.DataFrame()
            for i in f.sheet_names:
                d = pd.read_excel(path, sheet_name=i,engine='openpyxl')
                d['情感分类'] = d['情感分类'].map(str)
                sentiment_dict = pd.concat([sentiment_dict, d])
            sentiment_dict = sentiment_dict[sentiment_dict['情感分类']!='nan']
            return sentiment_dict


# 正则表达式匹配文字
rule = re.compile("[\w\u4e00-\u9fa5]+")
# 正则表达式匹配emoji
emoji_rule = re.compile("[\U00010000-\U0010ffffa]+")
# 其他一些颜文字
emoji_list = ["ᇂ_ᇂ|||", "ฅ ̳͒•ˑ̫• ̳͒ฅ♡", "ヘ(￣ω￣ヘ)", "x﹏x", "o(╥﹏╥)o",
              "٩(•̤̀ᵕ•̤́๑)ᵒᵏᵎᵎᵎᵎ", "། – _ – །", "✪ω✪", "✧◡✧", "♪٩(´ω`)و♪",
              "→→", "→_→", "⌓‿⌓", "⊙︿⊙", "˘ ³˘", "¯▽¯", "^_^", "＼（〇_ｏ）／",
              "：）", ":)", "(つд`)ノ", "(ﾟДﾟ≡ﾟдﾟ)!?", "(๑•̀ㅁ•́ฅ✧", "(◣_◢)",
              "(>﹏<)", "(｀∀´)Ψ", "(^o^)y", "(*￣3￣)╭♡", " (つД`)ノ"]
# 微博表情
weibo_eomiji_rule = re.compile("(\[.+?\])")


# 将多个emoji分开成一个个
def extract_emojis(text):
    emojis = [c for c in text if c in emoji.EMOJI_DATA]
    return emojis


def creat_sentiment_token(row, column='中文分词', emoji_column='emoji'):
    token_list = []
    for t in row[column]:
        word = t[0]  # 只需要分词的词语部分，去掉词性部分
        # 如果分词中含有(组合)emoji，则一个个拆开
        if len(extract_emojis(word)) != 0:
            emoji_token = extract_emojis(word)
            for emo in emoji_token:
                token_list.append(emo)
        # 颜文字
        elif word in emoji_list:
            token_list.append(word)
        # 普通词语
        elif len(rule.findall(word)) != 0:
            token_list.append(word)
    # 提取微博表情符号
    weibo_emoji = weibo_eomiji_rule.findall(str(row[emoji_column]))
    for weibo in weibo_emoji:
        token_list.append(weibo)
    # 返回包含一个个emoji,颜文字,普通词语的分词集
    return token_list

def cal_sentiment(row):
    sentiment = defaultdict(list)
    others = [t for t in row.index if t not in emotion_tags]
    for other in others:
        sentiment[other].append(row[other])
    happy = row["快乐(PA)"] + row["安心(PE)"]
    good = row["尊敬(PD)"] + row["赞扬(PH)"] + row["相信(PG)"] + row["喜爱(PB)"] + row["祝愿(PK)"]
    anger = row["愤怒(NNA)"]
    sad = row["悲伤(NB)"] + row["失望(NJ)"] + row["疚(NH)"] + row["思(PF)"]
    fear = row["慌(NI)"] + row["恐惧(NC)"] + row["羞(NG)"]
    disgust = row["烦闷(NE)"] + row["憎恶(ND)"] + row["贬责(NN)"] + row["妒忌(NK)"] + row["怀疑(NL)"]
    suprise = row["惊奇(PC)"]

    sentiment["积极"].append(happy + good)
    if row['sentiment_num'] > 0:
        sentiment["积极/词总数"].append((happy + good) / row['sentiment_num'])
        sentiment["积极/根号词总数"].append((happy + good) / math.sqrt(row['sentiment_num']))
    else:
        sentiment["积极/词总数"].append(0)
        sentiment["积极/根号词总数"].append(0)
    sentiment["消极"].append(anger + sad + fear + disgust)
    if row['sentiment_num'] > 0:
        sentiment["消极/词总数"].append((anger + sad + fear + disgust) / row['sentiment_num'])
        sentiment["消极/根号词总数"].append((anger + sad + fear + disgust) / math.sqrt(row['sentiment_num']))
    else:
        sentiment["消极/词总数"].append(0)
        sentiment["消极/根号词总数"].append(0)

    for tag in emotion_tags:
        sentiment[tag].append(row[tag])
    for tag in emotion_tags:
        if row['sentiment_num'] > 0:
            sentiment[tag + '/词总数'].append(row[tag] / row['sentiment_num'])
        else:
            sentiment[tag + '/词总数'].append(0)
    for tag in emotion_tags:
        if row['sentiment_num'] > 0:
            sentiment[tag + '/根号词总数'].append(row[tag] / math.sqrt(row['sentiment_num']))
        else:
            sentiment[tag + '/根号词总数'].append(0)
    sentiment['乐'].append(happy)
    sentiment['好'].append(good)
    sentiment['怒'].append(anger)
    sentiment['哀'].append(sad)
    sentiment['惧'].append(fear)
    sentiment['恶'].append(disgust)
    sentiment['惊'].append(suprise)
    if int(row['sentiment_num']) > 0:
        sentiment['乐/词总数'].append(happy / row['sentiment_num'])
        sentiment['好/词总数'].append(good / row['sentiment_num'])
        sentiment['怒/词总数'].append(anger / row['sentiment_num'])
        sentiment['哀/词总数'].append(sad / row['sentiment_num'])
        sentiment['惧/词总数'].append(fear / row['sentiment_num'])
        sentiment['恶/词总数'].append(disgust / row['sentiment_num'])
        sentiment['惊/词总数'].append(suprise / row['sentiment_num'])
    else:
        sentiment['乐/词总数'].append(0)
        sentiment['好/词总数'].append(0)
        sentiment['怒/词总数'].append(0)
        sentiment['哀/词总数'].append(0)
        sentiment['惧/词总数'].append(0)
        sentiment['恶/词总数'].append(0)
        sentiment['惊/词总数'].append(0)
    if int(row['sentiment_num']) > 0:
        sentiment['乐/根号词总数'].append(happy / math.sqrt(row['sentiment_num']))
        sentiment['好/根号词总数'].append(good / math.sqrt(row['sentiment_num']))
        sentiment['怒/根号词总数'].append(anger / math.sqrt(row['sentiment_num']))
        sentiment['哀/根号词总数'].append(sad / math.sqrt(row['sentiment_num']))
        sentiment['惧/根号词总数'].append(fear / math.sqrt(row['sentiment_num']))
        sentiment['恶/根号词总数'].append(disgust / math.sqrt(row['sentiment_num']))
        sentiment['惊/根号词总数'].append(suprise / math.sqrt(row['sentiment_num']))
    else:
        sentiment['乐/根号词总数'].append(0)
        sentiment['好/根号词总数'].append(0)
        sentiment['怒/根号词总数'].append(0)
        sentiment['哀/根号词总数'].append(0)
        sentiment['惧/根号词总数'].append(0)
        sentiment['恶/根号词总数'].append(0)
        sentiment['惊/根号词总数'].append(0)
    return pd.DataFrame(sentiment)

def sentiment_analysis(input,output):
    try:
        df = pd.read_pickle(input)
    except:
        df = input.copy()
    df['sentiment_token'] = df.apply(creat_sentiment_token, axis=1)
    df['sentiment_num'] = df['sentiment_token'].map(len)
    d = RuleClassifier()
    res = pd.DataFrame()
    for index, row in df.iterrows():
        r = d.classify(row['sentiment_token'])
        r = pd.DataFrame(r, index=[index])
        res = pd.concat([res, r])
    res = pd.concat([df, res], axis=1)
    score = res[['ID', 'sentiment_num'] + emotion_tags].copy()
    score.to_excel(output+"-spss.xlsx")  # 生成每个帖子的21种情感分数

    # 对每种情绪分数进行分数除法
    res_spss = pd.DataFrame()
    for index,row in res.iterrows():
        temp = cal_sentiment(row)
        res_spss = pd.concat([res_spss, temp])
    res_spss.to_excel(output+".xlsx")

"""
sentiment_analysis(input="./result/分词结果/超话-中文分词.pickle",
                   output="./result/整体文档/情感分析/超话-情感分析")
sentiment_analysis(input="./result/分词结果/社区外-中文分词.pickle",
                   output="./result/整体文档/情感分析/社区外-情感分析")
sentiment_analysis(input="./result/分词结果/社区外（包含重复）-中文分词.pickle",
                   output="./result/整体文档/情感分析/社区外（包含重复）-情感分析")
"""
