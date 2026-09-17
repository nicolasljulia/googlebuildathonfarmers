import concurrent.futures
from datetime import date

import ee

from app.config import FIELD_RADIUS_M, init_earth_engine
from app.data_sources.climate import get_climate_class
from app.data_sources.crop_recommendations import (
    get_climate_matched_crops,
    get_future_crop_recommendations,
)
from app.data_sources.maxent import get_maxent_suitability
from app.data_sources.soil import get_soil_data_at_point
from app.earth_engine.vegetation import compute_vegetation_indices, get_sentinel_composite

def analyze_agronomic_recommendations(lat, lon, crop_type, radius_m=FIELD_RADIUS_M):
    init_earth_engine()
    field = ee.Geometry.Point([lon, lat]).buffer(radius_m)
    today = date.today().strftime('%Y-%m-%d')

    def _fetch_soil():
        return get_soil_data_at_point(lat, lon)

    def _fetch_climate():
        return get_climate_class(lat, lon)

    def _fetch_maxent():
        return get_maxent_suitability(lat, lon, current_crop=crop_type)

    def _fetch_sentinel():
        img, sat_date = get_sentinel_composite(field, '2025-01-01', today)
        if img is None:
            img, sat_date = get_sentinel_composite(field, '2024-06-01', today)
        return img, sat_date

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        f_soil = ex.submit(_fetch_soil)
        f_climate = ex.submit(_fetch_climate)
        f_maxent = ex.submit(_fetch_maxent)
        f_sentinel = ex.submit(_fetch_sentinel)

        soil = f_soil.result()
        climate = f_climate.result()
        maxent_crops = f_maxent.result()
        img, satellite_date = f_sentinel.result()

    mean_ndvi = mean_ndmi = None
    if img is not None:
        veg = compute_vegetation_indices(img, field)
        mean_ndvi, mean_ndmi = veg["ndvi"], veg["ndmi"]

    future_recs = get_future_crop_recommendations(
        climate, soil, mean_ndvi, mean_ndmi, crop_type
    ) if not climate.get("error") else []

    climate_matched_crops = get_climate_matched_crops(
        climate, soil, crop_type
    ) if not climate.get("error") else []

    return {
        "climate": climate,
        "soil": soil,
        "crop_type": crop_type,
        "future_crop_recommendations": future_recs,
        "climate_matched_crops": climate_matched_crops,
        "maxent_crops": maxent_crops,
        "data_sources": {
            "satellite": satellite_date,
            "soil": soil.get("soil_source", "SoilGrids 2.0"),
            "climate": "Beck et al. 2023 Köppen-Geiger 1km rasters + NASA POWER",
        },
    }
