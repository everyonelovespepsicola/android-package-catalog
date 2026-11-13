"""
Android Package Catalog Sync & Sanitizer
Fetches community definitions, sanitizes red-flag terminology,
and generates clean, production-ready JSON and index catalogs.
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

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    result = text
    for pattern, replacement in SANITIZE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result.strip()

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
        description = sanitize_text(info.get("description", ""))

        catalog[pkg_name] = {
            "packageName": pkg_name,
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
