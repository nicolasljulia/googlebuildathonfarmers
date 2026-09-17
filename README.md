# OpenFarm Messaging

Seems to be broken: https://moscow-classifieds-chart-steal.trycloudflare.com/field-locator
New URL: https://sage-openfarm-l3rpuhkpxq-uc.a.run.app/field-locator

A WhatsApp/SMS-style chat interface for farmers, built on the same Google
Earth Engine + soil/weather/climate data stack as [OpenFarm](https://github.com/nicolasljulia/googlebuildathonfarmers)
(the drawn-field web app), but driven by natural language instead of a map.

## Conversational flow (target)

1. Farmer sends a free-text question — "how's my plant health today?",
   "how should I irrigate this week?", "what should I be planting?"
2. NLU classifies the message into one of three intents: **plant health**,
   **irrigation**, or **agronomic recommendations**.
3. Bot asks: *are you on your farm right now?*
   - **Yes** → request device location → use that exact point.
   - **No** → ask the farmer to drop a pin.
4. Bot asks *which crop* (autocomplete/lookup against the known crop list —
   no free-typed spelling to normalize).
5. Runs the matching analysis pipeline below against that single point.
6. Response is rendered as natural language only — no images/maps/tiles,
   since the channel is text/WhatsApp.

## What's in this repo so far

The **data layer** — everything upstream of step 6 — ported from
`openfarm-backend/main.py` and reorganized around a single farmer-reported
point instead of a drawn field polygon:

```
app/
  config.py                    Earth Engine init + all data file paths (env-driven)
  earth_engine/
    vegetation.py               Sentinel-2 NDVI/NDMI/NDRE/EVI/... + 1yr-ago trend
    thermal.py                  Landsat LST + MODIS ET/ESI (ECOSTRESS-style)
  data_sources/
    weather.py                   NASA POWER (7d conditions, ET0, anomaly) — no key
    soil.py                       iSDA (Africa) / POLARIS (US) / SoilGrids (global) — no key
    climate.py                    Köppen-Geiger current + projected (needs data/koppen)
    maxent.py                     98-crop bioclimatic suitability (needs data/maxent_suitability.db)
    disease_library.py            Loads data/disease_library.csv
    rules_engine.py               Threshold rules over the disease library
    crop_recommendations.py       Future-crop guidance + climate-matched crop shortlist
    soil_recommendations.py       Soil-informed irrigation guidance
  analysis/
    plant_health.py              Orchestrator for intent 1
    irrigation.py                 Orchestrator for intent 2
    agronomic.py                   Orchestrator for intent 3
  main.py                        FastAPI test endpoints (POST /analyze/plant-health etc.)
scripts/
  build_maxent_db.py             Regenerate data/maxent_suitability.db from raw TIFs
  convert_koppen_to_cog.py       Convert raw Köppen rasters to Cloud-Optimized GeoTIFF
data/
  disease_library.csv            Committed (small)
  README.md                       How to get koppen/ and maxent_suitability.db locally
```

**Not yet built:** the NLU intent classifier, the location/crop slot-filling
conversation state machine, the WhatsApp/Twilio webhook, and the
natural-language response generator (turning the structured JSON these
orchestrators return into a chat reply). That's the next phase.

Deliberately dropped from the original `/analyze` endpoint: the NDVI map
tile URL (`ndvi.getMapId`) and the photo-based disease-detection CV models
(ResNet/EfficientNet/Swin) — neither applies to a text-only, no-photo chat flow.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in EE_SERVICE_ACCOUNT_JSON for deployed use,
                        # or just run `earthengine authenticate` locally
```

See `data/README.md` for `data/koppen/` and `data/maxent_suitability.db` —
required for the climate and agronomic-recommendations paths, not committed.

Run the test API:

```bash
uvicorn app.main:app --reload
curl -X POST localhost:8000/analyze/plant-health \
  -H "content-type: application/json" \
  -d '{"lat": 36.6, "lon": -121.1, "crop_type": "Strawberry"}'
```

## Earth Engine access

Reuses the `openfarm-analytics` GCP/EE project. See the project owner for
service-account credentials, or register your own — full steps in the repo
history/PR description that introduced this data layer.
