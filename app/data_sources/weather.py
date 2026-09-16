import requests

def get_weather_data(lat, lon):
    try:
        
        from datetime import date as _d, timedelta as _td
        _today = _d.today()
        _start = (_today - _td(days=60)).strftime('%Y%m%d')
        _end   = _today.strftime('%Y%m%d')
        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M"
            f"&community=AG&longitude={lon}&latitude={lat}"
            f"&start={_start}&end={_end}&format=JSON"
        )

        
        resp = requests.get(url, timeout=15)
        data = resp.json()["properties"]["parameter"]

        t2m_daily     = data["T2M"]
        t2m_max_daily = data["T2M_MAX"]
        precip_daily  = data["PRECTOTCORR"]
        rh_daily      = data["RH2M"]

        
        dates = sorted(t2m_daily.keys())[-7:]

        temps_7d    = [t2m_daily[d]     for d in dates if t2m_daily.get(d, -999) > -900]
        temps_max_7d = [t2m_max_daily[d] for d in dates if t2m_max_daily.get(d, -999) > -900]
        precip_7d   = [precip_daily[d]  for d in dates if precip_daily.get(d, -999) > -900]
        rh_7d       = [rh_daily[d]      for d in dates if rh_daily.get(d, -999) > -900]

        avg_temp_7d    = round(sum(temps_7d) / len(temps_7d), 1)     if temps_7d    else None
        max_temp_7d    = round(max(temps_max_7d), 1)                  if temps_max_7d else None
        total_precip_7d = round(sum(precip_7d) / 1, 1)               if precip_7d   else None
        avg_rh_7d      = round(sum(rh_7d) / len(rh_7d), 1)          if rh_7d       else None

        
        all_dates  = sorted(precip_daily.keys())
        cons_dry   = 0
        for d in reversed(all_dates):
            val = precip_daily.get(d, -999)
            if val < 0: continue
            if val < 1: cons_dry += 1
            else:       break

        
        cons_wet = 0
        for d in reversed(all_dates):
            val = precip_daily.get(d, -999)
            if val < 0: continue
            if val > 5: cons_wet += 1
            else:       break

        
        et0_7d = None
        if temps_7d and temps_max_7d:
            temps_min_7d = [t2m_daily[d] for d in dates if t2m_daily.get(d, -999) > -900]
            if len(temps_max_7d) == len(temps_min_7d):
                et0_vals = []
                for tmax, tmean in zip(temps_max_7d, temps_7d):
                    tmin = tmean - (tmax - tmean)
                    td = max(tmax - tmin, 0.5)
                    et0_vals.append(0.0023 * (tmean + 17.8) * (td ** 0.5) * 15)
                et0_7d = round(sum(et0_vals), 1)

        
        clim_url = (
            f"https://power.larc.nasa.gov/api/temporal/climatology/point"
            f"?parameters=PRECTOTCORR&community=AG"
            f"&longitude={lon}&latitude={lat}&format=JSON"
        )
        clim_resp = requests.get(clim_url, timeout=15)
        clim_data = clim_resp.json()["properties"]["parameter"]["PRECTOTCORR"]
        month_normal_mm = clim_data.get("APR", clim_data.get("ANN", 3.0)) * 30
        weekly_normal   = month_normal_mm / 4
        precip_anomaly_pct = round(
            ((total_precip_7d - weekly_normal) / max(weekly_normal, 0.1)) * 100, 0
        ) if total_precip_7d is not None else None

        leaf_wetness_risk = (avg_rh_7d or 0) > 80 and (total_precip_7d or 0) > 5

        return {
            "avg_temp_7d":         avg_temp_7d,
            "max_temp_7d":         max_temp_7d,
            "total_precip_7d_mm":  total_precip_7d,
            "avg_rh_7d_pct":       avg_rh_7d,
            "consecutive_dry_days": cons_dry,
            "consecutive_wet_days": cons_wet,
            "et0_7d_mm":           et0_7d,
            "precip_anomaly_pct":  precip_anomaly_pct,
            "leaf_wetness_risk":   leaf_wetness_risk,
            "weekly_normal_mm":    round(weekly_normal, 1),
        }
    except Exception as e:
        return {"error": str(e)}
