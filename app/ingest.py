"""Safe URL ingestion: plain HTTP GET + trafilatura. Never synthesizes missing text."""
import ipaddress
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
import trafilatura

FETCH_FAILED = "Unable to retrieve article text. Please paste the source text directly into the text box."
MIN_CHARS = 200
MAX_BYTES = 3_000_000
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SignalAnalyzer/1.0)"}


def _is_public_host(host: str) -> bool:
    """Block SSRF to loopback/private/link-local addresses."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


def fetch_article(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns (text, warning). Exactly one is None."""
    p = urlparse(url.strip())
    if p.scheme not in ("http", "https") or not p.hostname or not _is_public_host(p.hostname):
        return None, FETCH_FAILED
    try:
        with requests.get(url.strip(), headers=HEADERS, timeout=10, stream=True) as r:
            if r.status_code != 200:
                return None, FETCH_FAILED
            html = r.raw.read(MAX_BYTES, decode_content=True).decode(r.encoding or "utf-8", errors="replace")
    except requests.RequestException:
        return None, FETCH_FAILED
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text or len(text.strip()) < MIN_CHARS:  # paywall / blocked / JS shell
        return None, FETCH_FAILED
    return text.strip(), None
