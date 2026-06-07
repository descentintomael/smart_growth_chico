#!/bin/zsh
# Download Butte County parcels filtered to City of Chico as a single GeoJSON.
# Source: ArcGIS Online public layer hosted by Butte County GIS.
# Service: Butte_County_Parcel_Public_Data (FeatureServer/0)
# Filter:  GP = 'City of Chico'  (uses general-plan jurisdiction, matches city limits)
# Total expected features: ~55,692
# Paginates at 2000 records per request (server maxRecordCount).

set -euo pipefail

OUT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE="https://services.arcgis.com/3t3QfTXFRFX44zo8/arcgis/rest/services/Butte_County_Parcel_Public_Data/FeatureServer/0/query"
WHERE='GP = '\''City of Chico'\'''
PAGE_SIZE=2000
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading Chico parcels in pages of $PAGE_SIZE -> $TMP_DIR"
offset=0
page=0
while :; do
  page_file="$TMP_DIR/page_${page}.geojson"
  curl -sfL --get "$SERVICE" \
    --data-urlencode "where=${WHERE}" \
    --data-urlencode "outFields=*" \
    --data-urlencode "f=geojson" \
    --data-urlencode "resultOffset=${offset}" \
    --data-urlencode "resultRecordCount=${PAGE_SIZE}" \
    --data-urlencode "orderByFields=FID" \
    --data-urlencode "geometryPrecision=6" \
    -o "$page_file"

  n=$(python3 -c "import json; print(len(json.load(open('$page_file'))['features']))")
  echo "  page $page offset=$offset got=$n"
  if (( n == 0 )); then
    rm -f "$page_file"
    break
  fi
  page=$((page + 1))
  offset=$((offset + n))
  if (( n < PAGE_SIZE )); then
    break
  fi
done

echo "Merging $page pages into chico-parcels.geojson"
python3 - "$TMP_DIR" "$OUT_DIR/chico-parcels.geojson" <<'PY'
import json, sys, glob, os
tmp_dir, out_path = sys.argv[1], sys.argv[2]
features = []
crs = None
for path in sorted(glob.glob(os.path.join(tmp_dir, "page_*.geojson")),
                   key=lambda p: int(os.path.basename(p).split('_')[1].split('.')[0])):
    with open(path) as fh:
        page = json.load(fh)
    features.extend(page.get("features", []))
    crs = crs or page.get("crs")
merged = {"type": "FeatureCollection", "features": features}
if crs:
    merged["crs"] = crs
with open(out_path, "w") as fh:
    json.dump(merged, fh)
print(f"wrote {len(features)} features to {out_path}")
PY
ls -lh "$OUT_DIR/chico-parcels.geojson"
