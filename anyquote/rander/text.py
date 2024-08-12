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
@File       : text.py

@Author     : hsn

@Date       : 2024/8/2 下午7:26
"""
import math
from os import PathLike

from PIL import ImageDraw, ImageFont
from fontTools.ttLib import TTFont


def is_halfwidth(char):
    """
    判断一个字符是否是半角
    """
    if len(char) != len(char.encode()):
        return False
    else:
        return True


def is_chinese(char: str):
    return 0x3400 <= ord(char) <= 0x4dbf or 0x4e00 <= ord(char) <= 0x9faf


def is_alpha(char: str):
    return 0x0030 <= ord(char) <= 0x0039 or 0x0041 <= ord(char) <= 0x005a or 0x0061 <= ord(char) <= 0x007a


class Font:
    def __init__(self, font: str | PathLike, size=20, offset: tuple[int, int] = None):
        self.font = font
        self.ttf = TTFont(font)
        self._imf = None
        self.offset = (0, 0) if offset is None else (offset[0] / size, offset[1] / size)
        self.best_cmap = self.ttf.getBestCmap()
        self.size = size
        self.glyphs = self.ttf.getGlyphSet()

    @property
    def imf(self):
        if self._imf is None:
            self._imf = ImageFont.truetype(self.font, self.size)
        return self._imf

    def get_char_size(self, _char):
        units_per_em = self.ttf['head'].unitsPerEm
        rate = self.size / units_per_em
        word_graph = self.glyphs.get(self.best_cmap[ord(_char)])
        return word_graph.width * rate, word_graph.height * rate

    def set_size(self, size):
        self.size = size
        self._imf = None


class Line:
    def __init__(self, text: str, fonts: [Font], spacing: int, align: str = 'left', max_width: int = math.inf,
                 symbol_push: bool = True, symbol_push_threshold: tuple[float, float] = (0.5, 1)):
        self.text = text
        self.align = align
        self.max_width = max_width
        self.fonts = fonts
        self.spacing = spacing
        self.symbol_push = symbol_push
        self.symbol_push_threshold = symbol_push_threshold
        self.full_width_symbols = '，。、；：？！\'":《（【“”』'

    def __iter__(self):
        return iter(self.text)

    def draw(self, draw: ImageDraw, xy: tuple[int, int], fill: tuple[int, int, int]):
        x, y = xy
        if self.text == '':
            return
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
                hf_count = len(list(filter(is_halfwidth, words)))
                count = words_count - hf_count

                if (diff := (self.max_width - total_length)) > 0:
                    if is_halfwidth(self.text[-1]):
                        q = 0.25
                    else:
                        q = 1
                    space = diff / (hf_count / 4 + count - q)
                    Text(text=self.text, fonts=self.fonts, spacing=space).draw(draw, (x, y), fill)
                else:
                    symbols = filter(lambda a: a in self.full_width_symbols, self.text)
                    symbol_count = len(list(symbols))
                    indentation = (-diff) / symbol_count
                    texts = []
                    for word, font, _len, font_offset in text.texts:
                        if word in self.full_width_symbols:
                            _len -= indentation
                        texts.append((word, font, _len, font_offset))
                    text.texts = texts
                    text.draw(draw, (x, y), fill)

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
            if self.symbol_push:
                symbols = filter(lambda x: x in self.full_width_symbols, self.text)
                symbol_count = len(list(symbols))
                symbol_count = 0.01 if symbol_count == 0 else symbol_count
                if (Text(text=text, fonts=self.fonts, spacing=0).get_length() / symbol_count <
                        1 - self.symbol_push_threshold[0]):
                    self.text += text
                    return

            raise EOFError('The text is too long to append')

    def __repr__(self):
        return self.text


class Paragraph:
    def __init__(self, fonts: list[Font], spacing: int = 0, line_spacing: int = 0, max_width: int = math.inf,
                 align='justify', symbol_push: bool = True, symbol_push_threshold: tuple[float, float] = (0.5, 1)):
        self.lines = []
        self.max_width = max_width
        self.line_spacing = line_spacing
        self.spacing = spacing
        self.fonts = fonts
        self.unfinished_line = Line('', fonts=fonts, spacing=0, align='left', max_width=max_width,
                                    symbol_push=symbol_push,
                                    symbol_push_threshold=symbol_push_threshold)
        self.align = align

    def add_text(self, text: str):
        try:
            self.unfinished_line.append(text)
        except EOFError:
            self.new_line(text)

    def check(self, text: str):
        return Text(text=self.unfinished_line.text + text, fonts=self.fonts,
                    spacing=self.spacing).get_length() <= self.max_width

    def new_line(self, text: str = ''):
        self.unfinished_line.align = self.align
        self.unfinished_line.text = self.unfinished_line.text.rstrip()
        self.lines.append(self.unfinished_line)
        self.unfinished_line = Line(text, fonts=self.fonts, spacing=0, align='left', max_width=self.max_width)

    def __iter__(self):
        return iter(self.lines + [self.unfinished_line])

    def __repr__(self):
        return repr(self.lines + [self.unfinished_line])


class TextBox:
    def __init__(self,
                 text: str,
                 fonts: [Font],
                 max_width: int = math.inf,
                 *,
                 line_spacing: int = 0,
                 spacing: int = 0,
                 symbol_push: bool = True,
                 symbol_push_threshold: tuple[float, float] = (0.5, 1),

                 ):
        self.text = text
        self.fonts = fonts
        self.max_width = max_width
        self.line_spacing = line_spacing
        self.spacing = spacing
        self.paragraphs = []
        self.full_width_symbols = '，。、；：？！:《（【“”』'
        self.symbols = self.full_width_symbols + '\'",.[](){}<>/\\'
        # split the text into paragraphs
        for paragraph in map(lambda x: list(x), text.split('\n')):
            # create a new paragraph
            p = Paragraph(line_spacing=line_spacing, spacing=spacing, fonts=fonts, max_width=max_width, align='justify',
                          symbol_push=symbol_push, symbol_push_threshold=symbol_push_threshold)

            word = ''

            for i, _char in enumerate(paragraph):
                _char: str

                # If the character is in the alphabet, add it as a word
                if is_alpha(_char):
                    word += _char

                else:

                    # If the character is a space and the word is not empty, add the word to the line
                    if word:
                        p.add_text(word)
                        word = ''
                        # if is_chinese(_char):
                        #     if p.check(' '):
                        #         p.add_text(' ')

                    # If the character is not in the alphabet, add it to the line directly
                    if p.check(_char):  # check if the character can be added to the line
                        p.add_text(_char)
                    else:
                        # If the character is a space, ignore it.
                        if _char == ' ':
                            continue
                        elif _char in self.symbols:
                            # if symbol_push is True, push the full-width symbol into small space
                            if symbol_push:
                                symbols = filter(lambda x: x in self.full_width_symbols, p.unfinished_line.text)
                                symbol_count = len(list(symbols))
                                symbol_count = 0.01 if symbol_count == 0 else symbol_count
                                if 1 / symbol_count < symbol_push_threshold[0]:
                                    p.add_text(_char)
                                    p.new_line()
                                    continue
                            if is_alpha(p.unfinished_line.text[-1]) or p.unfinished_line.text[-1] in self.symbols:
                                # if the last character is an alphabet, find the whole word's position
                                # find the last space
                                for index, c in enumerate(p.unfinished_line.text[::-1]):
                                    if not is_alpha(c) and c not in self.symbols:
                                        pos = len(p.unfinished_line.text) - index
                                        break
                                else:
                                    pos = len(p.unfinished_line.text)
                                ###

                                # move the extra characters to the next line
                                extra = p.unfinished_line.text[pos:]
                                p.unfinished_line.text = p.unfinished_line.text[:pos]
                            else:

                                extra = p.unfinished_line.text[-1]
                                p.unfinished_line.text = p.unfinished_line.text[:-1]

                            p.new_line(extra + _char)
                        else:
                            p.new_line(_char)

                # if i + 1 < len(paragraph):
                #
                #     if is_chinese(_char) and in_alphabet_range(paragraph[i + 1]):
                #         if p.check(' '):
                #             p.add_text(' ')
            if word:
                p.add_text(word)
            self.paragraphs.append(p)

    @property
    def high(self):
        _sum = 0
        for paragraph in self.paragraphs:
            for line in paragraph:
                _sum += line.getbbox()[1]  # y
                _sum += self.line_spacing
            _sum -= self.line_spacing
            _sum += self.line_spacing * 3
        _sum -= self.line_spacing * 3
        return _sum

    def draw(self, draw: ImageDraw, x, y):
        for paragraph in self.paragraphs:
            for line in paragraph:
                line.draw(draw, (x, y), (0, 0, 0))
                y += line.getbbox()[1]  # text.getbbox()[1] is the height of the text
                y += self.line_spacing
            y -= self.line_spacing
            y += self.line_spacing * 3
        y -= self.line_spacing * 3


class Text:  # blog: layout
    def __init__(self, text: str, fonts: list[Font], spacing: float = 0):
        self.text = text
        self.fonts = fonts
        self.spacing = spacing
        # rander text
        self.texts = []

        for i, word in enumerate(text):
            offset_x, offset_y = 0, 0
            for font in self.fonts:
                if ord(word) in font.best_cmap:
                    _len = font.get_char_size(word)[0]
                    # Chinese optimization
                    if i == 0 and word in "《（【〔“":
                        _len = _len / 2
                        offset_x = -_len
                    elif i == len(text) - 1 and word in "》）】〕”、。":
                        _len = _len / 2
                    if len(text) > i + 1:
                        if word in "》）】，。、；：？！”" and text[i + 1] in "《（【，。、“":
                            _len = _len / 2
                        if is_chinese(word) and is_alpha(text[i + 1]):
                            _len += font.size / 4
                        elif is_alpha(word) and is_chinese(text[i + 1]):
                            _len += font.size / 4
                        elif len(text) > i + 2 and is_chinese(word) and is_halfwidth(text[i + 1]) and is_alpha(
                                text[i + 2]):
                            _len += font.size / 4
                        elif i > 0 and is_alpha(text[i - 1]) and is_halfwidth(word) and is_chinese(text[i + 1]):
                            _len += font.size / 4

                    self.texts.append((word, font, _len, (offset_x, offset_y)))
                    break
            else:
                raise Exception(f'Can not find {word}:{ord(word)} in fonts')

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
        last_spacing = 0
        for word, font, _len, _ in self.texts:
            if is_halfwidth(word):
                x += _len + self.spacing / 4
                last_spacing = self.spacing / 4
            else:
                x += (_len + self.spacing)
                last_spacing = self.spacing
            y = max(y, font.size)
        x -= last_spacing
        return x, y

    def get_length(self):
        x = 0
        last_spacing = 0
        for word, font, _len, _ in self.texts:
            if is_halfwidth(word):
                x += _len + self.spacing / 4
                last_spacing = self.spacing / 4
            else:
                x += (_len + self.spacing)
                last_spacing = self.spacing
        x -= last_spacing

        return x

    def __repr__(self):
        return self.text
