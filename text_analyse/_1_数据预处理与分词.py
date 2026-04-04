import opencc
import jieba
from jieba import posseg
import regex as re
import pandas as pd
import numpy as np

###将繁体转换为简体
converter = opencc.OpenCC('t2s.json')
def simplified(text):
    if isinstance(text,str):
        return converter.convert(text)
    else: #空白帖子的情况
        return text


# 使用哈工大停止词表
f = open("./data/stopwords.txt",encoding='utf-8')
stopwords = f.readlines()
stopwords = [t.strip('\n') for t in stopwords] # 1661个词

def tokenize(text):
    # 替换一些字符
    text = re.sub("\u200b",'',text)
    text = re.sub("\U0001fa75",'',text)
    text = re.sub("&nbsp;",'',text)
    text = re.sub("&lt;",'',text)
    text = re.sub("&gt;",'',text)
    text = re.sub("小🍠","小红书",text)
    text = re.sub("🍠","小红书",text)
    text = re.sub("🐎","妈",text)
    text = re.sub("🥕","胡萝卜",text)
    text = re.sub("🐶","狗",text)
    text = re.sub("💰","钱",text)
    text = re.sub("🧣","微博",text)
    text = re.sub("🪜","梯子",text)
    text = re.sub("🍎","苹果",text)
    text = re.sub("🦈","杀",text)
    text = re.sub("🐟","娱",text)
    text = re.sub("👻","鬼",text)
    text = re.sub("jio","脚",text)
    text = re.sub("🤡","小丑",text)
    text = re.sub("⭕重","权重",text)
    text = re.sub("⭕ 钱", "圈钱", text)
    text = re.sub("2️⃣0️⃣1️⃣3️⃣", "2013", text)
    text = re.sub("2️⃣0️⃣2️⃣3️⃣", "2023", text)
    text = re.sub("5️⃣g", "5g", text)
    text = re.sub("8️⃣场", "8场", text)
    # 分词的匹配规则：能将一些特殊的表情符号分出来，如 →_→
    posseg.re_han_internal = re.compile("([\u4E00-\u9FD5\U00010000-\U0010ffffa-zA-Z0-9+#&\._\-\W\w% ]+)", re.U)
    # 加载用户分词词典
    jieba.load_userdict('./data/jieba_user_dict.txt')
    return posseg.lcut(text)

def remove_stop(tokens):
    res = []
    for t,flag in tokens:
        # 去掉停止词、换行符、Zero Width Joiner (ZWJ; 通常用于合并或连接多个字符，以创建复合字符或修改字符的显示方式，尤其是在表情符号中)
        # 例如，在某些表情符号中，ZWJ 被用来将多个符号连接成一个单一的复合表情符号，如手势与肤色的组合。
        if t not in stopwords and t !='\n' and t.encode('utf-8')!=b'\xef\xb8\x8f':
            res.append((t,flag))
    return res

# 读取替换字词字典，用于归一化词的说法，如“wmls”和“wm”指代的都是粉丝群体，因此将“wm”替换成“wmls”
replace_words={}
rw = open("./data/replace_words_dict.txt","r",encoding='utf-8')
rule = re.compile("【(.+?)】")
for line in rw:
    line = rule.findall(line)
    replace_words[line[0]]=(line[1],line[2])

# 词语归一化
def replace(lt):
    res = []
    if len(lt)>0: #避免空帖子的情况
        for t, flag in lt:
            if isinstance(t,str):
                if t in replace_words:
                    new_t = replace_words[t][0]
                    new_flag = replace_words[t][1]
                    res.append((new_t,new_flag))
                else:
                    res.append((t,flag))
    return res

# 进行转换为简体、分词、去除停止词、替换词操作
pipeline = [simplified,tokenize,remove_stop,replace]
def prepare(text,pipeline):
    if isinstance(text,str):
        tokens = text.lower()
        for transform in pipeline:
            tokens = transform(tokens)
        return tokens
    else:
        return ''

def process_data(input,output):
    # input：输入的原始数据集
    # output：输出的文件名，会生成xlsx和pickle两种形式的文件，xlsx方便查看，pickle则方便之后其他的操作
    np.random.seed(0)
    # 保留名词、动词、形容词、副词、习语等实词
    nva = ["a","ad","an","d","l","s",
           "n","nr","nrfg","nrt","ns","nt","nw","nz",
           "v","vd","vi","vn","vq"]
    df = pd.read_excel(input)
    df['中文分词'] = df['post'].apply(prepare,pipeline=pipeline)
    df['名动形'] = df['中文分词'].map(lambda ls:[t for t in ls if t[1] in nva])
    df['中文分词数目']=df['中文分词'].map(len)
    df['名动形数目']=df['名动形'].map(len)
    df[['name','ID','url','date','中文分词','名动形','中文分词数目','名动形数目','粉丝','粉丝_百分位','emoji']].to_excel(output+".xlsx")
    df[['name','ID','url','date','中文分词','名动形','中文分词数目','名动形数目','粉丝','粉丝_百分位','emoji']].to_pickle(output+".pickle")
    #return df[['name','ID','url','date','中文分词','名动形','中文分词数目','名动形数目']]