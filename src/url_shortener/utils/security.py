import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


async def check_url_is_alive(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)

        if not ip.is_global:
            log.warning(f"SSRF Attempt! Resolved {hostname} to non-global IP {ip_str}")
            return False

        safe_url = url.replace(hostname, ip_str, 1)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                safe_url, headers={"Host": hostname}, follow_redirects=False
            )

            return 200 <= response.status_code < 400

    except httpx.RequestError as re:
        log.info(f"URL {url} is dead: {re}")
        return False
    except Exception as e:  # noqa: BLE001
        log.error(f"Error checking URL {url}: {e}")
        return False
