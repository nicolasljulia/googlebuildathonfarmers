from app.analysis.agronomic import analyze_agronomic_recommendations
from app.analysis.irrigation import analyze_irrigation
from app.analysis.plant_health import analyze_plant_health


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
]

FEATURES_BY_ID = {f["id"]: f for f in FEATURE_REGISTRY}
