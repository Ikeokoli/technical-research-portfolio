"""An offline, conservative adapter for SearchApi-shaped organic results."""
import hashlib
import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


def canonical_url(value):
    """Normalize scheme/host/default port only; preserve query and fragment semantics."""
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("invalid_url")
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("invalid_url")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("invalid_url")
        host = parsed.hostname.encode("idna").decode("ascii").lower()
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            if len(host) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
                                         for part in host.split(".")):
                raise ValueError("invalid_url")
        else:
            host = f"[{ip.compressed}]" if ip.version == 6 else str(ip)
        port = parsed.port
        default = 443 if parsed.scheme == "https" else 80
        authority = host if port is None or port == default else f"{host}:{port}"
        return urlunsplit((parsed.scheme, authority, parsed.path, parsed.query, parsed.fragment))
    except (ValueError, UnicodeError):
        raise ValueError("invalid_url") from None


def adapt(payload, provenance):
    """Return candidates and an audit trail; do not fetch links or verify claims."""
    if not isinstance(payload, dict):
        return {"state": "schema_error", "candidates": [], "audit": []}
    if payload.get("error"):
        return {"state": "provider_error", "candidates": [], "audit": []}
    if "organic_results" not in payload:
        return {"state": "missing_organic_results", "candidates": [], "audit": []}
    rows = payload["organic_results"]
    if not isinstance(rows, list):
        return {"state": "schema_error", "candidates": [], "audit": []}
    if not rows:
        return {"state": "empty", "candidates": [], "audit": []}
    candidates, seen, audit = [], {}, []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            audit.append({"input_index": index, "action": "reject", "reason": "not_object"})
            continue
        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            audit.append({"input_index": index, "action": "reject", "reason": "missing_title"})
            continue
        try:
            url = canonical_url(row.get("link"))
        except ValueError:
            audit.append({"input_index": index, "action": "reject", "reason": "invalid_url"})
            continue
        occurrence = {"input_index": index, "position": row.get("position"), "raw_link": row["link"]}
        if url in seen:
            seen[url]["occurrences"].append(occurrence)
            audit.append({"input_index": index, "action": "duplicate", "candidate_id": seen[url]["id"]})
            continue
        snippet = row.get("snippet")
        candidate = {"id": "url_" + hashlib.sha256(url.encode()).hexdigest(),
                     "url": url, "title": title.strip(),
                     "snippet": snippet if isinstance(snippet, str) and snippet.strip() else None,
                     "content_kind": "search_snippet", "trust": "untrusted",
                     "claim_verified": False, "provenance": dict(provenance),
                     "occurrences": [occurrence]}
        seen[url] = candidate
        candidates.append(candidate)
        audit.append({"input_index": index, "action": "keep", "candidate_id": candidate["id"]})
    return {"state": "ok" if candidates else "no_usable_candidates",
            "candidates": candidates, "audit": audit}
