"""
url_service.py
--------------
Heuristic URL risk analyzer. Fully offline (no external API keys needed).

Signals: IP-literal hosts, Shannon entropy of the domain, suspicious TLDs,
brand-impersonation keywords, URL shorteners, excessive subdomains/hyphens,
'@' tricks, punycode, plain-HTTP, long paths, and an optional live TLS
certificate check.
"""

import math
import re
import socket
import ssl
from collections import Counter
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {"zip", "xyz", "top", "tk", "ml", "ga", "cf", "gq", "work",
                   "click", "link", "support", "loan", "country", "kim", "men"}
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
              "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at"}
KEYWORDS = ["login", "verify", "secure", "account", "update", "banking", "signin",
            "confirm", "password", "wallet", "payment", "billing", "suspend", "unlock"]
BRANDS = ["paypal", "amazon", "apple", "google", "microsoft", "netflix", "facebook",
          "instagram", "sbi", "hdfc", "icici", "paytm", "whatsapp", "linkedin"]
TRUSTED = {"google.com", "github.com", "microsoft.com", "apple.com", "amazon.com",
           "wikipedia.org", "linkedin.com", "paypal.com", "facebook.com", "youtube.com"}


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    return -sum((c / len(s)) * math.log2(c / len(s)) for c in counts.values())


def _registered_domain(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _check_ssl(host: str, timeout: float = 3.0) -> str:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as s:
                return "VALID" if s.getpeercert() else "NO CERT"
    except ssl.SSLCertVerificationError:
        return "INVALID"
    except Exception:
        return "UNREACHABLE"


def analyze_url(raw: str, check_ssl: bool = False) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {"error": "Please enter a URL."}
    if len(raw) > 2048:
        return {"error": "URL too long (max 2048 characters)."}
    url = raw if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw) else "http://" + raw
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
    except ValueError:
        return {"error": "Malformed URL."}
    if not host or "." not in host and not re.match(r"^[\d:]+$", host):
        return {"error": "Could not find a valid hostname."}

    score, indicators = 0, []

    def flag(points, severity, text):
        nonlocal score
        score += points
        indicators.append({"severity": severity, "text": text})

    reg = _registered_domain(host)
    tld = host.rsplit(".", 1)[-1]
    is_ip = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))
    label = reg.split(".")[0]
    ent = round(_entropy(label), 2)

    if is_ip:
        flag(30, "high", "Host is a raw IP address instead of a domain name")
    if p.scheme == "http":
        flag(12, "medium", "Connection is not encrypted (HTTP)")
    if "@" in p.netloc:
        flag(25, "high", "URL contains '@' — can disguise the real destination")
    if host.startswith("xn--") or ".xn--" in host:
        flag(20, "high", "Punycode domain — possible homograph attack")
    if reg in SHORTENERS:
        flag(30, "medium", "URL shortener hides the final destination")
    if tld in SUSPICIOUS_TLDS:
        flag(15, "medium", f"High-abuse top-level domain (.{tld})")
    if not is_ip and ent > 3.5 and len(label) > 10:
        flag(15, "medium", f"High domain entropy ({ent}) — looks randomly generated")

    sub_count = max(0, len(host.split(".")) - 2) if not is_ip else 0
    if sub_count >= 3:
        flag(15, "medium", f"Excessive subdomains ({sub_count})")
    if host.count("-") >= 2:
        flag(10, "medium", "Multiple hyphens in domain")

    kw_hits = [k for k in KEYWORDS if k in (host + p.path).lower()]
    if len(kw_hits) >= 2 or (kw_hits and reg not in TRUSTED):
        flag(min(8 * len(kw_hits), 20), "medium", "Sensitive keywords: " + ", ".join(kw_hits[:4]))

    for b in BRANDS:
        if b in host and not (reg.startswith(b + ".") and reg in TRUSTED):
            flag(25, "high", f"Possible brand impersonation ('{b}' in untrusted domain)")
            break

    if len(p.path) + len(p.query) > 75:
        flag(8, "low", "Unusually long path/query string")
    if reg in TRUSTED and not indicators:
        score = 0

    ssl_status = "N/A"
    if check_ssl and not is_ip and p.scheme == "https":
        ssl_status = _check_ssl(host)
        if ssl_status == "INVALID":
            flag(30, "high", "TLS certificate failed verification")
    elif p.scheme == "https":
        ssl_status = "HTTPS"
    else:
        ssl_status = "NONE"

    score = min(score, 100)
    if score >= 60:
        verdict, level = "MALICIOUS", "critical"
    elif score >= 30:
        verdict, level = "SUSPICIOUS", "warning"
    else:
        verdict, level = "SAFE", "safe"
    if not indicators:
        indicators.append({"severity": "info", "text": "No suspicious patterns detected"})

    special = len(re.findall(r"[^a-zA-Z0-9./:]", url))
    return {
        "url": raw, "host": host, "risk_score": score, "verdict": verdict, "level": level,
        "domain_entropy": ent, "path_length": len(p.path), "ssl_status": ssl_status,
        "special_chars": special, "indicators": indicators,
        "is_threat": level != "safe",
    }
