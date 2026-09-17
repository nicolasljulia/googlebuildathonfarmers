from datetime import date

import ee

from app.config import FIELD_RADIUS_M, init_earth_engine
from app.earth_engine.vegetation import compute_vegetation_indices, get_sentinel_composite


def analyze_spectral_indices(lat, lon, crop_type, radius_m=FIELD_RADIUS_M):
    init_earth_engine()
    field = ee.Geometry.Point([lon, lat]).buffer(radius_m)
    today = date.today().strftime('%Y-%m-%d')

    img, satellite_date = get_sentinel_composite(field, '2025-01-01', today)
    if img is None:
        img, satellite_date = get_sentinel_composite(field, '2024-06-01', today)
    if img is None:
        return {"error": "No cloud-free satellite imagery found for this location."}

    veg = compute_vegetation_indices(img, field)

    return {
        "indices": veg["indices"],
        "satellite_date": satellite_date,
        "crop_type": crop_type,
    }
