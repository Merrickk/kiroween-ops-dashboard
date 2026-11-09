"""Probing: HTTP liveness + TLS certificate expiry.

Standard library only (urllib / socket / ssl). No external probe service.
"""

import socket
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


def probe_http(address: str, timeout: float = 5.0) -> tuple[bool, int | None, str]:
    """GET the address. Returns (ok, latency_ms, detail)."""
    url = address if urlparse(address).scheme else "https://" + address
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ops-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = int((time.monotonic() - start) * 1000)
            return True, latency, f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001 - probe must never raise
        latency = int((time.monotonic() - start) * 1000)
        return False, latency, f"{type(exc).__name__}: {exc}"


def cert_days_left(address: str, timeout: float = 5.0) -> tuple[int | None, str | None]:
    """Return (days_left, expires_at_iso) for the TLS cert, or (None, None)."""
    parsed = urlparse(address)
    netloc = parsed.netloc or urlparse("https://" + address).netloc
    host, _, port_str = netloc.partition(":")
    port = int(port_str) if port_str else 443
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not not_after:
            return None, None
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days = (expires - datetime.now(timezone.utc)).days
        return days, expires.isoformat()
    except Exception:  # noqa: BLE001 - unknown cert is a normal outcome
        return None, None


def probe_host(address: str) -> dict:
    """One full probe: HTTP liveness + cert. Returns a dict for storage."""
    ok, latency, detail = probe_http(address)
    days, expires_at = cert_days_left(address)
    if days is not None:
        detail += f" | cert {days}d left"
    return {
        "ok": ok,
        "latency_ms": latency,
        "detail": detail,
        "cert_days_left": days,
        "cert_expires_at": expires_at,
    }
