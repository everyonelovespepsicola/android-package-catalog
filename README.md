# Android Package Optimization & Safety Catalog

An automated, sanitized, multi-source catalog of Android packages providing safety classifications, feature descriptions, and system impact evaluations.

This dataset powers application-level package managers, ADB utilities, and optimization tools (such as **Sideloader - ADB Toolkit**), allowing developers and power users to identify, inspect, and safely freeze or remove unused OEM, carrier, and ambient background services without breaking their devices.

---

## 📌 Where This Data Is Extrapolated From

This catalog is not created in isolation—it aggregates, refines, and normalizes crowdsourced intelligence tested across thousands of real-world Android devices:

1. **Universal Android Debloater Alliance (UAD-NG):**
   * **Source:** [Universal-Debloater-Alliance/universal-android-debloater-next-generation](https://github.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation)
   * The community benchmark for Android package definitions, maintaining active documentation of package behavior across hundreds of device manufacturers.
2. **Community Safe-Lists & OEM Hardware Matrices:**
   * Extrapolates verified package listings across OEM firmware builds (Samsung One UI, Xiaomi HyperOS/MIUI, Motorola/Lenovo ZUI & MyUI, Google Pixel, Huawei EMUI, BBK/Oppo/OnePlus ColorOS).
3. **Android Open Source Project (AOSP) & Hardware Layer Docs:**
   * Baseband and radio documentation identifying critical hardware abstraction layers (e.g., SAR radio power management daemons, SurfaceFlinger, Telephony providers).

---

## 🛡️ Sanitization & Store Compliance

Many raw community repositories contain informal or provocative language (e.g., terms like *spyware*, *bloatware*, *nuke*, *malware*) and binary uninstall commands that flag app-store security heuristics.

This repository runs an automated pipeline (`sync.py`) that:
- **Sanitizes Terminology:** Replaces store-sensitive terms with standardized engineering and optimization terminology.
- **Normalizes Risk Ratings:** Translates subjective community removal flags into uniform safety tiers suitable for consumer desktop applications (such as apps distributed via the Microsoft Store).
- **Separates Safe Freezing from Critical Hardware:** Clearly distinguishes between non-essential background services and critical radio/modem daemons.

---

## 🚦 Safety Classifications

Each entry in the catalog is assigned a safety level:

| Safety Tier | Action Guidance | Description | Examples |
| :--- | :--- | :--- | :--- |
| **`safe`** | Low Risk | 100% safe to disable or remove. Has no dependencies in Android framework. Pure analytics, redundant pre-installed apps, or ad training. | `com.google.android.federatedcompute`, `com.facebook.katana`, `com.amazon.mShop.android.shopping` |
| **`optional`** | Medium Risk | Safe to disable if you do not use the specific feature. Disabling will cleanly turn off that feature without causing crashes. | `com.google.android.as.oss` (Live Caption), `com.google.android.marvin.talkback` (Screen reader), `com.microsoft.skydrive` (Cloud sync) |
| **`warning`** | High Risk | Proceed with caution. Often tied to carrier services, diagnostic dialer codes, or emergency alert receivers. | `com.zui.SecretCode` (Dialer engineering menus), `com.google.android.cellbroadcastreceiver` (AMBER & disaster sirens) |
| **`critical`** | Do Not Touch | **Essential system component.** Removing or disabling may cause bootloops, UI crashes, or radio/modem failure. | `com.android.systemui`, `com.sar.main` (RF power compliance), default launchers |

---

## 📦 Distribution Endpoints

The catalog is automatically built into two formats:

- **Pretty JSON:** [`catalog.json`](https://raw.githubusercontent.com/everyonelovespepsicola/android-package-catalog/main/catalog.json) (human-readable, complete metadata).
- **Minified JSON:** [`catalog.min.json`](https://raw.githubusercontent.com/everyonelovespepsicola/android-package-catalog/main/catalog.min.json) (compressed, low-latency distribution for apps and CLI tools).

### Schema Sample
```json
{
  "com.google.android.federatedcompute": {
    "packageName": "com.google.android.federatedcompute",
    "category": "aosp",
    "safety": "safe",
    "description": "FederatedCompute. On-device machine learning optimization for personal devices. Introduced in Android 13."
  },
  "com.sar.main": {
    "packageName": "com.sar.main",
    "category": "misc",
    "safety": "critical",
    "description": "Specific Absorption Rate (SAR) radio-frequency power manager. Do not disable: regulates radio transmission power and wireless stability."
  }
}
```

---

## 🔄 Automated Updates

This repository is maintained autonomously:
* A scheduled GitHub Actions workflow (`.github/workflows/sync.yml`) runs **weekly every Sunday at 03:00 UTC**.
* It fetches the latest upstream contributions, runs the sanitization filter, updates both JSON catalogs, and commits new definitions automatically.

---

## 📄 License & Attribution

- Upstream package intelligence is credited to the contributors of the [Universal Android Debloater Alliance](https://github.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation) and the global Android reverse-engineering community.
- Distributed under the [MIT License](LICENSE).
