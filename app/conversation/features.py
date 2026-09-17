from app.analysis.agronomic import analyze_agronomic_recommendations
from app.analysis.crop_suitability import analyze_crop_suitability
from app.analysis.irrigation import analyze_irrigation
from app.analysis.plant_health import analyze_plant_health
from app.analysis.spectral_indices import analyze_spectral_indices
from app.analysis.weather_report import analyze_weather_forecast, analyze_weather_past


def _fmt_pct(v):
    return f"{v}%" if v is not None else "unknown"


def format_plant_health(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    lines = [
        f"Crop health: {result['health_status']} (NDVI {result['ndvi']})",
        f"Moisture: {result['moisture']} | Nitrogen: {result['nitrogen']}",
    ]
    if result.get("ndvi_change"):
        direction = "up" if result["ndvi_change"] > 0 else "down"
        lines.append(f"Trend vs last year: {direction} {abs(result['ndvi_change'])}")

    risks = result.get("risks", [])
    if risks:
        lines.append("")
        lines.append("Top issues:")
        for r in risks[:3]:
            lines.append(f"- [{r['level']}] {r['name']}: {r.get('recommendation', '')}")
    else:
        lines.append("")
        lines.append("No significant issues detected.")

    return "\n".join(lines)


def format_irrigation(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    lines = [
        f"Moisture status: {result['moisture_status']}",
    ]

    daily = result.get("daily_irrigation")
    if daily:
        amount = daily["net_irrigation_mm_day"]
        if amount > 0:
            lines.append(
                f"Irrigate about {amount} mm/day "
                f"({daily['crop_matched']}, {daily['growth_stage']} stage, Kc {daily['kc']})"
            )
        else:
            lines.append(
                f"No irrigation needed today — recent rainfall covers crop water demand "
                f"({daily['crop_matched']}, {daily['growth_stage']} stage)"
            )

    if result.get("et_mm_day") is not None:
        lines.append(f"Evapotranspiration: {result['et_mm_day']} mm/day ({result.get('et_status', 'n/a')})")

    recs = result.get("recommendations", [])
    if recs:
        lines.append("")
        top = recs[0]
        lines.append(f"Recommendation: {top['recommendation']}")
        lines.append(top["detail"])
    else:
        lines.append("")
        lines.append("No specific irrigation action needed right now.")

    return "\n".join(lines)


def format_agronomic(result):
    lines = []
    climate = result.get("climate", {})
    if climate and not climate.get("error"):
        lines.append(f"Current climate zone: {climate.get('name')} ({climate.get('koppen')})")
        if climate.get("climate_shifting"):
            lines.append(f"Climate is projected to shift ({climate.get('shift_direction')}).")

    matched = result.get("climate_matched_crops", [])
    if matched:
        lines.append("")
        lines.append("Crops well-matched to your climate:")
        for c in matched[:3]:
            lines.append(f"- {c['crop']} ({c['score']}% match)")

    future = result.get("future_crop_recommendations", [])
    if future:
        lines.append("")
        lines.append("Longer-term guidance:")
        for f in future[:2]:
            lines.append(f"- [{f['horizon']}] {f['title']}")

    maxent = result.get("maxent_crops", [])
    if maxent:
        lines.append("")
        lines.append("Highest-suitability crops for this location:")
        for m in maxent[:3]:
            lines.append(f"- {m['crop']}: {m['category']} ({_fmt_pct(m['suitability_pct'])})")

    if not lines:
        return "No agronomic recommendations available for this location."
    return "\n".join(lines)


def format_crop_suitability(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    matched = result.get("climate_matched_crops", [])
    if not matched:
        return "No well-matched crops found for this location's climate and soil profile."

    top = matched[0]
    if top.get("zone_changed"):
        subtitle = f"Scored against projected {top.get('future_zone')} conditions by 2071"
    else:
        koppen = result.get("climate", {}).get("koppen")
        subtitle = f"Scored against current {koppen} conditions and your soil profile"

    lines = ["Best-matched crops for your future conditions", subtitle, ""]
    for c in matched:
        lines.append(f"{c['crop']} — {c['score']}% match")
        reasons = c.get("match_reasons", [])
        if reasons:
            lines.append("  " + " · ".join(reasons))
        warnings = c.get("match_warnings", [])
        if warnings:
            lines.append("  Note: " + " · ".join(warnings))
        lines.append("")

    lines.append("Scored against perfect growing conditions in the OpenFarm disease library.")
    return "\n".join(lines).rstrip()


INDEX_RATING_THRESHOLDS = {
    "NDVI":  (0.3, 0.5, True),
    "EVI":   (0.2, 0.4, True),
    "MSAVI": (0.2, 0.4, True),
    "GNDVI": (0.4, 0.6, True),
    "NDMI":  (0.0, 0.2, True),
    "NDWI":  (-0.3, -0.1, True),
    "NDRE":  (0.2, 0.35, True),
    "ReCI":  (0.5, 1.0, True),
    "GCI":   (1.0, 2.5, True),
    "PSRI":  (0.1, 0.2, False),
}


def _rate_index(name, value):
    if value is None:
        return "Unknown"
    thresholds = INDEX_RATING_THRESHOLDS.get(name)
    if not thresholds:
        return "Unknown"
    poor_max, moderate_max, higher_is_better = thresholds
    if higher_is_better:
        if value < poor_max:
            return "Poor"
        if value < moderate_max:
            return "Moderate"
        return "Good"
    else:
        if value > moderate_max:
            return "Poor"
        if value > poor_max:
            return "Moderate"
        return "Good"


def format_spectral_indices(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    lines = [f"Spectral indices (Sentinel-2, {result.get('satellite_date', 'recent')}):", ""]
    for name, d in result.get("indices", {}).items():
        rating = _rate_index(name, d["mean"])
        lines.append(f"{name}: {d['mean']} — {rating}")
    return "\n".join(lines)


def format_weather_past(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    lines = [
        f"Avg temp: {result.get('avg_temp_7d')}°C | Max: {result.get('max_temp_7d')}°C",
        f"Total rainfall: {result.get('total_precip_7d_mm')}mm",
        f"Avg humidity: {result.get('avg_rh_7d_pct')}%",
    ]
    if result.get("consecutive_dry_days"):
        lines.append(f"Consecutive dry days: {result['consecutive_dry_days']}")
    if result.get("consecutive_wet_days"):
        lines.append(f"Consecutive wet days: {result['consecutive_wet_days']}")
    if result.get("precip_anomaly_pct") is not None:
        direction = "above" if result["precip_anomaly_pct"] > 0 else "below"
        lines.append(f"Rainfall is {abs(result['precip_anomaly_pct'])}% {direction} normal for this time of year")
    return "\n".join(lines)


def format_weather_forecast(result):
    if result.get("error"):
        return f"Couldn't run this check: {result['error']}"

    lines = [
        f"7-day outlook: {result['total_precip_mm']}mm total rain expected",
        f"Temps: {result['avg_temp_min_c']}-{result['avg_temp_max_c']}°C average",
        "",
    ]
    for d in result["days"]:
        lines.append(f"{d['date']}: {d['temp_min_c']}-{d['temp_max_c']}°C, {d['precip_mm']}mm rain")
    return "\n".join(lines)


FEATURE_REGISTRY = [
    {
        "id": "irrigation",
        "label": "Irrigation for the next week",
        "run": analyze_irrigation,
        "format": format_irrigation,
    },
    {
        "id": "plant_health",
        "label": "Crop health today",
        "run": analyze_plant_health,
        "format": format_plant_health,
    },
    {
        "id": "agronomic",
        "label": "Long-term crop & climate recommendations",
        "run": analyze_agronomic_recommendations,
        "format": format_agronomic,
    },
    {
        "id": "crop_suitability",
        "label": "Best crops for your climate",
        "run": analyze_crop_suitability,
        "format": format_crop_suitability,
    },
    {
        "id": "spectral_indices",
        "label": "Spectral indices",
        "run": analyze_spectral_indices,
        "format": format_spectral_indices,
    },
    {
        "id": "weather_past",
        "label": "Weather — past week",
        "run": analyze_weather_past,
        "format": format_weather_past,
    },
    {
        "id": "weather_forecast",
        "label": "Weather — next week",
        "run": analyze_weather_forecast,
        "format": format_weather_forecast,
    },
]

FEATURES_BY_ID = {f["id"]: f for f in FEATURE_REGISTRY}
