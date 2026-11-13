"""
Android Package Catalog Sync & Play Store Title Scraper
Fetches community definitions, scrapes official app names from Google Play Store,
caches verified titles to titles_cache.json, and produces clean mappings:
  {
    "com.google.android.youtube": "YouTube",
    "com.android.chrome": "Google Chrome",
    ...
  }
"""

import json
import urllib.request
import urllib.error
import re
import os
import sys
import time

UAD_PACKAGES_URL = "https://raw.githubusercontent.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation/main/resources/assets/uad_lists.json"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(ROOT_DIR, "titles_cache.json")
OUTPUT_JSON = os.path.join(ROOT_DIR, "catalog.json")
OUTPUT_MIN_JSON = os.path.join(ROOT_DIR, "catalog.min.json")

TLDS = {'com', 'org', 'net', 'io', 'gov', 'edu', 'co', 'uk', 'us', 'ca', 'de', 'fr', 'jp', 'cn', 'in', 'ch', 'cz', 'ru', 'app', 'dev'}
GENERIC_WORDS = {
    'android', 'apps', 'debug', 'release', 'basic', 'mobile',
    'ordering', 'ad', 'ads', 'client', 'main', 'phone', 'tv', 'vr',
    'lite', 'prod', 'production', 'free', 'express', 'global',
    'service', 'services', 'system', 'ui', 'wrapper', 'sdk',
    'nativeapp', 'mobilem8', 'emn8'
}

KNOWN_ACRONYMS = {
    'rro': 'Overlay',
    'ota': 'OTA Update',
    'sar': 'SAR Sensor',
    'nfc': 'NFC Service',
    'ims': 'IMS Service',
    'sms': 'SMS Service',
    'mms': 'MMS Service',
    'sim': 'SIM Toolkit',
    'stk': 'SIM Toolkit',
    'tts': 'Text-to-Speech',
    'vowifi': 'VoWiFi',
    'volte': 'VoLTE',
    'fota': 'Firmware Update',
    'dm': 'Device Management',
    'mdm': 'Device Management',
    'dsds': 'Dual SIM',
    'camerax': 'CameraX Extensions',
    'camera2': 'Camera Framework',
}

KNOWN_PREFIXES = {
    'com.google.android.': 'Google ',
    'com.android.chrome': 'Google Chrome',
    'com.android.vending': 'Google Play Store',
    'com.sec.android.app.': 'Samsung ',
    'com.samsung.android.': 'Samsung ',
    'com.motorola.': 'Motorola ',
    'com.lenovo.': 'Lenovo ',
    'com.xiaomi.': 'Xiaomi ',
    'com.miui.': 'MIUI ',
    'com.huawei.': 'Huawei ',
    'com.oppo.': 'OPPO ',
    'com.oneplus.': 'OnePlus ',
    'com.realme.': 'Realme ',
    'com.vivo.': 'Vivo ',
    'com.amazon.': 'Amazon ',
    'com.microsoft.': 'Microsoft ',
}

def derive_clean_name(pkg_name: str) -> str:
    """Fallback clean name from package ID if not on Google Play Store."""
    for prefix, brand in KNOWN_PREFIXES.items():
        if pkg_name == prefix:
            return brand.strip()
        if pkg_name.startswith(prefix):
            remainder = pkg_name[len(prefix):]
            parts = [p for p in remainder.replace('_', '.').replace('-', '.').split('.') if p]
            cleaned_parts = []
            for p in parts:
                p_lower = p.lower()
                if p_lower in KNOWN_ACRONYMS:
                    cleaned_parts.append(KNOWN_ACRONYMS[p_lower])
                elif p_lower not in TLDS and p_lower not in GENERIC_WORDS:
                    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', p).split()
                    cleaned_parts.append(" ".join(w.capitalize() for w in words if w))
            if cleaned_parts:
                return f"{brand}{' '.join(cleaned_parts)}".strip()

    # General extraction
    parts = pkg_name.split('.')
    cleaned = []
    for p in parts:
        p_lower = p.lower()
        if p_lower in TLDS:
            continue
        if p_lower in KNOWN_ACRONYMS:
            cleaned.append(KNOWN_ACRONYMS[p_lower])
        elif p_lower not in GENERIC_WORDS:
            words = re.sub(r'([a-z])([A-Z])', r'\1 \2', p.replace('_', ' ').replace('-', ' ')).split()
            cap = " ".join(w.capitalize() for w in words if w)
            if cap:
                cleaned.append(cap)
    
    if cleaned:
        return " ".join(cleaned[-2:]) if len(cleaned) >= 2 else cleaned[0]
    return parts[-1].capitalize() if parts else pkg_name

def scrape_play_store(pkg_name: str) -> str:
    """Attempts to scrape the real official app name from Google Play Store."""
    url = f"https://play.google.com/store/apps/details?id={pkg_name}&hl=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Check <h1><span>Title</span></h1>
            m = re.search(r'<h1[^>]*><span[^>]*>([^<]+)</span></h1>', html)
            if m:
                name = m.group(1).strip()
                if name:
                    return name
            # Check og:title
            m_og = re.search(r'<meta property="og:title" content="([^"]+)">', html)
            if m_og:
                title = m_og.group(1).strip()
                title = re.sub(r' - Apps on Google Play$', '', title).strip()
                if title:
                    return title
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Package not hosted on Play Store (OEM system app, overlay, carrier service)
            return ""
        print(f"    [!] HTTP {e.code} for {pkg_name}")
    except Exception as e:
        pass
    return ""

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def fetch_json(url: str):
    print(f"[*] Fetching: {url}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Android-Package-Catalog-Sync/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def sync(limit_scrape: int = None):
    cache = load_cache()
    print(f"[+] Loaded {len(cache)} existing cached titles.")

    raw_uad = fetch_json(UAD_PACKAGES_URL)
    pkg_list = list(raw_uad.keys())
    print(f"[+] Found {len(pkg_list)} total package definitions.")

    catalog = {}
    new_scrapes = 0
    
    for i, pkg_name in enumerate(pkg_list):
        if pkg_name in cache and cache[pkg_name]:
            app_name = cache[pkg_name]
        else:
            # Check if scrape limit hit for this run (to prevent GitHub Action timeouts)
            if limit_scrape is not None and new_scrapes >= limit_scrape:
                app_name = derive_clean_name(pkg_name)
            else:
                official = scrape_play_store(pkg_name)
                new_scrapes += 1
                if official:
                    app_name = official
                    cache[pkg_name] = official
                    print(f"  [{i+1}/{len(pkg_list)}] Scraped: {pkg_name} -> '{official}'")
                else:
                    app_name = derive_clean_name(pkg_name)
                    # Cache the derived clean name so we don't 404 repeatedly
                    cache[pkg_name] = app_name
                
                # Polite rate limit: 0.1s delay between web requests
                time.sleep(0.1)

                if new_scrapes % 50 == 0:
                    save_cache(cache)
                    print(f"    [i] Auto-saved cache at {len(cache)} entries.")

        # Clean simple format: all the user wants is the package name and real human name!
        catalog[pkg_name] = app_name

    save_cache(cache)
    print(f"[+] Final cache saved with {len(cache)} entries ({new_scrapes} scraped in this run).")

    # Save outputs (Formatted & Minified)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_MIN_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, separators=(',', ':'), ensure_ascii=False)

    print(f"[+] Successfully wrote {len(catalog)} packages to:")
    print(f"    - {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / 1024:.1f} KB)")
    print(f"    - {OUTPUT_MIN_JSON} ({os.path.getsize(OUTPUT_MIN_JSON) / 1024:.1f} KB)")

if __name__ == "__main__":
    limit = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])
    sync(limit_scrape=limit)
