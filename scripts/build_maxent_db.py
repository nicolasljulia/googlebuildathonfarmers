
import os, sqlite3, json, time
import numpy as np

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIF_DIR  = os.getenv(
    "MAXENT_TIF_SOURCE_DIR",
    "/Users/nicolasjulia/Library/CloudStorage/OneDrive-CalPoly/MaxentPilot/tifs",
)
DB_PATH  = os.getenv("MAXENT_DB_PATH", os.path.join(_REPO_ROOT, "data", "maxent_suitability.db"))

GRID_STEP = 0.5  

try:
    import rasterio
    from rasterio.transform import rowcol
except ImportError:
    print("ERROR: rasterio not installed. Run: pip install rasterio")
    exit(1)

if not os.path.isdir(TIF_DIR):
    print(f"ERROR: TIF directory not found: {TIF_DIR}")
    exit(1)

tifs = sorted([f for f in os.listdir(TIF_DIR) if f.endswith('.tif')])
print(f"Found {len(tifs)} TIF files")

with rasterio.open(os.path.join(TIF_DIR, tifs[0])) as src:
    bounds = src.bounds
    print(f"Bounds: {bounds}  Resolution: {src.res}")

lons = np.arange(bounds.left   + GRID_STEP/2, bounds.right, GRID_STEP)
lats = np.arange(bounds.bottom + GRID_STEP/2, bounds.top,   GRID_STEP)
print(f"Grid: {len(lons)} x {len(lats)} = {len(lons)*len(lats):,} points")
print(f"Output: {DB_PATH}\n")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Removed existing DB")

conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
crop_keys = [f.replace('.tif', '') for f in tifs]
cols_def  = ", ".join([f'"{k}" REAL' for k in crop_keys])
c.execute(f"CREATE TABLE suitability (lat REAL NOT NULL, lon REAL NOT NULL, {cols_def})")
c.execute("CREATE INDEX idx_lat_lon ON suitability(lat, lon)")
conn.commit()
print(f"Created table with {len(crop_keys)} crop columns")

print("\nLoading rasters into memory...")
raster_data = {}
t0 = time.time()
for i, tif_file in enumerate(tifs):
    key  = tif_file.replace('.tif', '')
    with rasterio.open(os.path.join(TIF_DIR, tif_file)) as src:
        raster_data[key] = {
            "data":      src.read(1).astype(np.float32),
            "transform": src.transform,
            "nodata":    src.nodata,
            "height":    src.height,
            "width":     src.width,
        }
    if (i + 1) % 10 == 0:
        print(f"  Loaded {i+1}/{len(tifs)} ({time.time()-t0:.0f}s)")
print(f"All loaded in {time.time()-t0:.1f}s")

print("\nSampling grid points...")
t1 = time.time()
batch = []
total = 0

for lat in lats:
    for lon in lons:
        row_vals = {"lat": round(float(lat), 4), "lon": round(float(lon), 4)}
        has_data = False
        for key, meta in raster_data.items():
            try:
                r, ci = rowcol(meta["transform"], lon, lat)
                if r < 0 or ci < 0 or r >= meta["height"] or ci >= meta["width"]:
                    row_vals[key] = None; continue
                val = float(meta["data"][r, ci])
                nd  = meta["nodata"]
                if nd is not None and abs(val - nd) < 0.0001:
                    row_vals[key] = None
                elif 0 <= val <= 1:
                    row_vals[key] = round(val, 4); has_data = True
                else:
                    row_vals[key] = None
            except:
                row_vals[key] = None
        if has_data:
            batch.append(tuple([row_vals["lat"], row_vals["lon"]] + [row_vals.get(k) for k in crop_keys]))
            total += 1
        if len(batch) >= 5000:
            ph = ", ".join(["?"] * (len(crop_keys) + 2))
            c.executemany(f"INSERT INTO suitability VALUES ({ph})", batch)
            conn.commit(); batch = []
            print(f"  {total:,} points written ({time.time()-t1:.0f}s)")

if batch:
    ph = ", ".join(["?"] * (len(crop_keys) + 2))
    c.executemany(f"INSERT INTO suitability VALUES ({ph})", batch)
    conn.commit()

c.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
c.execute("INSERT INTO metadata VALUES ('crop_keys', ?)",    (json.dumps(crop_keys),))
c.execute("INSERT INTO metadata VALUES ('grid_step', ?)",    (str(GRID_STEP),))
c.execute("INSERT INTO metadata VALUES ('total_points', ?)", (str(total),))
conn.commit()
conn.close()

db_mb = os.path.getsize(DB_PATH) / 1e6
print(f"\nDone: {total:,} points, {db_mb:.1f} MB, {time.time()-t0:.0f}s total")
print(f"DB at: {DB_PATH}")
print("Copy maxent_suitability.db to your backend folder and HuggingFace repo.")
