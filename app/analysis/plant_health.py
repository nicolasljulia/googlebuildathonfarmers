import concurrent.futures
from datetime import date, datetime, timedelta

import ee

from app.config import FIELD_RADIUS_M, init_earth_engine
from app.data_sources.rules_engine import run_rules_engine
from app.data_sources.soil import get_soil_data_at_point
from app.data_sources.weather import get_weather_data
from app.earth_engine.thermal import get_ecostress_data
from app.earth_engine.vegetation import (
    compute_vegetation_indices,
    get_historical_snapshot,
    get_index_thumbnail_url,
    get_sentinel_composite,
)


def analyze_plant_health(lat, lon, crop_type, radius_m=FIELD_RADIUS_M):
    init_earth_engine()
    field = ee.Geometry.Point([lon, lat]).buffer(radius_m)
    today = date.today().strftime('%Y-%m-%d')

    one_year_ago = date.today() - timedelta(days=365)
    trend_start = (one_year_ago - timedelta(days=30)).strftime('%Y-%m-%d')
    trend_end = one_year_ago.strftime('%Y-%m-%d')

    def _fetch_soil():
        return get_soil_data_at_point(lat, lon)

    def _fetch_weather():
        return get_weather_data(lat, lon)

    def _fetch_sentinel():
        img, sat_date = get_sentinel_composite(field, '2025-01-01', today)
        if img is None:
            img, sat_date = get_sentinel_composite(field, '2024-06-01', today)
        return img, sat_date

    def _fetch_early():
        return get_sentinel_composite(field, trend_start, trend_end)

    def _fetch_history():
        return get_historical_snapshot(field, today)

    def _fetch_eco():
        return get_ecostress_data(field, lat, lon)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        f_soil = ex.submit(_fetch_soil)
        f_weather = ex.submit(_fetch_weather)
        f_sentinel = ex.submit(_fetch_sentinel)
        f_early = ex.submit(_fetch_early)
        f_history = ex.submit(_fetch_history)
        f_eco = ex.submit(_fetch_eco)

        soil = f_soil.result()
        weather = f_weather.result()
        img, satellite_date = f_sentinel.result()
        early_img, _ = f_early.result()
        historical = f_history.result()
        ecostress = f_eco.result()

    if img is None:
        return {"error": "No cloud-free satellite imagery found for this location."}

    veg = compute_vegetation_indices(img, field, early_img=early_img)

    obs = {
        "ndvi": veg["ndvi"],
        "ndmi": veg["ndmi"],
        "ndre": veg["ndre"],
        "ndwi": veg["indices"]["NDWI"]["mean"],
        "psri": veg["indices"]["PSRI"]["mean"],
        "reci": veg["indices"]["ReCI"]["mean"],
        "gci": veg["indices"]["GCI"]["mean"],
        "avg_temp_7d": weather.get("avg_temp_7d") if not weather.get("error") else None,
        "max_temp_7d": weather.get("max_temp_7d") if not weather.get("error") else None,
        "min_temp_7d": weather.get("min_temp_7d") if not weather.get("error") else None,
        "avg_rh_7d_pct": weather.get("avg_rh_7d_pct") if not weather.get("error") else None,
        "consecutive_dry_days": weather.get("consecutive_dry_days", 0) if not weather.get("error") else 0,
        "consecutive_wet_days": weather.get("consecutive_wet_days", 0) if not weather.get("error") else 0,
        "total_precip_7d_mm": weather.get("total_precip_7d_mm") if not weather.get("error") else None,
        "et0_7d_mm": weather.get("et0_7d_mm") if not weather.get("error") else None,
        "ph": soil.get("ph") if not soil.get("error") else None,
        "clay_pct": soil.get("clay_pct") if not soil.get("error") else None,
        "sand_pct": soil.get("sand_pct") if not soil.get("error") else None,
        "soc_g_kg": soil.get("soc_g_kg") if not soil.get("error") else None,
        "bulk_density": soil.get("bulk_density") if not soil.get("error") else None,
        "cec_mmol_kg": soil.get("cec_mmol_kg") if not soil.get("error") else None,
        "soil_drainage": (soil.get("drainage", "").split("—")[0].strip() if not soil.get("error") else None),
        "soil_ec_ds_m": soil.get("ec_ds_m") if not soil.get("error") else None,
        "crop_type": crop_type,
        "lst_c": ecostress.get("lst_c"),
        "et_mm_day": ecostress.get("et_mm_day"),
        "esi": ecostress.get("esi"),
    }

    risks = run_rules_engine(obs)
    risks += _legacy_risks(veg, ecostress, existing_names={r["name"] for r in risks})

    actions = [
        {"action": r["recommendation"], "urgency": r["urgency"]}
        for r in risks
        if r.get("recommendation")
    ]

    try:
        map_snapshot_url = get_index_thumbnail_url(img, field, index='NDVI')
        map_caption = "NDVI — red is stressed, green is healthy"
    except Exception as e:
        print(f"[MAP SNAPSHOT] Error: {e}")
        map_snapshot_url = None
        map_caption = None

    return {
        "ndvi": veg["ndvi"],
        "ndvi_change": veg["ndvi_change"],
        "health_status": veg["health_status"],
        "heterogeneity": veg["heterogeneity"],
        "ndvi_spread": veg["ndvi_spread"],
        "zones": veg["zones"],
        "indices": veg["indices"],
        "moisture": veg["moisture"],
        "nitrogen": veg["nitrogen"],
        "weather": weather,
        "soil": soil,
        "risks": risks,
        "actions": actions,
        "crop_type": crop_type,
        "historical": historical,
        "ecostress": ecostress,
        "map_snapshot_url": map_snapshot_url,
        "map_caption": map_caption,
        "data_sources": {
            "satellite": satellite_date,
            "weather": date.today().strftime('%d %b %Y'),
            "soil": soil.get("soil_source", "SoilGrids 2.0"),
            "thermal": f"Landsat 8/9 LST (100m) + MODIS MOD16A2 ET (500m) ({ecostress.get('date', 'not available')})",
        },
    }


def _legacy_risks(veg, ecostress, existing_names):
    risks = []
    ndvi_change = veg["ndvi_change"]
    zones = veg["zones"]
    ndvi_spread = veg["ndvi_spread"]
    mean_psri = veg["indices"]["PSRI"]["mean"]
    mean_ndwi = veg["indices"]["NDWI"]["mean"]

    if ndvi_change is not None and ndvi_change < -0.05:
        risks.append({
            "name": "Declining crop health", "level": "High",
            "detail": f"NDVI dropped {abs(ndvi_change):.2f} over 3 months",
            "recommendation": "Scout field for pest or disease damage — identify cause of decline",
            "urgency": "Within 2 days",
        })
    if zones["severe_pct"] > 15:
        risks.append({
            "name": "Severe stress zone", "level": "High",
            "detail": f"{zones['severe_pct']}% of field in severe stress (NDVI < 0.2)",
            "recommendation": "Walk severe zones immediately — check soil, pest, and disease cause",
            "urgency": "Today",
        })

    stressed_total = (zones.get("stressed_pct", 0) or 0) + (zones.get("severe_pct", 0) or 0)
    if stressed_total > 50:
        level = "High" if stressed_total > 70 else "Medium"
        risks.append({
            "name": "Widespread crop stress",
            "level": level,
            "detail": f"{stressed_total:.0f}% of field is in stress (NDVI < 0.4) — only {zones.get('healthy_pct', 0):.0f}% healthy",
            "recommendation": "Whole-field scouting required — assess water, nutrient, and pest status across zones",
            "urgency": "Within 2 days" if level == "High" else "Within 1 week",
        })
    elif stressed_total > 25:
        risks.append({
            "name": "Partial field stress",
            "level": "Medium",
            "detail": f"{stressed_total:.0f}% of field showing stress (NDVI < 0.4)",
            "recommendation": "Scout stressed areas — check irrigation uniformity and soil variability",
            "urgency": "Within 1 week",
        })

    if ndvi_spread and ndvi_spread > 0.25:
        risks.append({
            "name": "Uneven crop development", "level": "Medium",
            "detail": f"NDVI spread {ndvi_spread} — variation suggests patchy stress",
            "recommendation": "Identify and address the cause of spatial variability in the field",
            "urgency": "Within 1 week",
        })

    if mean_psri is not None:
        if mean_psri > 0.2:
            risks.append({
                "name": "Advanced canopy senescence",
                "level": "High",
                "detail": f"PSRI {round(mean_psri, 3)} — significant chlorophyll breakdown and canopy deterioration detected",
                "recommendation": "Assess crop maturity stage; if not near harvest, investigate disease, nutrient deficiency, or water stress as cause",
                "urgency": "Within 2 days",
            })
        elif mean_psri > 0.1:
            risks.append({
                "name": "Early canopy senescence",
                "level": "Medium",
                "detail": f"PSRI {round(mean_psri, 3)} — early chlorophyll degradation detected, above normal for healthy vegetation",
                "recommendation": "Monitor closely; check for early disease symptoms, nitrogen deficiency, or drought stress",
                "urgency": "Within 1 week",
            })

    if mean_ndwi is not None and mean_ndwi < -0.4:
        risks.append({
            "name": "Severe canopy water deficit",
            "level": "High",
            "detail": f"NDWI {round(mean_ndwi, 3)} — very low canopy water content indicating severe moisture stress",
            "recommendation": "Irrigate urgently if applicable; check soil moisture at root depth",
            "urgency": "Today",
        })
    elif mean_ndwi is not None and mean_ndwi < -0.2:
        risks.append({
            "name": "Canopy water stress",
            "level": "Medium",
            "detail": f"NDWI {round(mean_ndwi, 3)} — below-normal canopy water content",
            "recommendation": "Check irrigation schedule and soil moisture; consider supplemental watering",
            "urgency": "Within 2 days",
        })

    if ecostress.get("lst_c") is not None:
        if ecostress["lst_c"] > 45:
            risks.append({
                "name": "Critical land surface temperature",
                "level": "Severe",
                "detail": f"ECOSTRESS LST {ecostress['lst_c']}°C — well above crop thermal limits. Canopy temperature at this level causes irreversible cell damage.",
                "recommendation": "Irrigate immediately to cool canopy; if possible apply kaolin reflectant; halt all field operations",
                "urgency": "Today",
            })
        elif ecostress["lst_c"] > 38:
            risks.append({
                "name": "High land surface temperature",
                "level": "High",
                "detail": f"ECOSTRESS LST {ecostress['lst_c']}°C — canopy is significantly hotter than air temperature. Pollen sterility risk at flowering.",
                "recommendation": "Irrigate early morning to cool canopy; avoid nitrogen application during heat event",
                "urgency": "Within 2 days",
            })

    if ecostress.get("esi") is not None and ecostress["esi"] < 0.4:
        risks.append({
            "name": "Confirmed crop water stress (ECOSTRESS)",
            "level": "High" if ecostress["esi"] < 0.3 else "Medium",
            "detail": f"Evaporative Stress Index {ecostress['esi']} — crop is transpiring at only {round(ecostress['esi'] * 100)}% of its potential. Actual ET: {ecostress.get('et_mm_day')}mm/day.",
            "recommendation": "Irrigate based on measured ET deficit — crop water demand is confirmed by thermal data, not just modelled",
            "urgency": "Today" if ecostress["esi"] < 0.3 else "Within 2 days",
        })

    return [r for r in risks if r["name"] not in existing_names]
