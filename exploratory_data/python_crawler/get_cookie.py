import json
import os
import time
from selenium import webdriver

# 始终写入本脚本所在目录，避免从别的文件夹运行时 cookie.json 落到错误位置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_PATH = os.path.join(SCRIPT_DIR, "cookie.json")

browser = webdriver.Chrome()
try:
    browser.get("https://www.weibo.com")
    browser.delete_all_cookies()
    time.sleep(30)  # 人工扫码登录账号
    login_cookies = browser.get_cookies()
    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(login_cookies))
    print(f"已保存 {len(login_cookies)} 条 cookie 到: {COOKIE_PATH}")
finally:
    browser.quit()
