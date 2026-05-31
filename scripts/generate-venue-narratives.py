#!/usr/bin/env python3
"""Generate per-venue speaker briefings for the top 50 venues in each district.

For each (venue, district) where priority_rank <= 50, synthesizes:
  - A 5-7 sentence narrative paragraph describing the catchment audience
    (legacy: kept for completeness but currently not rendered in the UI).
  - A research-grounded "Lead with" paragraph composed by the card library
    (scripts/narrative_cards.py), which matches the catchment against
    documented polling-regularity audience patterns and weaves 2-3 cards
    into a paragraph describing what topics likely matter to that audience.

Writes them directly into the venue entries of each district's
catchment-demographics.json so they travel with the data. Hand-written
Lead-with overrides for the top-10 venues per district live in
src/candidate/narratives.ts and take precedence in the UI.

Usage:
    python3 scripts/generate-venue-narratives.py
"""

import json
import sys
from pathlib import Path

# Allow `from narrative_cards import compose_lead_with` even when this script
# is run from the repo root (Python won't auto-add the script's directory).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from narrative_cards import compose_lead_with  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOP_N = 50


def safe_pct(num, den):
    return num / den if den else 0.0


def get_metrics(c):
    """Pull commonly-needed metrics from a catchment aggregate."""
    pop = c.get('total_population', 0)
    edu_total = sum(c.get(f'edu_{k}', 0) for k in (
        'less_than_hs', 'high_school', 'some_college', 'bachelors', 'graduate'
    ))
    income_total = sum(c.get(f'income_{k}', 0) for k in (
        'low_under_25k', 'lower_mid_25_50k', 'mid_50_75k',
        'upper_mid_75_125k', 'high_125k_plus'
    ))
    race_total = sum(c.get(f'race_{k}', 0) for k in (
        'white_nh', 'hispanic', 'asian_nh', 'black_nh',
        'two_or_more_nh', 'native_nh', 'pacific_nh', 'other_nh'
    ))
    tenure_total = c.get('tenure_owner', 0) + c.get('tenure_renter', 0)
    workers = c.get('commute_total_workers', 0)
    housing_total = sum(c.get(k, 0) for k in (
        'housing_single_family', 'housing_small_multifamily',
        'housing_large_multifamily', 'housing_mobile_home'
    ))
    reg24 = c.get('g24_total_registered', 0)
    reg22 = c.get('g22_total_registered', 0)
    tt24 = sum(c.get(f'g24_top_race_{p}', 0) for p in (
        'democratic', 'republican', 'libertarian', 'green',
        'peace_and_freedom', 'american_independent'
    ))
    tt22 = c.get('g22_top_race_democratic', 0) + c.get('g22_top_race_republican', 0)

    return {
        'pop': pop,
        'cvap': c.get('citizen_voting_age_population', 0),
        'households': c.get('households_total', 0),
        # age shares
        'senior_share': safe_pct(c.get('age_65_plus', 0), pop),
        'young_share': safe_pct(c.get('age_18_34', 0), pop),
        'kids_share': safe_pct(c.get('age_under_18', 0), pop),
        # race
        'white_share': safe_pct(c.get('race_white_nh', 0), race_total),
        'hispanic_share': safe_pct(c.get('race_hispanic', 0), race_total),
        'asian_share': safe_pct(c.get('race_asian_nh', 0), race_total),
        'multi_share': safe_pct(c.get('race_two_or_more_nh', 0), race_total),
        # education
        'college_share': safe_pct(
            c.get('edu_bachelors', 0) + c.get('edu_graduate', 0), edu_total
        ),
        'no_college_share': safe_pct(
            c.get('edu_less_than_hs', 0) + c.get('edu_high_school', 0), edu_total
        ),
        # income
        'low_income_share': safe_pct(
            c.get('income_low_under_25k', 0) + c.get('income_lower_mid_25_50k', 0),
            income_total
        ),
        'high_income_share': safe_pct(c.get('income_high_125k_plus', 0), income_total),
        # tenure / housing
        'renter_share': safe_pct(c.get('tenure_renter', 0), tenure_total),
        'owner_share': safe_pct(c.get('tenure_owner', 0), tenure_total),
        'single_family_share': safe_pct(c.get('housing_single_family', 0), housing_total),
        'multifamily_share': safe_pct(
            c.get('housing_large_multifamily', 0) + c.get('housing_small_multifamily', 0),
            housing_total
        ),
        # work
        'mgmt_share': safe_pct(
            c.get('occ_management_business_science_arts', 0),
            sum(c.get(k, 0) for k in (
                'occ_management_business_science_arts', 'occ_service', 'occ_sales_office',
                'occ_natural_resources_construction_maintenance',
                'occ_production_transportation_material_moving',
            ))
        ),
        'service_share': safe_pct(
            c.get('occ_service', 0),
            sum(c.get(k, 0) for k in (
                'occ_management_business_science_arts', 'occ_service', 'occ_sales_office',
                'occ_natural_resources_construction_maintenance',
                'occ_production_transportation_material_moving',
            ))
        ),
        'drove_alone_share': safe_pct(c.get('commute_drove_alone', 0), workers),
        'wfh_share': safe_pct(c.get('commute_work_from_home', 0), workers),
        'active_share': safe_pct(
            c.get('commute_walked', 0) + c.get('commute_bicycle', 0) + c.get('commute_public_transit', 0),
            workers
        ),
        # language
        'spanish_share': safe_pct(c.get('lang_spanish', 0), pop),
        # economic stress
        'rent_burdened_share': safe_pct(
            c.get('rent_burden_30_plus', 0), c.get('rent_burden_total', 0)
        ),
        'severe_rent_burdened_share': safe_pct(
            c.get('rent_burden_50_plus', 0), c.get('rent_burden_total', 0)
        ),
        'snap_share': safe_pct(c.get('snap_receiving', 0), c.get('snap_total_households', 0)),
        # politics
        'reg24': reg24,
        'd_share_24': safe_pct(c.get('g24_reg_democratic', 0), reg24),
        'r_share_24': safe_pct(c.get('g24_reg_republican', 0), reg24),
        'npp_share_24': safe_pct(c.get('g24_reg_no_party_preference', 0), reg24),
        'turnout_24': safe_pct(c.get('g24_total_votes', 0), reg24),
        'd_share_22': safe_pct(c.get('g22_reg_democratic', 0), reg22),
        'r_share_22': safe_pct(c.get('g22_reg_republican', 0), reg22),
        'turnout_22': safe_pct(c.get('g22_total_votes', 0), reg22),
        'top_d_24': safe_pct(c.get('g24_top_race_democratic', 0), tt24),
        'top_r_24': safe_pct(c.get('g24_top_race_republican', 0), tt24),
        'top_d_22': safe_pct(c.get('g22_top_race_democratic', 0), tt22),
        'top_r_22': safe_pct(c.get('g22_top_race_republican', 0), tt22),
    }


def pct(x):
    return f"{round(x * 100)}%"


def generate_narrative(venue_name, m, district):
    """Compose a 5-7 sentence narrative paragraph from the metrics."""
    sentences = []

    # ---- Sentence 1: anchor ----
    if m['pop'] < 100:
        size_phrase = "small, mostly residential pocket"
    elif m['pop'] < 400:
        size_phrase = "compact residential pocket"
    elif m['pop'] < 1000:
        size_phrase = "modest residential neighborhood"
    elif m['pop'] < 2000:
        size_phrase = "meaningfully sized neighborhood"
    else:
        size_phrase = "dense neighborhood"
    sentences.append(
        f"{venue_name}'s walking catchment is a {size_phrase} in D{district} — "
        f"roughly {m['pop']:,} residents and {m['cvap']:,} voting-age citizens within "
        f"a 15-minute walk."
    )

    # ---- Sentence 2: dominant demographic signal ----
    # Pick the most distinctive signal first.
    signals = []
    if m['senior_share'] >= 0.27 and m['young_share'] < 0.20:
        signals.append((
            'senior',
            f"The age skew is older: {pct(m['senior_share'])} of residents are 65 or older."
        ))
    if m['young_share'] >= 0.33 and m['senior_share'] < 0.18:
        signals.append((
            'young',
            f"The age skew is unusually young: {pct(m['young_share'])} of residents are 18-34 — "
            f"a student/early-career profile."
        ))
    if m['high_income_share'] >= 0.25 and m['low_income_share'] >= 0.30:
        signals.append((
            'bimodal',
            f"Income is bimodal: {pct(m['low_income_share'])} of households earn under $50k "
            f"while {pct(m['high_income_share'])} earn $125k+."
        ))
    elif m['high_income_share'] >= 0.35:
        signals.append((
            'affluent',
            f"It's an affluent area — {pct(m['high_income_share'])} of households earn $125k+ "
            f"and {pct(m['college_share'])} of adults hold a bachelor's or higher."
        ))
    elif m['low_income_share'] >= 0.45:
        signals.append((
            'low_income',
            f"It skews economically modest — {pct(m['low_income_share'])} of households earn "
            f"under $50k."
        ))
    if signals:
        sentences.append(signals[0][1])

    # ---- Sentence 3: housing + tenure (a second distinguishing characteristic) ----
    if m['renter_share'] >= 0.55 and m['multifamily_share'] >= 0.30:
        sentences.append(
            f"Housing is heavily rental and multifamily ({pct(m['renter_share'])} renter, "
            f"{pct(m['multifamily_share'])} multifamily units) — the typical resident here is a "
            f"renter, not an owner."
        )
    elif m['renter_share'] >= 0.50:
        sentences.append(
            f"It's renter-majority ({pct(m['renter_share'])} renter), with "
            f"{pct(m['single_family_share'])} single-family stock and "
            f"{pct(m['multifamily_share'])} multifamily."
        )
    elif m['single_family_share'] >= 0.85 and m['owner_share'] >= 0.65:
        sentences.append(
            f"Housing is overwhelmingly single-family ({pct(m['single_family_share'])}) "
            f"and owner-occupied ({pct(m['owner_share'])}) — a stable homeowner belt."
        )

    # ---- Sentence 4: workforce + commute ----
    if m['mgmt_share'] >= 0.50:
        work_line = (
            f"The workforce is dominated by management, business, science, and arts roles "
            f"({pct(m['mgmt_share'])})"
        )
    elif m['service_share'] >= 0.30:
        work_line = f"Service work is the largest occupation category ({pct(m['service_share'])})"
    else:
        work_line = None
    commute_bits = []
    if m['drove_alone_share'] >= 0.70:
        commute_bits.append(f"{pct(m['drove_alone_share'])} drive alone to work")
    if m['wfh_share'] >= 0.15:
        commute_bits.append(f"{pct(m['wfh_share'])} work from home")
    if m['active_share'] >= 0.12:
        commute_bits.append(f"{pct(m['active_share'])} commute by bike/walk/transit")
    if work_line and commute_bits:
        sentences.append(f"{work_line}; " + " and ".join(commute_bits) + ".")
    elif work_line:
        sentences.append(work_line + ".")
    elif commute_bits:
        sentences.append("Commute patterns: " + ", ".join(commute_bits) + ".")

    # ---- Sentence 5: cultural / language ----
    if m['spanish_share'] >= 0.12:
        sentences.append(
            f"There's a meaningful bilingual community — about {pct(m['spanish_share'])} of "
            f"residents speak Spanish at home."
        )

    # ---- Sentence 6: economic stress ----
    if m['rent_burdened_share'] >= 0.45 and m['renter_share'] >= 0.30:
        sentences.append(
            f"Cost stress is a live issue: {pct(m['rent_burdened_share'])} of renters are "
            f"rent-burdened (paying 30%+ of income on rent), with "
            f"{pct(m['severe_rent_burdened_share'])} severely so."
        )
    elif m['snap_share'] >= 0.20:
        sentences.append(
            f"Economic stress is visible — {pct(m['snap_share'])} of households here receive SNAP."
        )

    # ---- Sentences 7-8: politics + trend ----
    if m['reg24'] >= 50:
        lean = m['d_share_24'] - m['r_share_24']
        if abs(lean) <= 0.04:
            pol_lead = "Politically the neighborhood is competitive"
        elif lean >= 0.08:
            pol_lead = "The neighborhood leans Democratic"
        elif lean <= -0.08:
            pol_lead = "The neighborhood leans Republican"
        else:
            pol_lead = "The neighborhood tilts slightly " + ("Democratic" if lean > 0 else "Republican")
        sentences.append(
            f"{pol_lead} — {pct(m['d_share_24'])} D / {pct(m['r_share_24'])} R / "
            f"{pct(m['npp_share_24'])} NPP in registration, with "
            f"{pct(m['turnout_24'])} turnout in 2024."
        )
        # Trend
        if m['top_d_24'] > 0 and m['top_d_22'] > 0:
            shift = m['top_d_24'] - m['top_d_22']
            if shift >= 0.03:
                sentences.append(
                    f"The top-of-ticket vote shifted Democratic between cycles: Harris took "
                    f"{pct(m['top_d_24'])} of the vote here in 2024, up "
                    f"{round(shift * 100)} points from Newsom's {pct(m['top_d_22'])} in 2022."
                )
            elif shift <= -0.03:
                sentences.append(
                    f"The top-of-ticket vote shifted Republican between cycles: Harris took "
                    f"{pct(m['top_d_24'])} of the vote in 2024, down "
                    f"{round(-shift * 100)} points from Newsom's {pct(m['top_d_22'])} in 2022."
                )

    return " ".join(sentences)


def generate_lead_with(m, venue_id: str) -> str:
    """Compose a research-grounded Lead-with paragraph.

    Delegates to the card library in narrative_cards.py, which matches the
    catchment against documented audience patterns (PPIC, Pew, AP-NORC,
    ANES regularities) and weaves 2-3 cards into an audience-priorities
    paragraph. Variant selection is deterministic from venue_id so reruns
    produce stable output but adjacent venues vary phrasing.
    """
    return compose_lead_with(m, venue_id)




def process_district(district: int) -> tuple[int, int]:
    """Generate narratives for top-N venues in a district. Returns (total, generated)."""
    path = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}" / "catchment-demographics.json"
    venues_path = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}" / "venues.geojson"
    if not path.exists() or not venues_path.exists():
        return (0, 0)

    demo = json.loads(path.read_text())
    venues_data = json.loads(venues_path.read_text())

    # Map osm_id -> priority_rank
    rank_by_id = {
        f["properties"]["osm_id"]: f["properties"].get("priority_rank", 9_999)
        for f in venues_data["features"]
    }

    generated = 0
    for venue_id, vinfo in demo["venues"].items():
        rank = rank_by_id.get(venue_id, 9_999)
        if rank > TOP_N:
            continue
        walk_15 = vinfo.get("catchments", {}).get("walk_15", {}).get("in_district")
        if not walk_15:
            continue
        m = get_metrics(walk_15)
        if m["pop"] < 30:
            continue
        narrative = generate_narrative(vinfo["venue_name"], m, district)
        lead_with = generate_lead_with(m, venue_id)
        if narrative and lead_with:
            vinfo["narrative"] = narrative
            vinfo["lead_with"] = lead_with
            generated += 1

    path.write_text(json.dumps(demo, indent=2))
    return (len(demo["venues"]), generated)


def main() -> int:
    for d in (6, 4, 2):
        total, generated = process_district(d)
        print(f"D{d}: wrote {generated} narratives (of {total} venues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
