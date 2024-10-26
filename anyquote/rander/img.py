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
@File       : img.py

@Author     : hsn

@Date       : 2024/8/11 下午8:48
"""
from datetime import datetime
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

from .text import Font, TextBox, Text
from ..internet.twi import get_tweet_info_playwright


def gen_rounded_mask(radius):
    mask = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
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


from ..font_manager import get_font


def quote(user_name: str, user_avatar: Image, context: str, _time: datetime, user_id: str = "",
          medias: list[Image] = None, source: str = ""):
    medias = medias or []
    zoomer = Zoomer(0.5)
    font_zoomer = Zoomer(zoomer(90))
    if True:  # The define of fonts. Fold it pls.
        import anyquote

        font_regular = get_font("SourceHanSansSC", "Regular")
        font_bold = get_font("SourceHanSansSC", "Bold")
        font_light = get_font("SourceHanSansSC", "Light")
        font_variable = get_font("NotoEmoji-VariableFont")
        fonts_context = [
            Font(font_regular,
                 size=font_zoomer(1)),
            Font(font_variable,
                 size=font_zoomer(1),
                 offset=(0, font_zoomer(8)))
        ]
        fonts_name = [
            Font(
                font_bold,
                size=font_zoomer(1.2)
            ),
            Font(
                font_variable,
                size=font_zoomer(1.2),
                offset=(0, font_zoomer(8 * 1.2))
            )
        ]
        fonts_id = [
            Font(
                font_light,
                size=font_zoomer(0.64)
            ),
        ]

    # To calculate the high of context

    context_textbox = TextBox(
        text=context,
        fonts=fonts_context,
        max_width=zoomer(1800),
        line_spacing=font_zoomer(1 / 3),
        spacing=font_zoomer(1 / 6),
        symbol_push=True
    )

    # Init image

    img = Image.new('RGB', (zoomer(2000), int(context_textbox.high) + zoomer(900)), (255, 255, 255))
    # img.paste(user_avatar.resize((300, 300)), (100, 100), mask=gen_rounded_mask(5000).resize((300, 300)))

    img.paste(user_avatar.resize((zoomer(300), zoomer(300))), (zoomer(100), zoomer(100)),
              mask=gen_rounded_rectangle_mask((5000, 5000), 1000).resize((zoomer(300), zoomer(300))))
    draw = ImageDraw.Draw(img)

    user_info_x = zoomer(460)  # Base x of user info

    # Draw username

    Text(text=user_name, fonts=fonts_name).draw(draw, (user_info_x, zoomer(135)), (0, 0, 0))
    # Draw user id

    Text(f'@{user_id}', fonts_id).draw(draw, (user_info_x, zoomer(135) + font_zoomer(1.5)), (128, 128, 128))

    # Draw context

    context_textbox.draw(draw, zoomer(100), zoomer(500))
    Text(_time.strftime("%I:%M %p · %b %d, %y"), fonts_id).draw(draw, (zoomer(100), context_textbox.high + zoomer(700)),
                                                                (128, 128, 128))

    if source:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        # 如果想扫描二维码后跳转到网页，需要添加https://
        qr.add_data(source)
        qrc = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
        img.paste(qrc.resize((zoomer(300), zoomer(300))), (zoomer(1600), int(context_textbox.high) + zoomer(550)))

    img_rt = Image.new('RGBA', img.size, (255, 255, 255, 0))
    x, y = img.size
    img_rt.paste(img, (0, 0), mask=gen_rounded_rectangle_mask((x * 5, y * 5), zoomer(300)).resize((x, y)))

    return img_rt


async def quote_twitter_async(url: str):
    user_name, user_id, user_avatar, context, medias, t = await get_tweet_info_playwright(url)
    return quote(user_name=user_name, user_avatar=user_avatar, context=context, _time=t, user_id=user_id, medias=medias,
                 source=url)


def quote_twitter(url: str):
    import asyncio
    return asyncio.run(quote_twitter_async(url))
