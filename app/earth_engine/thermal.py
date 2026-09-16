import ee

def get_ecostress_data(field, centroid_lat, centroid_lon):
    from datetime import date, timedelta

    result = {
        "lst_c":      None,
        "esi":        None,
        "et_mm_day":  None,
        "lst_status": None,
        "et_status":  None,
        "date":       None,
        "available":  False,
        "source":     None,
    }

    today    = date.today().strftime('%Y-%m-%d')
    start_30 = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    start_60 = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')

    
    try:
        lst_col = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
            .merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'))
            .filterBounds(field)
            .filterDate(start_30, today)
            .filter(ee.Filter.lt('CLOUD_COVER', 30))
            .sort('system:time_start', False))

        
        if not lst_col.limit(1).toList(1).getInfo():
            lst_col = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                .merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'))
                .filterBounds(field)
                .filterDate(start_60, today)
                .filter(ee.Filter.lt('CLOUD_COVER', 30))
                .sort('system:time_start', False))

        lst_first_list = lst_col.limit(1).toList(1).getInfo()
        if lst_first_list:
            lst_img  = lst_col.first()
            date_ms  = lst_first_list[0]['properties']['system:time_start']
            from datetime import datetime, timezone
            result["date"]   = datetime.fromtimestamp(
                date_ms / 1000, tz=timezone.utc
            ).strftime('%d %b %Y')
            result["source"] = "Landsat 8/9 LST (100m) + MODIS MOD16A2 ET (500m)"

            
            lst_celsius = (lst_img.select('ST_B10')
                .multiply(0.00341802).add(149.0)
                .subtract(273.15)
                .rename('LST_C'))

            lst_stats = lst_celsius.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=field,
                scale=100,
                bestEffort=True,
            ).getInfo()

            raw = lst_stats.get('LST_C')
            if raw is not None:
                result["lst_c"]     = round(raw, 1)
                result["available"] = True
                lc = raw
                if lc > 45:   result["lst_status"] = "Critical heat stress"
                elif lc > 38: result["lst_status"] = "High heat stress"
                elif lc > 32: result["lst_status"] = "Moderate heat stress"
                elif lc < 5:  result["lst_status"] = "Chilling risk"
                else:         result["lst_status"] = "Normal"

    except Exception as e:
        print(f"[LST] Error: {e}")

    
    try:
        et_col = (ee.ImageCollection('MODIS/061/MOD16A2')
            .filterBounds(field)
            .filterDate(start_30, today)
            .sort('system:time_start', False))

        if not et_col.limit(1).toList(1).getInfo():
            et_col = (ee.ImageCollection('MODIS/061/MOD16A2')
                .filterBounds(field)
                .filterDate(start_60, today)
                .sort('system:time_start', False))

        if et_col.limit(1).toList(1).getInfo():
            et_img = et_col.first()

            
            et_band  = et_img.select('ET').multiply(0.1).divide(8)
            pet_band = et_img.select('PET').multiply(0.1).divide(8)

            et_stats = et_band.addBands(pet_band.rename('PET')).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=field,
                scale=500,
                bestEffort=True,
            ).getInfo()

            et_val  = et_stats.get('ET')
            pet_val = et_stats.get('PET')

            if et_val is not None:
                result["et_mm_day"] = round(et_val, 2)
                result["available"] = True

                
                if pet_val and pet_val > 0:
                    esi = round(et_val / pet_val, 2)
                    result["esi"] = min(max(esi, 0.0), 1.0)
                    if esi < 0.3:   result["et_status"] = "Severe water stress"
                    elif esi < 0.5: result["et_status"] = "Moderate water stress"
                    elif esi < 0.7: result["et_status"] = "Mild water stress"
                    else:           result["et_status"] = "No water stress"
                else:
                    result["et_status"] = "ET available — stress index not computed"

    except Exception as e:
        print(f"[ET/ESI] Error: {e}")

    return result
