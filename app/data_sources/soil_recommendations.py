
def get_soil_informed_recommendations(soil, mean_ndmi, mean_ndwi, mean_ndvi, weather, crop_type):
    recs = []

    clay  = soil.get("clay_pct", 0) or 0
    sand  = soil.get("sand_pct", 0) or 0
    silt  = soil.get("silt_pct", 0) or 0
    ph    = soil.get("ph", 7.0) or 7.0
    soc   = soil.get("soc_g_kg", 10) or 10
    cec   = soil.get("cec_mmol_kg", 15) or 15
    bd    = soil.get("bulk_density", 1.3) or 1.3
    texture = soil.get("texture_class", "Loam")
    drainage = soil.get("drainage", "Well drained")

    dry_days = (weather.get("consecutive_dry_days", 0) or 0) if not weather.get("error") else 0
    wet_days = (weather.get("consecutive_wet_days", 0) or 0) if not weather.get("error") else 0
    et0      = (weather.get("et0_7d_mm", 0) or 0) if not weather.get("error") else 0
    precip7  = (weather.get("total_precip_7d_mm", 0) or 0) if not weather.get("error") else 0

    
    if sand > 65 and mean_ndmi is not None and mean_ndmi < 0.0:
        recs.append({
            "category": "Irrigation",
            "priority": "High",
            "recommendation": f"Irrigate immediately and frequently",
            "detail": (
                f"Sandy soil ({sand}% sand) has very low water retention capacity — "
                f"it loses moisture 2–3× faster than loam. "
                f"NDMI of {round(mean_ndmi,3)} confirms active moisture deficit. "
                f"Apply smaller, more frequent irrigations (every 2–3 days) rather than large infrequent doses. "
                f"Drip irrigation is strongly preferred over flood irrigation on this soil type."
            ),
        })

    
    elif clay > 35 and mean_ndwi is not None and mean_ndwi > 0.0:
        recs.append({
            "category": "Irrigation",
            "priority": "Low",
            "recommendation": "Do not irrigate — waterlogging risk",
            "detail": (
                f"Clay-dominant soil ({clay}% clay) drains very slowly. "
                f"NDWI of {round(mean_ndwi,3)} indicates surface moisture is already elevated. "
                f"Adding water now risks waterlogging, root anoxia, and fungal disease. "
                f"Allow soil to dry before any irrigation. Check field drainage first."
            ),
        })

    
    elif 25 < clay <= 40 and mean_ndmi is not None and mean_ndmi < 0.05:
        recs.append({
            "category": "Irrigation",
            "priority": "Medium",
            "recommendation": "Irrigate moderately — clay loam holds water well",
            "detail": (
                f"Clay loam soil ({clay}% clay) has good water retention. "
                f"NDMI of {round(mean_ndmi,3)} suggests mild moisture stress. "
                f"Apply a single moderate irrigation and wait 5–7 days before reassessing. "
                f"Over-irrigation on this soil causes compaction and reduces aeration."
            ),
        })

    
    elif sand <= 65 and clay <= 25 and mean_ndmi is not None and mean_ndmi < -0.05:
        urgency = "Within 2 days" if dry_days > 7 else "Within 4 days"
        recs.append({
            "category": "Irrigation",
            "priority": "Medium",
            "recommendation": f"Irrigate — loam soil approaching stress threshold",
            "detail": (
                f"Loam/silt loam soil has balanced drainage — good water holding without waterlogging risk. "
                f"NDMI of {round(mean_ndmi,3)} and {dry_days} consecutive dry days indicate growing moisture deficit. "
                f"ET₀ this week was {et0}mm vs {precip7}mm rainfall — water demand exceeds supply. "
                f"Recommended: irrigate to field capacity. {urgency}."
            ),
        })

    
    elif mean_ndmi is not None and mean_ndmi >= 0.15:
        recs.append({
            "category": "Irrigation",
            "priority": "None",
            "recommendation": "No irrigation needed",
            "detail": (
                f"NDMI of {round(mean_ndmi,3)} indicates adequate canopy moisture. "
                f"{'Clay' if clay > 35 else 'Sandy' if sand > 65 else 'Loam'} soil type "
                f"is currently holding sufficient water. Monitor again in 5 days."
            ),
        })

    
    if soc < 8:
        water_impact = "significantly reducing water retention" if sand > 50 else "limiting nutrient cycling"
        recs.append({
            "category": "Soil Health",
            "priority": "Medium",
            "recommendation": "Improve organic matter — low SOC detected",
            "detail": (
                f"Soil organic carbon is {soc} g/kg — below the 8 g/kg threshold for good soil health. "
                f"On {texture} soil, low SOC is {water_impact}. "
                f"Recommendations: incorporate crop residues rather than burning, "
                f"apply compost at 2–4 t/ha, or introduce a legume cover crop in the off-season. "
                f"Even a 1% increase in SOM can increase water holding capacity by ~20,000 L/ha."
            ),
        })

    
    if ph < 5.5:
        crop_sensitivity = {
            "maize": "Maize is moderately sensitive to acidity — yields drop significantly below pH 5.5.",
            "wheat": "Wheat is sensitive to aluminum toxicity at low pH. Performance will be poor below 5.5.",
            "soybean": "Soybean rhizobium nitrogen fixation fails below pH 5.8. Critical to lime before planting.",
            "potato": "Potato tolerates mild acidity but scab risk increases above pH 5.5 — lime with caution.",
            "beans": "Common beans are highly sensitive to acidity. Liming is strongly recommended.",
            "rice": "Flooded rice is more tolerant of acidity than upland crops. Monitor but less urgent.",
        }.get(crop_type, f"{crop_type.capitalize()} may experience reduced nutrient uptake at this pH.")
        recs.append({
            "category": "Soil Chemistry",
            "priority": "High" if ph < 5.0 else "Medium",
            "recommendation": f"Apply lime to correct soil acidity (pH {ph})",
            "detail": (
                f"Soil pH of {ph} is below the optimal range (6.0–7.0) for most crops. "
                f"At this pH, phosphorus, calcium, and magnesium availability is reduced, "
                f"and aluminum and manganese toxicity become risks. "
                f"{crop_sensitivity} "
                f"Recommended: apply agricultural lime at 1–3 t/ha depending on buffer pH. "
                f"Re-test soil after 6 months."
            ),
        })

    
    if ph > 7.8:
        recs.append({
            "category": "Soil Chemistry",
            "priority": "Medium",
            "recommendation": f"Alkaline soil detected (pH {ph}) — monitor micronutrient deficiency",
            "detail": (
                f"Soil pH of {ph} is above 7.8. Iron, zinc, manganese, and boron availability "
                f"decrease sharply in alkaline soils. If NDRE is low, this may be contributing "
                f"to apparent nitrogen deficiency symptoms. "
                f"Recommended: apply chelated micronutrients (EDTA-Fe, zinc sulfate), "
                f"use ammonium-based fertilizers over nitrate-based, and consider elemental sulfur "
                f"at 200–500 kg/ha to gradually lower pH."
            ),
        })

    
    if bd > 1.5:
        recs.append({
            "category": "Soil Structure",
            "priority": "Medium",
            "recommendation": "High bulk density — possible compaction",
            "detail": (
                f"Bulk density of {bd} g/cm³ is above 1.5 — indicating potential compaction. "
                f"On {texture} soil, compaction restricts root penetration, reduces water infiltration, "
                f"and limits nutrient uptake. "
                f"Recommended: avoid heavy machinery on wet soil, subsoil till if compaction is confirmed, "
                f"and plant deep-rooted cover crops (radish, sunflower) to break up compaction layers."
            ),
        })

    
    if sand > 60 and cec < 10:
        recs.append({
            "category": "Nutrient Management",
            "priority": "Medium",
            "recommendation": "Low CEC on sandy soil — split fertilizer applications",
            "detail": (
                f"Sandy soil with CEC of {cec} mmol/kg cannot hold nutrients effectively. "
                f"Standard broadcast fertilizer applications will result in significant leaching — "
                f"especially nitrogen and potassium. "
                f"Recommended: split all fertilizer applications into 3–4 smaller doses throughout "
                f"the season. Fertigation (fertilizer through irrigation) is ideal for this soil type. "
                f"Consider polymer-coated slow-release fertilizers."
            ),
        })

    
    if mean_ndvi is not None and mean_ndvi < 0.4 and (soc < 8 or bd > 1.5 or ph < 5.5):
        soil_issues = []
        if soc < 8:  soil_issues.append(f"low organic carbon ({soc} g/kg)")
        if bd > 1.5: soil_issues.append(f"high bulk density ({bd} g/cm³)")
        if ph < 5.5: soil_issues.append(f"acidic pH ({ph})")
        recs.append({
            "category": "Combined Risk",
            "priority": "High",
            "recommendation": "Satellite stress linked to soil constraints",
            "detail": (
                f"NDVI of {round(mean_ndvi,3)} indicates stressed crop, and soil analysis shows: "
                f"{', '.join(soil_issues)}. These soil conditions are likely contributing to or "
                f"compounding the satellite-detected stress. Addressing soil constraints will "
                f"improve the crop's resilience to future stress events."
            ),
        })

    return recs
