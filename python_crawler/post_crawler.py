from jedi.api import file_name
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
from collections import defaultdict
import re
import traceback
import xlsxwriter

def scroll_page(scroll_height,driver,option):
    users = []
    try:
        # 获取点赞/评论/分享的用户一栏的节点高度
        user_node_height = driver.find_element(By.CLASS_NAME,"vue-recycle-scroller__item-view").get_attribute("scrollHeight")
    except: #没有用户点赞/评论/分享，就直接返回空列表
        #traceback.print_exc()
        return users
    js = "window.scrollTo(0," + str(scroll_height) + ")"
    driver.execute_script(js) # 滚到只显示点赞/评论/分享列表
    time.sleep(2)
    scroll_position = scroll_height

    page_len = driver.execute_script("return document.body.scrollHeight;") #返回页面高度
    if option == 1:  #查看点赞列表
        for j in range(1,10000):
            #获取点赞的用户节点
            user_names = driver.find_element(By.CLASS_NAME,"vue-recycle-scroller__item-wrapper").find_elements(By.CLASS_NAME,"vue-recycle-scroller__item-view")
            for t in user_names:
                t = t.find_element(By.CLASS_NAME,"text").find_element(By.TAG_NAME,"a")
                name = t.get_attribute("textContent") #抓取用户的昵称
                href = t.get_attribute("href") #抓取用户的微博主页
                name_href = (name,href)
                users.append(name_href)  #将抓取的信息存储到列表users中
            scroll = int(scroll_position) + int(user_node_height) * 12  #此时页面一般会呈现12名赞/评论/分享的用户
            js = "window.scrollTo(0," + str(scroll) + ")"
            scroll_position = scroll
            driver.execute_script(js) #滑动页面
            time.sleep(2)
            temp_len = driver.execute_script("return document.body.scrollHeight;") #获取当前页面的长度
            if temp_len == page_len:  #滚到底部就结束循环
                break
            else:  #还没达到底部就继续
                page_len = temp_len
    elif option == 2:  #查看分享列表
        for j in range(1,10000):
            share_users = driver.find_elements(By.CLASS_NAME,"item1in.woo-box-flex") #获取用户的分享列表
            for t in share_users:
                text = t.find_element(By.CLASS_NAME, "text").get_attribute("outerHTML") #抓取用户的昵称和个人主页
                woo = t.find_element(By.CLASS_NAME,
                                     "info.woo-box-flex.woo-box-alignCenter.woo-box-justifyBetween").find_elements(
                    By.TAG_NAME, "div") #获取分享的时间、ip地址，以及分享内容的点赞数目
                name_link_content = (text, woo[0].get_attribute("textContent"), woo[1].get_attribute("textContent"))
                if name_link_content not in users:
                    users.append(name_link_content)
            scroll = int(scroll_position) + int(user_node_height) * 12
            js = "window.scrollTo(0," + str(scroll) + ")"
            scroll_position = scroll
            driver.execute_script(js)
            time.sleep(2)
            temp_len = driver.execute_script("return document.body.scrollHeight;")
            if temp_len == page_len:
                break
            else:
                page_len = temp_len
    elif option == 3: #查看评论列表
        for j in range(1,10000):
            comment_users = driver.find_elements(By.CLASS_NAME, "item1") #获取评论的用户列表
            for t in comment_users:
                try:
                    text = t.find_element(By.CLASS_NAME, 'text').get_attribute("outerHTML") #获取评论用户的昵称和个人主页连接
                    woo = t.find_element(By.CLASS_NAME,"info.woo-box-flex.woo-box-alignCenter.woo-box-justifyBetween").find_elements(By.TAG_NAME, "div")
                    # 帖子下面的主评论
                    main_comment = (text, woo[0].get_attribute("textContent"), woo[1].get_attribute("textContent"))
                    # 爬取主评论下面的回复
                    try:
                        re_comment = t.find_element(By.CLASS_NAME,"list2")
                        floors = []
                        is_more = re_comment.get_attribute('textContent')
                        if is_more[-3:] != "条回复":  #没有更多回复的情况
                            re_comment = re_comment.find_elements(By.CLASS_NAME,"con2")
                            for r in re_comment:
                                text = r.find_element(By.CLASS_NAME, "text").get_attribute("outerHTML")
                                woo = r.find_element(By.CLASS_NAME,
                                                     "info.woo-box-flex.woo-box-alignCenter.woo-box-justifyBetween").find_elements(
                                    By.TAG_NAME, "div")
                                if (text+"<时间："+woo[0].get_attribute("textContent")+">"+"<点赞："+woo[1].get_attribute("textContent")+">") not in floors:
                                    floors.append(text+"<时间："+woo[0].get_attribute("textContent")+">"+"<点赞："+woo[1].get_attribute("textContent")+">")
                        else:  #有更多回复的情况
                            click_more = re_comment.find_elements(By.CLASS_NAME,"item2")[-1].find_element(By.TAG_NAME,"a")
                            try:
                                click_more.click()
                            except:
                                driver.execute_script("arguments[0].scrollIntoView();", t)
                                click_more.click()

                            time.sleep(2)
                            re_comment = driver.find_element(By.CLASS_NAME,"ReplyModal_scroll3_2kADQ")
                            replies = re_comment.find_elements(By.CLASS_NAME, "con2")
                            for r in replies:
                                text = r.find_element(By.CLASS_NAME, "text").get_attribute("outerHTML")
                                woo = r.find_element(By.CLASS_NAME,
                                                     "info.woo-box-flex.woo-box-alignCenter.woo-box-justifyBetween").find_elements(By.TAG_NAME, "div")
                                if (text + "<时间：" + woo[0].get_attribute("textContent") + ">" + "<点赞：" + woo[1].get_attribute("textContent") + ">") not in floors:
                                    floors.append(
                                        text + "<时间：" + woo[0].get_attribute("textContent") + ">" + "<点赞：" + woo[1].get_attribute("textContent") + ">")
                            win_scroll = 200
                            while True:
                                js = 'document.querySelector(".ReplyModal_scroll3_2kADQ").scrollTo(0,'+ str(win_scroll) + ')'
                                driver.execute_script(js)
                                time.sleep(2)
                                replies = re_comment.find_elements(By.CLASS_NAME, "con2")
                                for r in replies:
                                    text = r.find_element(By.CLASS_NAME, "text").get_attribute("outerHTML")
                                    woo = r.find_element(By.CLASS_NAME,
                                                         "info.woo-box-flex.woo-box-alignCenter.woo-box-justifyBetween").find_elements(
                                        By.TAG_NAME, "div")
                                    if (text + "<时间：" + woo[0].get_attribute("textContent") + ">" + "<" + woo[1].get_attribute(
                                            "textContent") + ">") not in floors:
                                        floors.append(text + "<时间：" + woo[0].get_attribute("textContent") + ">" + "<点赞：" + woo[1].get_attribute("textContent") + ">")
                                win_len = driver.execute_script("return document.querySelector('.ReplyModal_scroll3_2kADQ').scrollHeight;")
                                if win_scroll > int(win_len):
                                    close = driver.find_element(By.CLASS_NAME,"woo-font.woo-font--cross")
                                    close.click()
                                    break
                                win_scroll += 200
                    except Exception as error:
                        #print(error)
                        floors = []

                    under_main_comment = (main_comment,''.join(floors))

                    if under_main_comment not in users:
                        users.append(under_main_comment)
                except:
                    continue
            time.sleep(2)
            scroll = int(scroll_position) + int(user_node_height) * 6
            js = "window.scrollTo(0," + str(scroll) + ")"
            scroll_position = scroll
            driver.execute_script(js)
            time.sleep(2)
            temp_len = driver.execute_script("return document.body.scrollHeight;")
            if temp_len == page_len:
                break
            else:
                page_len = temp_len
    return set(users)

def precise_scratch(url,driver,file_name):
    global count
    count += 1
    try:
        driver.get(url)  # 打开网页
        # 读取cookie的json文件
        f = open('cookie.json', 'r')
        listCookie = json.loads(f.read())  # 读取文件中的cookies数据
        # 将cookie塞到浏览器中，绕过登录
        for cookie in listCookie:
            driver.add_cookie(cookie)
    except:  #以防第一次插入cookie不成功
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
    info = defaultdict(list)
    try:
        time.sleep(1)
        # 抓取基本信息：昵称、url、日期、ip地址、设备端名称
        nick_name = driver.find_element(By.CLASS_NAME,"_body_m3n8j_63").find_element(By.CLASS_NAME,"_default_fvu9w_3")
        info['name'] = nick_name.get_attribute("aria-label")
        info['link'] = nick_name.get_attribute("href")
        #print(nick_name.get_attribute("text"))
        url_info = driver.find_element(By.CLASS_NAME,"_time_1tpft_33")
        info['url'] = url_info.get_attribute("href")
        info['date'] = url_info.get_attribute("textContent")
        #print(url_info.get_attribute("href"))
        #print(url_info.get_attribute("text"))
        ip = driver.find_element(By.CLASS_NAME,"_ip_1tpft_41")
        info['ip'] = ip.get_attribute("textContent").strip()
        #print(ip.get_attribute("textContent"))
        try:
            service = driver.find_element(By.CLASS_NAME,"_cut_1tpft_29._source_1tpft_46")
            info['service'] = service.get_attribute("textContent").strip()
        except:
            info['service'] = "none"
        #print(service.get_attribute("textContent"))
        # 抓取超话名称、tag名称、emoji名称、视频链接
        ctev = driver.find_element(By.CLASS_NAME,"_wbtext_q1l14_14").find_elements(By.XPATH, "./*")
        community = []
        tag = []
        emoji = []
        video_num = 0
        other = []
        #获取帖子的内容
        text_outerhtml = driver.find_element(By.CLASS_NAME,"_wbtext_q1l14_14").get_attribute("outerHTML").replace("<br>", '\n')
        emoji_in_post = text_outerhtml
        #print(text_outerhtml)
        for t in ctev:
            if t.get_attribute("tagName")== "A" and t.get_attribute("textContent") != "":
                t_html = t.get_attribute("href")
                # 提取超话名称
                if t_html.startswith("https://weibo.com/p/"):
                    community.append(t.get_attribute("textContent"))
                # 提取话题名称
                elif t_html.startswith("https://s.weibo.com/weibo?q="):
                    tag.append(t.get_attribute("text"))
                    #print(t.get_attribute("text"))
                # 提取视频链接
                elif t_html.startswith("https://video.weibo.com/show"):
                    video_num += 1
                    #print(video_num)
                # 提取其他连接
                else:
                    other.append(t.get_attribute("textContent"))
                t_outerhtml = t.get_attribute("outerHTML")
                emoji_in_post = emoji_in_post.replace(t_outerhtml, "")
            elif t.get_attribute("tagName")== "IMG":
                emoji.append(t.get_attribute("title"))
                #print(t.get_attribute("title"))

            t_outerhtml = t.get_attribute("outerHTML")
            text_outerhtml = text_outerhtml.replace(t_outerhtml, "")

        info['video_num'] = video_num
        info['community'] = " ".join(community)
        info['tag'] = " ".join(tag)
        info['emoji'] = " ".join(emoji)
        info['other'] = " ".join(other)
        # 获取纯post
        node_regex = re.compile("(<.+?>)")
        drop = node_regex.findall(text_outerhtml)
        for ss in drop:
            text_outerhtml = text_outerhtml.replace(ss,'')
        info['post'] = text_outerhtml.strip()
        info['emoji_in_post'] = emoji_in_post.strip()

        #print(text_outerhtml)

        # 抓取图片/视频/live图的数目
        pic = 0
        live = 0
        video = 0
        try:
            pic_video = driver.find_element(By.CLASS_NAME,"picture._row_a3hty_13")
            pic_video_num = pic_video.find_element(By.TAG_NAME,"div").get_attribute("childElementCount")
            if pic_video.get_attribute("text"):
                live_reg = re.compile("(Live)")
                live = len(live_reg.findall(pic_video.get_attribute("textContent")))
                video_reg = re.compile("(:)")
                video = len(video_reg.findall(pic_video.get_attribute("textContent")))
            pic = int(pic_video_num) - live - video
            info['pic_num'] = pic
            info['live'] = live
            info['video_pic'] = video
        except:
            info['live'] = live
            info['video_pic'] = video
            info['pic_num'] = pic

        try:
            #抓取发帖地址
            site = driver.find_element(By.CLASS_NAME,"_title_iabfd_15._cut_iabfd_21")
            info['site'] = site.get_attribute("textContent").strip()
        except:
            info['site'] = "None"

        #抓取评论、点赞、分享数
        rcl = driver.find_element(By.TAG_NAME,"article").find_elements(By.TAG_NAME,"footer")
        rcl = rcl[0] if len(rcl) == 1 else rcl[1]
        rcl = rcl.find_elements(By.CLASS_NAME,"woo-box-item-flex._item_198pe_23._cursor_198pe_184")
        retweet = rcl[0]
        info['share'] = retweet.get_attribute("textContent").strip()
        comment = rcl[1]
        info['comment'] = comment.get_attribute("textContent").strip()
        like = rcl[2]
        info['like'] = like.get_attribute("textContent").strip()
    except Exception as error:
        traceback.print_exc()
        if len(info['name'])==0: info['name'] = "none"
        info['url'] = url
        if len(info['date'])==0: info['date'] = "none"
        if len(info['ip'])==0: info['ip'] = "none"
        if len(info['service'])==0: info['service'] = "none"
        info['community'] = "none"
        info['tag'] = "none"
        info['emoji'] = "none"
        info['other'] = "none"
        info['emoji_in_post'] = "none"
        info['post'] = "none"
        info['pic_num'] = "none"
        info['live'] = "none"
        info['video_pic'] = "none"
        info['video_num'] = "none"
        info['site'] = "none"
        info['share'] = "none"
        info['comment'] = "none"
        info['like'] = "none"
        print(count,' - ',url," : failed")


    try:
        article_height = driver.find_element(By.TAG_NAME,"article").get_attribute("scrollHeight")
        scroll_height = int(article_height)

        if info['like'] != '赞':
            attitude_url = url + "#attitude"
            driver.get(attitude_url)
            # 读取cookie的json文件
            f = open('cookie.json', 'r')
            listCookie = json.loads(f.read())  # 读取文件中的cookies数据
            # 将cookie塞到浏览器中，绕过登录
            for cookie in listCookie:
                driver.add_cookie(cookie)

            driver.refresh()
            driver.get(attitude_url)
            time.sleep(2)
            likes_users = scroll_page(scroll_height,driver,1)
            info['len_likes'] = len(likes_users)
            print("likes:", info['like'], len(likes_users))
            likes_name = ""
            likes_link = ""
            for t in likes_users:
                likes_name = likes_name + "<" + t[0] +">"
                likes_link = likes_link + "<" + t[1] +">"
            info['likes_name'] = likes_name
            info['likes_link'] = likes_link
        else:
            info['len_likes'] = 0
            info['likes_name'] = 'none'
            info['likes_link'] = 'none'

        is_share = info['share']
        is_comment = info['comment']
        if is_share != "转发":
            share_url = url + "#repost"
            driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1)
            driver.get(share_url)
            # 读取cookie的json文件
            f = open('cookie.json', 'r')
            listCookie = json.loads(f.read())  # 读取文件中的cookies数据
            # 将cookie塞到浏览器中，绕过登录
            for cookie in listCookie:
                driver.add_cookie(cookie)

            driver.refresh()
            driver.get(share_url)
            time.sleep(2)

            share_height = driver.find_element(By.CLASS_NAME,'_mar2_zsq3w_17').get_attribute("scrollHeight")
            scroll_height = scroll_height + int(share_height)
            share_users = scroll_page(scroll_height,driver,2)
            info['len_shares'] = len(share_users)
            print("shares:", is_share, len(share_users))
        else:
            info['shares'] = 0
            info['len_shares'] = 0
            info['share_content'] = 'none'


        comment_content = ""
        under_comment_content = ""
        if is_comment != "评论":
            info['comments'] = is_comment
            comment_url = url + "#comment"
            driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1)
            driver.get(comment_url)
            # 读取cookie的json文件
            f = open('cookie.json', 'r')
            listCookie = json.loads(f.read())  # 读取文件中的cookies数据
            # 将cookie塞到浏览器中，绕过登录
            for cookie in listCookie:
                driver.add_cookie(cookie)

            driver.refresh()
            driver.get(comment_url)
            time.sleep(2)
            share_height = driver.find_element(By.CLASS_NAME,'_mar2_zsq3w_17').get_attribute("scrollHeight")
            scroll_height = scroll_height + int(share_height)
            comment_users = scroll_page(scroll_height,driver,3)
            info['len_comments'] = len(comment_users)
            print("comments:", is_comment, len(comment_users))
            for t in comment_users:
                comment_content = comment_content + str(t[0])
                under_comment_content = under_comment_content + str(t)
        else:
            info['comments'] = 0
            info['len_comments'] = 0
        info['comment_content'] = comment_content
        info['under_comment_content'] = under_comment_content
    except Exception as error:
        traceback.print_exc()  # 打印异常追踪信息
        info['likes'] = ""
        info['len_likes'] = ""
        info['likes_name'] = ""
        info['likes_link'] = ""
        info['shares'] = ""
        info['len_shares'] = ""
        info['share_content'] = ""
        info['comments'] = ""
        info['len_comments'] = ""
        info['comment_content'] = ""
        info['under_comment_content'] = ""

    f = open(file_name + ".txt", "a+", encoding='utf-8')
    f.write(str(info))
    f.write('\n\n\n')
    info = pd.DataFrame(info, index=[0])
    try:
        df_old = pd.read_excel(file_name + ".xlsx")
    except:
        wb = xlsxwriter.Workbook(file_name + ".xlsx")
        sheet = wb.add_worksheet('Sheet1')
        wb.close()
        df_old = pd.read_excel(file_name + ".xlsx")
    df_info = pd.DataFrame(info, index=[0])
    df_new = pd.concat([df_old, df_info])
    df_new[['name', 'url', 'date', 'ip', 'service', 'community', 'tag', 'emoji', 'other',
                     'post', 'emoji_in_post', 'pic_num', 'live', 'video_pic', 'video_num', 'site', 'share',
                     'comment', 'like','len_likes','likes_name','likes_link','len_shares','share_content',
                     'len_comments','comment_content']].to_excel(file_name + ".xlsx")
    print(count, ' - ', url, " : finished")


count = -1
driver = webdriver.Chrome()  # 启动浏览器
driver.set_window_size(600, 1000)
file_name = "五月天超话帖子"
df = pd.read_excel("五月天超话url.xlsx")
df['url'][1:].apply(precise_scratch,driver=driver,file_name=file_name)
driver.close()