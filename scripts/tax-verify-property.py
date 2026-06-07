#!/usr/bin/env python3
"""
Sanity-check the per-parcel city property tax math against aggregate expectations.

Methodology:
    city_property_tax_estimate = total_assessed_value * 0.01 * CITY_SHARE

CITY_SHARE = 0.054 is Chico's effective share of the 1% Prop 13 levy, derived
from HdL Companies' 2023/24 Property Tax Newsletter for Chico (city share ~$7M
on $12.9B taxable AV).

Aggregate target: sum should land around $7M (Chico's actual 1% share revenue).
"""

import sys
from collections import defaultdict
from pathlib import Path

import shapefile

SHAPEFILE = Path(
    "/Users/seantodd/Downloads/Parcels_Chico_CityLimits/Parcels_Chico_CityLimits"
)
# Effective shares from City of Chico FY 2025-26 Budget in Brief:
#   Property Tax line:          $15.6M  -> share of 1% levy = 12.1%
#   Property Tax in Lieu of VLF: $10.9M  -> apportioned proportional to AV
#   Combined ~$26.5M is ~26% of the $100.6M General Fund.
# We model property tax + VLF in-lieu together because, post-2004 state-local
# swap, VLF in-lieu is a backfilled stream tied to AV growth and functions as
# property tax from the household's perspective.
CITY_SHARE_PROPTAX = 0.121         # share of 1% Prop 13 levy
CITY_SHARE_VLF_IN_LIEU = 0.0849    # 10.9M / 128.4M = AV-proportional share
CITY_SHARE_COMBINED = CITY_SHARE_PROPTAX + CITY_SHARE_VLF_IN_LIEU  # ~0.206
TARGET_AGGREGATE_PROPTAX = 15_600_000     # FY 2025-26 budget
TARGET_AGGREGATE_COMBINED = 26_500_000    # property tax + VLF in-lieu

# Legacy 5.4% rate from earlier HdL-chart read — kept for documentation only.
LEGACY_CITY_SHARE = 0.054

USE_CODE_LABELS = {
    "RS": "Single-family residential",
    "R2": "Duplex / 2-unit residential",
    "R4": "4-unit residential",
    "R7": "Larger multifamily",
    "RA": "Apartment",
    "RC": "Condo",
    "RD": "Duplex/PUD",
    "RV": "Vacant residential",
    "CP": "Commercial",
    "CS": "Commercial / store",
    "IL": "Industrial",
    "IM": "Industrial / manufacturing",
}


def fmt_dollars(n: float) -> str:
    return f"${n:>14,.0f}"


def fmt_address(rec) -> str:
    parts = [
        rec["S_House"],
        rec["S_Str_Dir"],
        rec["S_Str"],
        rec["S_Str_Suf"],
    ]
    return " ".join(p.strip() for p in parts if p and p.strip())


def main() -> int:
    sf = shapefile.Reader(str(SHAPEFILE))
    field_names = [f[0] for f in sf.fields[1:]]

    records = []
    for raw in sf.iterRecords():
        rec = dict(zip(field_names, raw))
        ttl = rec.get("Ttl_Vl") or 0
        rec["city_tax_est"] = ttl * 0.01 * CITY_SHARE_COMBINED
        records.append(rec)

    total_av = sum(r["Ttl_Vl"] or 0 for r in records)
    total_tax_billed = sum(r["Tax_Amnt"] or 0 for r in records)
    total_city_est = sum(r["city_tax_est"] for r in records)

    print("=" * 78)
    print("PER-PARCEL CITY PROPERTY TAX MATH — AGGREGATE CHECK")
    print("=" * 78)
    print(f"Parcels:                     {len(records):>16,}")
    print(f"Total assessed value:        {fmt_dollars(total_av)}")
    print(f"Total tax bill (1% + bonds): {fmt_dollars(total_tax_billed)}")
    print(f"  Implied effective rate:    {100*total_tax_billed/total_av:>15.4f}%")
    print(f"Estimated city share:        {fmt_dollars(total_city_est)}")
    print(f"  (using combined rate of {CITY_SHARE_COMBINED*100:.1f}% = prop tax 12.1% + VLF in-lieu 8.5%)")
    print(f"Budget target (FY 2025-26):  {fmt_dollars(TARGET_AGGREGATE_COMBINED)}")
    delta_pct = 100 * (total_city_est - TARGET_AGGREGATE_COMBINED) / TARGET_AGGREGATE_COMBINED
    print(f"  Delta vs city budget:      {delta_pct:>+15.1f}%")

    # Use code breakdown
    by_use = defaultdict(lambda: {"count": 0, "av": 0.0, "city_tax": 0.0})
    for r in records:
        uc = r.get("Use_Code") or "?"
        by_use[uc]["count"] += 1
        by_use[uc]["av"] += r["Ttl_Vl"] or 0
        by_use[uc]["city_tax"] += r["city_tax_est"]

    print()
    print("=" * 78)
    print("BREAKDOWN BY USE CODE (top 12 by city tax contribution)")
    print("=" * 78)
    print(f"{'Use':6s} {'Label':32s} {'Count':>7s} {'Total AV':>16s} {'City tax est':>16s}")
    top = sorted(by_use.items(), key=lambda kv: -kv[1]["city_tax"])[:12]
    for uc, agg in top:
        label = USE_CODE_LABELS.get(uc, "")
        print(
            f"{uc:6s} {label:32s} {agg['count']:>7,} "
            f"{fmt_dollars(agg['av'])} {fmt_dollars(agg['city_tax'])}"
        )

    # Distribution percentiles
    print()
    print("=" * 78)
    print("PER-PARCEL CITY TAX ESTIMATE — DISTRIBUTION")
    print("=" * 78)
    estimates = sorted(r["city_tax_est"] for r in records if (r["Ttl_Vl"] or 0) > 0)
    for label, pct in [
        ("min", 0),
        ("p10", 10),
        ("p25", 25),
        ("median", 50),
        ("p75", 75),
        ("p90", 90),
        ("p99", 99),
        ("max", 100),
    ]:
        idx = max(0, min(len(estimates) - 1, int(len(estimates) * pct / 100)))
        print(f"  {label:>6s} ({pct:>3d}th):  ${estimates[idx]:>12,.2f}")
    print(f"  zero AV / unassessed:        {sum(1 for r in records if (r['Ttl_Vl'] or 0) == 0):>6,}")

    # Diverse named samples
    print()
    print("=" * 78)
    print("DIVERSE SAMPLE PARCELS (for human gut-check)")
    print("=" * 78)
    samples = []

    # Median single-family
    rs = sorted(
        (r for r in records if r["Use_Code"] == "RS" and (r["Ttl_Vl"] or 0) > 0),
        key=lambda r: r["Ttl_Vl"],
    )
    if rs:
        samples.append(("Median SFR (use=RS)", rs[len(rs) // 2]))
        samples.append(("p10 SFR (lower-value home)", rs[len(rs) // 10]))
        samples.append(("p90 SFR (higher-value home)", rs[len(rs) * 9 // 10]))

    # Top commercial
    com = sorted(
        (r for r in records if r["Use_Code"] in ("CP", "CS") and (r["Ttl_Vl"] or 0) > 0),
        key=lambda r: -r["Ttl_Vl"],
    )
    if com:
        samples.append(("Top commercial", com[0]))

    # Top apartment
    apt = sorted(
        (r for r in records if r["Use_Code"] in ("RA", "R7") and (r["Ttl_Vl"] or 0) > 0),
        key=lambda r: -r["Ttl_Vl"],
    )
    if apt:
        samples.append(("Top multifamily", apt[0]))

    # Overall highest AV parcel (likely Sierra Nevada Brewing)
    top_overall = max(records, key=lambda r: r["Ttl_Vl"] or 0)
    samples.append(("Highest AV parcel", top_overall))

    for label, r in samples:
        print(f"\n  {label}")
        print(f"    APN:               {r['APN']}")
        print(f"    Address:           {fmt_address(r) or '(no situs)'}")
        print(f"    Use code:          {r['Use_Code']} ({USE_CODE_LABELS.get(r['Use_Code'], '')})")
        print(f"    Lot size:          {r['Lt_Acre']:.2f} ac ({r['Lt_SqFt']:,.0f} sq ft)")
        print(f"    Land value:        {fmt_dollars(r['Land_Vl'] or 0)}")
        print(f"    Improvement value: {fmt_dollars(r['Impr_Vl'] or 0)}")
        print(f"    Total AV:          {fmt_dollars(r['Ttl_Vl'] or 0)}")
        print(f"    Total tax bill:    {fmt_dollars(r['Tax_Amnt'] or 0)}")
        print(f"    Est city share:    {fmt_dollars(r['city_tax_est'])}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
