import os
import requests

from app.config import KOPPEN_DIR

_KOPPEN_BASE = KOPPEN_DIR

_KOPPEN_CODES = {
    1:"Af",  2:"Am",  3:"Aw",
    4:"BWh", 5:"BWk", 6:"BSh", 7:"BSk",
    8:"Csa", 9:"Csb", 10:"Csc",
    11:"Cwa",12:"Cwb",13:"Cwc",
    14:"Cfa",15:"Cfb",16:"Cfc",
    17:"Dsa",18:"Dsb",19:"Dsc",20:"Dsd",
    21:"Dwa",22:"Dwb",23:"Dwc",24:"Dwd",
    25:"Dfa",26:"Dfb",27:"Dfc",28:"Dfd",
    29:"ET", 30:"EF",
}

_KOPPEN_NAMES = {
    "Af":"Tropical Rainforest",      "Am":"Tropical Monsoon",
    "Aw":"Tropical Savanna",
    "BWh":"Hot Desert",              "BWk":"Cold Desert",
    "BSh":"Hot Semi-Arid",           "BSk":"Cold Semi-Arid",
    "Csa":"Mediterranean (hot summer)",
    "Csb":"Mediterranean (warm summer)",
    "Csc":"Mediterranean (cold summer)",
    "Cwa":"Humid Subtropical (dry winter)",
    "Cwb":"Subtropical Highland",
    "Cwc":"Subtropical Highland (cold)",
    "Cfa":"Humid Subtropical",       "Cfb":"Oceanic",
    "Cfc":"Subpolar Oceanic",
    "Dsa":"Continental Mediterranean (hot)",
    "Dsb":"Continental Mediterranean (warm)",
    "Dsc":"Continental Mediterranean (cold)",
    "Dsd":"Continental Mediterranean (very cold)",
    "Dwa":"Monsoon Continental (hot)",
    "Dwb":"Monsoon Continental (warm)",
    "Dwc":"Monsoon Continental (cold)",
    "Dwd":"Monsoon Continental (very cold)",
    "Dfa":"Humid Continental (hot)",
    "Dfb":"Humid Continental (warm)",
    "Dfc":"Subarctic",               "Dfd":"Subarctic (very cold)",
    "ET":"Tundra",                   "EF":"Ice Cap",
}


_SSP_LABELS = {
    "ssp126": "Low emissions (SSP1-2.6, Paris target)",
    "ssp245": "Intermediate emissions (SSP2-4.5)",
    "ssp585": "High emissions (SSP5-8.5, worst case)",
}


def _koppen_tif_path(period, ssp=None):
    if ssp:
        return os.path.join(_KOPPEN_BASE, period, ssp, "koppen_geiger_0p1.tif")
    return os.path.join(_KOPPEN_BASE, period, "koppen_geiger_0p1.tif")

def _sample_raster(path, lat, lon):
    try:
        import rasterio
        from rasterio.transform import rowcol
        with rasterio.open(path) as src:
            r, c = rowcol(src.transform, lon, lat)
            val = int(src.read(1)[r, c])
            code = _KOPPEN_CODES.get(val, "Cfb")
            return code, _KOPPEN_NAMES.get(code, "Temperate")
    except Exception:
        return None, None

def _detect_shift(hist, near, far_low, far_high):
    arid   = {"BWh","BWk","BSh","BSk"}
    tropic = {"Af","Am","Aw"}
    cold   = {"Dfa","Dfb","Dfc","Dfd","Dwa","Dwb","Dwc","Dwd",
               "Dsa","Dsb","Dsc","Dsd","ET","EF"}
    moist  = {"Af","Am","Cfa","Cfb","Cfc","Cwa","Cwb","Cwc"}

    
    if far_high and hist and far_high != hist:
        if far_high in arid and hist not in arid:
            return "aridification"
        if hist in arid and far_high not in arid:
            return "moistening"
        if far_high in cold and hist not in cold:
            return "continentalization"
        if hist in cold and far_high not in cold:
            return "warming"
        if far_high in tropic and hist not in tropic:
            return "tropicalization"
        return "zone_shift"
    return None

def get_climate_class(lat, lon):
    
    hist_path = _koppen_tif_path("1991_2020")
    hist_code, hist_name = _sample_raster(hist_path, lat, lon)

    
    near = {}
    for ssp in ("ssp126","ssp245","ssp585"):
        path = _koppen_tif_path("2041_2070", ssp)
        code, name = _sample_raster(path, lat, lon)
        near[ssp] = {"code": code, "name": name, "label": _SSP_LABELS[ssp]}

    
    far = {}
    for ssp in ("ssp126","ssp245","ssp585"):
        path = _koppen_tif_path("2071_2099", ssp)
        code, name = _sample_raster(path, lat, lon)
        far[ssp] = {"code": code, "name": name, "label": _SSP_LABELS[ssp]}

    
    shift_direction = _detect_shift(
        hist_code,
        near.get("ssp245",{}).get("code"),
        far.get("ssp126",{}).get("code"),
        far.get("ssp585",{}).get("code"),
    )

    shifting = (
        (near.get("ssp585",{}).get("code") != hist_code) or
        (far.get("ssp585",{}).get("code")  != hist_code)
    )

    
    ann_temp = ann_precip = min_month_temp = max_month_temp = None
    try:
        power_url = (
            f"https://power.larc.nasa.gov/api/temporal/climatology/point"
            f"?parameters=T2M,PRECTOTCORR&community=AG"
            f"&longitude={lon}&latitude={lat}&format=JSON"
        )
        resp = requests.get(power_url, timeout=15)
        data = resp.json()["properties"]["parameter"]
        t2m    = data["T2M"]
        precip = data["PRECTOTCORR"]
        months = ["JAN","FEB","MAR","APR","MAY","JUN",
                  "JUL","AUG","SEP","OCT","NOV","DEC"]
        ann_temp         = round(t2m["ANN"], 1)
        ann_precip       = round(precip["ANN"] * 365)
        min_month_temp   = round(min(t2m[m] for m in months), 1)
        max_month_temp   = round(max(t2m[m] for m in months), 1)
    except Exception:
        pass

    return {
        
        "koppen":           hist_code or "Cfb",
        "name":             hist_name or "Temperate",
        "ann_temp_c":       ann_temp,
        "ann_precip_mm":    ann_precip,
        "min_month_temp":   min_month_temp,
        "max_month_temp":   max_month_temp,
        
        "near_future":      near,
        
        "far_future":       far,
        
        "climate_shifting": shifting,
        "shift_direction":  shift_direction,
    }
