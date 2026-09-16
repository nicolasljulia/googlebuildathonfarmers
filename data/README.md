# data/

## Committed

- `disease_library.csv` — the rule library (issues, thresholds, recommendations
  by crop/category). Small (~170KB), safe to version.

## Not committed (see .gitignore)

These are large binaries — regenerate or copy locally, never `git add` them.

- **`koppen/`** (~243MB in the original openfarm-backend) — Köppen-Geiger
  climate rasters (Beck et al. 2023). `app/data_sources/climate.py` only
  reads the `koppen_geiger_0p1.tif` file in each period/SSP folder, not the
  higher-resolution variants — so you only actually need those files, not
  the full 243MB. Fastest path: copy them from the existing backend —
  ```bash
  mkdir -p data/koppen
  cd ../openfarm_publishable/openfarm-backend/koppen
  find . -name "koppen_geiger_0p1.tif" | cpio -pdm ../../../googlebuildathonfarmers/data/koppen
  ```
  Or regenerate/convert from scratch with `scripts/convert_koppen_to_cog.py`.

- **`maxent_suitability.db`** (~80MB) — pre-sampled MaxEnt crop-suitability
  grid (98 crops x 0.5deg global grid), built by `scripts/build_maxent_db.py`
  from the raw MaxEnt TIFs (source location not in this repo either — see
  `MAXENT_TIF_SOURCE_DIR` in that script). Fastest path: copy the existing
  one — `cp ../openfarm_publishable/openfarm-backend/maxent_suitability.db data/`.

- **`maxent_tifs/`** — only needed as a fallback if `maxent_suitability.db`
  is absent (slower, per-request rasterio reads instead of a SQL lookup).
  Skip this if you have the DB.

## Why excluded

GitHub blocks pushes with files >100MB outright and warns above 50MB; these
files sit right at/above that line and change rarely, so committing them
(even via Git LFS) buys little for a lot of repo weight. If this project
grows past hackathon scope, the better home for these is a GCS bucket the
service account already has read access to, loaded via `OPENFARM_DATA_DIR`
pointed at a mounted/synced path.
