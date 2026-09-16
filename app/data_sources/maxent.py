import os
import sqlite3 as _sqlite3

from app.config import MAXENT_DB_PATH, MAXENT_TIF_DIR


MAXENT_CROP_NAMES = {
    "actinidia_deliciosa":         "Kiwi",
    "allium_cepa":                 "Onion",
    "allium_sativum":              "Garlic",
    "amaranthus_cruentus":         "Amaranth",
    "ananas_comosus":              "Pineapple",
    "annona_muricata":             "Soursop",
    "arachis_hypogaea":            "Groundnut",
    "artocarpus_altilis":          "Breadfruit",
    "artocarpus_heterophyllus":    "Jackfruit",
    "asparagus_officinalis":       "Asparagus",
    "avena_sativa":                "Oats",
    "beta_vulgaris":               "Sugar Beet",
    "brassica_napus":              "Rapeseed",
    "brassica_oleracea":           "Cabbage",
    "brassica_rapa":               "Turnip",
    "cajanus_cajan":               "Pigeon Pea",
    "camellia_sinensis":           "Tea",
    "cannabis_sativa":             "Hemp",
    "capsicum_annuum":             "Pepper",
    "carica_papaya":               "Papaya",
    "carthamus_tinctorius":        "Safflower",
    "chenopodium_quinoa":          "Quinoa",
    "cicer_arietinum":             "Chickpea",
    "citrullus_lanatus":           "Watermelon",
    "citrus_limon":                "Lemon",
    "citrus_paradisi":             "Grapefruit",
    "citrus_reticulata":           "Mandarin",
    "citrus_sinensis":             "Orange",
    "cocos_nucifera":              "Coconut",
    "coffea_arabica":              "Coffee",
    "cucumis_melo":                "Melon",
    "cucumis_sativus":             "Cucumber",
    "cucurbita_maxima":            "Pumpkin",
    "cucurbita_pepo":              "Zucchini",
    "daucus_carota":               "Carrot",
    "durio_zibethinus":            "Durian",
    "elaeis_guineensis":           "Oil Palm",
    "eleusine_coracana":           "Finger Millet",
    "ficus_carica":                "Fig",
    "fragaria_ananassa":           "Strawberry",
    "garcinia_mangostana":         "Mangosteen",
    "glycine_max":                 "Soybean",
    "gossypium_hirsutum":          "Cotton",
    "helianthus_annuus":           "Sunflower",
    "hordeum_vulgare":             "Barley",
    "humulus_lupulus":             "Hops",
    "ipomoea_batatas":             "Sweet Potato",
    "jatropha_curcas":             "Jatropha",
    "lactuca_sativa":              "Lettuce",
    "lens_culinaris":              "Lentil",
    "linum_usitatissimum":         "Flax",
    "litchi_chinensis":            "Lychee",
    "lupinus_albus":               "Lupin",
    "lycopersicon_pimpinellifolium":"Wild Tomato",
    "malus_domestica":             "Apple",
    "mangifera_indica":            "Mango",
    "manihot_esculenta":           "Cassava",
    "medicago_sativa":             "Alfalfa",
    "musa_acuminata":              "Banana",
    "nephelium_lappaceum":         "Rambutan",
    "nicotiana_tabacum":           "Tobacco",
    "olea_europaea":               "Olive",
    "oryza_sativa":                "Rice",
    "panicum_miliaceum":           "Millet",
    "papaver_somniferum":          "Poppy",
    "passiflora_edulis":           "Passion Fruit",
    "pennisetum_glaucum":          "Pearl Millet",
    "persea_americana":            "Avocado",
    "phaseolus_vulgaris":          "Beans",
    "phoenix_dactylifera":         "Date Palm",
    "pisum_sativum":               "Pea",
    "prunus_armeniaca":            "Apricot",
    "prunus_avium":                "Cherry",
    "prunus_domestica":            "Plum",
    "prunus_persica":              "Peach",
    "psidium_guajava":             "Guava",
    "pyrus_communis":              "Pear",
    "raphanus_sativus":            "Radish",
    "ricinus_communis":            "Castor Bean",
    "rubus_idaeus":                "Raspberry",
    "saccharum_officinarum":       "Sugarcane",
    "secale_cereale":              "Rye",
    "sesamum_indicum":             "Sesame",
    "setaria_italica":             "Foxtail Millet",
    "solanum_lycopersicum":        "Tomato",
    "solanum_melongena":           "Eggplant",
    "solanum_quitoense":           "Naranjilla",
    "solanum_tuberosum":           "Potato",
    "sorghum_bicolor":             "Sorghum",
    "spinacia_oleracea":           "Spinach",
    "theobroma_cacao":             "Cocoa",
    "triticum_aestivum":           "Wheat",
    "vaccinium_corymbosum":        "Blueberry",
    "vicia_faba":                  "Faba Bean",
    "vigna_radiata":               "Mung Bean",
    "vigna_unguiculata":           "Cowpea",
    "vitis_vinifera":              "Grape",
    "zea_mays":                    "Maize",
}


MAXENT_AUC_SCORES = {
    "actinidia_deliciosa": 0.97, "allium_cepa": 0.867, "allium_sativum": 0.886,
    "amaranthus_cruentus": 0.862, "ananas_comosus": 0.885, "annona_muricata": 0.905,
    "arachis_hypogaea": 0.811, "artocarpus_altilis": 0.901, "artocarpus_heterophyllus": 0.876,
    "asparagus_officinalis": 0.652, "avena_sativa": 0.643, "beta_vulgaris": 0.659,
    "brassica_napus": 0.644, "brassica_oleracea": 0.723, "brassica_rapa": 0.658,
    "cajanus_cajan": 0.838, "camellia_sinensis": 0.929, "cannabis_sativa": 0.73,
    "capsicum_annuum": 0.784, "carica_papaya": 0.75, "carthamus_tinctorius": 0.844,
    "chenopodium_quinoa": 0.966, "cicer_arietinum": 0.804, "citrullus_lanatus": 0.745,
    "citrus_limon": 0.904, "citrus_paradisi": 0.888, "citrus_reticulata": 0.942,
    "citrus_sinensis": 0.954, "cocos_nucifera": 0.786, "coffea_arabica": 0.871,
    "cucumis_melo": 0.772, "cucumis_sativus": 0.833, "cucurbita_maxima": 0.881,
    "cucurbita_pepo": 0.806, "daucus_carota": 0.634, "durio_zibethinus": 0.983,
    "elaeis_guineensis": 0.932, "eleusine_coracana": 0.916, "ficus_carica": 0.642,
    "fragaria_ananassa": 0.816, "garcinia_mangostana": 0.976, "glycine_max": 0.958,
    "gossypium_hirsutum": 0.867, "helianthus_annuus": 0.625, "hordeum_vulgare": 0.622,
    "humulus_lupulus": 0.628, "ipomoea_batatas": 0.784, "jatropha_curcas": 0.863,
    "lactuca_sativa": 0.754, "lens_culinaris": 0.842, "linum_usitatissimum": 0.72,
    "litchi_chinensis": 0.961, "lupinus_albus": 0.919, "lycopersicon_pimpinellifolium": 0.964,
    "malus_domestica": 0.632, "mangifera_indica": 0.768, "manihot_esculenta": 0.793,
    "medicago_sativa": 0.632, "musa_acuminata": 0.903, "nephelium_lappaceum": 0.962,
    "nicotiana_tabacum": 0.84, "olea_europaea": 0.665, "oryza_sativa": 0.945,
    "panicum_miliaceum": 0.733, "papaver_somniferum": 0.695, "passiflora_edulis": 0.814,
    "pennisetum_glaucum": 0.754, "persea_americana": 0.835, "phaseolus_vulgaris": 0.741,
    "phoenix_dactylifera": 0.893, "pisum_sativum": 0.728, "prunus_armeniaca": 0.761,
    "prunus_avium": 0.81, "prunus_domestica": 0.725, "prunus_persica": 0.694,
    "psidium_guajava": 0.718, "pyrus_communis": 0.641, "raphanus_sativus": 0.76,
    "ricinus_communis": 0.648, "rubus_idaeus": 0.622, "saccharum_officinarum": 0.927,
    "secale_cereale": 0.732, "sesamum_indicum": 0.877, "setaria_italica": 0.827,
    "solanum_lycopersicum": 0.773, "solanum_melongena": 0.869, "solanum_quitoense": 0.963,
    "solanum_tuberosum": 0.818, "sorghum_bicolor": 0.699, "spinacia_oleracea": 0.905,
    "theobroma_cacao": 0.886, "triticum_aestivum": 0.943, "vaccinium_corymbosum": 0.819,
    "vicia_faba": 0.682, "vigna_radiata": 0.878, "vigna_unguiculata": 0.784,
    "vitis_vinifera": 0.7, "zea_mays": 0.711,
}


import sqlite3 as _sqlite3
_MAXENT_DB_CONN = None
_MAXENT_GRID_STEP = 0.5

def _get_maxent_conn():
    global _MAXENT_DB_CONN
    if _MAXENT_DB_CONN is None:
        if os.path.exists(MAXENT_DB_PATH):
            _MAXENT_DB_CONN = _sqlite3.connect(MAXENT_DB_PATH, check_same_thread=False)
            print(f"[MAXENT] DB connected: {MAXENT_DB_PATH}")
        else:
            print(f"[MAXENT] DB not found at {MAXENT_DB_PATH} — falling back to rasterio")

def get_maxent_suitability(lat, lon, current_crop=None):
    conn = _get_maxent_conn()

    if conn is not None:
        
        step     = _MAXENT_GRID_STEP
        snap_lat = round(round(lat / step) * step, 4)
        snap_lon = round(round(lon / step) * step, 4)

        try:
            row = conn.execute(
                "SELECT * FROM suitability WHERE lat=? AND lon=?",
                (snap_lat, snap_lon)
            ).fetchone()

            if row is None:
                
                for dlat in [-step, 0, step]:
                    for dlon in [-step, 0, step]:
                        row = conn.execute(
                            "SELECT * FROM suitability WHERE lat=? AND lon=?",
                            (round(snap_lat+dlat, 4), round(snap_lon+dlon, 4))
                        ).fetchone()
                        if row:
                            break
                    if row:
                        break

            if row is None:
                return []

            cols = [d[0] for d in conn.execute(
                "SELECT * FROM suitability LIMIT 1"
            ).description]

            current_lower = current_crop.lower() if current_crop else ""
            results = []

            for i, col in enumerate(cols):
                if col in ("lat", "lon"):
                    continue
                val = row[i]
                if val is None or val < 0.3:
                    continue
                common_name = MAXENT_CROP_NAMES.get(col)
                if not common_name:
                    continue
                if common_name.lower() == current_lower or col == current_lower:
                    continue

                auc = MAXENT_AUC_SCORES.get(col, 0.7)
                confidence = ("High"      if auc >= 0.90 else
                              "Moderate"  if auc >= 0.75 else
                              "Low"       if auc >= 0.70 else "Indicative")
                conf_color = ("#639922"   if auc >= 0.90 else
                              "#EF9F27"   if auc >= 0.75 else
                              "#E8830A"   if auc >= 0.70 else "#888888")

                results.append({
                    "crop":             common_name,
                    "scientific":       col.replace("_", " ").capitalize(),
                    "suitability":      round(float(val), 3),
                    "suitability_pct":  round(float(val) * 100, 1),
                    "category":         ("Highly suitable" if val >= 0.75 else
                                        "Suitable"        if val >= 0.5  else "Marginal"),
                    "auc":              auc,
                    "model_confidence": confidence,
                    "confidence_color": conf_color,
                })

            results.sort(key=lambda x: x["suitability"], reverse=True)
            return results[:15]

        except Exception as e:
            print(f"[MAXENT] DB query error: {e}")
            return []

    else:
        
        try:
            import rasterio
            from rasterio.transform import rowcol
        except ImportError:
            print("[MAXENT] rasterio not available and DB not found")
            return []

        if not os.path.isdir(MAXENT_TIF_DIR):
            print(f"[MAXENT] TIF directory not found: {MAXENT_TIF_DIR}")
            return []

        current_lower = current_crop.lower() if current_crop else ""
        results = []

        for scientific_key, common_name in MAXENT_CROP_NAMES.items():
            if common_name.lower() == current_lower or scientific_key == current_lower:
                continue
            tif_path = os.path.join(MAXENT_TIF_DIR, f"{scientific_key}.tif")
            if not os.path.exists(tif_path):
                continue
            try:
                with rasterio.open(tif_path) as src:
                    r, c = rowcol(src.transform, lon, lat)
                    if r < 0 or c < 0 or r >= src.height or c >= src.width:
                        continue
                    val = float(src.read(1)[r, c])
                    nd = src.nodata
                    if nd is not None and abs(val - nd) < 0.0001:
                        continue
                    if val < 0.3 or val > 1:
                        continue
            except Exception as e:
                print(f"[MAXENT] Rasterio error {scientific_key}: {e}")
                continue

            auc = MAXENT_AUC_SCORES.get(scientific_key, 0.7)
            confidence = ("High"     if auc >= 0.90 else
                          "Moderate" if auc >= 0.75 else
                          "Low"      if auc >= 0.70 else "Indicative")
            conf_color = ("#639922"  if auc >= 0.90 else
                          "#EF9F27"  if auc >= 0.75 else
                          "#E8830A"  if auc >= 0.70 else "#888888")

            results.append({
                "crop":             common_name,
                "scientific":       scientific_key.replace("_", " ").capitalize(),
                "suitability":      round(val, 3),
                "suitability_pct":  round(val * 100, 1),
                "category":         ("Highly suitable" if val >= 0.75 else
                                     "Suitable"        if val >= 0.5  else "Marginal"),
                "auc":              auc,
                "model_confidence": confidence,
                "confidence_color": conf_color,
            })

        results.sort(key=lambda x: x["suitability"], reverse=True)
        return results[:15]
