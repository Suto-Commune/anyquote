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
@File       : font_manager.py

@Author     : hsn

@Date       : 2024/10/26 下午2:12
"""
import json
import zipfile
from pathlib import Path
from typing import Literal

import httpx
from rich.progress import track


def get_noto_emoji_var():
    list_url = "https://fonts.google.com/download/list?family=Noto%20Emoji"
    json_str = httpx.get(list_url).text
    j = json.loads(json_str.split("\n", 1)[1])
    for i in j.get("manifest").get("fileRefs"):
        if i.get("filename") == "NotoEmoji-VariableFont_wght.ttf":
            url = i.get("url")
            break
    else:
        raise ValueError("Can't find NotoEmoji-VariableFont_wght.ttf")
    # Download
    cache = Path("./.cache")
    if not cache.exists():
        cache.mkdir()
    if not (cache / "NotoEmoji-VariableFont_wght.ttf").exists():
        with httpx.stream("GET", url, follow_redirects=True) as resp:
            with open(cache / "NotoEmoji-VariableFont_wght.ttf", "wb") as f:
                for chunk in track(resp.iter_bytes(1024 * 128), description="Downloading...",
                                   total=int(resp.headers.get("Content-Length")) / (1024 * 128)):
                    f.write(chunk)

    return cache / "NotoEmoji-VariableFont_wght.ttf"


def get_source_han_sans_sc(
        weight: Literal["Bold", "ExtraLight", "Heavy", "Light", "Medium", "Regular", "SemiBold", "Normal"]):
    url = "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip"
    # Download and unzip
    cache = Path("./.cache")
    if not cache.exists():
        cache.mkdir()
    if not (cache / "SourceHanSansSC.zip").exists():
        with httpx.stream("GET", url, follow_redirects=True) as resp:
            with open(cache / "SourceHanSansSC.zip", "wb") as f:
                for chunk in track(resp.iter_raw(1024 * 128), description="Downloading...",
                                   total=int(resp.headers.get("Content-Length")) / (1024 * 128)):
                    f.write(chunk)
    if not Path(cache / "SourceHanSansSC" / "OTF" / "SimplifiedChinese" / f"SourceHanSansSC-{weight}.otf").exists():
        with zipfile.ZipFile(cache / "SourceHanSansSC.zip", "r") as zip_ref:
            (cache / "SourceHanSansSC").mkdir(exist_ok=True)
            zip_ref.extractall(cache / "SourceHanSansSC")

    return Path(cache / "SourceHanSansSC" / "OTF" / "SimplifiedChinese" / f"SourceHanSansSC-{weight}.otf")


def get_font(
        name: Literal["SourceHanSansSC", "NotoEmoji-VariableFont"],
        weight: Literal["Bold", "ExtraLight", "Heavy", "Light", "Medium", "Regular", "SemiBold", "Normal"] = "Regular",
):
    match name:
        case "SourceHanSansSC":
            return get_source_han_sans_sc(weight)
        case "NotoEmoji-VariableFont":
            return get_noto_emoji_var()
        case _:
            raise ValueError("Unknown font name")


if __name__ == '__main__':
    print(get_font("NotoEmoji-VariableFont"))
