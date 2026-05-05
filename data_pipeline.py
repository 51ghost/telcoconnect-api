"""TelcoConnect API — Carrier Data Pipeline

Provides curated telecom carrier dataset (~50 records), caching,
and lookup/search utilities used by the main API.
"""
import time
import re
from typing import Optional


class DataCache:
    """Simple TTL-based in-memory cache."""
    def __init__(self, ttl=3600):
        self._cache = {}
        self._ttl = ttl

    def get(self, key):
        val, ts = self._cache.get(key, (None, 0))
        if val and time.time() - ts < self._ttl:
            return val
        return None

    def set(self, key, val):
        self._cache[key] = (val, time.time())


cache = DataCache()

# ---------------------------------------------------------------------------
# Curated dataset: ~50 real-world telecom carriers
# Each record has an id (unique slug), name, country (ISO code), prefix,
# type, and region.
# ---------------------------------------------------------------------------
DATASET = [
    {"id": "att-us",       "prefix": "+1",    "country": "US", "name": "AT&T",         "type": "mobile",   "region": "North America"},
    {"id": "verizon-us",   "prefix": "+1",    "country": "US", "name": "Verizon",       "type": "mobile",   "region": "North America"},
    {"id": "tmobile-us",   "prefix": "+1",    "country": "US", "name": "T-Mobile",      "type": "mobile",   "region": "North America"},
    {"id": "rogers-ca",    "prefix": "+1",    "country": "CA", "name": "Rogers",        "type": "mobile",   "region": "North America"},
    {"id": "bell-ca",      "prefix": "+1",    "country": "CA", "name": "Bell",          "type": "mobile",   "region": "North America"},
    {"id": "telus-ca",     "prefix": "+1",    "country": "CA", "name": "Telus",         "type": "mobile",   "region": "North America"},
    {"id": "telcel-mx",    "prefix": "+52",   "country": "MX", "name": "Telcel",        "type": "mobile",   "region": "Latin America"},
    {"id": "movistar-mx",  "prefix": "+52",   "country": "MX", "name": "Movistar",      "type": "mobile",   "region": "Latin America"},
    {"id": "claro-ar",     "prefix": "+54",   "country": "AR", "name": "Claro",         "type": "mobile",   "region": "Latin America"},
    {"id": "vivo-br",      "prefix": "+55",   "country": "BR", "name": "Vivo",          "type": "mobile",   "region": "Latin America"},
    {"id": "claro-br",     "prefix": "+55",   "country": "BR", "name": "Claro",         "type": "mobile",   "region": "Latin America"},
    {"id": "tim-br",       "prefix": "+55",   "country": "BR", "name": "TIM",           "type": "mobile",   "region": "Latin America"},
    {"id": "vodafone-uk",  "prefix": "+44",   "country": "GB", "name": "Vodafone",      "type": "mobile",   "region": "Europe"},
    {"id": "ee-uk",        "prefix": "+44",   "country": "GB", "name": "EE",            "type": "mobile",   "region": "Europe"},
    {"id": "o2-uk",        "prefix": "+44",   "country": "GB", "name": "O2",            "type": "mobile",   "region": "Europe"},
    {"id": "tmobile-de",   "prefix": "+49",   "country": "DE", "name": "T-Mobile",      "type": "mobile",   "region": "Europe"},
    {"id": "vodafone-de",  "prefix": "+49",   "country": "DE", "name": "Vodafone",      "type": "mobile",   "region": "Europe"},
    {"id": "o2-de",        "prefix": "+49",   "country": "DE", "name": "O2",            "type": "mobile",   "region": "Europe"},
    {"id": "orange-fr",    "prefix": "+33",   "country": "FR", "name": "Orange",        "type": "mobile",   "region": "Europe"},
    {"id": "sfr-fr",       "prefix": "+33",   "country": "FR", "name": "SFR",           "type": "mobile",   "region": "Europe"},
    {"id": "bouygues-fr",  "prefix": "+33",   "country": "FR", "name": "Bouygues",      "type": "mobile",   "region": "Europe"},
    {"id": "tim-it",       "prefix": "+39",   "country": "IT", "name": "TIM",           "type": "mobile",   "region": "Europe"},
    {"id": "vodafone-it",  "prefix": "+39",   "country": "IT", "name": "Vodafone",      "type": "mobile",   "region": "Europe"},
    {"id": "wind3-it",     "prefix": "+39",   "country": "IT", "name": "Wind Tre",      "type": "mobile",   "region": "Europe"},
    {"id": "movistar-es",  "prefix": "+34",   "country": "ES", "name": "Movistar",      "type": "mobile",   "region": "Europe"},
    {"id": "orange-es",    "prefix": "+34",   "country": "ES", "name": "Orange",        "type": "mobile",   "region": "Europe"},
    {"id": "kpn-nl",       "prefix": "+31",   "country": "NL", "name": "KPN",           "type": "mobile",   "region": "Europe"},
    {"id": "swisscom-ch",  "prefix": "+41",   "country": "CH", "name": "Swisscom",      "type": "mobile",   "region": "Europe"},
    {"id": "telenor-no",   "prefix": "+47",   "country": "NO", "name": "Telenor",       "type": "mobile",   "region": "Europe"},
    {"id": "telia-se",     "prefix": "+46",   "country": "SE", "name": "Telia",         "type": "mobile",   "region": "Europe"},
    {"id": "mts-ru",       "prefix": "+7",    "country": "RU", "name": "MTS",           "type": "mobile",   "region": "Europe / Asia"},
    {"id": "beeline-ru",   "prefix": "+7",    "country": "RU", "name": "Beeline",       "type": "mobile",   "region": "Europe / Asia"},
    {"id": "megafon-ru",   "prefix": "+7",    "country": "RU", "name": "MegaFon",       "type": "mobile",   "region": "Europe / Asia"},
    {"id": "ntt-jp",       "prefix": "+81",   "country": "JP", "name": "NTT Docomo",    "type": "mobile",   "region": "Asia Pacific"},
    {"id": "softbank-jp",  "prefix": "+81",   "country": "JP", "name": "SoftBank",      "type": "mobile",   "region": "Asia Pacific"},
    {"id": "kddi-jp",      "prefix": "+81",   "country": "JP", "name": "KDDI",          "type": "mobile",   "region": "Asia Pacific"},
    {"id": "china-mobile", "prefix": "+86",   "country": "CN", "name": "China Mobile",  "type": "mobile",   "region": "Asia Pacific"},
    {"id": "china-unicom", "prefix": "+86",   "country": "CN", "name": "China Unicom",  "type": "mobile",   "region": "Asia Pacific"},
    {"id": "china-telecom","prefix": "+86",   "country": "CN", "name": "China Telecom", "type": "mobile",   "region": "Asia Pacific"},
    {"id": "airtel-in",    "prefix": "+91",   "country": "IN", "name": "Airtel",        "type": "mobile",   "region": "Asia Pacific"},
    {"id": "jio-in",       "prefix": "+91",   "country": "IN", "name": "Jio",           "type": "mobile",   "region": "Asia Pacific"},
    {"id": "vi-in",        "prefix": "+91",   "country": "IN", "name": "Vodafone Idea", "type": "mobile",   "region": "Asia Pacific"},
    {"id": "telstra-au",   "prefix": "+61",   "country": "AU", "name": "Telstra",       "type": "mobile",   "region": "Asia Pacific"},
    {"id": "optus-au",     "prefix": "+61",   "country": "AU", "name": "Optus",         "type": "mobile",   "region": "Asia Pacific"},
    {"id": "singtel-sg",   "prefix": "+65",   "country": "SG", "name": "Singtel",       "type": "mobile",   "region": "Asia Pacific"},
    {"id": "starhub-sg",   "prefix": "+65",   "country": "SG", "name": "StarHub",       "type": "mobile",   "region": "Asia Pacific"},
    {"id": "kt-kr",        "prefix": "+82",   "country": "KR", "name": "KT",            "type": "mobile",   "region": "Asia Pacific"},
    {"id": "skt-kr",       "prefix": "+82",   "country": "KR", "name": "SK Telecom",    "type": "mobile",   "region": "Asia Pacific"},
    {"id": "vodacom-za",   "prefix": "+27",   "country": "ZA", "name": "Vodacom",       "type": "mobile",   "region": "Africa"},
    {"id": "mtn-za",       "prefix": "+27",   "country": "ZA", "name": "MTN",           "type": "mobile",   "region": "Africa"},
    {"id": "safaricom-ke", "prefix": "+254",  "country": "KE", "name": "Safaricom",     "type": "mobile",   "region": "Africa"},
]

# CARRIERS is exported as a list so main.py can iterate:
#   for c in CARRIERS: c["id"], c["name"], c["country"]
# Internal prefix-indexed lookup is maintained in _CARRIER_BY_PREFIX.
CARRIERS = list(DATASET)  # mutable copy for iteration

_CARRIER_BY_PREFIX = {}
for rec in DATASET:
    _CARRIER_BY_PREFIX.setdefault(rec["prefix"], []).append(rec)

# Build a quick id -> record lookup
_CARRIER_BY_ID = {rec["id"]: rec for rec in DATASET}


def search_carriers(query: str = "", country: Optional[str] = None, limit: int = 20) -> list:
    """Search carriers by query text, optionally filtered by country.

    Args:
        query: Search string (matched against name, prefix, id, region, country).
        country: ISO country code filter (optional, case-insensitive).
        limit: Max results to return (default 20, max 100).

    Returns:
        List of matching carrier records.
    """
    q = query.lower().strip() if query else ""
    results = []

    for rec in DATASET:
        if country and rec["country"].upper() != country.upper():
            continue
        if q:
            fields = [str(v).lower() for v in rec.values()]
            if not any(q in f for f in fields):
                continue
        results.append(rec)

    results = results[:min(limit, 100)] if limit else results
    cache.set("last_search", results)
    return results


def get_carrier(carrier_id: str) -> Optional[dict]:
    """Look up a single carrier by its unique id (e.g. 'att-us', 'vodafone-uk').

    Also accepts a phone prefix (e.g. '+1', '+44') as a fallback; when multiple
    carriers share the same prefix the first match is returned.

    Args:
        carrier_id: Carrier id slug or phone prefix.

    Returns:
        Carrier record dict, or None if not found.
    """
    # Primary: try exact id match
    if carrier_id in _CARRIER_BY_ID:
        return _CARRIER_BY_ID[carrier_id]

    # Fallback: try as a phone prefix
    p = carrier_id if carrier_id.startswith("+") else "+" + carrier_id
    matches = _CARRIER_BY_PREFIX.get(p)
    if matches:
        return matches[0]

    return None


def identify_carrier(phone_number: str) -> dict:
    """Identify the carrier for a given phone number.

    Strips non-digit characters, matches the longest possible prefix,
    and returns carrier information.

    Args:
        phone_number: Full phone number, optionally with '+' prefix.

    Returns:
        Dict with carrier info on success, or dict with 'error' key on failure.
    """
    cleaned = phone_number.strip()
    has_plus = cleaned.startswith("+")
    digits_only = re.sub(r"\D", "", cleaned)
    if not digits_only:
        return {"error": "Invalid phone number: no digits found"}

    # Try longest prefix matches first
    for i in range(len(digits_only), 0, -1):
        candidate = ("+" if has_plus else "") + digits_only[:i]
        if candidate in _CARRIER_BY_PREFIX:
            matches = _CARRIER_BY_PREFIX[candidate]
            return {
                "phone": phone_number,
                "prefix": candidate,
                "carrier": matches[0]["name"],
                "country": matches[0]["country"],
                "carrier_id": matches[0]["id"],
                "candidates": len(matches),
            }

    return {"error": f"Unknown carrier for number: {phone_number}"}
