"""SSRF guard: block private/loopback/link-local targets before any fetch of user-influenced URLs."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "jar"}


def is_safe_url(url: str) -> tuple[bool, str]:
    try:
        p = urlparse(url)
    except Exception:
        return False, "unparseable URL"
    if p.scheme not in ("http", "https"):
        return False, f"blocked scheme: {p.scheme}"
    host = (p.hostname or "").lower()
    if not host:
        return False, "missing host"
    if host in ("localhost",):
        return False, "blocked host"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, "DNS resolution failed"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False, f"blocked IP range: {ip}"
    return True, "ok"
