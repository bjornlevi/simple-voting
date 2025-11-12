# app/services/eligibility.py
import re
from urllib.parse import quote
import requests
from datetime import datetime, date

def _normalize_search(field: str, search: str) -> str:
    s = (search or "").strip()
    if field == "ssn":
        # keep digits only: "000000-0000" -> "0000000000"
        s = re.sub(r"\D+", "", s)
    # for username/name we just trim
    return s

def _fetch_member_added(base: str, api_key: str, field: str, search: str, timeout: float = 5.0) -> str | None:
    if not base or not api_key:
        return None
    norm = _normalize_search(field, search)
    url = f"{base.rstrip('/')}/member/api/get/{field}/{quote(norm, safe='')}/"
    resp = requests.post(url, data={"json_api_key": api_key}, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        return None
    data = payload.get("data") or {}
    # "added" is the key in your payload; keep fallback just in case
    return data.get("added") or data.get("date_joined")

def _parse_added_to_date(s: str) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace(" ", "T")).date()
    except Exception:
        return None

def user_is_eligible(kennitala: str, cutoff: date, *, base: str, api_key: str, field: str = "ssn") -> bool:
    if not cutoff:
        return True
    added_str = _fetch_member_added(base, api_key, field, kennitala)
    if not added_str:
        return False
    added_date = _parse_added_to_date(added_str)
    if not added_date:
        return False
    return added_date <= cutoff

# optional: richer debug you already wired
def debug_eligibility(kennitala, cutoff, *, base, api_key, field="ssn"):
    info = {
        "base_set": bool(base),
        "api_key_set": bool(api_key),
        "field": field,
        "search_raw": kennitala,
        "search_norm": _normalize_search(field, kennitala),
        "added_str": None,
        "added_date": None,
        "ok": False,
        "reason": None,
    }
    if not base or not api_key:
        info["reason"] = "missing_config"
        return False, info
    added_str = _fetch_member_added(base, api_key, field, kennitala)
    info["added_str"] = added_str
    if not added_str:
        info["reason"] = "lookup_failed"
        return False, info
    d = _parse_added_to_date(added_str)
    info["added_date"] = d.isoformat() if d else None
    if not d:
        info["reason"] = "parse_failed"
        return False, info
    if cutoff and d > cutoff:
        info["reason"] = "too_new"
        return False, info
    info["ok"] = True
    info["reason"] = "ok"
    return True, info
