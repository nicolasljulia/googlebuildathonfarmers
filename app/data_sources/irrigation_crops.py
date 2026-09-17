import re
from datetime import date

IRRIG_CROPS = {
    "artichoke": {"name": "Artichoke", "kc": (0.50,1.00,0.95), "L": (40,40,250,30), "plant_month_n": 3, "cat": "Vegetable"},
    "asparagus": {"name": "Asparagus", "kc": (0.50,0.95,0.30), "L": (50,90,100,50), "plant_month_n": 3, "cat": "Vegetable"},
    "beet_table": {"name": "Beet (table)", "kc": (0.50,1.05,0.95), "L": (25,30,25,10), "plant_month_n": 3, "cat": "Vegetable"},
    "broccoli": {"name": "Broccoli", "kc": (0.70,1.05,0.95), "L": (35,45,40,15), "plant_month_n": 8, "cat": "Vegetable"},
    "brussels_sprouts": {"name": "Brussels Sprouts", "kc": (0.70,1.05,0.95), "L": (30,35,90,40), "plant_month_n": 5, "cat": "Vegetable"},
    "cabbage": {"name": "Cabbage", "kc": (0.70,1.05,0.95), "L": (40,60,50,15), "plant_month_n": 3, "cat": "Vegetable"},
    "cantaloupe": {"name": "Cantaloupe", "kc": (0.50,0.85,0.60), "L": (30,45,35,10), "plant_month_n": 4, "cat": "Vegetable"},
    "carrot": {"name": "Carrot", "kc": (0.70,1.05,0.95), "L": (30,40,60,20), "plant_month_n": 3, "cat": "Vegetable"},
    "cauliflower": {"name": "Cauliflower", "kc": (0.70,1.05,0.95), "L": (35,50,40,15), "plant_month_n": 8, "cat": "Vegetable"},
    "celery": {"name": "Celery", "kc": (0.70,1.05,1.00), "L": (25,40,95,20), "plant_month_n": 4, "cat": "Vegetable"},
    "cucumber": {"name": "Cucumber", "kc": (0.60,1.00,0.75), "L": (20,30,40,15), "plant_month_n": 5, "cat": "Vegetable"},
    "eggplant": {"name": "Eggplant", "kc": (0.60,1.05,0.90), "L": (30,40,40,20), "plant_month_n": 4, "cat": "Vegetable"},
    "garlic": {"name": "Garlic", "kc": (0.70,1.00,0.70), "L": (25,25,30,20), "plant_month_n": 10, "cat": "Vegetable"},
    "kale": {"name": "Kale", "kc": (0.70,1.05,0.95), "L": (30,35,40,25), "plant_month_n": 8, "cat": "Vegetable"},
    "leek": {"name": "Leek", "kc": (0.70,1.10,1.05), "L": (25,75,70,30), "plant_month_n": 3, "cat": "Vegetable"},
    "lettuce": {"name": "Lettuce", "kc": (0.70,1.00,0.95), "L": (20,30,15,10), "plant_month_n": 2, "cat": "Vegetable"},
    "okra": {"name": "Okra", "kc": (0.60,0.95,0.80), "L": (20,30,40,20), "plant_month_n": 5, "cat": "Vegetable"},
    "onion_dry": {"name": "Onion (dry)", "kc": (0.70,1.05,0.75), "L": (15,25,70,40), "plant_month_n": 3, "cat": "Vegetable"},
    "onion_green": {"name": "Onion (green)", "kc": (0.70,1.00,1.00), "L": (25,30,10,5), "plant_month_n": 3, "cat": "Vegetable"},
    "peas_fresh": {"name": "Peas (fresh)", "kc": (0.60,1.15,1.10), "L": (15,25,35,15), "plant_month_n": 3, "cat": "Vegetable"},
    "pepper": {"name": "Sweet Pepper", "kc": (0.60,1.05,0.90), "L": (30,40,110,30), "plant_month_n": 4, "cat": "Vegetable"},
    "pumpkin": {"name": "Pumpkin / Winter Squash", "kc": (0.50,1.00,0.80), "L": (20,30,30,20), "plant_month_n": 5, "cat": "Vegetable"},
    "radish": {"name": "Radish", "kc": (0.70,0.90,0.85), "L": (5,10,15,5), "plant_month_n": 3, "cat": "Vegetable"},
    "spinach": {"name": "Spinach", "kc": (0.70,1.00,0.95), "L": (20,20,15,5), "plant_month_n": 3, "cat": "Vegetable"},
    "squash": {"name": "Squash (summer/zucchini)", "kc": (0.50,0.90,0.75), "L": (20,30,25,15), "plant_month_n": 5, "cat": "Vegetable"},
    "sweet_corn": {"name": "Sweet Corn", "kc": (0.30,1.20,1.05), "L": (20,25,25,10), "plant_month_n": 4, "cat": "Vegetable"},
    "swiss_chard": {"name": "Swiss Chard", "kc": (0.70,1.05,1.00), "L": (25,30,25,10), "plant_month_n": 3, "cat": "Vegetable"},
    "tomato_fresh": {"name": "Tomato (fresh)", "kc": (0.60,1.15,0.80), "L": (30,40,40,25), "plant_month_n": 4, "cat": "Vegetable"},
    "tomato_proc": {"name": "Tomato (processing)", "kc": (0.60,1.15,0.80), "L": (30,40,45,30), "plant_month_n": 4, "cat": "Vegetable"},
    "turnip": {"name": "Turnip", "kc": (0.50,1.10,0.95), "L": (25,30,35,10), "plant_month_n": 8, "cat": "Vegetable"},
    "watermelon": {"name": "Watermelon", "kc": (0.40,1.00,0.75), "L": (20,30,30,30), "plant_month_n": 5, "cat": "Vegetable"},
    "cassava": {"name": "Cassava", "kc": (0.30,0.80,0.50), "L": (60,90,120,60), "plant_month_n": 4, "cat": "Root/Tuber"},
    "potato": {"name": "Potato", "kc": (0.50,1.15,0.75), "L": (25,30,45,30), "plant_month_n": 3, "cat": "Root/Tuber"},
    "sweet_potato": {"name": "Sweet Potato", "kc": (0.50,1.15,0.65), "L": (20,30,60,40), "plant_month_n": 4, "cat": "Root/Tuber"},
    "yam": {"name": "Yam", "kc": (0.50,1.00,0.75), "L": (25,60,120,45), "plant_month_n": 4, "cat": "Root/Tuber"},
    "bean_dry": {"name": "Bean (dry)", "kc": (0.40,1.15,0.35), "L": (20,30,40,20), "plant_month_n": 5, "cat": "Legume"},
    "bean_green": {"name": "Bean (green/snap)", "kc": (0.40,1.05,0.90), "L": (20,30,30,10), "plant_month_n": 4, "cat": "Legume"},
    "chickpea": {"name": "Chickpea", "kc": (0.40,1.00,0.35), "L": (20,35,45,25), "plant_month_n": 10, "cat": "Legume"},
    "cowpea": {"name": "Cowpea", "kc": (0.40,1.05,0.50), "L": (20,35,45,25), "plant_month_n": 5, "cat": "Legume"},
    "fava_bean": {"name": "Fava Bean", "kc": (0.50,1.15,1.10), "L": (90,45,40,0), "plant_month_n": 10, "cat": "Legume"},
    "groundnut": {"name": "Groundnut / Peanut", "kc": (0.40,1.15,0.60), "L": (35,35,35,35), "plant_month_n": 5, "cat": "Legume"},
    "lentil": {"name": "Lentil", "kc": (0.40,1.10,0.30), "L": (25,35,70,40), "plant_month_n": 10, "cat": "Legume"},
    "soybean": {"name": "Soybean", "kc": (0.40,1.15,0.50), "L": (20,30,60,25), "plant_month_n": 5, "cat": "Legume"},
    "barley": {"name": "Barley", "kc": (0.30,1.15,0.25), "L": (30,60,40,20), "plant_month_n": 10, "cat": "Cereal"},
    "corn_maize": {"name": "Corn / Maize", "kc": (0.30,1.20,0.60), "L": (25,40,45,15), "plant_month_n": 4, "cat": "Cereal"},
    "millet": {"name": "Millet", "kc": (0.30,1.00,0.30), "L": (15,25,40,25), "plant_month_n": 6, "cat": "Cereal"},
    "oat": {"name": "Oat", "kc": (0.30,1.15,0.25), "L": (25,50,60,30), "plant_month_n": 3, "cat": "Cereal"},
    "quinoa": {"name": "Quinoa", "kc": (0.52,1.00,0.56), "L": (30,50,40,30), "plant_month_n": 4, "cat": "Cereal"},
    "rice": {"name": "Rice (paddy)", "kc": (1.05,1.20,1.05), "L": (30,30,60,30), "plant_month_n": 6, "cat": "Cereal"},
    "rye": {"name": "Rye", "kc": (0.30,1.15,0.25), "L": (30,65,40,30), "plant_month_n": 10, "cat": "Cereal"},
    "sorghum": {"name": "Sorghum", "kc": (0.30,1.00,0.55), "L": (20,35,40,30), "plant_month_n": 5, "cat": "Cereal"},
    "wheat_winter": {"name": "Wheat (winter)", "kc": (0.40,1.15,0.40), "L": (30,140,40,30), "plant_month_n": 10, "cat": "Cereal"},
    "wheat_spring": {"name": "Wheat (spring)", "kc": (0.30,1.15,0.25), "L": (30,40,60,40), "plant_month_n": 3, "cat": "Cereal"},
    "canola": {"name": "Canola / Rapeseed", "kc": (0.35,1.15,0.35), "L": (35,65,50,40), "plant_month_n": 9, "cat": "Oil Crop"},
    "cotton": {"name": "Cotton", "kc": (0.45,1.20,0.60), "L": (30,50,60,55), "plant_month_n": 4, "cat": "Oil Crop"},
    "flax": {"name": "Flax / Linseed", "kc": (0.40,1.10,0.25), "L": (25,35,50,40), "plant_month_n": 3, "cat": "Oil Crop"},
    "safflower": {"name": "Safflower", "kc": (0.35,1.10,0.25), "L": (20,35,55,30), "plant_month_n": 3, "cat": "Oil Crop"},
    "sesame": {"name": "Sesame", "kc": (0.35,1.10,0.25), "L": (20,30,40,20), "plant_month_n": 5, "cat": "Oil Crop"},
    "sunflower": {"name": "Sunflower", "kc": (0.35,1.10,0.35), "L": (25,35,45,25), "plant_month_n": 5, "cat": "Oil Crop"},
    "sugarcane": {"name": "Sugarcane", "kc": (0.40,1.25,0.75), "L": (35,60,190,120), "plant_month_n": 1, "cat": "Sugar"},
    "sugar_beet": {"name": "Sugar Beet", "kc": (0.35,1.20,0.70), "L": (35,60,70,40), "plant_month_n": 3, "cat": "Sugar"},
    "avocado": {"name": "Avocado", "kc": (0.60,0.85,0.75), "L": (60,90,120,60), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "banana": {"name": "Banana", "kc": (0.50,1.10,1.00), "L": (120,60,180,5), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "citrus_orange": {"name": "Citrus (orange)", "kc": (0.70,0.90,0.75), "L": (60,90,120,95), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "citrus_lemon": {"name": "Citrus (lemon/lime)", "kc": (0.70,0.90,0.75), "L": (60,90,120,95), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "coconut": {"name": "Coconut", "kc": (0.90,1.00,1.00), "L": (180,180,180,180), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "coffee": {"name": "Coffee", "kc": (0.90,1.05,1.05), "L": (90,90,90,90), "plant_month_n": 1, "cat": "Tropical Crop"},
    "mango": {"name": "Mango", "kc": (0.60,1.05,0.75), "L": (30,50,30,10), "plant_month_n": 10, "cat": "Tropical Fruit"},
    "papaya": {"name": "Papaya", "kc": (0.60,1.05,0.90), "L": (60,60,180,60), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "pineapple": {"name": "Pineapple", "kc": (0.50,0.30,0.30), "L": (60,120,240,10), "plant_month_n": 1, "cat": "Tropical Fruit"},
    "tea": {"name": "Tea", "kc": (0.90,1.00,1.00), "L": (180,180,180,180), "plant_month_n": 1, "cat": "Tropical Crop"},
    "almond": {"name": "Almond", "kc": (0.40,1.05,0.65), "L": (20,70,80,30), "plant_month_n": 3, "cat": "Tree Nut"},
    "apple": {"name": "Apple", "kc": (0.45,1.20,0.85), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "apricot": {"name": "Apricot", "kc": (0.45,1.05,0.65), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "cherry": {"name": "Cherry", "kc": (0.45,1.10,0.75), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "olive": {"name": "Olive", "kc": (0.65,0.70,0.70), "L": (30,90,60,90), "plant_month_n": 3, "cat": "Tree Nut/Oil"},
    "peach": {"name": "Peach / Nectarine", "kc": (0.45,1.20,0.85), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "pear": {"name": "Pear", "kc": (0.45,1.20,0.85), "L": (20,60,90,45), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "pistachio": {"name": "Pistachio", "kc": (0.40,1.10,0.45), "L": (20,60,70,30), "plant_month_n": 3, "cat": "Tree Nut"},
    "plum": {"name": "Plum / Prune", "kc": (0.45,1.15,0.80), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Deciduous Fruit"},
    "walnut": {"name": "Walnut", "kc": (0.50,1.10,0.65), "L": (20,70,90,30), "plant_month_n": 3, "cat": "Tree Nut"},
    "blueberry": {"name": "Blueberry", "kc": (0.30,0.90,0.75), "L": (30,60,90,30), "plant_month_n": 4, "cat": "Berry"},
    "grape_table": {"name": "Grape (table)", "kc": (0.30,0.90,0.45), "L": (20,40,120,60), "plant_month_n": 4, "cat": "Vine"},
    "grape_wine": {"name": "Grape (wine)", "kc": (0.30,0.85,0.45), "L": (20,40,120,60), "plant_month_n": 4, "cat": "Vine"},
    "raspberry": {"name": "Raspberry", "kc": (0.30,1.05,0.85), "L": (20,50,50,20), "plant_month_n": 4, "cat": "Berry"},
    "strawberry": {"name": "Strawberry", "kc": (0.40,0.85,0.75), "L": (40,30,60,20), "plant_month_n": 3, "cat": "Berry"},
    "alfalfa": {"name": "Alfalfa (multi-cut)", "kc": (0.40,1.20,1.15), "L": (10,30,15,10), "plant_month_n": 3, "cat": "Forage"},
    "bermuda_grass": {"name": "Bermuda Grass", "kc": (0.60,1.05,0.85), "L": (10,30,120,60), "plant_month_n": 4, "cat": "Forage"},
    "clover": {"name": "Clover", "kc": (0.40,1.15,1.05), "L": (10,30,120,60), "plant_month_n": 3, "cat": "Forage"},
    "ryegrass": {"name": "Ryegrass / Pasture", "kc": (0.95,1.05,1.00), "L": (10,20,150,50), "plant_month_n": 9, "cat": "Forage"},
    "basil": {"name": "Basil", "kc": (0.40,1.05,0.75), "L": (25,30,40,20), "plant_month_n": 4, "cat": "Herb"},
    "cilantro": {"name": "Cilantro / Coriander", "kc": (0.40,0.95,0.85), "L": (20,25,15,5), "plant_month_n": 3, "cat": "Herb"},
    "hemp": {"name": "Hemp / Cannabis", "kc": (0.40,1.05,0.70), "L": (30,45,45,30), "plant_month_n": 5, "cat": "Specialty"},
    "hops": {"name": "Hops", "kc": (0.30,1.05,0.85), "L": (25,45,70,30), "plant_month_n": 4, "cat": "Specialty"},
    "mint": {"name": "Mint", "kc": (0.60,1.15,1.10), "L": (25,30,100,35), "plant_month_n": 4, "cat": "Herb"},
    "tobacco": {"name": "Tobacco", "kc": (0.30,1.10,1.05), "L": (30,45,45,30), "plant_month_n": 4, "cat": "Specialty"},
}


def kc_at_day(crop, day):
    Lini, Ldev, Lmid, Llate = crop["L"]
    kc_ini, kc_mid, kc_end = crop["kc"]
    if day <= Lini:
        return kc_ini
    if day <= Lini + Ldev:
        return kc_ini + ((day - Lini) / Ldev) * (kc_mid - kc_ini) if Ldev else kc_mid
    if day <= Lini + Ldev + Lmid:
        return kc_mid
    frac = min((day - Lini - Ldev - Lmid) / max(Llate, 1), 1)
    return kc_mid + frac * (kc_end - kc_mid)


def growth_stage_at_day(crop, day):
    Lini, Ldev, Lmid, Llate = crop["L"]
    if day <= Lini:
        return "initial"
    if day <= Lini + Ldev:
        return "development"
    if day <= Lini + Ldev + Lmid:
        return "mid-season"
    return "late-season"


def estimate_kc_today(crop, lat, today=None):
    today = today or date.today()
    plant_month = crop["plant_month_n"]
    if lat < 0:
        plant_month = ((plant_month - 1 + 6) % 12) + 1
    total_days = sum(crop["L"])
    plant_date = date(today.year, plant_month, 1)
    if plant_date > today:
        plant_date = date(today.year - 1, plant_month, 1)
    day_of_season = (today - plant_date).days % max(total_days, 1)
    return kc_at_day(crop, day_of_season), day_of_season, total_days


def _normalize(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return s.strip()


def find_irrig_crop(crop_type):
    target = _normalize(crop_type)
    if not target:
        return None
    target_words = set(target.split())
    best = None
    best_score = 0
    for key, crop in IRRIG_CROPS.items():
        name_norm = _normalize(crop["name"])
        if target == name_norm:
            return key, crop
        if target in name_norm or name_norm in target:
            score = 100
        else:
            score = len(target_words & set(name_norm.split())) * 10
        if score > best_score:
            best_score = score
            best = (key, crop)
    return best if best_score > 0 else None


def estimate_daily_irrigation(crop_type, lat, weather):
    if weather.get("error"):
        return None
    match = find_irrig_crop(crop_type)
    if not match:
        return None
    _, crop = match

    et0_7d = weather.get("et0_7d_mm")
    precip_7d = weather.get("total_precip_7d_mm")
    if et0_7d is None or precip_7d is None:
        return None

    et0_daily = et0_7d / 7
    precip_daily = precip_7d / 7
    kc, day_of_season, total_days = estimate_kc_today(crop, lat)
    etc_daily = et0_daily * kc
    net_daily = max(0.0, etc_daily - precip_daily)

    return {
        "crop_matched": crop["name"],
        "growth_stage": growth_stage_at_day(crop, day_of_season),
        "day_of_season": day_of_season,
        "season_length_days": total_days,
        "kc": round(kc, 2),
        "eto_mm_day": round(et0_daily, 2),
        "etc_mm_day": round(etc_daily, 2),
        "rain_mm_day": round(precip_daily, 2),
        "net_irrigation_mm_day": round(net_daily, 2),
    }
