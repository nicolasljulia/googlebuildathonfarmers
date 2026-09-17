from app.data_sources.forecast import get_weather_forecast
from app.data_sources.weather import get_weather_data


def analyze_weather_past(lat, lon, crop_type):
    return get_weather_data(lat, lon)


def analyze_weather_forecast(lat, lon, crop_type):
    return get_weather_forecast(lat, lon)
