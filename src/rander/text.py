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
@File       : text.py

@Author     : hsn

@Date       : 2024/8/2 下午7:26
"""
import math
from os import PathLike

from PIL import ImageDraw, ImageFont
from fontTools.ttLib import TTFont


class Font:
    def __init__(self, font: str | PathLike, size=20, offset: tuple[int, int] = None):
        self.font = font
        self.ttf = TTFont(font)
        self.imf = ImageFont.truetype(font, size)
        self.offset = offset


def in_alphabet_range(char: str):
    return char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


class Line:
    def __init__(self, text: str, fonts: [Font], spacing: int, align: str = 'left', max_width: int = math.inf):
        self.text = text
        self.align = align
        self.max_width = max_width
        self.fonts = fonts
        self.spacing = spacing

    def __iter__(self):
        return iter(self.text)

    def draw(self, draw: ImageDraw, xy: tuple[int, int], fill: tuple[int, int, int]):
        x, y = xy
        text = Text(text=self.text, fonts=self.fonts, spacing=self.spacing)
        if self.align == 'left':
            text.draw(draw, (x, y), fill)
        elif self.align == 'center':
            text.draw(draw, (int(x + (self.max_width - text.get_length()) / 2), y), fill)
        elif self.align == 'right':
            text.draw(draw, (x + self.max_width - text.get_length(), y), fill)
        elif self.align == 'justify':
            words = list(self.text)
            words_count = len(words)
            if words_count == 1:
                text.draw(draw, (x, y), fill)
            else:
                total_length = text.get_length()
                space = (self.max_width - total_length) / (words_count - 1)
                for word in words:
                    text = Text(text=word, fonts=self.fonts, spacing=0)
                    text.draw(draw, (x, y), fill)
                    x += text.get_length() + space+self.spacing


    def getbbox(self):
        if self.align == 'left':
            return Text(text=self.text, fonts=self.fonts, spacing=self.spacing).getbbox()
        elif self.align == 'right':
            text = Text(text=self.text, fonts=self.fonts, spacing=self.spacing)
            _, y = text.getbbox()
            return self.max_width, y

        elif self.align == 'center':
            text = Text(text=self.text, fonts=self.fonts, spacing=self.spacing)
            x, y = text.getbbox()
            return self.max_width, y
        elif self.align == 'justify':
            text = Text(text=self.text, fonts=self.fonts, spacing=self.spacing)
            x, y = text.getbbox()
            return self.max_width, y

    def append(self, text: str):
        if Text(text=self.text + text, fonts=self.fonts, spacing=self.spacing).get_length() <= self.max_width:
            self.text += text
        else:
            raise EOFError('The text is too long to append')

    def __repr__(self):
        return self.text


def is_chinese(char: str):
    return '\u4e00' <= char <= '\u9fa5'


class Paragraph:
    def __init__(self, fonts: list[Font], spacing: int = 0, line_spacing: int = 0, max_width: int = math.inf):
        self.lines = []
        self.max_width = max_width
        self.line_spacing = line_spacing
        self.spacing = spacing
        self.fonts = fonts
        self.unfinished_line = Line('', fonts=fonts, spacing=0, align='left', max_width=max_width)

    def add_text(self, text: str):
        try:
            self.unfinished_line.append(text)
        except EOFError:
            self.new_line(text)

    def check(self, text: str):
        print(self.max_width)
        return Text(text=self.unfinished_line.text + text, fonts=self.fonts,
                    spacing=self.spacing).get_length() <= self.max_width

    def new_line(self, text: str = ''):
        self.unfinished_line.align = 'justify'
        self.lines.append(self.unfinished_line)
        self.unfinished_line = Line(text, fonts=self.fonts, spacing=0, align='left', max_width=self.max_width)

    def __iter__(self):
        return iter(self.lines + [self.unfinished_line])

    def __repr__(self):
        return repr(self.lines + [self.unfinished_line])


class TextBox:
    def __init__(self, text: str, fonts: [Font], max_width: int = math.inf, line_spacing: int = 0, spacing: int = 0):
        self.text = text
        self.fonts = fonts
        self.max_width = max_width
        self.line_spacing = line_spacing
        self.spacing = spacing
        self.paragraphs = []
        for paragraph in map(lambda x: list(x), text.split('\n')):
            p = Paragraph(line_spacing=line_spacing, spacing=spacing, fonts=fonts, max_width=max_width)

            word = ''

            for i,_char in enumerate(paragraph):
                _char:str

                # If the character is in the alphabet, add it as a word
                if in_alphabet_range(_char):
                    word += _char

                else:
                    # If the character is a space and the word is not empty, add the word to the line
                    # if word:
                    # if Text(text=line + word, fonts=self.fonts, spacing=self.spacing).get_length() <= max_width:
                    #     line += word
                    # else:
                    #     # If the word is too long, add the line to the paragraph and start a new line
                    #     lines.append(Line(line, spacing=spacing, fonts=fonts, align='justify', max_width=max_width))
                    #     line = word
                    #
                    # word = ''
                    if word:
                        p.add_text(word)
                        word = ''
                        if is_chinese(_char):
                            if p.check(' '):
                                p.add_text(' ')
                    # If the character is not in the alphabet, add it to the line directly
                    # if Text(text=line + _char, fonts=self.fonts, spacing=self.spacing).get_length() <= max_width:
                    #     line += _char
                    # else:
                    #     # If the line is too long, add the line to the paragraph and start a new line
                    #     lines.append(Line(line, fonts=fonts, spacing=spacing, align='justify', max_width=max_width))
                    #     line = _char if _char != ' ' else ''  # If the character is a space, delete it
                    if p.check(_char):
                        p.add_text(_char)
                    else:
                        if _char == ' ':
                            p.new_line()
                        elif _char in '，。、；：？！\':《（【“”』':
                            if in_alphabet_range(p.unfinished_line.text[-1]):
                                pos = p.unfinished_line.text.rfind(' ')
                                extra = p.unfinished_line.text[pos:]
                                p.unfinished_line.text = p.unfinished_line.text[:pos]
                            else:
                                extra = p.unfinished_line.text[-1]
                                p.unfinished_line.text = p.unfinished_line.text[:-1]

                            p.new_line(extra+_char)
                        else:
                            p.add_text(_char)

                if i+1 < len(paragraph):

                    if is_chinese(_char) and in_alphabet_range(paragraph[i+1]):
                        if p.check(' '):

                            p.add_text(' ')
            if word:
                p.add_text(word)
            self.paragraphs.append(p)
        print(self.paragraphs)

    @property
    def high(self):
        _sum = 0
        for paragraph in self.paragraphs:
            for line in paragraph:
                # x, y = Text(text=line.text, fonts=self.fonts, spacing=self.spacing).getbbox()
                _sum += line.getbbox()[1]  # y
                _sum += self.line_spacing
            _sum -= self.line_spacing
            _sum += self.line_spacing * 3
        _sum -= self.line_spacing * 3
        return _sum

    def draw(self, draw: ImageDraw, x, y):
        for paragraph in self.paragraphs:
            for line in paragraph:
                # text = Text(line.text, self.fonts, spacing=self.spacing)
                # text.draw(draw=draw, xy=(x, y), fill=(0, 0, 0))
                line.draw(draw, (x, y), (0, 0, 0))
                # print(line)
                y += line.getbbox()[1]  # text.getbbox()[1] is the height of the text
                # y += y
                y += self.line_spacing
            y -= self.line_spacing
            y += self.line_spacing * 3
        y -= self.line_spacing * 3


def is_halfwidth(char):
    """
    判断一个字符是否是半角
    """
    if len(char) != len(char.encode()):
        return False
    else:
        return True


class Text:  # blog: layout
    def __init__(self, text: str, fonts: list[Font], spacing: int = 0):
        self.text = text
        self.fonts = fonts
        self.spacing = spacing
        # rander text
        self.texts = []

        for i, word in enumerate(text):
            offset_x, offset_y = 0, 0
            for font in self.fonts:
                ttf = font.ttf

                if ord(word) in ttf.getBestCmap():
                    _len = font.imf.getlength(word)
                    # Chinese optimization
                    if i == 0 and word in "《（【“":
                        _len = font.imf.getlength(word) / 2
                        offset_x = -_len
                    if len(text) > i + 1:
                        if word in "》）】，。、；：？！”" and text[i + 1] in "《（【，。、“":
                            _len = font.imf.getlength(word) / 2

                    self.texts.append((word, font, _len, (offset_x, offset_y)))
                    break
            else:
                raise Exception(f'Can not find {word} in fonts')

    def draw(self, draw: ImageDraw, xy: tuple[int, int], fill: tuple[int, int, int]):
        x, y = xy
        for word, font, _len, font_offset in self.texts:
            pil_font = font.imf
            font_offset_x, font_offset_y = font_offset
            offset_x, offset_y = font.offset if font.offset else (0, 0)
            draw.text((x + offset_x + font_offset_x, y + offset_y + font_offset_y), word, font=pil_font, fill=fill)
            if is_halfwidth(word):
                x += _len + self.spacing / 4
            else:
                x += (_len + self.spacing)

    def getbbox(self):
        x, y = 0, 0

        for word, font, _len, _ in self.texts:
            if is_halfwidth(word):
                x += _len + self.spacing / 4
            else:
                x += (_len + self.spacing)
            y = max(y,
                    font.imf.getbbox(word)[3] - font.imf.getbbox(word)[1])

        return x, y

    def get_length(self):
        return self.getbbox()[0]

    def __repr__(self):
        return self.text
