#!/usr/bin/env python3
"""Compute a per-venue forum-host priority score and rank.

For each venue in a district, derives a composite score (0–1) from four
component scores, then ranks venues 1..N within the district:

  1. AUDIENCE (40%)    Walk-15-min in-district CVAP, log-scaled so 100 voters
                       ≈ 0.5, 1,000 ≈ 0.75, 10,000+ ≈ 1.0.
  2. CONFIDENCE (25%)  hosting_status: confirmed=1, likely=0.7,
                       needs_verification=0.4, excluded=0.
  3. FIT (25%)         Category-appropriateness for a 50-150 person forum
                       (events venues 1.0, restaurants 0.6, gyms 0.4, etc.).
  4. LEGITIMACY (10%)  Google rating × review count signal that the venue is
                       real and well-regarded.

Modifiers:
  + Public-facility bonus (+0.05) for libraries, community centres, schools,
    and CARD-operated venues — these are typically free/cheap and neutral.
  - Out-of-district-no-reach penalty (×0.3) for venues whose walk-15
    catchment doesn't contain ANY in-district residents.

Writes priority_score / priority_tier / priority_rank / priority_components
back into venues.geojson.

Usage:
    python3 scripts/score-venue-priority.py 6
"""

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WEIGHT_AUDIENCE = 0.40
WEIGHT_CONFIDENCE = 0.25
WEIGHT_FIT = 0.25
WEIGHT_LEGITIMACY = 0.10

CONFIDENCE_SCORES = {
    "confirmed": 1.0,
    "likely": 0.7,
    "needs_verification": 0.4,
    "excluded": 0.0,
}

CATEGORY_FIT_FORUM = {
    # Purpose-built event spaces — top tier
    "events_venue": 1.0,
    "conference_centre": 1.0,
    "arts_centre": 1.0,
    "theatre": 1.0,
    "music_venue": 0.95,
    "cinema": 0.9,
    # Civic / community spaces — high tier
    "community_centre": 0.9,
    "social_centre": 0.9,
    "library": 0.9,
    "townhall": 0.9,
    "clubhouse": 0.85,
    # Education — auditoriums work but require approval
    "college": 0.8,
    "university": 0.8,
    "school": 0.8,
    # Tourism / hospitality
    "tourism_museum": 0.75,
    "tourism_gallery": 0.65,
    "tourism_hotel": 0.65,
    "tourism_motel": 0.5,
    # Clubs / golf / fraternal
    "golf_course": 0.75,
    "club_country_club": 0.8,
    "club_social": 0.75,
    "club_veterans": 0.8,  # VFW/Legion halls regularly host civic events
    "club_sport": 0.55,
    "club_freemasonry": 0.6,
    # Eating + drinking establishments
    "restaurant": 0.6,
    "craft_brewery": 0.7,
    "craft_winery": 0.7,
    "craft_distillery": 0.7,
    "biergarten": 0.65,
    "pub": 0.55,
    "bar": 0.55,
    "cafe": 0.5,
    # Marketplaces, offices, social facilities
    "marketplace": 0.6,
    "office_coworking": 0.65,
    "social_facility": 0.4,
    # Retail (rarely event-friendly)
    "shop_books": 0.55,
}
DEFAULT_FIT = 0.45  # categories we haven't enumerated

PUBLIC_CATEGORIES = {
    "library", "community_centre", "social_centre", "townhall",
    "college", "university", "school", "clubhouse",
}
PUBLIC_OPERATOR_PATTERNS = [
    "Chico Area Recreation", "CARD", "City of Chico",
    "County of Butte", "Butte College", "California State University",
]


def district_dir(n: int) -> Path:
    return PROJECT_ROOT / "public" / "data" / f"candidate-district-{n}"


def audience_score(in_district_cvap: int) -> float:
    """log10(cvap+10) / 4 with a 1.0 ceiling. 100 voters ≈ 0.5, 10000 ≈ 1.0."""
    if in_district_cvap <= 0:
        return 0.0
    return min(math.log10(in_district_cvap + 10) / 4.0, 1.0)


def confidence_score(hosting_status: str) -> float:
    return CONFIDENCE_SCORES.get(hosting_status, 0.4)


def fit_score(category: str) -> float:
    return CATEGORY_FIT_FORUM.get(category, DEFAULT_FIT)


def legitimacy_score(props: dict) -> float:
    if props.get("google_business_status") == "CLOSED_PERMANENTLY":
        return 0.0
    rating = props.get("google_rating")
    n_reviews = props.get("google_user_ratings_count")
    if rating is None or n_reviews is None:
        return 0.5  # operational but unrated — neutral
    if rating >= 4.0 and n_reviews >= 100:
        return 1.0
    if rating >= 3.5 or n_reviews >= 50:
        return 0.7
    return 0.5


def is_public_facility(props: dict) -> bool:
    if props.get("category") in PUBLIC_CATEGORIES:
        return True
    operator = (props.get("operator") or "")
    return any(pat.lower() in operator.lower() for pat in PUBLIC_OPERATOR_PATTERNS)


def tier_from_score(score: float) -> str:
    if score >= 0.75:
        return "top"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int)
    args = parser.parse_args()

    d = args.district
    venues_path = district_dir(d) / "venues.geojson"
    demo_path = district_dir(d) / "catchment-demographics.json"
    if not venues_path.exists() or not demo_path.exists():
        print(f"Required files missing for district {d}.", file=sys.stderr)
        return 1

    venues = json.loads(venues_path.read_text())
    demo = json.loads(demo_path.read_text())["venues"]

    # Score everyone
    for feat in venues["features"]:
        props = feat["properties"]
        venue_id = props["osm_id"]
        cd = demo.get(venue_id, {}).get("catchments", {})
        walk_15_in = cd.get("walk_15", {}).get("in_district", {})
        in_district_cvap = walk_15_in.get("citizen_voting_age_population", 0)
        in_district_pop = walk_15_in.get("total_population", 0)

        a = audience_score(in_district_cvap)
        c = confidence_score(props.get("hosting_status", "needs_verification"))
        f = fit_score(props.get("category", "other"))
        l = legitimacy_score(props)

        composite = (
            WEIGHT_AUDIENCE * a
            + WEIGHT_CONFIDENCE * c
            + WEIGHT_FIT * f
            + WEIGHT_LEGITIMACY * l
        )
        public_bonus = 0.05 if is_public_facility(props) else 0.0
        composite = min(composite + public_bonus, 1.0)

        # Heavy penalty if the walk-15 catchment doesn't reach any in-district residents.
        if in_district_pop == 0:
            composite *= 0.3

        props["priority_score"] = round(composite, 4)
        props["priority_tier"] = tier_from_score(composite)
        props["priority_components"] = {
            "audience": round(a, 3),
            "confidence": round(c, 3),
            "fit": round(f, 3),
            "legitimacy": round(l, 3),
            "public_facility_bonus": public_bonus,
            "in_district_walk_15_cvap": int(in_district_cvap),
        }

    # Assign rank 1..N (1 = highest)
    ranked = sorted(
        venues["features"],
        key=lambda f: f["properties"]["priority_score"],
        reverse=True,
    )
    for rank, feat in enumerate(ranked, start=1):
        feat["properties"]["priority_rank"] = rank

    venues_path.write_text(json.dumps(venues, indent=2))

    # Console summary
    top10 = ranked[:10]
    print(f"\n=== Top 10 venues for District {d} ===")
    print(f"{'#':>2} {'score':>6} {'tier':>7} {'inD-CVAP':>9} {'fit':>5} {'conf':>5} {'name'}")
    for v in top10:
        p = v["properties"]
        comp = p["priority_components"]
        print(f"{p['priority_rank']:>2} {p['priority_score']:>6.3f} "
              f"{p['priority_tier']:>7} {comp['in_district_walk_15_cvap']:>9,} "
              f"{comp['fit']:>5.2f} {comp['confidence']:>5.2f} {p['name']}")

    tier_counts = {"top": 0, "high": 0, "medium": 0, "low": 0}
    for v in venues["features"]:
        tier_counts[v["properties"]["priority_tier"]] += 1
    print(f"\nTier counts: {tier_counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
