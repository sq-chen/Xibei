"""爬虫脚本与仓库根目录 crawled_data、本目录下 cookie 的路径。"""
import os

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CRAWLER_DIR)
CRAWLED_DIR = os.path.join(REPO_ROOT, "crawled_data")
COOKIE_FILE = os.path.join(CRAWLER_DIR, "cookie.json")


def ensure_crawled_dir():
    os.makedirs(CRAWLED_DIR, exist_ok=True)


def crawled_path(filename: str) -> str:
    """crawled_data 下的文件绝对路径。"""
    return os.path.join(CRAWLED_DIR, filename)
