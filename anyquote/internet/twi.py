#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#  Copyright (C) 2023. HCAT-Project-Team
#  _
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  _
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  _
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
@File       : twi.py

@Author     : hsn

@Date       : 2024/8/11 下午8:47
"""
import json
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from chromedriver_py import binary_path
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options
from twitter.scraper import Scraper


def get_tweet_info_login(url: str):
    s = Scraper(cookies=c)
    j = s.tweets_by_ids([int(url.split('/')[-1])])[0]

    user_name = j.get('data').get('tweetResult')[0].get('result').get('core').get('user_results').get('result').get(
        'legacy').get('name')
    # /data/tweetResult/result/legacy/entities/media
    medias = j.get('data').get('tweetResult')[0].get('result').get('legacy').get('entities').get('media')
    # /data/tweetResult/result/note_tweet/note_tweet_results/result/text
    note_tweet = j.get('data', {}).get('tweetResult', {})[0].get('result', {}).get('note_tweet', {}).get(
        'note_tweet_results', {}).get('result', {}).get('text', {})

    # /data/tweetResult/result/legacy/full_text
    full_text: str = j.get('data').get('tweetResult')[0].get('result').get('legacy').get('full_text')
    if note_tweet:
        context = note_tweet
    else:
        context = full_text[:full_text.rfind('https://t.co/')]
    # /data/tweetResult/result/core/user_results/result/legacy/screen_name
    user_id = j.get('data').get('tweetResult')[0].get('result').get('core').get('user_results').get('result').get(
        'legacy').get('screen_name')
    # /data/tweetResult/result/core/user_results/result/legacy/profile_image_url_https
    user_avatar_url: str = j.get('data').get('tweetResult')[0].get('result').get('core').get('user_results').get(
        'result').get(
        'legacy').get('profile_image_url_https')
    user_avatar_url = user_avatar_url.replace('_normal.jpg', '.jpg')
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'
    }
    # req = request.Request("https://pbs.twimg.com/profile_images/1601123559812009984/2vI25CZP_normal.jpg",headers=headers)
    # proxy_host = 'http://localhost:7890'
    # if proxy_host:
    #     req.set_proxy(proxy_host, 'http')
    #
    # response = request.urlopen(req)
    resp = requests.get(user_avatar_url, headers=headers)
    user_avatar_raw = resp.content
    user_avatar = Image.open(BytesIO(user_avatar_raw))

    # /data/tweetResult/result/legacy/created_at
    time_ctime = j.get('data').get('tweetResult')[0].get('result').get('legacy').get('created_at')
    t = datetime.strptime(time_ctime, "%a %b %d %H:%M:%S %z %Y")

    return user_name, user_id, user_avatar, context, medias, t


def get_tweet_info(url: str):
    options = Options()

    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.add_argument("--headless")
    svc = webdriver.ChromeService(binary_path)
    driver = webdriver.Chrome(options=options, service=svc)
    driver.get(url)

    performance_log = driver.get_log("performance")

    for packet in performance_log:
        message = json.loads(packet.get("message")).get("message")
        packet_method = message.get("method")
        if "Network" in packet_method:
            request_id = message.get("params").get("requestId")
            try:
                resp = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                body = resp.get("body")
                j = json.loads(body)
                if 'data' in j:
                    break
            except json.JSONDecodeError:
                pass
            except WebDriverException:
                pass
    else:
        raise Exception("No data found")
    driver.quit()
    # /data/tweetResult/result/core/user_results/result/legacy/name
    user_name = j.get('data').get('tweetResult').get('result').get('core').get('user_results').get('result').get(
        'legacy').get('name')
    # /data/tweetResult/result/legacy/entities/media
    medias = j.get('data').get('tweetResult').get('result').get('legacy').get('entities').get('media')
    # /data/tweetResult/result/note_tweet/note_tweet_results/result/text
    note_tweet = j.get('data', {}).get('tweetResult', {}).get('result', {}).get('note_tweet', {}).get(
        'note_tweet_results', {}).get('result', {}).get('text', {})

    # /data/tweetResult/result/legacy/full_text
    full_text: str = j.get('data').get('tweetResult').get('result').get('legacy').get('full_text')
    if note_tweet:
        context = note_tweet
    else:
        context = full_text[:full_text.rfind('https://t.co/')]
    # /data/tweetResult/result/core/user_results/result/legacy/screen_name
    user_id = j.get('data').get('tweetResult').get('result').get('core').get('user_results').get('result').get(
        'legacy').get('screen_name')
    # /data/tweetResult/result/core/user_results/result/legacy/profile_image_url_https
    user_avatar_url: str = j.get('data').get('tweetResult').get('result').get('core').get('user_results').get(
        'result').get(
        'legacy').get('profile_image_url_https')
    user_avatar_url = user_avatar_url.replace('_normal.jpg', '.jpg')
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'
    }
    # req = request.Request("https://pbs.twimg.com/profile_images/1601123559812009984/2vI25CZP_normal.jpg",headers=headers)
    # proxy_host = 'http://localhost:7890'
    # if proxy_host:
    #     req.set_proxy(proxy_host, 'http')
    #
    # response = request.urlopen(req)
    # resp = requests.get(user_avatar_url, headers=headers,
    #                     proxies={'http': 'http://localhost:7890', 'https': 'http://localhost:7890'})
    resp = requests.get(user_avatar_url, headers=headers)
    user_avatar_raw = resp.content
    user_avatar = Image.open(BytesIO(user_avatar_raw))

    # /data/tweetResult/result/legacy/created_at
    time_ctime = j.get('data').get('tweetResult').get('result').get('legacy').get('created_at')
    t = datetime.strptime(time_ctime, "%a %b %d %H:%M:%S %z %Y")

    return user_name, user_id, user_avatar, context, medias, t
