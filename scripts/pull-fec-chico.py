#!/usr/bin/env python3
"""Stream-parse FEC individual contributions (indiv24.zip) for Chico-area ZIPs
and produce a per-ZIP partisan-giving summary.

The FEC publishes a ~4 GB compressed (~11 GB uncompressed) pipe-delimited
file of every individual contribution made nationwide in the 2024 cycle.
We stream it from disk (no full decompression to memory), keep only rows
where STATE='CA' and ZIP_CODE starts with a Chico-area prefix, look up
the receiving committee's party affiliation in cm.txt, and accumulate
totals per ZIP × party.

Output: public/data/_shared/fec-chico-by-zip.json with the shape
  {
    "generated": "...",
    "cycle": 2024,
    "by_zip": {
      "95926": {
        "donor_count": N, "total_amount": $,
        "by_party": { "DEM": {amount, donor_count}, "REP": {...}, ... }
      },
      ...
    }
  }
"""

import csv
import json
import time
import zipfile
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "fec"

# 95926 = downtown / CSU
# 95928 = south Chico
# 95973 = east Chico / Forest Ranch
# 95975 = north Chico
# 95976 = PO box only (skip if no real residences)
# 95927 = west Chico
# 95929 = CSU campus housing
CHICO_ZIP_PREFIXES = ("95926", "95927", "95928", "95929", "95973", "95975", "95976")

# FEC indiv field positions (per FEC bulk-data docs).
F_CMTE_ID = 0
F_NAME = 7
F_CITY = 8
F_STATE = 9
F_ZIP = 10
F_EMPLOYER = 11
F_OCCUPATION = 12
F_TRANSACTION_DT = 13
F_TRANSACTION_AMT = 14

# CM (committee master) field positions
CM_CMTE_ID = 0
CM_CMTE_NM = 1
CM_PARTY = 10


def load_committee_party() -> dict[str, str]:
    """Build CMTE_ID → party affiliation map from cm.txt."""
    cm_path = CACHE_DIR / "cm.txt"
    if not cm_path.exists():
        raise FileNotFoundError(
            f"{cm_path} missing. Download cm24.zip first and unzip into .cache/fec/."
        )
    by_id: dict[str, str] = {}
    with cm_path.open(encoding="latin-1") as f:
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) <= CM_PARTY:
                continue
            party = (cols[CM_PARTY] or "").strip().upper()
            by_id[cols[CM_CMTE_ID]] = party or "NONE"
    return by_id


def party_bucket(p: str) -> str:
    """Collapse FEC party codes into a small set for display."""
    if p in ("DEM",):
        return "DEM"
    if p in ("REP",):
        return "REP"
    if p in ("LIB",):
        return "LIB"
    if p in ("GRE",):
        return "GRE"
    if p in ("IND",):
        return "IND"
    return "OTHER"  # PACs without a party (most corporate/issue PACs)


def main() -> int:
    indiv_zip = CACHE_DIR / "indiv24.zip"
    if not indiv_zip.exists():
        print(f"{indiv_zip} missing.")
        return 1

    print("Loading committee party affiliations from cm.txt...")
    cmte_party = load_committee_party()
    print(f"  {len(cmte_party):,} committees indexed")

    print("Streaming indiv24.zip → filtering to Chico ZIPs ...")
    by_zip: dict[str, dict] = defaultdict(lambda: {
        "donor_count": 0,
        "total_amount": 0.0,
        "by_party": defaultdict(lambda: {"amount": 0.0, "donor_count": 0}),
    })

    # Track unique donor records (name + zip) so we don't double-count multi-contribution donors.
    seen_donors_by_zip = defaultdict(set)
    seen_donors_by_zip_party = defaultdict(set)

    total_seen = 0
    total_matched = 0
    t0 = time.time()
    with zipfile.ZipFile(indiv_zip) as z:
        with z.open("itcont.txt") as f:
            for raw in f:
                total_seen += 1
                if total_seen % 1_000_000 == 0:
                    rate = total_seen / (time.time() - t0)
                    print(f"  scanned {total_seen:,} rows ({rate:,.0f}/s), kept {total_matched:,}")
                line = raw.decode("latin-1", errors="replace")
                # Quick reject: state must be CA
                if "|CA|" not in line:
                    continue
                cols = line.rstrip("\n").split("|")
                if len(cols) <= F_TRANSACTION_AMT:
                    continue
                if cols[F_STATE] != "CA":
                    continue
                zip_full = cols[F_ZIP] or ""
                # ZIPs are usually 5 digits or 5+4; take first 5.
                zip5 = zip_full[:5]
                if zip5 not in CHICO_ZIP_PREFIXES:
                    continue
                try:
                    amount = float(cols[F_TRANSACTION_AMT] or 0)
                except ValueError:
                    amount = 0.0
                if amount <= 0:
                    continue  # skip refunds / zero rows
                cmte = cols[F_CMTE_ID]
                party = party_bucket(cmte_party.get(cmte, "NONE"))
                name = cols[F_NAME].strip().upper()
                donor_key = f"{name}|{zip5}"

                zr = by_zip[zip5]
                zr["total_amount"] += amount
                if donor_key not in seen_donors_by_zip[zip5]:
                    seen_donors_by_zip[zip5].add(donor_key)
                    zr["donor_count"] += 1
                pr = zr["by_party"][party]
                pr["amount"] += amount
                pk = (party, donor_key)
                if pk not in seen_donors_by_zip_party[zip5]:
                    seen_donors_by_zip_party[zip5].add(pk)
                    pr["donor_count"] += 1
                total_matched += 1

    elapsed = time.time() - t0
    print(f"\nScanned {total_seen:,} rows in {elapsed:.0f}s ({total_seen/elapsed:,.0f}/s)")
    print(f"Matched {total_matched:,} Chico-area contributions across {len(by_zip)} ZIPs")

    # Convert defaultdicts and round
    output_by_zip = {}
    for zip5, agg in by_zip.items():
        by_party = {}
        for party, pa in agg["by_party"].items():
            by_party[party] = {
                "amount": round(pa["amount"], 2),
                "donor_count": pa["donor_count"],
            }
        output_by_zip[zip5] = {
            "donor_count": agg["donor_count"],
            "total_amount": round(agg["total_amount"], 2),
            "by_party": by_party,
        }

    output = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cycle": 2024,
        "source": "FEC bulk download indiv24.zip + cm24.zip",
        "note": (
            "Sums of individual contributions per Chico ZIP, classified by the "
            "receiving committee's FEC party affiliation. PACs without a party "
            "affiliation aggregate to OTHER. Donor counts dedupe by NAME|ZIP."
        ),
        "by_zip": output_by_zip,
    }

    out_dir = PROJECT_ROOT / "public" / "data" / "_shared"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fec-chico-by-zip.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote {out_path}")

    # Aggregate summary
    print("\nPer-ZIP summary:")
    for zip5, agg in sorted(output_by_zip.items()):
        print(f"  {zip5}: {agg['donor_count']:>4} donors, ${agg['total_amount']:>11,.2f}")
        for party in ("DEM", "REP", "LIB", "GRE", "IND", "OTHER"):
            pa = agg["by_party"].get(party)
            if pa:
                pct = pa["amount"] / agg["total_amount"] * 100 if agg["total_amount"] else 0
                print(f"     {party:5s}: ${pa['amount']:>10,.2f} ({pct:>4.1f}%)  {pa['donor_count']} donors")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
