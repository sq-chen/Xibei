# 西贝单数据源：分词 → 词频/TF-IDF/热图/贡献率/共现 → 情感分析（五月天流水线见 main_mayday.py，勿改）
# 任意工作目录执行: python path/to/main_xibei.py

import os

from paths_config import ROOT, crawled_join, join as P
from _1_数据预处理与分词 import process_data
from _2_统计词频 import count_word
from _4_绘制时间热图 import draw_heatmap
from _5_计算TFIDF import word_tfidf
from _6_计算热词贡献率 import keyword_contriution
from _7_计算高频词的相关词 import calculate_co_currence
from _9_情感分析 import sentiment_analysis


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(path, ": Folder created")
    else:
        print(path, ": Folder already exists")


# 输入：crawled_data/xibei_supertopic_posts.xlsx
INPUT_XLSX = crawled_join("xibei_supertopic_posts.xlsx")
PICKLE = P("result", "xibei", "segmentation", "xibei_supertopic_tokens.pickle")
PREFIX = P("result", "xibei", "overall")
SEG_BASE = P("result", "xibei", "segmentation", "xibei_supertopic_tokens")

if __name__ == "__main__":
    os.chdir(ROOT)
    create_folder(P("result", "xibei", "segmentation"))
    create_folder(os.path.join(PREFIX, "word_freq"))
    create_folder(os.path.join(PREFIX, "tfidf"))
    create_folder(os.path.join(PREFIX, "time_heatmap"))
    create_folder(os.path.join(PREFIX, "keyword_contribution"))
    create_folder(os.path.join(PREFIX, "cowords"))
    create_folder(os.path.join(PREFIX, "sentiment"))

    process_data(INPUT_XLSX, SEG_BASE)

    count_word(
        input_pickle=PICKLE,
        column="中文分词",
        output=os.path.join(PREFIX, "word_freq", "xibei_overall_freq"),
    )
    count_word(
        input_pickle=PICKLE,
        column="名动形",
        output=os.path.join(PREFIX, "word_freq", "xibei_overall_freq_nva"),
    )

    word_tfidf(
        input_pickle=PICKLE,
        input_freq=os.path.join(PREFIX, "word_freq", "xibei_overall_freq.xlsx"),
        input_nva=os.path.join(PREFIX, "word_freq", "xibei_overall_freq_nva.xlsx"),
        output=os.path.join(PREFIX, "tfidf", "xibei_overall_tfidf"),
    )

    draw_heatmap(
        input_pickle=PICKLE,
        input_keyword=os.path.join(PREFIX, "tfidf", "xibei_overall_tfidf-名动形.xlsx"),
        output=os.path.join(PREFIX, "time_heatmap", "xibei_nva_tfidf"),
    )

    kw_dir = os.path.join(PREFIX, "keyword_contribution")
    kw_out = kw_dir + os.sep
    keyword_contriution(
        input_pickle=PICKLE,
        read_token=os.path.join(PREFIX, "word_freq", "xibei_overall_freq.xlsx"),
        nva="",
        token_col="freq",
        output=kw_out,
    )
    keyword_contriution(
        input_pickle=PICKLE,
        read_token=os.path.join(PREFIX, "word_freq", "xibei_overall_freq_nva.xlsx"),
        nva="名动形",
        token_col="freq",
        output=kw_out,
    )
    keyword_contriution(
        input_pickle=PICKLE,
        read_token=os.path.join(PREFIX, "tfidf", "xibei_overall_tfidf.xlsx"),
        nva="",
        token_col="tfidf",
        output=kw_out,
    )
    keyword_contriution(
        input_pickle=PICKLE,
        read_token=os.path.join(PREFIX, "tfidf", "xibei_overall_tfidf-名动形.xlsx"),
        nva="名动形",
        token_col="tfidf",
        output=kw_out,
    )

    calculate_co_currence(
        input_pickle=PICKLE,
        keywords=os.path.join(kw_dir, "中文热词_freq__0.05.xlsx"),
        output=os.path.join(PREFIX, "cowords", "xibei_cowords_freq_005_all"),
    )
    calculate_co_currence(
        input_pickle=PICKLE,
        keywords=os.path.join(kw_dir, "中文热词_freq_名动形_0.05.xlsx"),
        output=os.path.join(PREFIX, "cowords", "xibei_cowords_freq_005_nva"),
        column="名动形",
    )

    sentiment_analysis(
        input=PICKLE,
        output=os.path.join(PREFIX, "sentiment", "xibei_sentiment"),
    )

    print(
        "完成。先看词频表找错误切分：",
        os.path.join(PREFIX, "word_freq", "xibei_overall_freq.xlsx"),
    )
