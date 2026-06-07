#!/usr/bin/env python3
"""
Sanity-check the per-block-group city sales tax math.

Methodology:
1. For each BG, estimate aggregate annual sales/excise tax burden using ACS income
   brackets weighted by ITEP California Who Pays? 7th Edition (2024) quintile rates.
2. Pro-rate to Chico's actual annual city sales tax revenue (~$26M) so the
   aggregate matches observed reality.
3. Per-household estimate = BG aggregate / BG household count.

Note: this script runs over ALL Butte County BGs (200). For the production layer
we'll filter to Chico-specific BGs, but the methodology check is geographic-
agnostic — what we want to verify is that the income-bracket-weighted apportionment
produces sensible per-household numbers with the expected regressivity pattern.
"""

import json
import sys
from pathlib import Path

ACS_PATH = Path("public/data/_shared/butte-bg-acs.json")
CHICO_ANNUAL_CITY_SALES_TAX = 26_000_000  # approx, per earlier research

# ITEP "Who Pays?" 7th Edition CA — sales/excise tax as % of income, by quintile.
# Source: https://itep.org/california-who-pays-7th-edition/
# These are TOTAL state+local sales+excise burden; we use them as relative-weight
# inputs and pro-rate aggregate to Chico's actual city sales tax revenue.
ITEP_CA = {
    # ACS bracket name             ITEP rate    Bracket midpoint income
    "low_under_25k":      (0.076,   15_000),  # Lowest 20%
    "lower_mid_25_50k":   (0.063,   37_500),  # Second 20%
    "mid_50_75k":         (0.054,   62_500),  # Middle 20%
    "upper_mid_75_125k":  (0.041,  100_000),  # Fourth 20%
    "high_125k_plus":     (0.031,  200_000),  # Top 20% (top 1% is 1.0%, blended)
}


def relative_burden(income_bucket: dict) -> tuple[float, int]:
    """Returns (relative_sales_tax_burden, total_households) for a BG."""
    total_burden = 0.0
    total_hh = 0
    for bracket, (rate, midpoint) in ITEP_CA.items():
        hh = income_bucket.get(bracket, 0) or 0
        total_burden += hh * midpoint * rate
        total_hh += hh
    return total_burden, total_hh


def main() -> int:
    with ACS_PATH.open() as f:
        data = json.load(f)

    bgs = data["block_groups"]
    print(f"ACS source: {data['source']}")
    print(f"Generated:  {data['generated']}")
    print(f"BGs loaded: {len(bgs)}")
    print()

    enriched = []
    grand_burden = 0.0
    grand_hh = 0
    for geoid, bg in bgs.items():
        inc = bg.get("household_income") or {}
        burden, hh = relative_burden(inc)
        if hh == 0:
            continue
        enriched.append({
            "geoid": geoid,
            "tract": bg.get("tract"),
            "bg": bg.get("block_group"),
            "households": hh,
            "rel_burden": burden,
            "income_brackets": inc,
        })
        grand_burden += burden
        grand_hh += hh

    # Pro-rate to Chico's $26M
    for bg in enriched:
        bg["city_sales_tax_est"] = (
            CHICO_ANNUAL_CITY_SALES_TAX * bg["rel_burden"] / grand_burden
        )
        bg["per_household"] = bg["city_sales_tax_est"] / bg["households"]

    print("=" * 78)
    print("PER-BG SALES TAX APPORTIONMENT — AGGREGATE CHECK")
    print("=" * 78)
    print(f"BGs with households:      {len(enriched):>14,}")
    print(f"Total households:         {grand_hh:>14,}")
    print(f"Total relative burden:    ${grand_burden:>13,.0f}")
    print(f"Citywide pro-rate target: ${CHICO_ANNUAL_CITY_SALES_TAX:>13,.0f}")
    print(f"Citywide avg per hh:      ${CHICO_ANNUAL_CITY_SALES_TAX / grand_hh:>13.2f}")
    print()
    print("NOTE: running on all 200 Butte County BGs, not just Chico. Aggregate")
    print("naturally over-counts; the per-household distribution is what matters")
    print("for methodology validation.")

    # Distribution of per-household estimates
    print()
    print("=" * 78)
    print("PER-HOUSEHOLD CITY SALES TAX ESTIMATE — DISTRIBUTION")
    print("=" * 78)
    per_hh = sorted(b["per_household"] for b in enriched)
    for label, pct in [
        ("min", 0), ("p10", 10), ("p25", 25), ("median", 50),
        ("p75", 75), ("p90", 90), ("max", 100),
    ]:
        idx = max(0, min(len(per_hh) - 1, int(len(per_hh) * pct / 100)))
        print(f"  {label:>6s} ({pct:>3d}th):  ${per_hh[idx]:>8.2f}/yr per household")

    # Regressivity check — should see lower-income BGs paying smaller absolute
    # but LARGER % of income; higher-income BGs paying more absolute but smaller %.
    print()
    print("=" * 78)
    print("REGRESSIVITY CHECK — DIVERSE SAMPLE BGs BY INCOME PROFILE")
    print("=" * 78)

    def low_income_share(bg):
        inc = bg["income_brackets"]
        total = sum(v for k, v in inc.items() if k != "total_households") or 1
        return (inc.get("low_under_25k", 0) + inc.get("lower_mid_25_50k", 0)) / total

    def high_income_share(bg):
        inc = bg["income_brackets"]
        total = sum(v for k, v in inc.items() if k != "total_households") or 1
        return (inc.get("high_125k_plus", 0) + inc.get("upper_mid_75_125k", 0)) / total

    by_low_share = sorted(enriched, key=low_income_share, reverse=True)
    by_high_share = sorted(enriched, key=high_income_share, reverse=True)

    print("\n  Top 3 BGs by share of low-income households:")
    for bg in by_low_share[:3]:
        inc = bg["income_brackets"]
        print(f"\n    GEOID {bg['geoid']} (tract {bg['tract']} bg {bg['bg']})")
        print(f"      Households: {bg['households']:,}")
        print(f"      Low-income share:    {low_income_share(bg)*100:>5.1f}%")
        print(f"      High-income share:   {high_income_share(bg)*100:>5.1f}%")
        print(f"      Brackets: <25k={inc.get('low_under_25k',0)}, "
              f"25-50k={inc.get('lower_mid_25_50k',0)}, "
              f"50-75k={inc.get('mid_50_75k',0)}, "
              f"75-125k={inc.get('upper_mid_75_125k',0)}, "
              f"125k+={inc.get('high_125k_plus',0)}")
        print(f"      Per-household sales tax est: ${bg['per_household']:.2f}/yr")

    print("\n  Top 3 BGs by share of high-income households:")
    for bg in by_high_share[:3]:
        inc = bg["income_brackets"]
        print(f"\n    GEOID {bg['geoid']} (tract {bg['tract']} bg {bg['bg']})")
        print(f"      Households: {bg['households']:,}")
        print(f"      Low-income share:    {low_income_share(bg)*100:>5.1f}%")
        print(f"      High-income share:   {high_income_share(bg)*100:>5.1f}%")
        print(f"      Brackets: <25k={inc.get('low_under_25k',0)}, "
              f"25-50k={inc.get('lower_mid_25_50k',0)}, "
              f"50-75k={inc.get('mid_50_75k',0)}, "
              f"75-125k={inc.get('upper_mid_75_125k',0)}, "
              f"125k+={inc.get('high_125k_plus',0)}")
        print(f"      Per-household sales tax est: ${bg['per_household']:.2f}/yr")

    # Show the regressivity story explicitly
    print()
    print("=" * 78)
    print("REGRESSIVITY AS % OF INCOME (the actual fairness story)")
    print("=" * 78)
    print("\n  For each ITEP bracket, the % of income paid in sales/excise tax:")
    for bracket, (rate, midpoint) in ITEP_CA.items():
        print(f"    {bracket:25s}  rate={rate*100:.1f}%   midpoint=${midpoint:>6,}   "
              f"$/yr={int(rate*midpoint):>4,}")
    print()
    print("  Even though high-income households pay more dollars total, they pay a")
    print("  much SMALLER share of their income — this is the regressivity point.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
