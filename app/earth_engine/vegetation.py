from datetime import datetime, timezone

import ee


def get_sentinel_composite(field, start, end):
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(field)
        .filterDate(start, end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
        .sort('system:time_start', False))
    first_list = col.limit(1).toList(1).getInfo()
    if not first_list:
        return None, None
    date_ms = first_list[0]['properties']['system:time_start']
    date_str = datetime.fromtimestamp(date_ms / 1000, tz=timezone.utc).strftime('%d %b %Y')
    return col.median(), date_str


def compute_vegetation_indices(img, field, early_img=None):
    
    b2  = img.select('B2').divide(10000)
    b3  = img.select('B3').divide(10000)
    b4  = img.select('B4').divide(10000)
    b5  = img.select('B5').divide(10000)
    b6  = img.select('B6').divide(10000)
    b7  = img.select('B7').divide(10000)
    b8  = img.select('B8').divide(10000)
    b8a = img.select('B8A').divide(10000)
    b11 = img.select('B11').divide(10000)

    
    msavi = (b8.multiply(2).add(1).subtract(
        b8.multiply(2).add(1).pow(2).subtract(b8.subtract(b4).multiply(8)).sqrt()
    )).divide(2).rename('MSAVI')
    savi = b8.subtract(b4).divide(b8.add(b4).add(0.5)).multiply(1.5).rename('SAVI')
    ndvi  = img.normalizedDifference(['B8','B4']).rename('NDVI')
    evi   = b8.subtract(b4).multiply(2.5).divide(
        b8.add(b4.multiply(6)).subtract(b2.multiply(7.5)).add(1)
    ).rename('EVI')
    gndvi = b8.subtract(b3).divide(b8.add(b3)).rename('GNDVI')
    ndre  = img.normalizedDifference(['B8A','B5']).rename('NDRE')
    reci  = b7.divide(b5).subtract(1).rename('ReCI')
    gci   = b8a.divide(b3).subtract(1).rename('GCI')
    ndmi  = img.normalizedDifference(['B8','B11']).rename('NDMI')
    ndwi  = img.normalizedDifference(['B3','B8']).rename('NDWI')
    psri  = b4.subtract(b2).divide(b6).rename('PSRI')

    index_stack = (ndvi.addBands(ndmi).addBands(ndre).addBands(evi)
                       .addBands(msavi).addBands(savi).addBands(gndvi)
                       .addBands(reci).addBands(gci).addBands(ndwi)
                       .addBands(psri))

    
    all_stats = index_stack.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.percentile([10, 90]), sharedInputs=True),
        geometry=field,
        scale=10,
        bestEffort=True,
    ).getInfo()

    def _extract(band):
        return {
            "mean": all_stats.get(f"{band}_mean") or all_stats.get(band),
            "p10":  all_stats.get(f"{band}_p10"),
            "p90":  all_stats.get(f"{band}_p90"),
        }

    ndvi_stats  = _extract('NDVI')
    ndmi_stats  = _extract('NDMI')
    ndre_stats  = _extract('NDRE')
    evi_stats   = _extract('EVI')
    msavi_stats = _extract('MSAVI')
    savi_stats  = _extract('SAVI')
    gndvi_stats = _extract('GNDVI')
    reci_stats  = _extract('ReCI')
    gci_stats   = _extract('GCI')
    ndwi_stats  = _extract('NDWI')
    psri_stats  = _extract('PSRI')

    mean_ndvi  = ndvi_stats["mean"]
    mean_ndmi  = ndmi_stats["mean"]
    mean_ndre  = ndre_stats["mean"]
    mean_evi   = evi_stats["mean"]
    mean_msavi = msavi_stats["mean"]
    mean_gndvi = gndvi_stats["mean"]
    mean_reci  = reci_stats["mean"]
    mean_gci   = gci_stats["mean"]
    mean_ndwi  = ndwi_stats["mean"]
    mean_psri  = psri_stats["mean"]

    ndvi_spread = None
    if ndvi_stats["p90"] is not None and ndvi_stats["p10"] is not None:
        ndvi_spread = round(ndvi_stats["p90"] - ndvi_stats["p10"], 3)

    ndvi_change = 0
    if early_img is not None:
        early_ndvi = early_img.normalizedDifference(['B8','B4'])
        early_val  = early_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=field, scale=10
        ).getInfo().get('nd')
        if early_val:
            ndvi_change = round(mean_ndvi - early_val, 3)

    
    ndvi_for_zones = ndvi.rename('NDVI')
    zone_hist = ndvi_for_zones.reduceRegion(
        reducer=ee.Reducer.fixedHistogram(-0.2, 1.0, 12),
        geometry=field,
        scale=10,
        bestEffort=True,
    ).getInfo()
    _bins = zone_hist.get('NDVI', [])
    _total_px = sum(b[1] for b in _bins) if _bins else 1
    def _zone_pct_from_hist(lo, hi):
        if not _bins or _total_px == 0:
            return 0.0
        count = sum(b[1] for b in _bins if lo <= b[0] < hi)
        return round((count / _total_px) * 100, 1)
    zones = {
        "healthy_pct":  _zone_pct_from_hist(0.6, 1.1),
        "fair_pct":     _zone_pct_from_hist(0.4, 0.6),
        "stressed_pct": _zone_pct_from_hist(0.2, 0.4),
        "severe_pct":   _zone_pct_from_hist(-0.2, 0.2),
    }


    if mean_ndvi < 0.2:   health = "Severe stress"
    elif mean_ndvi < 0.4: health = "Moderate stress"
    elif mean_ndvi < 0.6: health = "Fair"
    else:                 health = "Healthy"

    if mean_ndmi < -0.2:  moisture = "Severe deficit"
    elif mean_ndmi < 0.0: moisture = "Low"
    elif mean_ndmi < 0.2: moisture = "Adequate"
    else:                 moisture = "High"

    if mean_ndre is None:       nitrogen = "Unknown"
    elif mean_ndre < 0.2:       nitrogen = "Deficient"
    elif mean_ndre < 0.35:      nitrogen = "Moderate"
    else:                       nitrogen = "Sufficient"

    if ndvi_spread is None:     heterogeneity = "Unknown"
    elif ndvi_spread < 0.15:    heterogeneity = "Uniform"
    elif ndvi_spread < 0.25:    heterogeneity = "Moderate variation"
    else:                       heterogeneity = "High variation — stress hotspots likely"

    def safe_round(val, digits=3):
        return round(val, digits) if val is not None else None

    return {
        "ndvi": safe_round(mean_ndvi),
        "ndvi_change": safe_round(ndvi_change),
        "health_status": health,
        "heterogeneity": heterogeneity,
        "ndvi_spread": ndvi_spread,
        "zones": zones,
        "indices": {
            "NDVI":  {"mean": safe_round(mean_ndvi),  "p10": safe_round(ndvi_stats["p10"]),  "p90": safe_round(ndvi_stats["p90"]),  "label": "Crop health"},
            "EVI":   {"mean": safe_round(mean_evi),   "p10": safe_round(evi_stats["p10"]),   "p90": safe_round(evi_stats["p90"]),   "label": "Canopy vigour"},
            "MSAVI": {"mean": safe_round(mean_msavi), "p10": safe_round(msavi_stats["p10"]), "p90": safe_round(msavi_stats["p90"]), "label": "Sparse canopy"},
            "GNDVI": {"mean": safe_round(mean_gndvi), "p10": safe_round(gndvi_stats["p10"]), "p90": safe_round(gndvi_stats["p90"]), "label": "Chlorophyll"},
            "NDMI":  {"mean": safe_round(mean_ndmi),  "p10": safe_round(ndmi_stats["p10"]),  "p90": safe_round(ndmi_stats["p90"]),  "label": moisture},
            "NDWI":  {"mean": safe_round(mean_ndwi),  "p10": safe_round(ndwi_stats["p10"]),  "p90": safe_round(ndwi_stats["p90"]),  "label": "Surface water"},
            "NDRE":  {"mean": safe_round(mean_ndre),  "p10": safe_round(ndre_stats["p10"]),  "p90": safe_round(ndre_stats["p90"]),  "label": nitrogen + " N"},
            "ReCI":  {"mean": safe_round(mean_reci),  "p10": safe_round(reci_stats["p10"]),  "p90": safe_round(reci_stats["p90"]),  "label": "Chlorophyll index"},
            "GCI":   {"mean": safe_round(mean_gci),   "p10": safe_round(gci_stats["p10"]),   "p90": safe_round(gci_stats["p90"]),   "label": "Green chlorophyll"},
            "PSRI":  {"mean": safe_round(mean_psri),  "p10": safe_round(psri_stats["p10"]),  "p90": safe_round(psri_stats["p90"]),  "label": "Senescence"},
        },
        "ndmi": safe_round(mean_ndmi),
        "ndre": safe_round(mean_ndre),
        "moisture": moisture,
        "nitrogen": nitrogen,
    }
def get_historical_snapshot(field, today_str):
    from datetime import datetime, timedelta
    today = datetime.strptime(today_str, '%Y-%m-%d')
    one_year_ago = today - timedelta(days=365)
    start = (one_year_ago - timedelta(days=30)).strftime('%Y-%m-%d')
    end   = one_year_ago.strftime('%Y-%m-%d')
    period_label = one_year_ago.strftime('%b %Y')

    try:
        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(field)
            .filterDate(start, end)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .sort('system:time_start', False))

        if not col.limit(1).toList(1).getInfo():
            return {"error": "No imagery available for this period", "period": period_label}

        img = col.median()

        ndvi_hist = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndmi_hist = img.normalizedDifference(['B8', 'B11']).rename('NDMI')
        ndre_hist = img.normalizedDifference(['B8A', 'B5']).rename('NDRE')

        stack = ndvi_hist.addBands(ndmi_hist).addBands(ndre_hist)
        stats = stack.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=field,
            scale=10,
            bestEffort=True
        ).getInfo()

        h_ndvi = stats.get('NDVI')
        h_ndmi = stats.get('NDMI')
        h_ndre = stats.get('NDRE')

        
        if h_ndvi is None:       h_health = "Unknown"
        elif h_ndvi < 0.2:       h_health = "Severe stress"
        elif h_ndvi < 0.4:       h_health = "Moderate stress"
        elif h_ndvi < 0.6:       h_health = "Fair"
        else:                    h_health = "Healthy"

        if h_ndmi is None:       h_moisture = "Unknown"
        elif h_ndmi < -0.2:      h_moisture = "Severe deficit"
        elif h_ndmi < 0.0:       h_moisture = "Low"
        elif h_ndmi < 0.2:       h_moisture = "Adequate"
        else:                    h_moisture = "High"

        return {
            "period":    period_label,
            "ndvi":      round(h_ndvi, 3) if h_ndvi else None,
            "ndmi":      round(h_ndmi, 3) if h_ndmi else None,
            "ndre":      round(h_ndre, 3) if h_ndre else None,
            "health":    h_health,
            "moisture":  h_moisture,
        }
    except Exception as e:
        return {"error": str(e), "period": period_label}
