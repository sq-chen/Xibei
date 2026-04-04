from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
from collections import defaultdict
import re


driver = webdriver.Chrome()  # 启动浏览器
driver.set_window_size(100, 800)
base_url = ("https://s.weibo.com/topic?q=%E8%A5%BF%E8%B4%9D&pagetype=topic&topic=1&Refer=topic_topic&page=")
regex = re.compile("(\d+)")
page = 0
result = defaultdict(list)
#while True:
while page < 10:
    page += 1
    try:
        url = base_url + str(page)
        driver.get(url)  # 打开网页
        # 读取cookie的json文件
        f = open('cookie.json', 'r')
        listCookie = json.loads(f.read())  # 读取文件中的cookies数据
        # 将cookie塞到浏览器中，绕过登录
        for cookie in listCookie:
            driver.add_cookie(cookie)

        driver.refresh()
        driver.get(url)
        time.sleep(3)
        #scroll_page(driver)

        infos = driver.find_elements(By.CLASS_NAME, "info")
        for f in infos:
            tag_name = f.find_element(By.TAG_NAME,'a').text
            tag_link = f.find_element(By.TAG_NAME,'a').get_attribute('href')
            tag_data = f.find_elements(By.TAG_NAME,'p')[1].text    #读取讨论量数据
            result['tag'].append(tag_name)
            result['link'].append(tag_link)
            result['data'].append(tag_data)
        print(page, ": finished")
    except:
        break


result = pd.DataFrame(result)
result.to_excel("西贝话题.xlsx")
driver.close()