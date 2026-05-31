#!/usr/bin/env python3
"""Apply hand-curated, web-research-derived hosting assessments to venues.geojson.

This script merges assessment records (hosting_status + notes) into the venues
file by name match. Idempotent — re-running with the same assessments yields
the same output. Assessments are kept in this file so they're versioned and
auditable; new ones can be added as research progresses.

Usage:
    python3 scripts/apply-venue-assessments.py 6
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Each entry maps a venue name (exact match against OSM `name`) to an assessment.
# `status` is the hosting_status enum value. `notes` is human-readable evidence.
# `confidence` is a free-form indicator of how settled the assessment is.
ASSESSMENTS: dict[int, dict[str, dict]] = {
    6: {
        # === In-district ===
        "Canyon Oaks Country Club": {
            "status": "confirmed",
            "notes": "Private country club; access available through resident contact. "
                     "Hosts weddings and customizable events per club website. "
                     "Book via clubhouse: canyonoakscc.com.",
            "confidence": "high",
        },
        "Lakeside Pavilion": {
            "status": "confirmed",
            "notes": "Operated by Chico Area Recreation & Park District (CARD). "
                     "6,000 sq ft, capacity 275. Caterer's kitchen, PA system, "
                     "wood dance floor, lake views. Suitable for business meetings "
                     "through weddings. Book: (530) 895-4711, rentals@chicorec.gov.",
            "confidence": "high",
        },
        "Bidwell Park Golf Course": {
            "status": "likely",
            "notes": "Has clubhouse with Bidwell Bar & Grill and active "
                     "events/tournaments program. Confirm capacity and rates: "
                     "(530) 891-8417.",
            "confidence": "medium",
        },
        "Hotel Káterina": {
            "status": "likely",
            "notes": "3,900 sq ft of event space confirmed on website. Part of the "
                     "Oxford Collection regional chain (CA/ID/OR/WA). Confirm political-"
                     "event policy and capacity layouts: (530) 571-9060.",
            "confidence": "medium",
        },
        "Butte College Skyway Center": {
            "status": "needs_verification",
            "notes": "Workforce development / training center (automotive tech, Small "
                     "Business Dev Center, Health Workforce Initiative). Public rental "
                     "policy not stated on facility page. Contact Butte College "
                     "Conference Services or main line (530) 895-2511.",
            "confidence": "low",
        },
        "Butte College": {
            "status": "needs_verification",
            "notes": "Public community college with multiple rentable rooms (auditoria, "
                     "meeting rooms). Route through Butte College Conference Services.",
            "confidence": "low",
        },
        "Chico Rod & Gun Club": {
            "status": "needs_verification",
            "notes": "Membership-driven shooting facility (1456 Upper Park Rd). Active "
                     "internal social calendar but no clear external rental policy on "
                     "website. Worth a call: (530) 715-0145, chicogunclub@gmail.com.",
            "confidence": "medium",
        },
        "Hula's Chinese Bar-B-Q": {
            "status": "needs_verification",
            "notes": "Independent, owner-operated by Jeff & Leasa Hill. No event "
                     "info on website. Direct inquiry: (530) 715-7614.",
            "confidence": "low",
        },
        "Cocodine Thai Cuisine": {
            "status": "needs_verification",
            "notes": "Independent local restaurant. No event-rental info on website.",
            "confidence": "low",
        },
        "Tbar": {
            "status": "likely",
            "notes": "Tea Bar & Fusion Cafe — small regional chain (4 locations, "
                     "2 in Chico). EXPLICITLY event-friendly: monthly Tea Talks, "
                     "Tuesday Family Night, Wednesday Trivia, Thursday Take Over "
                     "Night (fundraising). Confirm WHICH Chico location is this "
                     "OSM point (Vallombrosa downtown is in D5; second location may "
                     "be in D6).",
            "confidence": "medium",
        },
        "J&J Cafe": {
            "status": "needs_verification",
            "notes": "Small independent cafe. No website found to assess.",
            "confidence": "low",
        },
        "Sake": {
            "status": "needs_verification",
            "notes": "Local restaurant. No website found in OSM to assess.",
            "confidence": "low",
        },

        # === Adjacency zone (walking-catchment may reach D6) ===
        "Arc Pavilion": {
            "status": "confirmed",
            "notes": "3,600 sq ft; seats 160 at tables / 240 lecture-style. "
                     "Restaurant-style kitchen, business-class internet. Available "
                     "weekday eves (not Tues) and Sat/Sun. Operated by The Arc of "
                     "Butte County (501c3); pavilion rentals are a fundraising "
                     "vehicle and accept commercial bookings. ~$850 + deposit. "
                     "Book: (530) 891-5865.",
            "confidence": "high",
        },
        "Creekside Rose Garden": {
            "status": "confirmed",
            "notes": "CARD-operated. Indoor reception (cap ~200) + outdoor terrace "
                     "with 200+ roses. Caterer's kitchen, PA, tables/chairs included. "
                     "Adjacent to Bidwell Park. Book: (530) 895-4711, "
                     "rentals@chicorec.gov.",
            "confidence": "high",
        },
        "Dorothy F. Johnson Center": {
            "status": "confirmed",
            "notes": "CARD-operated, in Chapman Neighborhood (775 E 16th St). "
                     "6,375 sq ft: gym, meeting rooms, kitchen, toddler classrooms. "
                     "'Business meetings, trainings, classes, weddings, memorials.' "
                     "Book: (530) 895-4711.",
            "confidence": "high",
        },
        "CARD Community Center": {
            "status": "confirmed",
            "notes": "Same operator and booking line as Creekside Rose Garden — they "
                     "share a campus. CARD facility, rentable for civic events. "
                     "Book: (530) 895-4711, rentals@chicorec.gov.",
            "confidence": "high",
        },
        "The Commons Social Empourium": {
            "status": "confirmed",
            "notes": "Taproom + outdoor music venue (2412 Park Ave). 28 rotating "
                     "taps, on-site pizzeria. Offers private party rentals via "
                     "thecommonschico.com/private-parties. Worth a direct inquiry: "
                     "(530) 774-2999.",
            "confidence": "high",
        },
        "Sierra Nevada Brewing Company Taproom": {
            "status": "likely",
            "notes": "Iconic Chico venue with multiple event spaces (taproom, "
                     "biergarten, banquet hall). Hosts public and private events "
                     "regularly. Confirm political-event policy and meeting-room "
                     "rental rates direct: sierranevada.com (contact via Visit page).",
            "confidence": "medium",
        },
        "Chico's Elks Lodge 423": {
            "status": "needs_verification",
            "notes": "Fraternal order (BPOE). Local lodges typically rent their hall "
                     "to members and the broader community for events. Confirm rental "
                     "policy and any political-event restrictions direct.",
            "confidence": "medium",
        },
        "Park Avenue Pub": {
            "status": "needs_verification",
            "notes": "Local pub. Check directly for private-event hosting.",
            "confidence": "low",
        },
        "Mulberry Station": {
            "status": "needs_verification",
            "notes": "Local restaurant. Check directly for private-room availability.",
            "confidence": "low",
        },
    },
}


def apply(district: int) -> int:
    data_dir = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}"
    venues_path = data_dir / "venues.geojson"
    if not venues_path.exists():
        print(f"venues.geojson not found at {venues_path}", file=sys.stderr)
        return 1

    venues = json.loads(venues_path.read_text())
    assessments = ASSESSMENTS.get(district, {})

    updated = 0
    matched_names = set()
    for feature in venues["features"]:
        props = feature["properties"]
        name = props.get("name")
        if name in assessments:
            assessment = assessments[name]
            props["hosting_status"] = assessment["status"]
            props["notes"] = assessment["notes"]
            props["assessment_confidence"] = assessment.get("confidence", "unknown")
            matched_names.add(name)
            updated += 1

    venues_path.write_text(json.dumps(venues, indent=2))

    unmatched = set(assessments) - matched_names
    print(f"Applied {updated} assessments to {venues_path}")
    if unmatched:
        print(f"  ⚠ {len(unmatched)} assessments had no matching venue (name may have changed):")
        for name in sorted(unmatched):
            print(f"     - {name!r}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number")
    args = parser.parse_args()
    return apply(args.district)


if __name__ == "__main__":
    sys.exit(main())
