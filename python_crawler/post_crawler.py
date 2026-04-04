from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import json
import pandas as pd
from collections import defaultdict
import re
import traceback
import urllib.error
import urllib.request
import xlsxwriter

WEIBO_ORIGIN = "https://weibo.com"
# 帖子页偶发加载失败 / 选择器未就绪时，刷新并重新打开
MAX_POST_PAGE_RETRIES = 4
MAX_EXTRA_BLOCK_RETRIES = 3


def normalize_post_url(post_url: str) -> str:
    """去掉 #comment、#attitude 等 fragment。带 hash 打开时常落在评论/点赞视图，正文 article 可能不完整。"""
    u = (post_url or "").strip()
    if not u:
        return u
    return u.split("#")[0].rstrip("/")


def open_weibo_post(driver, url, wait_extra=0):
    driver.get(WEIBO_ORIGIN)
    time.sleep(0.8)
    inject_cookies(driver)
    driver.get(normalize_post_url(url))
    time.sleep(3 + wait_extra)


def inject_cookies(driver):
    """在 weibo.com 域下页面调用；跳过域名不匹配或格式无效的 cookie，避免 InvalidCookieDomain 中断。"""
    try:
        with open("cookie.json", "r", encoding="utf-8") as f:
            cookies = json.loads(f.read())
    except FileNotFoundError:
        return
    for c in cookies:
        try:
            c = dict(c)
            if "expiry" in c:
                c["expiry"] = int(float(c["expiry"]))
            driver.add_cookie(c)
        except Exception:
            continue


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


def _find_nickname_el(driver):
    """蓝 V / 视频号等模板 class 哈希可能不同，失败时在 article 内找用户主页链。"""
    try:
        return driver.find_element(By.CLASS_NAME, "_body_m3n8j_63").find_element(
            By.CLASS_NAME, "_default_fvu9w_3"
        )
    except NoSuchElementException:
        article = driver.find_element(By.TAG_NAME, "article")
        return article.find_element(
            By.XPATH,
            ".//a[contains(@href,'weibo.com/u/') or contains(@href,'weibo.com/n/')][1]",
        )


def _find_time_el(driver):
    try:
        return driver.find_element(By.CLASS_NAME, "_time_1tpft_33")
    except NoSuchElementException:
        article = driver.find_element(By.TAG_NAME, "article")
        return article.find_element(By.XPATH, ".//*[contains(@class,'_time_')][1]")


def _find_ip_el(driver):
    """部分模板不展示 IP 属地，找不到时返回 None。"""
    try:
        return driver.find_element(By.CLASS_NAME, "_ip_1tpft_41")
    except NoSuchElementException:
        pass
    try:
        article = driver.find_element(By.TAG_NAME, "article")
        return article.find_element(By.XPATH, ".//*[contains(@class,'_ip_')][1]")
    except NoSuchElementException:
        pass
    try:
        article = driver.find_element(By.TAG_NAME, "article")
        return article.find_element(
            By.XPATH,
            ".//*[contains(normalize-space(text()),'发布于')][1]",
        )
    except NoSuchElementException:
        return None


def _find_text_root(driver):
    try:
        return driver.find_element(By.CLASS_NAME, "_wbtext_q1l14_14")
    except NoSuchElementException:
        article = driver.find_element(By.TAG_NAME, "article")
        return article.find_element(By.XPATH, ".//*[contains(@class,'_wbtext_')][1]")


def _post_bid_from_url(post_url: str):
    """详情页 URL 最后一节为 bid，如 .../1718259005/Q4cjFlaHD"""
    base = post_url.split("#")[0].split("?")[0].rstrip("/")
    seg = base.split("/")[-1]
    if seg and re.match(r"^[A-Za-z0-9]+$", seg):
        return seg
    return None


def _cookie_header_from_json():
    try:
        with open("cookie.json", "r", encoding="utf-8") as f:
            cookies = json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return ""
    parts = []
    for c in cookies:
        if not isinstance(c, dict):
            continue
        n, v = c.get("name"), c.get("value")
        if n and v is not None:
            parts.append(f"{n}={v}")
    return "; ".join(parts)


def fetch_status_show_ajax(bid: str, referer=None):
    """
    与 weibo-search-master 中 get_ip() 相同接口：
    https://weibo.com/ajax/statuses/show?id={bid}&locale=zh-CN
    返回 JSON（含 region_name、user、text 等），不依赖详情页前端 class。
    """
    cookie = _cookie_header_from_json()
    if not cookie:
        return None
    api = f"https://weibo.com/ajax/statuses/show?id={bid}&locale=zh-CN"
    ref = referer if referer else "https://weibo.com/"
    req = urllib.request.Request(
        api,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Cookie": cookie,
            "Referer": ref,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("ok") == 0:
        return None
    return data


def enrich_info_from_ajax(post_url, info):
    """页面 DOM 因红/蓝 V 等模板不一致失败时，用 Ajax 补昵称、正文、IP 等。"""
    base = normalize_post_url(post_url)
    bid = _post_bid_from_url(post_url)
    if not bid:
        return
    root = fetch_status_show_ajax(bid, referer=base)
    if not root:
        return
    body = root.get("data") if isinstance(root.get("data"), dict) else root
    if not isinstance(body, dict):
        return

    region = (body.get("region_name") or "").strip()
    if region:
        tail = region.split()[-1]
        cur_ip = (info.get("ip") or "").strip()
        if not cur_ip or cur_ip == "none":
            info["ip"] = f"发布于 {tail}"

    user = body.get("user")
    if isinstance(user, dict):
        sn = (user.get("screen_name") or user.get("name") or "").strip()
        if sn:
            cur_n = (info.get("name") or "").strip()
            if not cur_n or cur_n == "none":
                info["name"] = sn
        uid = user.get("id")
        if uid:
            cur_l = (info.get("link") or "").strip()
            if not cur_l or cur_l == "none":
                info["link"] = f"https://weibo.com/u/{uid}"

    raw_text = body.get("text_long") or body.get("text") or ""
    if raw_text:
        plain = re.sub(r"<[^>]+>", " ", str(raw_text))
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            cur_p = (info.get("post") or "").strip()
            # 视频号等：页面只抓到超话卡片一句，接口常有完整正文
            if not cur_p or cur_p == "none" or len(plain) > len(cur_p) + 15:
                info["post"] = plain

    src = (body.get("source") or "").strip()
    if src and (not info.get("service") or info.get("service") == "none"):
        info["service"] = f"来自 {src}" if not str(src).startswith("来自") else src

    uid_merge = None
    if isinstance(user, dict):
        uid_merge = user.get("id") or user.get("idstr")
    if bid and uid_merge:
        canon = f"https://weibo.com/{uid_merge}/{bid}"
        cur_u = (info.get("url") or "").strip()
        if not cur_u or cur_u == "none" or "visitor" in cur_u.lower():
            info["url"] = canon


def precise_scratch(url,driver,file_name):
    global count
    count += 1
    base_url = normalize_post_url(url)
    for attempt in range(1, MAX_POST_PAGE_RETRIES + 1):
        open_weibo_post(driver, base_url, wait_extra=attempt - 1)
        info = defaultdict(list)
        try:
            time.sleep(1)
            # 抓取基本信息：昵称、url、日期、ip地址、设备端名称
            nick_name = _find_nickname_el(driver)
            info["name"] = nick_name.get_attribute("aria-label") or (
                nick_name.get_attribute("textContent") or ""
            ).strip()
            info["link"] = nick_name.get_attribute("href")
            #print(nick_name.get_attribute("text"))
            url_info = _find_time_el(driver)
            info["url"] = url_info.get_attribute("href")
            info["date"] = url_info.get_attribute("textContent")
            #print(url_info.get_attribute("href"))
            #print(url_info.get_attribute("text"))
            ip_el = _find_ip_el(driver)
            info["ip"] = (
                ip_el.get_attribute("textContent").strip() if ip_el is not None else "none"
            )
            #print(ip.get_attribute("textContent"))
            try:
                service = driver.find_element(By.CLASS_NAME,"_cut_1tpft_29._source_1tpft_46")
                info['service'] = service.get_attribute("textContent").strip()
            except:
                info['service'] = "none"
            #print(service.get_attribute("textContent"))
            # 抓取超话名称、tag名称、emoji名称、视频链接
            text_root = _find_text_root(driver)
            ctev = text_root.find_elements(By.XPATH, "./*")
            community = []
            tag = []
            emoji = []
            video_num = 0
            other = []
            text_outerhtml = text_root.get_attribute("outerHTML").replace("<br>", "\n")
            emoji_in_post = text_outerhtml

            def _consume_link(a_el):
                nonlocal emoji_in_post, video_num
                t_html = a_el.get_attribute("href") or ""
                t_txt = (a_el.get_attribute("textContent") or "").strip()
                if not t_txt:
                    for img_el in a_el.find_elements(By.TAG_NAME, "img"):
                        t_txt = (
                            img_el.get_attribute("title")
                            or img_el.get_attribute("alt")
                            or ""
                        ).strip()
                        if t_txt:
                            break
                if not t_txt:
                    t_txt = (a_el.get_attribute("innerText") or "").strip()
                if not t_txt:
                    return
                if t_html.startswith("https://weibo.com/p/"):
                    community.append(t_txt)
                elif t_html.startswith("https://s.weibo.com/weibo?q="):
                    tag.append(a_el.get_attribute("text") or t_txt)
                elif t_html.startswith("https://video.weibo.com/show"):
                    video_num += 1
                else:
                    other.append(t_txt)
                emoji_in_post = emoji_in_post.replace(a_el.get_attribute("outerHTML") or "", "")

            if not ctev:
                # 仅超话链接等：有时没有直接子元素节点，./* 为空，改用全文与所有 a
                for a_el in text_root.find_elements(By.XPATH, ".//a"):
                    _consume_link(a_el)
                for img_el in text_root.find_elements(By.TAG_NAME, "img"):
                    tit = img_el.get_attribute("title")
                    if tit:
                        emoji.append(tit)
                    emoji_in_post = emoji_in_post.replace(img_el.get_attribute("outerHTML") or "", "")
                raw_post = (text_root.get_attribute("innerText") or text_root.get_attribute("textContent") or "").strip()
                info["post"] = raw_post
                info["emoji_in_post"] = emoji_in_post.strip()
            else:
                for t in ctev:
                    tn = (t.tag_name or "").lower()
                    if tn == "a":
                        tc = (t.get_attribute("textContent") or "").strip()
                        if tc or t.find_elements(By.TAG_NAME, "img"):
                            _consume_link(t)
                    elif tn == "img":
                        tit = t.get_attribute("title")
                        if tit:
                            emoji.append(tit)
                        emoji_in_post = emoji_in_post.replace(
                            t.get_attribute("outerHTML") or "", ""
                        )

                    t_outerhtml = t.get_attribute("outerHTML")
                    text_outerhtml = text_outerhtml.replace(t_outerhtml, "")

                node_regex = re.compile("(<.+?>)")
                drop = node_regex.findall(text_outerhtml)
                for ss in drop:
                    text_outerhtml = text_outerhtml.replace(ss, "")
                info["post"] = text_outerhtml.strip()
                info["emoji_in_post"] = emoji_in_post.strip()

            if not (info.get("post") or "").strip() and community:
                info["post"] = " ".join(community)

            info['video_num'] = video_num
            info['community'] = " ".join(community)
            info['tag'] = " ".join(tag)
            info['emoji'] = " ".join(emoji)
            info['other'] = " ".join(other)

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

            #抓取评论、点赞、分享数（短文/仅超话时 footer 按钮可能少于 3 个）
            article_el = driver.find_element(By.TAG_NAME, "article")
            footers = article_el.find_elements(By.TAG_NAME, "footer")
            if not footers:
                info["share"] = "转发"
                info["comment"] = "评论"
                info["like"] = "赞"
            else:
                footer_el = footers[0] if len(footers) == 1 else footers[1]
                btns = footer_el.find_elements(
                    By.CLASS_NAME,
                    "woo-box-item-flex._item_198pe_23._cursor_198pe_184",
                )
                if len(btns) >= 3:
                    info["share"] = btns[0].get_attribute("textContent").strip()
                    info["comment"] = btns[1].get_attribute("textContent").strip()
                    info["like"] = btns[2].get_attribute("textContent").strip()
                elif len(btns) == 2:
                    info["share"] = btns[0].get_attribute("textContent").strip()
                    info["comment"] = btns[1].get_attribute("textContent").strip()
                    info["like"] = "赞"
                elif len(btns) == 1:
                    info["share"] = btns[0].get_attribute("textContent").strip()
                    info["comment"] = "评论"
                    info["like"] = "赞"
                else:
                    info["share"] = "转发"
                    info["comment"] = "评论"
                    info["like"] = "赞"
        except Exception as error:
            traceback.print_exc()
            print(count + 1, " - ", base_url, f" : 正文解析失败，重试 {attempt}/{MAX_POST_PAGE_RETRIES}")
            if attempt < MAX_POST_PAGE_RETRIES:
                try:
                    driver.refresh()
                    time.sleep(2 + attempt)
                except Exception:
                    pass
            if attempt == MAX_POST_PAGE_RETRIES:
                if len(info['name']) == 0:
                    info['name'] = "none"
                info["url"] = base_url
                if len(info['date']) == 0:
                    info['date'] = "none"
                if len(info['ip']) == 0:
                    info['ip'] = "none"
                if len(info['service']) == 0:
                    info['service'] = "none"
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
                print(count + 1, " - ", base_url, " : 正文解析已达最大重试")
        else:
            break

    for extra_attempt in range(1, MAX_EXTRA_BLOCK_RETRIES + 1):
        try:
            article_height = driver.find_element(By.TAG_NAME,"article").get_attribute("scrollHeight")
            scroll_height = int(article_height)

            if info['like'] != '赞':
                attitude_url = base_url + "#attitude"
                driver.get(WEIBO_ORIGIN)
                time.sleep(0.5)
                inject_cookies(driver)
                driver.get(attitude_url)
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
                share_url = base_url + "#repost"
                driver.execute_script("window.scrollTo(0,0)")
                time.sleep(1)
                driver.get(WEIBO_ORIGIN)
                time.sleep(0.5)
                inject_cookies(driver)
                driver.get(share_url)
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
                comment_url = base_url + "#comment"
                driver.execute_script("window.scrollTo(0,0)")
                time.sleep(1)
                driver.get(WEIBO_ORIGIN)
                time.sleep(0.5)
                inject_cookies(driver)
                driver.get(comment_url)
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
            traceback.print_exc()
            print(
                count + 1,
                " - ",
                base_url,
                f" : 点赞/转发/评论块失败，重试 {extra_attempt}/{MAX_EXTRA_BLOCK_RETRIES}",
            )
            if extra_attempt < MAX_EXTRA_BLOCK_RETRIES:
                open_weibo_post(driver, base_url, wait_extra=extra_attempt)
                time.sleep(1)
            else:
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
        else:
            break

    enrich_info_from_ajax(base_url, info)

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
    print(count + 1, " - ", base_url, " : finished")


count = -1

if __name__ == "__main__":
    driver = webdriver.Chrome()  # 启动浏览器
    driver.set_window_size(600, 1000)
    file_name = "西贝超话帖子"
    df = pd.read_excel("西贝超话url.xlsx")
    # 勿用 [1:]：会丢掉 Excel 里第一行数据；逐条 try 避免一条报错后整表中断
    for _url in df["url"].dropna().tolist():
        try:
            precise_scratch(_url, driver=driver, file_name=file_name)
        except Exception as e:
            print("本条跳过（未捕获异常）: ", _url, e)
            traceback.print_exc()

    driver.close()