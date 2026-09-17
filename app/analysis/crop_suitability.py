from app.data_sources.climate import get_climate_class
from app.data_sources.crop_recommendations import get_climate_matched_crops
from app.data_sources.soil import get_soil_data_at_point


def analyze_crop_suitability(lat, lon, crop_type):
    climate = get_climate_class(lat, lon)
    soil = get_soil_data_at_point(lat, lon)

    matched_crops = get_climate_matched_crops(climate, soil, crop_type)

    return {
        "climate": climate,
        "soil": soil,
        "crop_type": crop_type,
        "climate_matched_crops": matched_crops,
        "data_sources": {
            "soil": soil.get("soil_source", "SoilGrids 2.0"),
            "climate": "Beck et al. 2023 Köppen-Geiger 1km rasters + NASA POWER",
        },
    }
