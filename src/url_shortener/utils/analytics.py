import hashlib

from url_shortener.core.config import settings


def hash_ip(ip: str) -> str:
    if not ip or ip == "unknown":
        return "unknown"

    raw = f"{ip}:{settings.ANALYTICS_SALT}".encode()
    return hashlib.sha256(raw).hexdigest()
