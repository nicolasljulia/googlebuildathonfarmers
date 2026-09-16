import csv
import json

from app.config import DISEASE_LIBRARY_PATH

_NUMERIC_FIELDS = (
    'ndvi_threshold', 'ndmi_threshold', 'ndre_threshold',
    'temp_min_c', 'temp_max_c', 'temp_opt_c',
    'rh_min_pct', 'rh_opt_pct', 'leaf_wetness_hrs',
    'soil_ph_min', 'soil_ph_max',
    'consecutive_dry_days_trigger', 'consecutive_wet_days_trigger',
    'temp_stress_threshold_c', 'soil_ec_threshold_ds_m',
)


def _load_library():
    rows = []
    try:
        with open(DISEASE_LIBRARY_PATH, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try:
                    row['rule_logic'] = json.loads(row['rule_logic'])
                except Exception:
                    row['rule_logic'] = None
                for field in _NUMERIC_FIELDS:
                    v = row.get(field, '')
                    try:
                        row[field] = float(v) if v not in ('', 'None', None) else None
                    except (ValueError, TypeError):
                        row[field] = None
                rows.append(row)
    except Exception as e:
        print(f"[WARNING] Could not load disease library: {e}")
    return rows


DISEASE_LIBRARY = _load_library()
print(f"[INFO] Loaded {len(DISEASE_LIBRARY)} records from disease library")
