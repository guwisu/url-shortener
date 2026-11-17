import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


async def check_url_is_alive(
    url: str, semaphore: asyncio.Semaphore, client: httpx.AsyncClient
) -> bool:
    async with semaphore:
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False

            loop = asyncio.get_running_loop()
            addr_infos = await loop.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)

            for info in addr_infos:
                ip_str = info[4][0]
                ip = ipaddress.ip_address(ip_str)

                if not ip.is_global:
                    log.warning(f"SSRF block: {hostname} resolved to local IP {ip_str}")
                    return False

            response = await client.head(url, follow_redirects=False)

            if response.status_code in (403, 405, 501):
                response = await client.get(url, follow_redirects=False)

            return 200 <= response.status_code < 400

        except socket.gaierror as e:
            log.info(f"URL {url} is dead (DNS): {e}")
            return False
        except httpx.RequestError as re:
            log.info(f"URL {url} is dead: {re}")
            return False
        except Exception as e:  # noqa: BLE001
            log.error(f"URL {url} check failed: {e}")
            return False
