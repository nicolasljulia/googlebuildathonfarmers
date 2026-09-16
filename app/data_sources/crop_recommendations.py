from app.data_sources.disease_library import DISEASE_LIBRARY

def get_future_crop_recommendations(climate, soil, mean_ndvi, mean_ndmi, crop_type):
    recs = []

    hist_code  = climate.get("koppen", "Cfb")
    shift_dir  = climate.get("shift_direction")
    shifting   = climate.get("climate_shifting", False)
    near_585   = climate.get("near_future", {}).get("ssp585", {}).get("code")
    far_585    = climate.get("far_future",  {}).get("far_future", {}).get("ssp585", {})
    far_126    = climate.get("far_future",  {}).get("ssp126", {}).get("code")
    far_585c   = climate.get("far_future",  {}).get("ssp585", {}).get("code")

    ph      = soil.get("ph",          7.0) or 7.0
    sand    = soil.get("sand_pct",    30)  or 30
    clay    = soil.get("clay_pct",    30)  or 30
    soc     = soil.get("soc_g_kg",    10)  or 10
    cec     = soil.get("cec_mmol_kg", 15)  or 15
    texture = soil.get("texture_class","Loam")
    crop    = crop_type.lower()

    ann_precip = climate.get("ann_precip_mm") or 800
    ann_temp   = climate.get("ann_temp_c")    or 20

    
    if shift_dir == "aridification":
        recs.append({
            "horizon": "5–15 years",
            "title": "Transition toward drought-tolerant crops",
            "detail": (
                f"Your location is projected to shift from {hist_code} toward drier conditions "
                f"({far_585c or near_585} by 2071 under high emissions). "
                f"Begin introducing drought-tolerant varieties or crops now — "
                + ({
                    "maize":    "drought-tolerant maize hybrids (DT maize) or replace with sorghum in the driest years.",
                    "wheat":    "CIMMYT drought-tolerant wheat varieties or dual-purpose barley.",
                    "rice":     "aerobic or upland rice varieties; reduce paddy area in favour of sorghum or cowpea.",
                    "potato":   "move potato to cooler/wetter seasons only; introduce sweet potato as a dry-season alternative.",
                    "beans":    "cowpea or tepary bean, which tolerate 30% less rainfall than common bean.",
                    "coffee":   "shade-grown Robusta or Liberica; Arabica will face severe heat stress.",
                    "banana":   "plantain varieties with higher drought tolerance; reduce overall area.",
                }.get(crop,
                    f"explore sorghum, millet, cowpea, or cassava as more resilient alternatives to {crop}."
                ))
            )
        })
        recs.append({
            "horizon": "Now",
            "title": "Build soil water storage before aridification accelerates",
            "detail": (
                f"Your {texture} soil currently holds "
                f"{'limited' if sand > 55 else 'moderate'} water. "
                f"SOC at {soc} g/kg — every 1% increase in soil organic matter adds ~20,000 L/ha "
                f"water holding capacity. Apply compost at 3–5 t/ha annually, retain all crop residues, "
                f"and introduce a legume cover crop in the off-season. "
                f"This is the single highest-return investment for drought resilience."
            )
        })
        if sand > 55:
            recs.append({
                "horizon": "2–5 years",
                "title": "Install water harvesting infrastructure",
                "detail": (
                    f"Sandy soil ({sand}% sand) drains rapidly and will lose water faster under aridification. "
                    f"Consider tied ridges, half-moon catchments, or zai pits to capture rainfall. "
                    f"Micro-irrigation (drip or pitcher) will become economically necessary within 10 years "
                    f"at current climate trajectories."
                )
            })

    elif shift_dir == "moistening":
        recs.append({
            "horizon": "5–15 years",
            "title": "Prepare drainage and disease management for wetter conditions",
            "detail": (
                f"Projected shift from {hist_code} toward wetter conditions means fungal and bacterial "
                f"disease pressure will increase significantly. "
                f"Invest in field drainage now — raised beds or ridge-furrow systems on your "
                f"{texture} soil. Select disease-resistant varieties. "
                + ({
                    "maize":  "Grey leaf spot and northern blight will become more frequent.",
                    "wheat":  "Fusarium head blight and septoria are the primary risks.",
                    "potato": "Late blight pressure will intensify — resistant varieties are critical.",
                    "coffee": "Coffee leaf rust will spread to higher altitudes.",
                    "banana": "Black Sigatoka will require more frequent fungicide cycles.",
                }.get(crop, f"Scout regularly for new fungal and bacterial diseases in {crop}."))
            )
        })

    elif shift_dir == "continentalization":
        recs.append({
            "horizon": "5–15 years",
            "title": "Adapt to hotter summers and colder winters",
            "detail": (
                f"Shift from {hist_code} toward a more continental climate means more extreme temperatures "
                f"in both directions. Select varieties with wide temperature tolerance. "
                f"Winter frost risk increases — protect perennial crops. "
                f"Summer heat stress at flowering will become a more frequent yield constraint. "
                f"Barley, rye, and winter wheat are better adapted to this trajectory than maize."
            )
        })

    elif shift_dir == "warming" or shift_dir == "tropicalization":
        recs.append({
            "horizon": "5–15 years",
            "title": "Warming climate opens new crop opportunities",
            "detail": (
                f"Shift from {hist_code} toward warmer conditions by 2041–2070. "
                f"Crops currently limited by temperature (sugarcane, banana, cassava) will become viable. "
                f"Existing crops face higher pest and disease pressure year-round as winters become milder. "
                f"Pollinators and beneficial insects will also shift — monitor carefully."
            )
        })

    elif shift_dir == "zone_shift":
        recs.append({
            "horizon": "5–15 years",
            "title": "Climate zone boundary is moving through your farm",
            "detail": (
                f"This location sits near a Köppen-Geiger zone boundary that will shift "
                f"from {hist_code} ({climate.get('name')}) under all emissions scenarios. "
                f"Even under low emissions ({far_126}), conditions will change. "
                f"Diversify your crop mix now to hedge across possible futures."
            )
        })

    
    if soc < 8 and shifting:
        recs.append({
            "horizon": "Now — urgent",
            "title": "Low organic matter is your biggest climate vulnerability",
            "detail": (
                f"SOC of {soc} g/kg gives this {texture} soil almost no buffer against climate extremes. "
                f"Under any climate trajectory, low SOC means faster moisture loss, weaker nutrient cycling, "
                f"and lower yield stability. Target 15+ g/kg SOC through compost, cover crops, and "
                f"minimum tillage. This is the most cost-effective climate adaptation available."
            )
        })

    if ph < 5.5 and shift_dir == "aridification":
        recs.append({
            "horizon": "This season",
            "title": "Lime before aridification worsens aluminium toxicity",
            "detail": (
                f"Acid soils (pH {ph}) concentrate toxic Al3+ and Mn2+ as they dry. "
                f"Under aridification, drying-rewetting cycles will intensify this effect. "
                f"Apply agricultural lime at 2–3 t/ha now; target pH 6.0–6.5. "
                f"This also improves P availability and reduces {crop} sensitivity to drought."
            )
        })

    if clay > 40 and shift_dir in ("moistening", None):
        recs.append({
            "horizon": "2–5 years",
            "title": "Clay soil drainage is critical under any wetter scenario",
            "detail": (
                f"Heavy clay ({clay}% clay) will waterlog rapidly under increased rainfall. "
                f"Install subsurface drainage or switch to raised-bed cropping systems. "
                f"Gypsum at 1–2 t/ha improves clay structure and drainage capacity."
            )
        })

    
    crops_at_risk_under_arid = {
        "rice", "potato", "wheat", "lettuce", "spinach", "strawberry",
        "barley", "oats", "tea", "coffee", "apple", "grape"
    }
    crops_resilient_under_arid = {
        "sorghum", "millet", "cassava", "cowpea", "groundnut",
        "cotton", "sesame", "pigeon pea", "okra"
    }

    if shift_dir == "aridification" and crop in crops_at_risk_under_arid:
        recs.append({
            "horizon": "10–20 years",
            "title": f"{crop.capitalize()} may not be viable here long-term",
            "detail": (
                f"{crop.capitalize()} requires reliable moisture that this location will increasingly "
                f"lack under aridification. Plan now for a 10–20 year transition. "
                f"Identify an alternative primary crop, diversify income streams, and "
                f"use {crop} only in the wettest years or with full irrigation."
            )
        })

    if shift_dir == "aridification" and crop not in crops_at_risk_under_arid:
        recs.append({
            "horizon": "10–20 years",
            "title": f"{crop.capitalize()} is relatively well-positioned for this climate trajectory",
            "detail": (
                f"{crop.capitalize()} has moderate to good drought tolerance. "
                f"Focus on variety selection within {crop} rather than crop substitution — "
                f"drought-tolerant varieties can maintain 70–80% of yield under 30% less rainfall."
            )
        })

    return recs


def _koppen_to_climate_envelope(code):
    
    if code == "Af":  return (18, 32, 35)   
    if code == "Am":  return (18, 32, 22)   
    if code == "Aw":  return (18, 36, 8)    

    
    if code == "BWh": return (18, 42, 2)    
    if code == "BWk": return (-5, 28, 2)    
    if code == "BSh": return (18, 38, 5)    
    if code == "BSk": return (-5, 32, 5)    

    
    if code == "Csa": return (2, 34, 8)    
    if code == "Csb": return (2, 24, 10)   
    if code == "Csc": return (2, 18, 10)   
    if code == "Cwa": return (5, 34, 14)   
    if code == "Cwb": return (5, 24, 14)   
    if code == "Cwc": return (5, 18, 12)   
    if code == "Cfa": return (2, 34, 20)   
    if code == "Cfb": return (2, 22, 18)   
    if code == "Cfc": return (-3, 18, 18)   

    
    if code == "Dsa": return (-10, 34, 10)
    if code == "Dsb": return (-10, 22, 10)
    if code == "Dsc": return (-20, 18, 10)
    if code == "Dsd": return (-30, 18, 10)
    if code == "Dwa": return (-10, 34, 12)
    if code == "Dwb": return (-10, 22, 12)
    if code == "Dwc": return (-20, 18, 10)
    if code == "Dwd": return (-30, 18, 8)
    if code == "Dfa": return (-10, 34, 14)
    if code == "Dfb": return (-15, 22, 14)
    if code == "Dfc": return (-20, 18, 12)
    if code == "Dfd": return (-30, 18, 10)

    
    if code == "ET":  return (-20, 10, 8)
    if code == "EF":  return (-40, 0, 4)

    return (None, None, None)

    print(f"[MATCH] future_code={future_code} fut_tmin={fut_tmin} fut_tmax={fut_tmax} fut_precip_wk={round(fut_precip_wk,1) if fut_precip_wk else None}")


def get_climate_matched_crops(climate, soil, crop_type):
    current_crop = crop_type.lower()

    def _num(v):
        try:
            return float(v) if v not in (None, "", "None") else None
        except (ValueError, TypeError):
            return None

    
    future_code = (
        climate.get("far_future", {}).get("ssp245", {}).get("code")
        or climate.get("koppen", "Cfb")
    )
    hist_code = climate.get("koppen", "Cfb")

    fut_tmin, fut_tmax, fut_precip_wk = _koppen_to_climate_envelope(future_code)

    
    if fut_tmin is None:
        fut_tmin      = climate.get("min_month_temp") or 5
        fut_tmax      = climate.get("max_month_temp") or 28
        fut_precip_wk = (climate.get("ann_precip_mm") or 600) / 52

    fut_temp_mid  = (fut_tmin + fut_tmax) / 2

    
    if future_code.startswith("A"):
        fut_rh_mid = 82
    elif future_code.startswith("B"):
        fut_rh_mid = 35
    elif future_code.startswith("C"):
        fut_rh_mid = 68
    elif future_code.startswith("D"):
        fut_rh_mid = 62
    else:
        fut_rh_mid = 55

    
    ph       = _num(soil.get("ph"))          or 6.5
    sand     = _num(soil.get("sand_pct"))    or 30
    clay     = _num(soil.get("clay_pct"))    or 30
    drainage = soil.get("drainage", "Well drained")

    if "Poor" in drainage or "waterlog" in drainage.lower():
        drain_cat = "Poor"
    elif "Excessive" in drainage:
        drain_cat = "Excessive"
    elif "Moderate" in drainage:
        drain_cat = "Moderate"
    else:
        drain_cat = "Well"

    
    def _range_score(val, lo, hi):
        if lo is None or hi is None or val is None:
            return 0.5
        span = max(hi - lo, 1.0)
        if lo <= val <= hi:
            return 1.0
        dist = min(abs(val - lo), abs(val - hi))
        return max(0.0, 1.0 - dist / (span * 0.5))

    
    scored = []
    seen   = set()

    for row in DISEASE_LIBRARY:
        if row.get("category") != "Perfect Conditions":
            continue

        crop_name = row.get("crop", "").strip()
        if not crop_name or crop_name in seen:
            continue
        if crop_name.lower() == current_crop:
            continue
        seen.add(crop_name)

        points = 0.0
        total  = 0.0
        reasons  = []
        warnings = []

        
        p_tmin = _num(row.get("perfect_temp_min_c"))
        p_tmax = _num(row.get("perfect_temp_max_c"))
        if p_tmin is not None and p_tmax is not None:
            t_score = _range_score(fut_temp_mid, p_tmin, p_tmax)
            points += 2.0 * t_score
            total  += 2.0
            
            if fut_tmax < p_tmin:
                points -= 1.5
                warnings.append(
                    f"projected max {fut_tmax}°C too cold for {crop_name} (needs >{p_tmin}°C)"
                )
            elif fut_tmin > p_tmax:
                points -= 1.5
                warnings.append(
                    f"projected min {fut_tmin}°C too hot for {crop_name} (needs <{p_tmax}°C)"
                )
            elif t_score >= 0.8:
                reasons.append(
                    f"temperature {fut_tmin}-{fut_tmax}°C fits ideal {p_tmin}-{p_tmax}°C"
                )

        
        p_rain = _num(row.get("perfect_rainfall_mm_week"))
        if p_rain is not None:
            r_score = _range_score(fut_precip_wk, p_rain * 0.45, p_rain * 1.9)
            points += 2.0 * r_score
            total  += 2.0
            if r_score >= 0.75:
                reasons.append(
                    f"rainfall ~{round(fut_precip_wk)}mm/wk meets {crop_name} ideal"
                )
            elif fut_precip_wk < p_rain * 0.45:
                warnings.append(
                    f"rainfall ~{round(fut_precip_wk)}mm/wk below minimum "
                    f"(needs ~{round(p_rain * 0.45)}mm/wk) — irrigation required"
                )

        
        p_ph1 = _num(row.get("perfect_soil_ph_min"))
        p_ph2 = _num(row.get("perfect_soil_ph_max"))
        if p_ph1 is not None and p_ph2 is not None:
            ph_score = _range_score(ph, p_ph1, p_ph2)
            points  += 2.0 * ph_score
            total   += 2.0
            if ph_score >= 0.8:
                reasons.append(f"soil pH {ph} within ideal {p_ph1}-{p_ph2}")
            else:
                warnings.append(f"soil pH {ph} outside ideal {p_ph1}-{p_ph2}")

        
        p_rh1 = _num(row.get("perfect_rh_min_pct"))
        p_rh2 = _num(row.get("perfect_rh_max_pct"))
        if p_rh1 is not None and p_rh2 is not None:
            points += 1.0 * _range_score(fut_rh_mid, p_rh1, p_rh2)
            total  += 1.0

        
        p_drain = row.get("perfect_soil_drainage", "")
        if p_drain:
            total += 1.0
            if "Flooded" in p_drain:
                d_score = 1.0 if drain_cat == "Poor" else 0.2
            elif "Well" in p_drain:
                d_score = (1.0 if drain_cat == "Well" else
                           0.6 if drain_cat == "Moderate" else 0.1)
            elif "Moderate" in p_drain:
                d_score = (1.0 if drain_cat == "Moderate" else
                           0.7 if drain_cat == "Well" else 0.3)
            else:
                d_score = 0.5
            points += 1.0 * d_score

        if total == 0:
            continue
        
        final_score = round(max(0.0, (points / total) * 100), 1)
        
                
        if final_score < 40:
            continue

        scored.append({
            "crop":            crop_name,
            "score":           final_score,
            "future_zone":     future_code,
            "current_zone":    hist_code,
            "zone_changed":    future_code != hist_code,
            "match_reasons":   reasons[:3],
            "match_warnings":  warnings[:2],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    
    min_score = 70 if not climate.get("climate_shifting") else 40
    filtered = []
    for c in scored:
        if c["score"] < min_score:
            continue
        
        if any(abs(c["score"] - f["score"]) < 1.0 for f in filtered):
            continue
        filtered.append(c)

    return filtered[:5]
