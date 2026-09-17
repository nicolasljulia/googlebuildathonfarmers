import requests


def get_weather_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except Exception as e:
        return {"error": str(e)}

    days = []
    for i, date_str in enumerate(daily["time"]):
        days.append({
            "date": date_str,
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precip_mm": daily["precipitation_sum"][i],
            "et0_mm": daily.get("et0_fao_evapotranspiration", [None] * len(daily["time"]))[i],
        })

    precip_vals = [d["precip_mm"] for d in days if d["precip_mm"] is not None]
    tmax_vals = [d["temp_max_c"] for d in days if d["temp_max_c"] is not None]
    tmin_vals = [d["temp_min_c"] for d in days if d["temp_min_c"] is not None]

    return {
        "days": days,
        "total_precip_mm": round(sum(precip_vals), 1) if precip_vals else None,
        "avg_temp_max_c": round(sum(tmax_vals) / len(tmax_vals), 1) if tmax_vals else None,
        "avg_temp_min_c": round(sum(tmin_vals) / len(tmin_vals), 1) if tmin_vals else None,
        "source": "Open-Meteo forecast API",
    }
