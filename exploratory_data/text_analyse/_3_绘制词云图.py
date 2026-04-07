from wordcloud import WordCloud
from matplotlib import pyplot as plt
import pandas as pd
import nltk
from collections import Counter
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']

def wordcloud(word_freq,title=None,max_words=150,stopwords=None):
    wc=WordCloud(width=1980,height=1024,font_path='msyh.ttc',background_color="white",colormap="Paired",max_font_size=250,max_words=max_words,prefer_horizontal=1)
    #将DataFrame转换为字典
    if type(word_freq)==pd.Series:
        #实际上运行这个
        counter=Counter(word_freq.fillna(0).to_dict())
    else:
        counter=word_freq
    #在频率计数器中过滤停止词
    if stopwords is not None:
        counter={str(token):freq for (token,freq) in counter.items()
                            if token not in stopwords}
    counter = {str(token): freq for (token, freq) in counter.items()}
    #print(dict(counter))
    wc.generate_from_frequencies(counter)
    plt.title(title)
    plt.imshow(wc,interpolation='bilinear')
    plt.axis("off")
    plt.savefig('brand.png', dpi=1000)
    plt.show()

#freq_df = pd.read_excel("./中文分词/中文分词_整体freq.xlsx")
freq_df = pd.read_excel("huaxin.xlsx",sheet_name="Sheet1")
freq_df.set_index('品牌',inplace=True)
wordcloud(freq_df['freq'], max_words=100)

"""
for t in range(3,10):
    freq_t_df = pd.read_excel("./中文分词/中文分词_freq_date.xlsx",sheet_name=str(t))
    freq_t_df.set_index('token',inplace=True)
    nva_t_df = pd.read_excel("./中文分词/中文分词_freq_date.xlsx",sheet_name=str(t)+"名动形")
    nva_t_df.set_index('token',inplace=True)
    plt.figure()
    wordcloud(freq_t_df['freq'],max_words=100,title=("12月"+str(t)+"日"))
    wordcloud(freq_t_df['freq'],max_words=100,title=("12月"+str(t)+"日"+"-remove_top_50)"),stopwords=freq_df.head(50).index)
    wordcloud(nva_t_df['freq'],max_words=100,title=("12月"+str(t)+"日"+"-名动形"))
"""