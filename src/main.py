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
@File       : main.py

@Author     : hsn

@Date       : 2024/7/31 下午1:12
"""
import json
import shutil
import tomllib
from argparse import ArgumentParser
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
import requests
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from twitter.scraper import Scraper

from src.rander.text import TextBox, Text, Font


def get_tweet_info_login(url: str):
    c = {
        "ct0": "8f78c81df8b8ff75884c01e42ab587eb015255b3fa6ad4371a057794a8539d4725c737d5c533e4bdfeedaa97e4340b4c3ca5a91020696f7f14710fb839f3e2b5ffb823cae82a8d50a78e634533b078ed",
        "auth_token": "1b127eed37a06327ca9f151021d23ca12d0de28d"}
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
    driver = webdriver.Chrome(options=options)
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


def gen_rounded_mask(radius):
    mask = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
    # draw.ellipse((0, height - radius * 2, radius * 2, height), fill=255)
    # draw.ellipse((width - radius * 2, 0, width, radius * 2), fill=255)
    # draw.ellipse((width - radius * 2, height - radius * 2, width, height), fill=255)
    return mask


def gen_rounded_rectangle_mask(size, raduis):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    width, height = size
    draw.rectangle((raduis, 0, width - raduis, height), fill=255)
    draw.rectangle((0, raduis, width, height - raduis), fill=255)
    draw.ellipse((0, 0, raduis * 2, raduis * 2), fill=255)
    draw.ellipse((0, height - raduis * 2, raduis * 2, height), fill=255)
    draw.ellipse((width - raduis * 2, 0, width, raduis * 2), fill=255)
    draw.ellipse((width - raduis * 2, height - raduis * 2, width, height), fill=255)
    return mask


class Zoomer:
    def __init__(self, base_ratio: float):
        self.base_ratio = base_ratio

    def zoom(self, size):
        return int(size * self.base_ratio)

    def zoom_tuple(self, size: tuple):
        return tuple(map(self.zoom, size))

    def __call__(self, size):
        return self.zoom(size)


def gen_image_twitter(url: str):
    user_name, user_id, user_avatar, context, medias, t = get_tweet_info(url)
    return gen_image(user_name, user_id, user_avatar, context, medias, t,url)


def gen_image(user_name: str, user_id: str, user_avatar: Image, context: str, medias: list, t: datetime,
              source: str = ""):
    print("set zoomer")
    zoomer = Zoomer(0.5)
    base_font_size = zoomer(90)
    font_zoomer = Zoomer(zoomer(90))
    if True:  # The define of fonts. Fold it pls.
        print("set fonts")
        fonts_context = [
            Font(Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf'),
                 size=font_zoomer(1)),
            Font(Path('assets/NotoEmoji-VariableFont_wght.ttf'),
                 size=font_zoomer(1),
                 offset=(0, font_zoomer(20 / 90)))
        ]
        fonts_name = [
            Font(
                Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf'),
                size=font_zoomer(1.2)
            ),
            Font(
                Path('assets/NotoEmoji-VariableFont_wght.ttf'),
                size=font_zoomer(1.2),
                offset=(0, font_zoomer(20 * 1.2 / 90))
            )
        ]
        fonts_id = [
            Font(
                Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Light.otf'),
                size=font_zoomer(0.64)
            ),
        ]

    # To calculate the high of context
    print("set context")
    context_textbox = TextBox(
        text=context,
        fonts=fonts_context,
        max_width=zoomer(1800),
        line_spacing=font_zoomer(1 / 3),
        spacing=font_zoomer(1 / 7)
    )

    # Init image
    print("init image")
    img = Image.new('RGB', (zoomer(2000), int(context_textbox.high) + zoomer(900)), (255, 255, 255))
    # img.paste(user_avatar.resize((300, 300)), (100, 100), mask=gen_rounded_mask(5000).resize((300, 300)))
    print("paste avatar")
    img.paste(user_avatar.resize((zoomer(300), zoomer(300))), (zoomer(100), zoomer(100)),
              mask=gen_rounded_rectangle_mask((5000, 5000), 1000).resize((zoomer(300), zoomer(300))))
    draw = ImageDraw.Draw(img)

    user_info_x = zoomer(460)  # Base x of user info

    # Draw username
    print("draw username")
    Text(text=user_name, fonts=fonts_name).draw(draw, (user_info_x, zoomer(135)), (0, 0, 0))
    # Draw user id
    print("draw user id")
    Text(f'@{user_id}', fonts_id).draw(draw, (user_info_x, zoomer(135) + font_zoomer(1.5)), (128, 128, 128))

    # Draw context
    print("draw context")
    context_textbox.draw(draw, zoomer(100), zoomer(500))
    Text(t.strftime("%I:%M %p · %b %d, %y"), fonts_id).draw(draw, (zoomer(100), context_textbox.high + zoomer(700)),
                                                            (128, 128, 128))
    print("draw qr")
    if source:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        # 如果想扫描二维码后跳转到网页，需要添加https://
        qr.add_data(source)
        qrc = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
        img.paste(qrc.resize((zoomer(300), zoomer(300))), (zoomer(1600), int(context_textbox.high) + zoomer(550)))
    print("mask")
    img_rt = Image.new('RGBA', img.size, (255, 255, 255, 0))
    x, y = img.size
    img_rt.paste(img, (0, 0), mask=gen_rounded_rectangle_mask((x * 5, y * 5), zoomer(300)).resize((x, y)))
    print("return")
    return img_rt


#
# def main():
#     # print(get_tweet_info('https://x.com/Cldeop/status/1818310350112182313'))
#     # print(gen_image('https://x.com/boiledwater/status/1818074624799785134'))
#     # gen_image('https://x.com/tuan_xiaowu/status/1813225555573239851')
#     # gen_image('https://x.com/yqua_/status/1798916338104340988')
#     gen_image('https://x.com/B_cat38324/status/1821884768029663303').save('bcat.png')
#     gen_image('https://x.com/HANLIANYI331/status/1799144853785256427').save('temp.png')
#     gen_image('https://x.com/boiledwater/status/1818074624799785134').save('temp4.png')
#     gen_image('https://x.com/POTUS/status/1819058362698400016').save('temp2.png')
#     gen_image('https://x.com/HANLIANYI331/status/1790585954220298420').save('temp1.png')
#
#     gen_image('https://x.com/Cldeop/status/1818310350112182313').save('temp3.png')
config = {}

def main():
#     gen_image("hsn","hsn8086",Image.open(Path("photo_2023-05-26_21-13-12.jpg")),"""
# 方法一：修改 /etc/rc.d/rc.local 文件
#     """,[],datetime.now())
    gen_image_twitter('https://x.com/B_cat38324/status/1821884768029663303').save('bcat_q.png')
    gen_image_twitter('https://x.com/HANLIANYI331/status/1799144853785256427').save('temp_q.png')
    gen_image_twitter('https://x.com/boiledwater/status/1818074624799785134').save('temp4_q.png')
    gen_image_twitter('https://x.com/POTUS/status/1819058362698400016').save('temp2_q.png')
    gen_image_twitter('https://x.com/HANLIANYI331/status/1790585954220298420').save('temp1_q.png')

    gen_image_twitter('https://x.com/Cldeop/status/1818310350112182313').save('temp3_q.png')

if __name__ == '__main__':
    # Text('你好😋',
    #     ['assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Medium.otf', 'assets/NotoColorEmoji.ttf'])
    main()
    # gen_rounded_rectangle_mask((1000,1000),300).resize((100,100)).show()
