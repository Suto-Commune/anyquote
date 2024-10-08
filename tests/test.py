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
@File       : test.py

@Author     : hsn

@Date       : 2024/8/11 下午8:43
"""
import unittest
from datetime import datetime


class Test(unittest.TestCase):
    def test_quote(self):
        from PIL import Image
        from anyquote import quote

        img = Image.new("RGB", (128, 128))
        quote(user_name='hsn', user_avatar=img, context='Hello World', _time=datetime.now(), user_id='@hsn8086')

    def test_start(self):
        from anyquote import quote_twitter
        quote_twitter('https://x.com/B_cat38324/status/1819902409319313541')


if __name__ == '__main__':
    unittest.main()
