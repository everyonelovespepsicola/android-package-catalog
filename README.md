# Android Package Catalog

Curated, multi-source Android package safety & optimization catalog.

Automatically pulls from community repositories (including Universal Android Debloater next-generation and OEM device safe-lists), sanitizes store-restricted keywords, and standardizes safety ratings for developer toolkits.

## Endpoints
- **Full Catalog (Pretty):** `catalog.json`
- **Minified Catalog (Production):** `catalog.min.json`

## Safety Classifications
- `safe`: 100% safe to disable or remove with zero system impact (pure telemetry, unused accessibility tools, marketing apps).
- `optional`: Safe to disable if specific features are not used (e.g., Live Caption, cloud sync, assistant voice triggers).
- `warning`: Diagnostic tools, engineering dialer codes, or cell broadcast emergency alerts. Proceed with caution.
- `critical`: Core system frameworks, modems, RF / SAR power control, or launchers. Do not touch.

## Automation
Updates automatically every Sunday via GitHub Actions (`.github/workflows/sync.yml`).
