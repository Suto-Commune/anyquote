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
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

from src.rander.text import TextBox, Text, Font


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
    resp = requests.get(user_avatar_url, headers=headers,
                        proxies={'http': 'http://localhost:7890', 'https': 'http://localhost:7890'})
    user_avatar_raw = resp.content
    user_avatar = Image.open(BytesIO(user_avatar_raw))
    print(context)
    return user_name, user_id, user_avatar, context, medias


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


def gen_image(url: str):
    user_name, user_id, user_avatar, context, medias = get_tweet_info(url)
    base_size = 90
    if True:  # The define of fonts. Fold it pls.
        fonts_context = [
            Font(Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf'),
                 size=base_size * 1),
            Font(Path('assets/NotoEmoji-VariableFont_wght.ttf'),
                 size=base_size * 1,
                 offset=(0, int(20 * 1)))
        ]
        fonts_name = [
            Font(
                Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf'),
                size=int(base_size * 1.2)
            ),
            Font(
                Path('assets/NotoEmoji-VariableFont_wght.ttf'),
                size=int(base_size * 1.2),
                offset=(0, int(20 * 1.2))
            )
        ]
        fonts_id = [
            Font(
                Path('assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Light.otf'),
                size=int(base_size * 0.64)
            ),
        ]

    # To calculate the high of context
    context_textbox = TextBox(
        text=context,
        fonts=fonts_context,
        max_width=1800,
        line_spacing=int(base_size / 3),
        spacing=int(base_size / 7)
    )

    # Init image
    img = Image.new('RGB', (2000, context_textbox.high + 600), (255, 255, 255))
    # img.paste(user_avatar.resize((300, 300)), (100, 100), mask=gen_rounded_mask(5000).resize((300, 300)))
    img.paste(user_avatar.resize((300, 300)), (100, 100),
              mask=gen_rounded_rectangle_mask((5000, 5000), 1000).resize((300, 300)))
    draw = ImageDraw.Draw(img)

    user_info_x = 460  # Base x of user info

    # Draw username
    Text(text=user_name, fonts=fonts_name).draw(draw, (user_info_x, 135), (0, 0, 0))
    # Draw user id
    Text(f'@{user_id}', fonts_id).draw(draw, (user_info_x, 135 + int(base_size * 1.5)), (128, 128, 128))
    # Draw context
    context_textbox.draw(draw, 100, 500)

    img_rt=Image.new('RGBA',img.size,(255,255,255,255))
    x,y=img.size
    img_rt.paste(img,(0,0),mask=gen_rounded_rectangle_mask((x*5,y*5),300).resize((x,y)))
    return img_rt


def main():
    # print(get_tweet_info('https://x.com/Cldeop/status/1818310350112182313'))
    # print(gen_image('https://x.com/boiledwater/status/1818074624799785134'))
    # gen_image('https://x.com/tuan_xiaowu/status/1813225555573239851')
    # gen_image('https://x.com/yqua_/status/1798916338104340988')
    gen_image('https://x.com/boiledwater/status/1818074624799785134').save('temp4.png')
    gen_image('https://x.com/POTUS/status/1819058362698400016').save('temp2.png')
    gen_image('https://x.com/HANLIANYI331/status/1790585954220298420').save('temp1.png')

    gen_image('https://x.com/Cldeop/status/1818310350112182313').save('temp3.png')



if __name__ == '__main__':
    # Text('你好😋',
    #     ['assets/SourceHanSansSC/OTF/SimplifiedChinese/SourceHanSansSC-Medium.otf', 'assets/NotoColorEmoji.ttf'])
    main()
    # gen_rounded_rectangle_mask((1000,1000),300).resize((100,100)).show()
