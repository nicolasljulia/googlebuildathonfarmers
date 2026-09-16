import requests

def _classify_region(lat, lon):
    
    if -35 <= lat <= 38 and -18 <= lon <= 52:
        return "isda"
    
    if 24 <= lat <= 50 and -125 <= lon <= -66:
        return "polaris"
    return "soilgrids"


def _get_isda(lat, lon):
    base = "https://api.isda-africa.com/v1/soilproperty"
    props = {
        "clay":  ("clay_content",      "value", 1,   0.1,  "%"),
        "sand":  ("sand_content",      "value", 1,   0.1,  "%"),
        "ph":    ("ph",                "value", 1,   0.01, ""),
        "soc":   ("carbon_organic",    "value", 1,   1.0,  "g/kg"),
        "bdod":  ("bulk_density",      "value", 1,   0.01, "g/cm³"),
        "nitrogen": ("nitrogen_total", "value", 1,   1.0,  "mg/kg"),
    }
    result = {}
    for key, (prop, field, depth_idx, scale, unit) in props.items():
        try:
            url = f"{base}?lon={lon}&lat={lat}&property={prop}&depth=0-20cm"
            resp = requests.get(url, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                
                val = (data.get("property", {})
                           .get("0-20cm", {})
                           .get("value", {})
                           .get("mean"))
                if val is not None:
                    result[key] = round(float(val) * scale, 2)
        except Exception:
            pass
    return result, "iSDA Africa (30m, CC-BY 4.0)"


def _get_polaris(lat, lon):
    try:
        import rasterio
        from rasterio.crs import CRS
        import math

        base = "http://hydrology.cee.duke.edu/POLARIS/PROPERTIES/v1.0"
        
        
        lat_lo = math.floor(lat)
        lat_hi = lat_lo + 1
        lon_lo = math.floor(lon)
        lon_hi = lon_lo + 1

        def tile_url(var, stat="mean", depth="0_5"):
            return (f"{base}/{var}/{stat}/"
                    f"lat{lat_lo}to{lat_hi}_lon{lon_lo}to{lon_hi}.tif")

        polaris_vars = {
            "ph":   ("ph", "mean"),
            "clay": ("clay", "mean"),
            "sand": ("sand", "mean"),
            "silt": ("silt", "mean"),
            "om":   ("om", "mean"),
            "bdod": ("bd", "mean"),
        }

        result = {}
        for key, (var, stat) in polaris_vars.items():
            try:
                url = f"/vsicurl/{tile_url(var, stat)}"
                with rasterio.open(url) as src:
                    row, col = src.index(lon, lat)
                    window = rasterio.windows.Window(col, row, 1, 1)
                    data = src.read(1, window=window)
                    val = float(data[0, 0])
                    if val != src.nodata and -1e10 < val < 1e10:
                        if key == "ph":    result[key] = round(val, 2)
                        elif key in ("clay","sand","silt"): result[key] = round(val, 1)
                        elif key == "om":  result["soc_g_kg"] = round(val * 10, 1)  
                        elif key == "bdod": result[key] = round(val, 2)
            except Exception:
                pass

        return result, "POLARIS USA (30m, public domain)"
    except ImportError:
        
        return {}, "POLARIS (rasterio not installed — fell back)"


def _get_soilgrids(lat, lon):
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon, "lat": lat,
        "property": ["clay","sand","silt","phh2o","soc","bdod","cec","nitrogen"],
        "depth": ["0-5cm","5-15cm"],
        "value": ["mean"],
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[SOIL ERROR] SoilGrids request failed for ({lat},{lon}): {type(e).__name__}: {e}")
        return {}, f"SoilGrids (error: {e})"

    result = {}
    for layer in data.get("properties", {}).get("layers", []):
        name = layer["name"]
        depth_data = layer.get("depths", [{}])[0]
        mean_raw = depth_data.get("values", {}).get("mean")
        if mean_raw is None:
            continue
        if name == "clay":     result["clay_pct"]     = round(mean_raw / 10, 1)
        if name == "sand":     result["sand_pct"]     = round(mean_raw / 10, 1)
        if name == "silt":     result["silt_pct"]     = round(mean_raw / 10, 1)
        if name == "phh2o":    result["ph"]           = round(mean_raw / 10, 1)
        if name == "soc":      result["soc_g_kg"]     = round(mean_raw / 10, 1)
        if name == "bdod":     result["bulk_density"] = round(mean_raw / 100, 2)
        if name == "cec":      result["cec_mmol_kg"]  = round(mean_raw / 10, 1)
        if name == "nitrogen": result["nitrogen_mg_kg"] = round(mean_raw / 100, 1)

    return result, "SoilGrids 2.0 (250m, CC-BY 4.0)"


def _derive_soil_classes(result):
    clay = result.get("clay_pct", result.get("clay", 0)) or 0
    sand = result.get("sand_pct", result.get("sand", 0)) or 0
    silt = result.get("silt_pct", result.get("silt", 0)) or 0
    cec  = result.get("cec_mmol_kg", 0) or 0
    soc  = result.get("soc_g_kg", 0) or 0

    
    result["clay_pct"] = clay
    result["sand_pct"] = sand
    result["silt_pct"] = silt

    if sand > 70:      texture = "Sandy"
    elif clay > 40:    texture = "Clay"
    elif clay > 27:    texture = "Clay loam"
    elif sand > 52:    texture = "Sandy loam"
    elif silt > 50:    texture = "Silt loam"
    else:              texture = "Loam"

    if sand > 70:    drainage = "Excessive — high drought risk"
    elif clay > 40:  drainage = "Poor — waterlogging risk"
    elif clay > 27:  drainage = "Moderate"
    else:            drainage = "Well drained"

    if sand > 65:    hyd = "High (fast drainage)"
    elif clay > 40:  hyd = "Low (slow drainage)"
    elif clay > 27:  hyd = "Moderate"
    else:            hyd = "Moderate-high"

    if cec > 20 and soc > 15:   fertility = "High"
    elif cec > 10 or soc > 8:   fertility = "Moderate"
    else:                        fertility = "Low"

    result["texture_class"]  = texture
    result["drainage"]       = drainage
    result["hydraulic_cond"] = hyd
    result["fertility"]      = fertility
    return result


def get_soil_data(coordinates):
    lons = [c[0] for c in coordinates]
    lats = [c[1] for c in coordinates]
    lon = round(sum(lons) / len(lons), 4)
    lat = round(sum(lats) / len(lats), 4)

    region = _classify_region(lat, lon)

    raw = {}
    source_label = ""

    if region == "isda":
        raw, source_label = _get_isda(lat, lon)
        
        if "clay" in raw: raw["clay_pct"] = raw.pop("clay")
        if "sand" in raw: raw["sand_pct"] = raw.pop("sand")
        if "ph"   in raw: pass  
        if "soc"  in raw: raw["soc_g_kg"] = raw.pop("soc")
        if "bdod" in raw: raw["bulk_density"] = raw.pop("bdod")
        
        if not raw:
            raw, source_label = _get_soilgrids(lat, lon)

    elif region == "polaris":
        raw, source_label = _get_polaris(lat, lon)
        if not raw:
            raw, source_label = _get_soilgrids(lat, lon)

    else:
        raw, source_label = _get_soilgrids(lat, lon)

    if "error" in raw:
        return raw

    
    if not raw:
        print(f"[SOIL ERROR] All sources returned empty data for ({lat},{lon}), region={region}")
        return {"error": "Soil data unavailable for this location (all sources failed)"}

    result = _derive_soil_classes(raw)
    result["centroid"]     = {"lat": lat, "lon": lon}
    result["soil_source"]  = source_label
    result["soil_resolution"] = "30m" if region in ("isda","polaris") else "250m"
    return result

def get_soil_data_at_point(lat, lon):
    return get_soil_data([[lon, lat]])
