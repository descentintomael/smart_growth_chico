#!/usr/bin/env python3
"""Regenerate council-priorities-3yr.json and public-comment-themes-3yr.json
from the macstudio council-meeting-analyzer DB.

Designed to be executed on macstudio (the host where meetings.db lives) via:
    scp this_file.py macstudio:/tmp/build-council-data.py
    ssh macstudio "python3 /tmp/build-council-data.py --out-dir /tmp/council-out"
    scp macstudio:/tmp/council-out/*.json public/data/_shared/

Writes two JSON files matching the existing schema in public/data/_shared/.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / "Projects/council-meeting-analyzer/data/meetings.db"
DATE_FROM = "2023-01-01"

# Topic taxonomy. Order matters: first matching topic wins for an agenda item.
# Patterns are case-insensitive regexes run against the concatenated
# (title + summary) text.
TOPIC_PATTERNS = [
    # Substantive topics first — ceremonial_admin runs last as a fallback so
    # items that mention substantive policy (e.g. a Presentation on the
    # Active Transportation Plan) don't get swallowed by procedural patterns.
    ("litigation_closed_session", [
        r"\bclosed session\b",
        r"\bconference with legal counsel\b",
        r"\blitigation\b",
        r"\bwarren v\.? chico\b",
        r"\banticipated litigation\b",
    ]),
    ("budget_finance", [
        r"\bbudget\b",
        r"\bappropriation\b",
        r"\bfinancial (report|update|statement)\b",
        r"\bquarterly (financial|finance)\b",
        r"\bmid-?year (budget|review)\b",
        r"\bCAFR\b",
        r"\baudited financial\b",
        r"\bfund balance\b",
        r"\bgeneral fund\b",
        r"\bfiscal year\b",
        r"\bTEFRA\b",
        r"\b(bond|revenue bond) (issuance|approval)\b",
        r"\bdebt service\b",
    ]),
    ("homelessness", [
        r"\bhomeless(ness)?\b",
        r"\bunhoused\b",
        r"\bencampment\b",
        r"\balternate camping site\b",
        r"\bACS\b",
        r"\btiny homes? on church lots\b",
        r"\bpallet shelter\b",
        r"\bnavigation center\b",
        r"\bsafe sleeping\b",
    ]),
    ("sanctuary_immigration", [
        r"\bsanctuary\b",
        r"\bimmigration\b",
        r"\bICE\b(?! cream)",
        r"\bequitable enforcement\b",
        r"\bundocumented\b",
    ]),
    ("housing_supply_zoning", [
        r"\bhousing element\b",
        r"\bzoning (amendment|change|map)\b",
        r"\brezone\b",
        r"\bgeneral plan amendment\b",
        r"\bmissing middle\b",
        r"\bADU\b",
        r"\baccessory dwelling\b",
        r"\baffordable housing\b",
        r"\b(SB|AB) ?(9|10|35|330|423|684|1287)\b",
        r"\bdensity bonus\b",
        r"\bGreenfield Family Apartments\b",
        r"\btentative (tract|parcel) map\b",
        r"\bsubdivision\b",
        r"\bRHNA\b",
    ]),
    ("tenant_protections_code_enforce", [
        r"\btenant protection\b",
        r"\btenant harassment\b",
        r"\bjust cause\b",
        r"\brent (control|stabilization|increase)\b",
        r"\bcode enforcement\b",
        r"\banti-displacement\b",
        r"\beviction\b",
    ]),
    ("downtown_parking_vitality", [
        r"\bdowntown\b",
        r"\bparking (meter|garage|lot|study|permit|forgiveness)\b",
        r"\bpark & go\b",
        r"\bparklet\b",
        r"\bholiday parking\b",
        r"\bDLBT\b",
        r"\bdowntown business\b",
    ]),
    ("parks_bidwell", [
        r"\bbidwell park\b",
        r"\bpark master\b",
        r"\bone[- ]mile recreation\b",
        r"\bcaper acres\b",
        r"\bparks? (plan|management)\b",
        r"\bplayground\b",
        r"\bgreenway\b",
        r"\bpark and recreation\b",
    ]),
    ("active_transportation", [
        r"\bbike (lane|path|plan|share)\b",
        r"\bbicycle\b",
        r"\bpedestrian\b",
        r"\bcrosswalk\b",
        r"\bsidewalk\b",
        r"\bcomplete street\b",
        r"\bactive transportation\b",
        r"\bATP\b",
        r"\btraffic calming\b",
        r"\bsafe routes to school\b",
        r"\bSRTS\b",
        r"\bmulti[- ]use path\b",
    ]),
    ("infrastructure_streets_roads", [
        r"\bpavement\b",
        r"\bstreet (overlay|repair|rehab|reconstruction)\b",
        r"\broad (repair|maintenance|widen)\b",
        r"\bSB ?1\b",
        r"\bRMRA\b",
        r"\bcapital improvement\b",
        r"\bCIP\b",
        r"\btraffic signal\b",
        r"\bsignal(ization)?\b",
        r"\bsignalized intersection\b",
    ]),
    ("infrastructure_sewer_water", [
        r"\bsewer\b",
        r"\bwastewater\b",
        r"\bstorm(water)? (drain|system)\b",
        r"\bBell[- ]Muir\b",
        r"\blift station\b",
        r"\bwater (main|treatment|line|service)\b",
        r"\bgroundwater\b",
    ]),
    ("public_safety_police", [
        r"\bpolice (department|chief|grant|MOU)\b",
        r"\bCPD\b",
        r"\bcrime (rate|reduction|prevention)\b",
        r"\bpublic safety\b(?! committee)",
        r"\bbody[- ]worn camera\b",
        r"\b911\b",
        r"\bdispatch\b",
        r"\bcommunity service officer\b",
    ]),
    ("fire_emergency", [
        r"\bfire department\b",
        r"\bCFD\b",
        r"\bfire (station|chief|hazard|prevention)\b",
        r"\bemergency (operations|management|services)\b",
        r"\bOES\b",
        r"\bwildfire\b",
        r"\bdefensible space\b",
        r"\bWUI\b",
        r"\bevacuation\b",
    ]),
    ("climate_sustainability", [
        r"\bclimate (action|plan|emergency)\b",
        r"\bCAP\b",
        r"\bgreenhouse gas\b",
        r"\bGHG\b",
        r"\bsolar\b",
        r"\belectric vehicle\b",
        r"\bEV charging\b",
        r"\bsustainab\w+\b",
        r"\bdecarbon\w+\b",
        r"\bcarbon (neutral|reduction)\b",
        r"\btree (canopy|protection|ordinance)\b",
        r"\bclean energy\b",
    ]),
    ("cannabis_alcohol_business", [
        r"\bcannabis\b",
        r"\bmarijuana\b",
        r"\bdispensary\b",
        r"\balcohol(ic)? beverage\b",
        r"\bABC license\b",
        r"\bliquor license\b",
        r"\bbusiness license\b",
        r"\btobacco retailer\b",
    ]),
    ("labor_personnel", [
        r"\b(MOU|memorandum of understanding) with\b",
        r"\bbargaining unit\b",
        r"\bcompensation (plan|study)\b",
        r"\bclassification (plan|study)\b",
        r"\bunion\b",
        r"\bemployee (benefit|contract)\b",
        r"\bpersonnel\b",
        r"\bsalary (resolution|schedule)\b",
        r"\bCalPERS\b",
    ]),
    ("elections_governance", [
        r"\belection(s)?\b",
        r"\bredistricting\b",
        r"\bdistrict map\b",
        r"\bcouncil district\b",
        r"\bcharter (amendment|review)\b",
        r"\bballot measure\b",
        r"\bvoter\b",
        r"\bmunicipal code (update|amendment)\b",
        r"\bordinance amend\b",
    ]),
    # Ceremonial / administrative — fallback bucket for procedural items.
    ("ceremonial_admin", [
        r"\bpledge of allegiance\b",
        r"\binvocation\b",
        r"\bmoment of silence\b",
        r"\bproclamation\b",
        r"\bconsent (agenda|calendar)\b",
        r"\bapproval of minutes\b",
        r"\broll call\b",
        r"\bcomment(s)? from council\b",
        r"\bcity manager('s)? report\b",
        r"\badjourn(ment)?\b",
        r"\b(call to order|reports? from boards)\b",
        r"\bappointment(s)?\b",
        r"\bpublic comment(s)?\b",
        r"\bbusiness from the floor\b",
        r"\bpresentation\b\s*[-–]",
        r"\bcouncilmember requests?\b",
        r"\bmayor's? message\b",
        r"\breorganization of council\b",
    ]),
]

# Patterns that signal a public-comment period. We extract key_quotes from
# advocacy_intel only for these items.
PUBLIC_COMMENT_PATTERNS = [
    re.compile(r"\bpublic comment(s)?\b", re.I),
    re.compile(r"\bbusiness from the floor\b", re.I),
    re.compile(r"\bcitizen comments\b", re.I),
]


def is_public_comment(title: str) -> bool:
    return any(p.search(title) for p in PUBLIC_COMMENT_PATTERNS)


def categorize(text: str) -> str | None:
    """Return the first matching topic, or None if nothing matches.

    Used for single-topic categorization (quotes, where we want one bucket).
    """
    if not text:
        return None
    for topic, patterns in TOPIC_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return topic
    return None


def categorize_all(text: str) -> list[str]:
    """Return every topic that matches.

    Used for items, where a single agenda item often spans multiple topics
    (e.g. a consent-agenda item covering both a pedestrian ordinance and
    a parking enforcement device).
    """
    if not text:
        return []
    matches: list[str] = []
    for topic, patterns in TOPIC_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(topic)
                break
    return matches


def extract_summary_text(summary_obj) -> str:
    """Flatten the summary JSON (which may be a list of bullets, a string, or
    a dict containing either) into a single searchable string."""
    if summary_obj is None:
        return ""
    if isinstance(summary_obj, str):
        return summary_obj
    if isinstance(summary_obj, list):
        return " ".join(extract_summary_text(item) for item in summary_obj)
    if isinstance(summary_obj, dict):
        parts: list[str] = []
        for key in ("summary", "topic", "description", "raw_response", "bullets"):
            if key in summary_obj:
                parts.append(extract_summary_text(summary_obj[key]))
        return " ".join(p for p in parts if p)
    return ""


def safe_json_loads(raw):
    """Parse JSON, returning None on failure."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def build(db_path: Path, out_dir: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # All City Council + Special Meeting items since DATE_FROM (Planning
    # Commission excluded — it's a different body with different jurisdiction).
    rows = conn.execute(
        """
        SELECT
            m.meeting_date,
            m.meeting_type,
            ai.id            AS agenda_item_id,
            ai.item_number,
            ai.title,
            a_sum.result     AS summary_json,
            a_adv.result     AS advocacy_json
        FROM agenda_items ai
        JOIN meetings m ON m.clip_id = ai.clip_id
        LEFT JOIN analysis a_sum
               ON a_sum.agenda_item_id = ai.id
              AND a_sum.analysis_type = 'summary'
        LEFT JOIN analysis a_adv
               ON a_adv.agenda_item_id = ai.id
              AND a_adv.analysis_type = 'advocacy_intel'
        WHERE m.meeting_date IS NOT NULL
          AND m.meeting_date >= ?
          AND m.meeting_type IN ('City Council', 'Special Meeting')
          AND m.status = 'analyzed'
        ORDER BY m.meeting_date, ai.item_number
        """,
        (DATE_FROM,),
    ).fetchall()

    print(f"Loaded {len(rows)} agenda items from {DATE_FROM} onward", file=sys.stderr)

    topic_totals: dict[str, int] = defaultdict(int)
    topic_by_year: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    examples: dict[str, list[dict]] = defaultdict(list)

    quotes_per_topic: dict[str, list[dict]] = defaultdict(list)

    max_date = DATE_FROM

    for row in rows:
        meeting_date = row["meeting_date"]
        if meeting_date > max_date:
            max_date = meeting_date
        year = meeting_date[:4]
        title = row["title"] or ""

        summary_text = extract_summary_text(safe_json_loads(row["summary_json"]))
        text_for_topic = (title + " " + summary_text).strip()

        # Multi-topic match: an item that discusses both housing and parking
        # legitimately counts for both. Matches the prior script's behavior
        # where topic_totals summed higher than total items.
        topics = categorize_all(text_for_topic)
        for topic in topics:
            topic_totals[topic] += 1
            topic_by_year[topic][year] += 1
            if len(examples[topic]) < 12:
                examples[topic].append({
                    "date": meeting_date,
                    "item": row["item_number"],
                    "title": (title[:120] + "…") if len(title) > 120 else title,
                })

        # Extract public-comment quotes independent of item categorization —
        # public-comment headers themselves are procedural, but the quotes
        # within them carry the topic signal we want.
        if is_public_comment(title):
            advocacy = safe_json_loads(row["advocacy_json"]) or {}
            key_quotes = advocacy.get("key_quotes") if isinstance(advocacy, dict) else None
            if isinstance(key_quotes, list):
                for quote in key_quotes:
                    if not isinstance(quote, str) or len(quote) < 20:
                        continue
                    # Categorize the quote itself, not the (procedural) item.
                    quote_topic = categorize(quote)
                    if quote_topic is None:
                        continue
                    quotes_per_topic[quote_topic].append({
                        "date": meeting_date,
                        "quote": quote.strip(),
                    })

    # Cap quotes per topic to keep file size reasonable, prefer most recent.
    for topic in quotes_per_topic:
        quotes_per_topic[topic].sort(key=lambda q: q["date"], reverse=True)
        quotes_per_topic[topic] = quotes_per_topic[topic][:25]

    generated = datetime.now(timezone.utc).isoformat()

    priorities = {
        "date_range": {"from": DATE_FROM, "to_inclusive": max_date},
        "source": "Chico City Council meeting transcripts + LLM-extracted advocacy_intel",
        "source_db": str(db_path),
        "generated": generated,
        "total_agenda_items": len(rows),
        "topic_totals_3yr": dict(sorted(topic_totals.items(), key=lambda kv: -kv[1])),
        "topic_counts_by_year": {
            t: dict(sorted(years.items())) for t, years in topic_by_year.items()
        },
        "examples_per_topic": dict(examples),
    }

    comment_themes = {
        "date_range": {"from": DATE_FROM, "to_inclusive": max_date},
        "source": "Chico City Council public-comment periods (transcripts + LLM advocacy_intel extraction)",
        "source_db": str(db_path),
        "generated": generated,
        "quote_count_per_topic": dict(
            sorted({t: len(qs) for t, qs in quotes_per_topic.items()}.items(),
                   key=lambda kv: -kv[1])
        ),
        "quotes_per_topic": dict(quotes_per_topic),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "council-priorities-3yr.json").write_text(
        json.dumps(priorities, indent=2)
    )
    (out_dir / "public-comment-themes-3yr.json").write_text(
        json.dumps(comment_themes, indent=2)
    )

    print(
        f"Wrote council-priorities-3yr.json "
        f"({sum(topic_totals.values())} categorized items)",
        file=sys.stderr,
    )
    print(
        f"Wrote public-comment-themes-3yr.json "
        f"({sum(len(qs) for qs in quotes_per_topic.values())} quotes)",
        file=sys.stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    build(args.db, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
