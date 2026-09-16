
import os
import subprocess
import shutil

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOPPEN_BASE = os.getenv("KOPPEN_DIR", os.path.join(_REPO_ROOT, "data", "koppen"))
GDAL_TRANSLATE = "/Applications/QGIS-LTR.app/Contents/MacOS/bin/gdal_translate"


if not os.path.exists(GDAL_TRANSLATE):
    GDAL_TRANSLATE = "gdal_translate"


tif_paths = []
for root, dirs, files in os.walk(KOPPEN_BASE):
    for f in files:
        if f.endswith(".tif"):
            tif_paths.append(os.path.join(root, f))

print(f"Found {len(tif_paths)} Köppen TIF files:")
for p in tif_paths:
    size_mb = os.path.getsize(p) / 1e6
    print(f"  {p.replace(KOPPEN_BASE, '')} ({size_mb:.1f} MB)")

print()

converted = 0
errors = []

for tif_path in tif_paths:
    tmp_path = tif_path + ".cog_tmp.tif"

    print(f"Converting: {tif_path.replace(KOPPEN_BASE, 'koppen')}")

    
    cmd = [
        GDAL_TRANSLATE,
        "-of", "GTiff",
        "-co", "TILED=YES",
        "-co", "COMPRESS=DEFLATE",
        "-co", "PREDICTOR=2",
        "-co", "BLOCKXSIZE=512",
        "-co", "BLOCKYSIZE=512",
        "-co", "COPY_SRC_OVERVIEWS=YES",
        "--config", "GDAL_TIFF_OVR_BLOCKSIZE", "512",
        tif_path,
        tmp_path
    ]

    
    ovr_cmd = [
        GDAL_TRANSLATE.replace("gdal_translate", "gdaladdo"),
        "-r", "nearest",
        tif_path,
        "2", "4", "8", "16"
    ]

    
    gdaladdo = GDAL_TRANSLATE.replace("gdal_translate", "gdaladdo")
    r1 = subprocess.run(
        [gdaladdo, "-r", "nearest", tif_path, "2", "4", "8", "16"],
        capture_output=True, text=True
    )
    if r1.returncode != 0:
        print(f"  Warning: gdaladdo failed: {r1.stderr[:100]}")

    
    r2 = subprocess.run(cmd, capture_output=True, text=True)

    if r2.returncode == 0 and os.path.exists(tmp_path):
        orig_mb = os.path.getsize(tif_path) / 1e6
        new_mb  = os.path.getsize(tmp_path) / 1e6
        
        os.replace(tmp_path, tif_path)
        print(f"  OK: {orig_mb:.1f} MB -> {new_mb:.1f} MB")
        converted += 1
    else:
        print(f"  ERROR: {r2.stderr[:150]}")
        errors.append(tif_path)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

print(f"\nDone: {converted}/{len(tif_paths)} converted")
if errors:
    print(f"Errors: {errors}")


print("\nVerifying COG validity...")
try:
    import subprocess
    for tif in tif_paths[:1]:
        r = subprocess.run(
            [GDAL_TRANSLATE.replace("gdal_translate", "gdalinfo"), tif],
            capture_output=True, text=True
        )
        if "LAYOUT=COG" in r.stdout or "Block=" in r.stdout:
            print(f"  Tiling confirmed in: {tif}")
        else:
            print(f"  Note: {tif} may not have COG layout — check with gdalinfo")
except:
    pass
