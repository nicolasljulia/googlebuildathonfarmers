import json
import os

import ee

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("OPENFARM_DATA_DIR", os.path.join(REPO_ROOT, "data"))


EE_PROJECT_ID = os.getenv("EE_PROJECT_ID", "openfarm-analytics")
EE_SERVICE_ACCOUNT_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")

_ee_initialized = False


def init_earth_engine():
    global _ee_initialized
    if _ee_initialized:
        return

    if EE_SERVICE_ACCOUNT_JSON:
        info = json.loads(EE_SERVICE_ACCOUNT_JSON)
        credentials = ee.ServiceAccountCredentials(
            info["client_email"], key_data=EE_SERVICE_ACCOUNT_JSON,
        )
        ee.Initialize(credentials, project=EE_PROJECT_ID)
        print("[EE] Initialized with service account JSON.")
        _ee_initialized = True
        return

    try:
        import google.auth
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/earthengine"]
        )
        ee.Initialize(credentials, project=EE_PROJECT_ID)
        print("[EE] Initialized with Application Default Credentials.")
        _ee_initialized = True
        return
    except Exception as e:
        print(f"[EE] ADC init failed ({e}); falling back to local user credentials.")

    ee.Initialize(project=EE_PROJECT_ID)
    print("[EE] Initialized with local user credentials (earthengine authenticate).")
    _ee_initialized = True


DISEASE_LIBRARY_PATH = os.getenv(
    "DISEASE_LIBRARY_PATH", os.path.join(DATA_DIR, "disease_library.csv")
)
MAXENT_TIF_DIR = os.getenv("MAXENT_TIF_DIR", os.path.join(DATA_DIR, "maxent_tifs"))
MAXENT_DB_PATH = os.getenv("MAXENT_DB_PATH", os.path.join(DATA_DIR, "maxent_suitability.db"))
KOPPEN_DIR = os.getenv("KOPPEN_DIR", os.path.join(DATA_DIR, "koppen"))

FIELD_RADIUS_M = int(os.getenv("FIELD_RADIUS_M", "15"))
