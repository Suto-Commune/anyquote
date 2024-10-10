# AnyQuote

a simple quote generator using python.

# Usage

```python
from PIL import Image

from anyquote import quote
from anyquote import quote_twitter

img = Image.new("RGB", (128, 128))
quote(user_name='hsn', user_avatar=img, context='Hello World', _time=datetime.now(), user_id='@hsn8086').show()

quote_twitter("https://x.com/realDonaldTrump/status/1347555316863553542").show()
```

# Installation

```bash
pip install anyquote
```

# License

```text
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
We hope this program will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
```
