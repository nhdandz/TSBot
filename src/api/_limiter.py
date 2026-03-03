"""Rate limiter instance — tách ra module riêng để tránh circular import.

main.py → import limiter từ đây
chat.py → import limiter từ đây
admin.py → import limiter từ đây
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
