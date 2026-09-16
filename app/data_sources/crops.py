from app.data_sources.disease_library import DISEASE_LIBRARY
from app.data_sources.maxent import MAXENT_CROP_NAMES


def _load_all_crops():
    names = set(MAXENT_CROP_NAMES.values())
    for row in DISEASE_LIBRARY:
        crop = (row.get("crop") or "").strip()
        if crop and crop != "Generic":
            names.add(crop)
    seen_lower = {}
    for name in names:
        seen_lower.setdefault(name.lower(), name)
    return sorted(seen_lower.values())


ALL_CROPS = _load_all_crops()


def crop_slug(name):
    return name.strip().lower()


def is_known_crop(name):
    return crop_slug(name) in {crop_slug(c) for c in ALL_CROPS}
