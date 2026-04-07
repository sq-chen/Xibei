"""路径约定：exploratory_data/ 为套件根（与 text_analyse/ 同级）；其下 data/、crawled_data/；result/ 在 text_analyse/。"""
import os

# 本文件位于 text_analyse/
TEXT_ANALYSE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEXT_ANALYSE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CRAWLED_DIR = os.path.join(PROJECT_ROOT, "crawled_data")

# 兼容旧代码：原 ROOT 即 text_analyse 目录
ROOT = TEXT_ANALYSE_DIR


def join(*parts):
    """相对 text_analyse（如 result/整体文档/...）。"""
    return os.path.normpath(os.path.join(TEXT_ANALYSE_DIR, *parts))


def data_join(*parts):
    """相对套件根下 data/（词典、停用词等）。"""
    return os.path.normpath(os.path.join(DATA_DIR, *parts))


def crawled_join(*parts):
    """相对套件根下 crawled_data/（爬虫产出的 xlsx、txt）。"""
    return os.path.normpath(os.path.join(CRAWLED_DIR, *parts))


def resolve(path: str) -> str:
    """相对路径解析：result/ → text_analyse；data/、crawled_data/ → 套件根；其它 → 套件根。"""
    if not path:
        return path
    if os.path.isabs(path):
        return os.path.normpath(path)
    rel = path.replace("\\", "/").strip()
    if rel.startswith("./"):
        rel = rel[2:]
    parts = [p for p in rel.split("/") if p and p != "."]
    if not parts:
        return TEXT_ANALYSE_DIR
    head = parts[0].lower()
    if head == "result":
        return os.path.normpath(os.path.join(TEXT_ANALYSE_DIR, *parts))
    if head in ("data", "crawled_data"):
        return os.path.normpath(os.path.join(PROJECT_ROOT, *parts))
    return os.path.normpath(os.path.join(PROJECT_ROOT, *parts))
