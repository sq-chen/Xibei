from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
import time
from collections import defaultdict
import pandas as pd
from appium.options.android import UiAutomator2Options

app_parameter = {
    "platformName": "Android",
    "platformVersion": "12",
    "deviceName": "BNE-AL00",
    "appPackage": "com.sina.weibo",
    "appActivity": ".MainTabActivity",
    "ignoreHiddenApp": True,
    "noReset": True
}
count = -1
def collect_info(name):
    global count
    count += 1
    result = defaultdict(list)
    search.send_keys(name)  #输入用户的名称
    driver.press_keycode(66) #回车
    time.sleep(2)
    try:
        user_icon = driver.find_elements(AppiumBy.ID,'com.sina.weibo:id/tvContent')[1] #将搜索结果限定为用户
        user_icon.click() #点击
        time.sleep(2)
        user = driver.find_elements(AppiumBy.XPATH,
                                    """//android.widget.ListView[@resource-id="com.sina.weibo:id/lv_content"]/android.widget.RelativeLayout""")
        if len(user) == 1:
            user = user[0]  #搜索结果只有一个时即为想要查找的用户
        elif len(user) > 1:
            name = str(name).encode('utf-8')  #先将目标用户的名字编码为utf-8
            for t in user:
                get_name = t.find_element(AppiumBy.CLASS_NAME, 'android.widget.TextView').get_attribute('text')  #获取搜索结果的列表
                get_name = str(get_name.strip()).encode('utf-8')  #搜索结果都编码为utf-8
                #print(name, get_name, get_name == name)
                if name == get_name:
                    user = t   #找到目标用户
                    name = name.decode('utf-8')
                    break
                else:
                    continue
        experience = user.find_element(AppiumBy.ANDROID_UIAUTOMATOR, ('textContains("经验值")')).get_attribute(
            'text')  #抓取用户的经验值
        user.click() #点击进入用户的个人主页
        time.sleep(3)
        #driver.save_screenshot(file_name)
        sign_num = driver.find_element(AppiumBy.ID,'com.sina.weibo:id/tv_sign_num').get_attribute('text') #抓取用户的连续签到天数
        post_num = driver.find_element(AppiumBy.ID,'com.sina.weibo:id/tv_post_num').get_attribute('text') #抓取用户的发帖数
        desc_arr = driver.find_elements(AppiumBy.ID,'com.sina.weibo:id/tv_desc')
        rank = desc_arr[0].get_attribute('text') #抓取用户的等级
        join_time = desc_arr[1].get_attribute('text') #抓取用户的加入超话时间
        result['name'].append(name)
        result['sign_num'].append(sign_num)
        result['post_num'].append(post_num)
        result['rank'].append(rank)
        result['experience'].append(experience)
        result['join_time'].append(join_time)
        df_old = pd.read_excel("collect_name.xlsx")
        res = pd.DataFrame(result)
        df_new = pd.concat([df_old, res])
        df_new.to_excel("collect_name.xlsx")
        print(count, '-', name, " : finished")
        driver.find_element(AppiumBy.ID, 'com.sina.weibo:id/imgBack').click()  #返回到搜索
        time.sleep(1)
        search.clear() #清空搜索
        time.sleep(2)
    except:
        print(count,'-',name," : 404")

options = UiAutomator2Options().load_capabilities(app_parameter)
# 打开微博app
driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub",options=options)
time.sleep(10) #在休眠时点开需要爬取的超话
# 获取屏幕尺寸
size = driver.get_window_size()
width = size['width']
height = size['height']
# 计算滑动起始和结束位置
start_x = width / 2
start_y = height * 0.95  # 从底部 80% 的位置开始滑动
end_y = height * 0.05  # 滑动到顶部 20% 的位置
while True:
# 执行滑动操作
    driver.swipe(start_x, start_y, start_x, end_y, duration=1000)  # duration 是滑动时间，单位为毫秒
    # 可选：再滑动一次
    time.sleep(0.5)

"""
driver.find_element(AppiumBy.ACCESSIBILITY_ID,'搜索').click()
time.sleep(5)
search  = driver.find_element(AppiumBy.ID,'com.sina.weibo:id/tv_search_keyword')
file_name = "post_information.xlsx"
df = pd.read_excel(file_name)
df['name'].map(collect_info)
driver.quit()
"""