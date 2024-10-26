#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#   Copyright (C) 2024. Suto-Commune
#   _
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#   _
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#   _
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
@File       : twi.py

@Author     : hsn

@Date       : 2024/8/11 下午8:47
"""

import asyncio
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from playwright.async_api import async_playwright, Response
from twitter.scraper import Scraper


def get_tweet_info_login(url: str):
    s = Scraper(cookies=c)
    j = s.tweets_by_ids([int(url.split("/")[-1])])[0]

    user_name = (
        j.get("data")
        .get("tweetResult")[0]
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("name")
    )
    # /data/tweetResult/result/legacy/entities/media
    medias = (
        j.get("data")
        .get("tweetResult")[0]
        .get("result")
        .get("legacy")
        .get("entities")
        .get("media")
    )
    # /data/tweetResult/result/note_tweet/note_tweet_results/result/text
    note_tweet = (
        j.get("data", {})
        .get("tweetResult", {})[0]
        .get("result", {})
        .get("note_tweet", {})
        .get("note_tweet_results", {})
        .get("result", {})
        .get("text", {})
    )

    # /data/tweetResult/result/legacy/full_text
    full_text: str = (
        j.get("data").get("tweetResult")[0].get("result").get("legacy").get("full_text")
    )
    if note_tweet:
        context = note_tweet
    else:
        context = full_text[: full_text.rfind("https://t.co/")]
    # /data/tweetResult/result/core/user_results/result/legacy/screen_name
    user_id = (
        j.get("data")
        .get("tweetResult")[0]
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("screen_name")
    )
    # /data/tweetResult/result/core/user_results/result/legacy/profile_image_url_https
    user_avatar_url: str = (
        j.get("data")
        .get("tweetResult")[0]
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("profile_image_url_https")
    )
    user_avatar_url = user_avatar_url.replace("_normal.jpg", ".jpg")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
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
    time_ctime = (
        j.get("data")
        .get("tweetResult")[0]
        .get("result")
        .get("legacy")
        .get("created_at")
    )
    t = datetime.strptime(time_ctime, "%a %b %d %H:%M:%S %z %Y")

    return user_name, user_id, user_avatar, context, medias, t


async def get_tweet_info_playwright(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        res = []

        async def handle_response(response: Response):
            if response.url.find("TweetResultByRestId") != -1:
                res.append(await response.json())
            # print(f"Response Status: {response.status}")
            # print(f"Response Headers: {response.headers}")
            # print(f"Response Body: {await response.body()}")

        page.on("response", handle_response)
        await page.goto(url)
        for i in range(50):
            if res:
                break
            await asyncio.sleep(0.1)
        await browser.close()
    if not res:
        raise Exception("No data found")
    j = res[0]
    user_name = (
        j.get("data")
        .get("tweetResult")
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("name")
    )
    # /data/tweetResult/result/legacy/entities/media
    medias = (
        j.get("data")
        .get("tweetResult")
        .get("result")
        .get("legacy")
        .get("entities")
        .get("media")
    )
    # /data/tweetResult/result/note_tweet/note_tweet_results/result/text
    note_tweet = (
        j.get("data", {})
        .get("tweetResult", {})
        .get("result", {})
        .get("note_tweet", {})
        .get("note_tweet_results", {})
        .get("result", {})
        .get("text", {})
    )

    # /data/tweetResult/result/legacy/full_text
    full_text: str = (
        j.get("data").get("tweetResult").get("result").get("legacy").get("full_text")
    )
    if note_tweet:
        context = note_tweet
    else:
        context = full_text[: full_text.rfind("https://t.co/")]
    # /data/tweetResult/result/core/user_results/result/legacy/screen_name
    user_id = (
        j.get("data")
        .get("tweetResult")
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("screen_name")
    )
    # /data/tweetResult/result/core/user_results/result/legacy/profile_image_url_https
    user_avatar_url: str = (
        j.get("data")
        .get("tweetResult")
        .get("result")
        .get("core")
        .get("user_results")
        .get("result")
        .get("legacy")
        .get("profile_image_url_https")
    )
    user_avatar_url = user_avatar_url.replace("_normal.jpg", ".jpg")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
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
    time_ctime = (
        j.get("data").get("tweetResult").get("result").get("legacy").get("created_at")
    )
    t = datetime.strptime(time_ctime, "%a %b %d %H:%M:%S %z %Y")

    return user_name, user_id, user_avatar, context, medias, t


def get_tweet_info(url: str):
    return asyncio.run(get_tweet_info_playwright(url))


async def test():
    print(await get_tweet_info_playwright(
        "https://x.com/kuroikage1732/status/1844928238713463071?t=Z-ln6KL9jiWJT9ETDZHmcQ&s=19"
    ))


if __name__ == "__main__":
    asyncio.run(
        test()
    )
