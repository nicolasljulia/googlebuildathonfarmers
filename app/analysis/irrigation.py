import concurrent.futures
from datetime import date

import ee

from app.config import init_earth_engine
from app.data_sources.soil import get_soil_data_at_point
from app.data_sources.soil_recommendations import get_soil_informed_recommendations
from app.data_sources.weather import get_weather_data
from app.earth_engine.thermal import get_ecostress_data
from app.earth_engine.vegetation import compute_vegetation_indices, get_sentinel_composite

DEFAULT_FIELD_RADIUS_M = 60


def analyze_irrigation(lat, lon, crop_type, radius_m=DEFAULT_FIELD_RADIUS_M):
    init_earth_engine()
    field = ee.Geometry.Point([lon, lat]).buffer(radius_m)
    today = date.today().strftime('%Y-%m-%d')

    def _fetch_soil():
        return get_soil_data_at_point(lat, lon)

    def _fetch_weather():
        return get_weather_data(lat, lon)

    def _fetch_sentinel():
        img, sat_date = get_sentinel_composite(field, '2025-01-01', today)
        if img is None:
            img, sat_date = get_sentinel_composite(field, '2024-06-01', today)
        return img, sat_date

    def _fetch_eco():
        return get_ecostress_data(field, lat, lon)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        f_soil = ex.submit(_fetch_soil)
        f_weather = ex.submit(_fetch_weather)
        f_sentinel = ex.submit(_fetch_sentinel)
        f_eco = ex.submit(_fetch_eco)

        soil = f_soil.result()
        weather = f_weather.result()
        img, satellite_date = f_sentinel.result()
        ecostress = f_eco.result()

    if img is None:
        return {"error": "No cloud-free satellite imagery found for this location."}

    veg = compute_vegetation_indices(img, field)
    mean_ndwi = veg["indices"]["NDWI"]["mean"]

    soil_recs = get_soil_informed_recommendations(
        soil, veg["ndmi"], mean_ndwi, veg["ndvi"], weather, crop_type
    ) if not soil.get("error") else []

    return {
        "moisture_status": veg["moisture"],
        "ndmi": veg["ndmi"],
        "ndwi": mean_ndwi,
        "et_mm_day": ecostress.get("et_mm_day"),
        "esi": ecostress.get("esi"),
        "et_status": ecostress.get("et_status"),
        "weather": weather,
        "soil": soil,
        "recommendations": soil_recs,
        "crop_type": crop_type,
        "data_sources": {
            "satellite": satellite_date,
            "weather": date.today().strftime('%d %b %Y'),
            "soil": soil.get("soil_source", "SoilGrids 2.0"),
            "thermal": f"Landsat 8/9 LST (100m) + MODIS MOD16A2 ET (500m) ({ecostress.get('date', 'not available')})",
        },
    }
