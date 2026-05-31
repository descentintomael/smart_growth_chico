#!/usr/bin/env python3
"""Enrich venues.geojson with Google Places API (New) attributes.

SAFETY ARCHITECTURE
-------------------
The Google Places API key is sensitive — runaway scripts can rack up real
charges. This script is designed to make abuse difficult by construction:

  1. HARD_MAX_REQUESTS_PER_RUN  — the script refuses to make more requests
     than this in a single invocation, regardless of CLI flags.
  2. ESTIMATED_COST_CAP_USD     — pre-flight cost estimate must fit under
     this, or the script aborts before making any calls.
  3. CONFIRM_THRESHOLD_USD      — if the estimated cost exceeds this, the
     user must pass --confirm explicitly.
  4. Per-place response caching to .cache/google-places/ so re-runs do not
     re-pay for the same data.
  5. --dry-run flag estimates cost and plans calls without making any API
     requests.
  6. RequestBudget tracker enforces caps in real time as calls are made.
  7. Run log written to .cache/google-places/run-{timestamp}.log.
  8. The API key is never printed, logged, or written to any tracked file.
  9. Reads from .env (gitignored) — never accepts the key on the CLI.

Usage:
    python3 scripts/enrich-venues-google-places.py 6 --dry-run
    python3 scripts/enrich-venues-google-places.py 6                # OK if est < $0.50
    python3 scripts/enrich-venues-google-places.py 6 --confirm      # OK at any cap
    python3 scripts/enrich-venues-google-places.py 6 --limit 5      # First 5 only
"""

import argparse
import json
import os
import sys
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- Hard safety caps. Do not raise without a deliberate reason. -----------
# Why these numbers:
#   - 200 requests caps a runaway loop at ~2× the size of a full D6 enrichment.
#   - $5 caps a worst-case (no-free-tier, Enterprise+ pricing) run at well under
#     any meaningful loss. The Google 10k/SKU/month free tier means actual cost
#     for normal use will be $0; the cap exists to bound a runaway bug.
#   - $0.50 --confirm threshold matches "more than a casual test"; a single
#     re-run of a cached dataset is $0 and runs without --confirm.
HARD_MAX_REQUESTS_PER_RUN = 200
ESTIMATED_COST_CAP_USD = 5.00
CONFIRM_THRESHOLD_USD = 0.50

# ---- Conservative cost estimates (upper bounds; actual will usually be free
# under the 10k/month free tier). Keep these high to guard against pricing
# changes. ------------------------------------------------------------------
COST_TEXT_SEARCH_USD = 0.035   # Text Search (Pro SKU + location bias)
COST_PLACE_DETAILS_USD = 0.040  # Place Details w/ Enterprise fields (editorial summary)
COST_PER_VENUE_MAX = COST_TEXT_SEARCH_USD + COST_PLACE_DETAILS_USD

# ---- Field masks (deliberately scoped — fewer fields = lower SKU = less $) -
TEXT_SEARCH_FIELDS = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.primaryType",
])
PLACE_DETAILS_FIELDS = ",".join([
    "id",
    "displayName",
    "formattedAddress",
    "location",
    "types",
    "primaryType",
    "businessStatus",
    "nationalPhoneNumber",
    "websiteUri",
    "regularOpeningHours",
    "rating",
    "userRatingCount",
    "editorialSummary",
])

CACHE_DIR = PROJECT_ROOT / ".cache" / "google-places"


def load_env(path: Path) -> dict[str, str]:
    """Minimal .env parser — avoid depending on python-dotenv."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def cache_path_for(query: str) -> Path:
    """Stable, content-addressed cache file path for a query string."""
    h = sha256(query.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


class RequestBudget:
    """Enforces hard caps in real time. Raises BudgetExceeded to abort."""

    def __init__(self, max_requests: int, max_cost_usd: float):
        self.max_requests = max_requests
        self.max_cost_usd = max_cost_usd
        self.requests_made = 0
        self.cost_accrued = 0.0

    def reserve(self, est_cost: float) -> None:
        if self.requests_made + 1 > self.max_requests:
            raise BudgetExceeded(
                f"Would exceed HARD_MAX_REQUESTS_PER_RUN={self.max_requests}"
            )
        if self.cost_accrued + est_cost > self.max_cost_usd:
            raise BudgetExceeded(
                f"Would exceed ESTIMATED_COST_CAP_USD=${self.max_cost_usd:.2f}"
            )

    def commit(self, cost: float) -> None:
        self.requests_made += 1
        self.cost_accrued += cost


class BudgetExceeded(RuntimeError):
    pass


def text_search(
    name: str,
    lat: float,
    lon: float,
    api_key: str,
    budget: RequestBudget,
    log,
) -> dict[str, Any]:
    """Find a place by name near (lat, lon). Caches results."""
    query = f"{name} Chico CA"
    cache = cache_path_for(f"textsearch::{query}::{lat:.5f}::{lon:.5f}")
    if cache.exists():
        log("cache_hit", "text_search", query)
        return json.loads(cache.read_text())

    budget.reserve(COST_TEXT_SEARCH_USD)
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": TEXT_SEARCH_FIELDS,
    }
    body = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": 500.0,
            }
        },
        "maxResultCount": 1,
    }
    log("api_call", "text_search", query)
    response = requests.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    data = response.json()
    budget.commit(COST_TEXT_SEARCH_USD)
    cache.write_text(json.dumps(data, indent=2))
    return data


def place_details(
    place_id: str, api_key: str, budget: RequestBudget, log
) -> dict[str, Any]:
    """Fetch full place details by Google place_id. Caches results."""
    cache = cache_path_for(f"details::{place_id}")
    if cache.exists():
        log("cache_hit", "place_details", place_id)
        return json.loads(cache.read_text())

    budget.reserve(COST_PLACE_DETAILS_USD)
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": PLACE_DETAILS_FIELDS,
    }
    log("api_call", "place_details", place_id)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    budget.commit(COST_PLACE_DETAILS_USD)
    cache.write_text(json.dumps(data, indent=2))
    return data


def estimate_plan(venues: list[dict]) -> dict[str, Any]:
    """Pre-flight: count how many calls are uncached and compute upper-bound cost."""
    new_text_searches = 0
    for v in venues:
        name = v["properties"]["name"]
        lon, lat = v["geometry"]["coordinates"]
        ts_cache = cache_path_for(
            f"textsearch::{name} Chico CA::{lat:.5f}::{lon:.5f}"
        )
        if not ts_cache.exists():
            new_text_searches += 1
    # Conservative: assume each new text search will trigger a Place Details call.
    new_details_max = new_text_searches
    total_requests_max = new_text_searches + new_details_max
    estimated_cost = (
        new_text_searches * COST_TEXT_SEARCH_USD
        + new_details_max * COST_PLACE_DETAILS_USD
    )
    return {
        "total_venues": len(venues),
        "cached_text_searches": len(venues) - new_text_searches,
        "new_text_searches": new_text_searches,
        "new_place_details_max": new_details_max,
        "total_requests_max": total_requests_max,
        "estimated_cost_usd": round(estimated_cost, 4),
    }


def merge_google_into_venue(venue_props: dict, details: dict[str, Any]) -> None:
    """Merge selected Google fields into venue properties — preserve OSM keys."""
    venue_props["google_place_id"] = details.get("id")
    venue_props["google_types"] = details.get("types", [])
    venue_props["google_primary_type"] = details.get("primaryType")
    venue_props["google_business_status"] = details.get("businessStatus")
    venue_props["google_rating"] = details.get("rating")
    venue_props["google_user_ratings_count"] = details.get("userRatingCount")
    es = details.get("editorialSummary")
    venue_props["google_editorial_summary"] = es.get("text") if es else None
    venue_props["google_formatted_address"] = details.get("formattedAddress")
    # Fill OSM gaps without overwriting existing OSM data
    if not venue_props.get("website"):
        venue_props["website"] = details.get("websiteUri")
    if not venue_props.get("phone"):
        venue_props["phone"] = details.get("nationalPhoneNumber")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the cost estimate and exit without making any API calls.",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help=f"Required when estimated cost > ${CONFIRM_THRESHOLD_USD:.2f}.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Process at most N venues from the list (useful for testing).",
    )
    args = parser.parse_args()

    # Load API key from .env — never accept on CLI, never echo.
    env = load_env(PROJECT_ROOT / ".env")
    api_key = env.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print(
            "GOOGLE_PLACES_API_KEY not found in .env or environment. Aborting.",
            file=sys.stderr,
        )
        return 2

    venues_path = (
        PROJECT_ROOT
        / "public"
        / "data"
        / f"candidate-district-{args.district}"
        / "venues.geojson"
    )
    venues_data = json.loads(venues_path.read_text())
    venues = venues_data["features"]
    if args.limit is not None:
        venues = venues[: args.limit]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    plan = estimate_plan(venues)

    print(f"Pre-flight plan for District {args.district}:")
    print(f"  Total venues to process:     {plan['total_venues']}")
    print(f"  Cached text searches:        {plan['cached_text_searches']}")
    print(f"  New text-search requests:    {plan['new_text_searches']}")
    print(f"  Max place-details requests:  {plan['new_place_details_max']}")
    print(f"  Max total requests:          {plan['total_requests_max']}")
    print(f"  Hard request cap:            {HARD_MAX_REQUESTS_PER_RUN}")
    print(f"  Estimated cost (upper):      ${plan['estimated_cost_usd']:.4f}")
    print(f"  Hard cost cap:               ${ESTIMATED_COST_CAP_USD:.2f}")
    print(f"  --confirm threshold:         ${CONFIRM_THRESHOLD_USD:.2f}")

    if plan["total_requests_max"] > HARD_MAX_REQUESTS_PER_RUN:
        print(
            f"\nABORT: plan exceeds HARD_MAX_REQUESTS_PER_RUN={HARD_MAX_REQUESTS_PER_RUN}. "
            f"Use --limit to process a subset.",
            file=sys.stderr,
        )
        return 1
    if plan["estimated_cost_usd"] > ESTIMATED_COST_CAP_USD:
        print(
            f"\nABORT: plan exceeds ESTIMATED_COST_CAP_USD=${ESTIMATED_COST_CAP_USD:.2f}.",
            file=sys.stderr,
        )
        return 1
    if args.dry_run:
        print("\nDry run — no API calls made.")
        return 0
    if plan["estimated_cost_usd"] > CONFIRM_THRESHOLD_USD and not args.confirm:
        print(
            f"\nREFUSING: estimated cost ${plan['estimated_cost_usd']:.4f} > "
            f"--confirm threshold ${CONFIRM_THRESHOLD_USD:.2f}.\n"
            "Re-run with --confirm to proceed.",
            file=sys.stderr,
        )
        return 1

    log_path = CACHE_DIR / f"run-{int(time.time())}.log"

    def log(kind: str, op: str, item: str) -> None:
        with log_path.open("a") as f:
            f.write(f"{int(time.time())}\t{kind}\t{op}\t{item}\n")

    budget = RequestBudget(HARD_MAX_REQUESTS_PER_RUN, ESTIMATED_COST_CAP_USD)
    enriched = 0
    no_match = 0
    errored = 0

    try:
        for venue in venues:
            name = venue["properties"]["name"]
            lon, lat = venue["geometry"]["coordinates"]
            try:
                ts = text_search(name, lat, lon, api_key, budget, log)
            except BudgetExceeded as e:
                print(f"\nStopping: {e}", file=sys.stderr)
                break
            except requests.HTTPError as e:
                log("error", "text_search", f"{name}: {e}")
                errored += 1
                continue

            places = ts.get("places") or []
            if not places:
                venue["properties"]["google_match"] = None
                no_match += 1
                continue
            place_id = places[0].get("id")
            if not place_id:
                no_match += 1
                continue
            try:
                details = place_details(place_id, api_key, budget, log)
            except BudgetExceeded as e:
                print(f"\nStopping: {e}", file=sys.stderr)
                break
            except requests.HTTPError as e:
                log("error", "place_details", f"{place_id}: {e}")
                errored += 1
                continue

            merge_google_into_venue(venue["properties"], details)
            enriched += 1
    finally:
        # Write whatever we got, even if we aborted mid-loop
        venues_data["features"][: len(venues)] = venues
        venues_path.write_text(json.dumps(venues_data, indent=2))
        print(
            f"\nDone. Enriched {enriched} venue(s); "
            f"{no_match} had no Google match; "
            f"{errored} HTTP errors. "
            f"Requests made: {budget.requests_made}, "
            f"accrued cost ≤ ${budget.cost_accrued:.4f}."
        )
        print(f"Log: {log_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
