#!/usr/bin/env python3
"""Pull Butte County precinct-level voter registration + election results from
the Statewide Database (UC Berkeley) for one or more elections.

Downloads the SR-precinct shapefile and CSVs for each requested election,
joins them, and writes per-precinct GeoJSON files containing:

  - Party registration counts (D, R, NPP/DCL, Lib, Grn, AIP, etc.)
  - Top-of-ticket vote shares by party
  - Turnout (TOTVOTE / TOTREG)

Output: public/data/_shared/butte-precincts-g{YY}.geojson per election.

Usage:
    python3 scripts/pull-swdb-voter-data.py            # default: pulls g24 + g22
    python3 scripts/pull-swdb-voter-data.py g24        # just one
"""

import csv
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "swdb"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

COUNTY = "007"  # Butte

# Per-election config: which top-of-ticket race columns to pull.
ELECTION_CONFIG = {
    "g24": {
        "label": "2024 General",
        "top_race": "presidential_2024",
        "top_race_columns": {
            "PRSDEM01": "democratic",
            "PRSREP01": "republican",
            "PRSLIB01": "libertarian",
            "PRSGRN01": "green",
            "PRSPAF01": "peace_and_freedom",
            "PRSAIP01": "american_independent",
        },
        "senate_columns": {"USSDEM01": "democratic", "USSREP01": "republican"},
    },
    "g22": {
        "label": "2022 General",
        "top_race": "gubernatorial_2022",
        "top_race_columns": {
            "GOVDEM01": "democratic",
            "GOVREP01": "republican",
        },
        "senate_columns": {"USSDEM01": "democratic", "USSREP01": "republican"},
    },
}


def download_if_missing(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    print(f"  Downloading {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def load_csv(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def to_int(v) -> int:
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def pull_election(election: str) -> None:
    cfg = ELECTION_CONFIG[election]
    base = f"https://statewidedatabase.org/pub/data/{election.upper()}/c{COUNTY}"
    print(f"\n=== {cfg['label']} ({election}) ===")

    shp_zip = CACHE_DIR / f"srprec_{COUNTY}_{election}_shp.zip"
    download_if_missing(f"{base}/srprec_{COUNTY}_{election}_v01_shp.zip", shp_zip)
    with zipfile.ZipFile(shp_zip) as z:
        z.extractall(CACHE_DIR)
    shp_path = CACHE_DIR / f"srprec_{COUNTY}_{election}_v01.shp"

    reg_csv = CACHE_DIR / f"c{COUNTY}_{election}_reg_sr.csv"
    download_if_missing(
        f"{base}/c{COUNTY}_{election}_registration_by_{election}_srprec.csv",
        reg_csv,
    )

    sov_csv = CACHE_DIR / f"c{COUNTY}_{election}_sov_sr.csv"
    download_if_missing(
        f"{base}/c{COUNTY}_{election}_sov_data_by_{election}_srprec.csv",
        sov_csv,
    )

    precincts = gpd.read_file(shp_path).to_crs(epsg=4326)
    # Different election vintages capitalize the column differently.
    col = "srprec" if "srprec" in precincts.columns else "SRPREC"
    precincts["srprec"] = precincts[col].astype(str)
    reg_by_prec = {row["srprec"]: row for row in load_csv(reg_csv)}
    sov_by_prec = {row["srprec"]: row for row in load_csv(sov_csv)}
    print(f"  {len(precincts)} precincts · {len(reg_by_prec)} reg · {len(sov_by_prec)} sov")

    features = []
    for _, prow in precincts.iterrows():
        srprec = prow["srprec"]
        reg = reg_by_prec.get(srprec, {})
        sov = sov_by_prec.get(srprec, {})

        total_reg = to_int(reg.get("totreg_r")) or to_int(sov.get("TOTREG"))
        total_vote = to_int(sov.get("TOTVOTE"))

        registration = {
            "total_registered": total_reg,
            "democratic": to_int(reg.get("dem")),
            "republican": to_int(reg.get("rep")),
            "no_party_preference": to_int(reg.get("dcl")),
            "american_independent": to_int(reg.get("aip")),
            "libertarian": to_int(reg.get("lib")),
            "green": to_int(reg.get("grn")),
            "peace_and_freedom": to_int(reg.get("paf")),
            "other": (to_int(reg.get("msc")) + to_int(reg.get("nlp")) + to_int(reg.get("ref"))),
            "male": to_int(reg.get("male")),
            "female": to_int(reg.get("female")),
        }

        top_race = {label: to_int(sov.get(col)) for col, label in cfg["top_race_columns"].items()}
        senate = {label: to_int(sov.get(col)) for col, label in cfg["senate_columns"].items()}
        turnout = (total_vote / total_reg) if total_reg else 0.0

        features.append({
            "type": "Feature",
            "geometry": prow.geometry.__geo_interface__,
            "properties": {
                "srprec": srprec,
                "election": election,
                "total_registered": total_reg,
                "total_votes": total_vote,
                "turnout": round(turnout, 4),
                "registration": registration,
                "top_race_name": cfg["top_race"],
                "top_race": top_race,
                "senate": senate,
            },
        })

    fc = {"type": "FeatureCollection", "features": features}
    out_dir = PROJECT_ROOT / "public" / "data" / "_shared"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"butte-precincts-{election}.geojson"
    out_path.write_text(json.dumps(fc))
    print(f"  Wrote {out_path} ({out_path.stat().st_size:,} bytes)")

    # Citywide sanity
    total_reg_all = sum(f["properties"]["registration"]["total_registered"] for f in features)
    dem = sum(f["properties"]["registration"]["democratic"] for f in features)
    rep = sum(f["properties"]["registration"]["republican"] for f in features)
    npp = sum(f["properties"]["registration"]["no_party_preference"] for f in features)
    total_votes = sum(f["properties"]["total_votes"] for f in features)
    pct = lambda v, t: f"{v/t*100:.1f}%" if t else "0%"
    print(
        f"  Butte total: {total_reg_all:,} reg · "
        f"D {dem:,} ({pct(dem, total_reg_all)}) · "
        f"R {rep:,} ({pct(rep, total_reg_all)}) · "
        f"NPP {npp:,} ({pct(npp, total_reg_all)})"
    )
    if total_votes:
        print(f"  Turnout: {pct(total_votes, total_reg_all)}")
    if any(top_race.values() for f in features for top_race in [f["properties"]["top_race"]]):
        tr_total = {k: 0 for k in cfg["top_race_columns"].values()}
        for f in features:
            for k, v in f["properties"]["top_race"].items():
                tr_total[k] += v
        tr_sum = sum(tr_total.values())
        print(f"  {cfg['top_race']}: " + " · ".join(
            f"{k[:3].upper()} {v:,} ({pct(v, tr_sum)})" for k, v in tr_total.items() if v
        ))


def main() -> int:
    elections = sys.argv[1:] if len(sys.argv) > 1 else list(ELECTION_CONFIG.keys())
    for e in elections:
        if e not in ELECTION_CONFIG:
            print(f"Unknown election: {e}", file=sys.stderr)
            return 1
        pull_election(e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
