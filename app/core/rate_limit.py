from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Basic global limiter; can be extended to use Redis storage
limiter = Limiter(key_func=get_remote_address)
