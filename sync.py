"""
Android Package Catalog Sync & Sanitizer
Fetches community definitions, extracts human-readable app names,
sanitizes red-flag terminology, and generates clean, production-ready
JSON and minified catalogs.
"""

import json
import urllib.request
import re
import os
import sys

UAD_PACKAGES_URL = "https://raw.githubusercontent.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation/main/resources/assets/uad_lists.json"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(ROOT_DIR, "catalog.json")
OUTPUT_MIN_JSON = os.path.join(ROOT_DIR, "catalog.min.json")

SAFETY_MAPPING = {
    "recommended": "safe",     # 100% safe to disable/remove, no system impact
    "advanced": "optional",     # Safe if feature not used (e.g. cloud sync, live caption)
    "expert": "warning",        # Proceed with caution (e.g. emergency alerts, dialer codes)
    "unsafe": "critical",       # DO NOT TOUCH (e.g. modem, systemui, SAR sensor)
}

SANITIZE_PATTERNS = [
    (re.compile(r'\bdebloat(er|ing)?\b', re.IGNORECASE), 'optimization'),
    (re.compile(r'\bbloat(ware)?\b', re.IGNORECASE), 'pre-installed package'),
    (re.compile(r'\bnuke(d)?\b', re.IGNORECASE), 'remove'),
    (re.compile(r'\bspyware\b', re.IGNORECASE), 'telemetry'),
    (re.compile(r'\bmalware\b', re.IGNORECASE), 'unwanted software'),
    (re.compile(r'\bhack(s|ing)?\b', re.IGNORECASE), 'tweak'),
]

TLDS = {'com', 'org', 'net', 'io', 'gov', 'edu', 'co', 'uk', 'us', 'ca', 'de', 'fr', 'jp', 'cn', 'in', 'ch', 'cz', 'ru', 'app', 'dev'}
GENERIC_WORDS = {
    'android', 'apps', 'debug', 'release', 'basic', 'mobile',
    'ordering', 'ad', 'ads', 'client', 'main', 'phone', 'tv', 'vr',
    'lite', 'prod', 'production', 'free', 'express', 'global',
    'service', 'services', 'system', 'ui', 'wrapper', 'sdk',
    'nativeapp', 'mobilem8', 'emn8'
}

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    result = text
    for pattern, replacement in SANITIZE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result.strip()

def derive_name_from_package(pkg_name: str) -> str:
    parts = pkg_name.split('.')
    if len(parts) > 1:
        for i in range(len(parts) - 1, -1, -1):
            p = parts[i].strip()
            if not p:
                continue
            p_lower = p.lower()
            if p_lower in TLDS:
                continue
            if p_lower in GENERIC_WORDS and i > 0:
                prev = parts[i - 1].lower()
                if prev not in TLDS:
                    continue
            words = re.sub(r'([a-z])([A-Z])', r'\1 \2', p.replace('_', ' ').replace('-', ' ')).split()
            clean = " ".join(w.capitalize() for w in words if w)
            if clean:
                return clean
    return parts[-1].capitalize() if parts else pkg_name

def extract_app_name(pkg_name: str, description: str) -> str:
    if not description:
        return derive_name_from_package(pkg_name)

    # Grab the first line or sentence of the description
    first_line = description.strip().splitlines()[0].strip()
    
    # Strip leading warnings or exclamation notes (e.g. "!!! WARNING !!! DO NOT DELETE...")
    if first_line.startswith("!") or "WARNING" in first_line[:15]:
        lines = [l.strip() for l in description.splitlines() if l.strip() and not l.strip().startswith("!") and "WARNING" not in l[:15]]
        if lines:
            first_line = lines[0]

    # Remove URLs like (https://play.google.com/...)
    clean_line = re.sub(r'\(?https?://[^\s\)]+\)?', '', first_line).strip()

    # Match up to first delimiter: period, comma, dash, parenthesis, semicolon, or colon
    split_match = re.split(r'[\.,;:\-\(\[\{]', clean_line)
    candidate = split_match[0].strip() if split_match else ""

    # Clean up trailing words like "app", "application", "service", "daemon", "client", "stuff"
    candidate = re.sub(r'\b(app|application|service|daemon|client|stuff|feature)\b', '', candidate, flags=re.IGNORECASE).strip()

    # Check candidate validity (must be reasonable length and not generic sentence)
    if candidate and 2 <= len(candidate) <= 35 and not any(w in candidate.lower() for w in ['safe to', 'removing', 'causes', 'this package', 'do not', 'note that']):
        return candidate

    return derive_name_from_package(pkg_name)

def fetch_json(url: str):
    print(f"[*] Fetching: {url}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Android-Package-Catalog-Sync/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def sync():
    raw_uad = fetch_json(UAD_PACKAGES_URL)
    print(f"[+] Loaded {len(raw_uad)} package definitions from upstream.")

    catalog = {}
    for pkg_name, info in raw_uad.items():
        raw_removal = str(info.get("removal", "advanced")).lower()
        safety = SAFETY_MAPPING.get(raw_removal, "optional")
        category = info.get("list", "general").lower()
        raw_desc = info.get("description", "")
        description = sanitize_text(raw_desc)
        app_name = extract_app_name(pkg_name, raw_desc)

        catalog[pkg_name] = {
            "packageName": pkg_name,
            "appName": app_name,
            "category": category,
            "safety": safety,       # safe, optional, warning, critical
            "description": description
        }

    # Pretty output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # Minified output for high-performance mobile/desktop clients
    with open(OUTPUT_MIN_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, separators=(',', ':'), ensure_ascii=False)

    print(f"[+] Successfully wrote {len(catalog)} packages to:")
    print(f"    - {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / 1024:.1f} KB)")
    print(f"    - {OUTPUT_MIN_JSON} ({os.path.getsize(OUTPUT_MIN_JSON) / 1024:.1f} KB)")

if __name__ == "__main__":
    sync()
