from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
import random
from collections import defaultdict
import re

from crawler_paths import COOKIE_FILE, crawled_path, ensure_crawled_dir

def scroll_page(driver):
    time.sleep(1)
    page_len = driver.execute_script("return document.body.scrollHeight;") #获取页面的长度
    for t in range(1,20):
        js1 = "window.scrollTo(0," + str(page_len/2) + ")"
        driver.execute_script(js1) # 滑动到页面一半处
        time.sleep(1)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)") #滑到底部
        time.sleep(2)
        temp = driver.execute_script("return document.body.scrollHeight;") #获取此时的页面的长度
        if temp > page_len:
            page_len = temp #如果此时的页面长度大于最初的，继续循环，知道滑动到页面底部
        elif temp == page_len:
            break    #如果此时的页面长度等于最初的，说明已滑动到页面底部
    return page_len

#西贝道歉话题（末尾必须是 &page=，页码由下面 page 与循环里的 str(p) 拼接，不要写成 &page=6）
base_url = "https://s.weibo.com/weibo?q=%23%E8%A5%BF%E8%B4%9D%E9%81%93%E6%AD%89%23&page="
# 话题；注意加上&page=
#base_url = "https://s.weibo.com/weibo?q=%23%E4%BA%94%E6%9C%88%E5%A4%A9%E5%81%87%E5%94%B1%23&page="
######################page：需要查找要抓取的时间范围在超话中的第几页######################
page = 50
ensure_crawled_dir()
result = defaultdict(list)
driver = webdriver.Chrome()  # 启动浏览器
driver.set_window_size(600, 800)
for p in range(page,0,-1):
    url = base_url + str(p)
    try:
        driver.get(url)  # 打开网页
        # 读取cookie的json文件
        f = open(COOKIE_FILE, "r", encoding="utf-8")
        listCookie = json.loads(f.read())  # 读取文件中的cookies数据
        # 将cookie塞到浏览器中，绕过登录
        for cookie in listCookie:
            driver.add_cookie(cookie)
        driver.refresh()
        driver.get(url)
    except: #以防第一次插入cookie不成功，再重新加载cookie
        driver.get(url)  # 打开网页
        # 读取cookie的json文件
        f = open(COOKIE_FILE, "r", encoding="utf-8")
        listCookie = json.loads(f.read())  # 读取文件中的cookies数据
        # 将cookie塞到浏览器中，绕过登录
        for cookie in listCookie:
            driver.add_cookie(cookie)
        driver.refresh()
        driver.get(url)

    page_len = scroll_page(driver) #滚动页面，使当前页面中的帖子都加载出来


    # 如果是超话中的帖子
    # feeds = driver.find_elements(By.CLASS_NAME,"WB_feed_detail.clearfix") #查找每个帖子
    feeds = driver.find_elements(By.CLASS_NAME,"card-feed")
    for f in feeds:
        # f = f.find_element(By.CLASS_NAME,"WB_detail").find_element(By.CLASS_NAME,"WB_from.S_txt2")
        # date = f.find_element(By.TAG_NAME,'a').get_attribute('title')  #抓取发帖时间
        # url = f.find_element(By.TAG_NAME,'a').get_attribute('href') #抓取帖子url
        # 如果是超话中的帖子
        f = f.find_element(By.CLASS_NAME,"from")
        date = f.find_element(By.TAG_NAME,'a').get_attribute('innerText')  #抓取发帖时间
        url = f.find_element(By.TAG_NAME,'a').get_attribute('href') #抓取帖子url
        result['date'].append(date)
        result['url'].append(url)

    print("帖子页数：", p, ": finished", page_len)

    time.sleep(random.randint(3, 5))
driver.close()

result = pd.DataFrame(result)
#result[['date','url']].to_excel(r"西贝超话url.xlsx")
result[['date','url']].to_excel(crawled_path("xibei_topic_urls.xlsx"))