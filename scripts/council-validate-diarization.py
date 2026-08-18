#!/usr/bin/env python3
"""Score speaker diarization and attribution against ground truth in the audio.

Attributing a quote to the wrong councilmember is the most damaging error this
corpus can make, so the naming step needs evidence, not trust. Every Chico
council meeting opens with a roll call — the clerk reads each member's name and
that member answers "Here." That gives us, for free and with no hand-labelling,
a set of labelled voice anchors per meeting plus one for the clerk.

Four checks, in decreasing strength:

  clerk misattribution  When the clerk reads "Council Member Goldstein?", the
                        speaker is the CLERK. Labelling that segment "Goldstein"
                        means the identifier is reading names out of the text
                        instead of recognising the voice — the single most
                        diagnostic failure, and it is silent without this test.
  response absorption   The one-word answer should be a different cluster from
                        the clerk reading the name. Same cluster means short
                        utterances are being swallowed by the dominant speaker.
  anchor consistency    The cluster that answered for Goldstein should be named
                        Goldstein everywhere else in the meeting.
  roster validity       Every assigned name must be someone the roll call
                        actually named, or recognised staff. Catches invented
                        people.

Plus structural sanity: implausible speaker counts, one cluster dominating the
meeting, and how much of the meeting got a name at all.

READ-ONLY. This script never writes to the corpus or the database.

Designed to be SCP'd to macstudio and run there:

    scp scripts/council-validate-diarization.py macstudio:/tmp/
    ssh macstudio "python3 /tmp/council-validate-diarization.py"
    ssh macstudio "python3 /tmp/council-validate-diarization.py --clip-id 1321 --samples 10"
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~/Projects/council-meeting-analyzer/data"))
CLIP_URL = "https://chico-ca.granicus.com/player/clip/{clip_id}?starttime={start:.0f}"

# The clerk reading the roll: a title, a surname, and nothing else.
ROLL_CALL_READ = re.compile(
    r"^\W*(?:Council\s?Member|Councilmember|Councilor|Vice\s+Mayor|Mayor)\s+"
    r"(?P<name>(?:van\s+|Van\s+)?[A-Z][\w'’-]+)\s*\?\W*$"
)
# The member answering.
AFFIRMATIVE = re.compile(r"^\W*(here|present|yes|aye|yep|yeah)\W*$", re.I)

# Names that are legitimately not councilmembers.
STAFF_PATTERN = re.compile(
    r"city\s+(clerk|manager|attorney|engineer)|deputy|director|chief|staff"
    r"|unknown|speaker|public|unidentified",
    re.I,
)

# A council meeting has a handful of members plus staff and public commenters.
# Outside this band something structural is wrong — the broken run produced 3996.
PLAUSIBLE_SPEAKERS = (3, 120)
# One cluster holding more than this share of segments means under-clustering.
DOMINANCE_LIMIT = 0.60


def as_float(value) -> float:
    """Segment timings are sometimes stored as strings."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_diarization(clip_id: int) -> dict | None:
    """Load a diarization file, or None when the meeting has none."""
    path = DATA_DIR / "transcripts" / f"{clip_id}_diarization.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def surname(name: str | None) -> str:
    """Last word of a name, lowercased, for tolerant comparison."""
    if not name:
        return ""
    cleaned = re.sub(r"[^\w\s'’-]", " ", str(name)).strip()
    return cleaned.split()[-1].lower() if cleaned else ""


def find_roll_call(segments: list[dict]) -> list[dict]:
    """Pair each 'Council Member X?' with the answer that follows it.

    Returns one record per name read, carrying the reading segment, the
    answering segment when there is one, and the surname being called.
    """
    anchors = []
    for index, segment in enumerate(segments):
        text = str(segment.get("text") or "").strip()
        match = ROLL_CALL_READ.match(text)
        if not match:
            continue

        answer = None
        # The answer is normally the next segment; allow a small gap for a
        # stray artefact between the two.
        for candidate in segments[index + 1:index + 3]:
            if AFFIRMATIVE.match(str(candidate.get("text") or "").strip()):
                answer = candidate
                break

        anchors.append({
            "called": surname(match.group("name")),
            "read_segment": segment,
            "answer_segment": answer,
        })
    return anchors


def check_clerk_misattribution(anchors: list[dict]) -> dict:
    """Is the roll-reading segment labelled with the name it reads?"""
    checked = wrong = 0
    examples = []
    for anchor in anchors:
        assigned = surname(anchor["read_segment"].get("speaker_name"))
        if not assigned:
            continue
        checked += 1
        if assigned == anchor["called"]:
            wrong += 1
            if len(examples) < 3:
                examples.append({
                    "start": as_float(anchor["read_segment"].get("start")),
                    "text": str(anchor["read_segment"].get("text") or "").strip()[:60],
                    "assigned": anchor["read_segment"].get("speaker_name"),
                })
    return {"checked": checked, "failures": wrong, "examples": examples}


def check_response_absorption(anchors: list[dict]) -> dict:
    """Does the one-word answer share a cluster with the clerk reading it?"""
    checked = absorbed = 0
    for anchor in anchors:
        answer = anchor["answer_segment"]
        if not answer:
            continue
        checked += 1
        if answer.get("speaker_id") == anchor["read_segment"].get("speaker_id"):
            absorbed += 1
    return {"checked": checked, "failures": absorbed}


def check_anchor_consistency(anchors: list[dict], segments: list[dict]) -> dict:
    """Is the cluster that answered for X named X elsewhere in the meeting?"""
    by_cluster: dict[str, Counter] = {}
    for segment in segments:
        cluster = segment.get("speaker_id")
        if cluster is None:
            continue
        by_cluster.setdefault(str(cluster), Counter())[surname(segment.get("speaker_name"))] += 1

    checked = agree = 0
    disagreements = []
    for anchor in anchors:
        answer = anchor["answer_segment"]
        if not answer or answer.get("speaker_id") is None:
            continue
        # An answering cluster that also read the roll tells us nothing about
        # the member's voice — absorption already counts that failure.
        if answer.get("speaker_id") == anchor["read_segment"].get("speaker_id"):
            continue

        names = by_cluster.get(str(answer["speaker_id"]), Counter())
        named = [n for n in names if n and n not in ("", "-")]
        if not named:
            continue
        checked += 1
        dominant = max(named, key=lambda n: names[n])
        if dominant == anchor["called"]:
            agree += 1
        elif len(disagreements) < 3:
            disagreements.append({
                "expected": anchor["called"],
                "cluster_says": dominant,
                "cluster": answer.get("speaker_id"),
            })
    return {"checked": checked, "agree": agree, "disagreements": disagreements}


def check_roster(anchors: list[dict], segments: list[dict]) -> dict:
    """Flag assigned names that the roll call never mentioned and aren't staff."""
    roster = {a["called"] for a in anchors if a["called"]}
    if not roster:
        return {"roster": [], "unknown_names": {}, "checked": 0}

    unknown: Counter = Counter()
    checked = 0
    for segment in segments:
        raw = segment.get("speaker_name")
        if not raw:
            continue
        checked += 1
        if STAFF_PATTERN.search(str(raw)):
            continue
        if surname(raw) not in roster:
            unknown[str(raw)] += 1
    return {
        "roster": sorted(roster),
        "unknown_names": dict(unknown.most_common(5)),
        "checked": checked,
    }


def check_structure(payload: dict, segments: list[dict]) -> dict:
    """Speaker count, cluster dominance, and how much got a name."""
    clusters = Counter(str(s.get("speaker_id")) for s in segments if s.get("speaker_id"))
    total = sum(clusters.values()) or 1
    # "Unknown (frequent)" is a placeholder, not an identification. Counting it
    # as named reports 100% attribution on meetings where nobody was named.
    named = sum(1 for s in segments
                if s.get("speaker_name")
                and not re.match(r"\s*unknown", str(s["speaker_name"]), re.I))
    dominant_share = max(clusters.values()) / total if clusters else 0.0
    count = payload.get("total_speakers") or len(clusters)
    return {
        "segments": len(segments),
        "speaker_count": count,
        "count_plausible": PLAUSIBLE_SPEAKERS[0] <= count <= PLAUSIBLE_SPEAKERS[1],
        "dominant_cluster_share": round(dominant_share, 3),
        "dominance_ok": dominant_share <= DOMINANCE_LIMIT,
        "named_share": round(named / len(segments), 3) if segments else 0.0,
        "singleton_clusters": sum(1 for c in clusters.values() if c == 1),
    }


def validate_meeting(clip_id: int) -> dict | None:
    """Produce a scorecard for one meeting."""
    payload = load_diarization(clip_id)
    if not payload:
        return None
    segments = payload.get("segments") or []
    if not segments:
        return None

    anchors = find_roll_call(segments)
    return {
        "clip_id": clip_id,
        "roll_call_anchors": len(anchors),
        "clerk_misattribution": check_clerk_misattribution(anchors),
        "response_absorption": check_response_absorption(anchors),
        "anchor_consistency": check_anchor_consistency(anchors, segments),
        "roster": check_roster(anchors, segments),
        "structure": check_structure(payload, segments),
    }


def verdict(card: dict) -> str:
    """One-word judgement, worst signal wins."""
    structure = card["structure"]
    if not structure["count_plausible"] or not structure["dominance_ok"]:
        return "BROKEN"
    if card["clerk_misattribution"]["failures"]:
        return "NAMES-WRONG"
    if card["roll_call_anchors"] == 0:
        return "NO-ANCHORS"
    consistency = card["anchor_consistency"]
    if consistency["checked"] and consistency["agree"] / consistency["checked"] < 0.5:
        return "NAMES-WEAK"
    if card["response_absorption"]["checked"]:
        absorbed = card["response_absorption"]["failures"] / card["response_absorption"]["checked"]
        if absorbed > 0.5:
            return "CLUSTERS-MERGED"
    return "OK"


def print_samples(clip_id: int, count: int) -> None:
    """Emit attributed quotes with clickable timestamps for human spot-check."""
    payload = load_diarization(clip_id)
    if not payload:
        return
    segments = [s for s in payload.get("segments") or []
                if s.get("speaker_name") and len(str(s.get("text") or "").strip()) > 40]
    if not segments:
        print("  (no named segments long enough to sample)")
        return

    step = max(1, len(segments) // count)
    print(f"\n  Spot-check for {clip_id} — click, listen, confirm the voice:")
    for segment in segments[::step][:count]:
        start = as_float(segment.get("start"))
        print(f"    {segment.get('speaker_name')}")
        print(f"      \"{str(segment.get('text') or '').strip()[:88]}\"")
        print(f"      {CLIP_URL.format(clip_id=clip_id, start=start)}")


def discover_clips() -> list[int]:
    """Every clip with a diarization file."""
    clips = []
    for path in (DATA_DIR / "transcripts").glob("*_diarization.json"):
        try:
            clips.append(int(path.name.split("_")[0]))
        except ValueError:
            continue
    return sorted(clips)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip-id", type=int, default=None, help="Score one meeting.")
    parser.add_argument("--samples", type=int, default=0,
                        help="Also print N attributed quotes with timestamp links.")
    parser.add_argument("--json-out", type=Path, default=None,
                        help="Write the full scorecards as JSON.")
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    clips = [args.clip_id] if args.clip_id else discover_clips()

    cards = []
    for clip_id in clips:
        card = validate_meeting(clip_id)
        if card:
            card["verdict"] = verdict(card)
            cards.append(card)

    if not cards:
        print("No diarization files to score.")
        return 0

    header = (f"{'clip':>6}  {'verdict':<16} {'spk':>4} {'domin':>6} {'named':>6} "
              f"{'anchors':>7} {'clerk-err':>9} {'absorbed':>8} {'consistent':>10}")
    print(header)
    print("-" * len(header))
    for card in cards:
        s, c, a = card["structure"], card["clerk_misattribution"], card["anchor_consistency"]
        r = card["response_absorption"]
        consistency = f"{a['agree']}/{a['checked']}" if a["checked"] else "-"
        print(f"{card['clip_id']:>6}  {card['verdict']:<16} {s['speaker_count']:>4} "
              f"{s['dominant_cluster_share']:>6.2f} {s['named_share']:>6.2f} "
              f"{card['roll_call_anchors']:>7} {c['failures']:>9} "
              f"{r['failures']:>8} {consistency:>10}")

    print(f"\nverdicts: {dict(Counter(c['verdict'] for c in cards))}")

    flagged = [c for c in cards if c["verdict"] != "OK"]
    if flagged:
        print(f"\nfirst failures in detail:")
        for card in flagged[:3]:
            print(f"\n  clip {card['clip_id']} — {card['verdict']}")
            for example in card["clerk_misattribution"]["examples"]:
                print(f"    clerk read {example['text']!r} -> labelled "
                      f"{example['assigned']!r} at t={example['start']:.0f}s")
            for bad in card["anchor_consistency"]["disagreements"]:
                print(f"    cluster {bad['cluster']} answered for {bad['expected']!r} "
                      f"but is named {bad['cluster_says']!r}")
            unknown = card["roster"]["unknown_names"]
            if unknown:
                print(f"    names not in this meeting's roll call: {unknown}")

    if args.samples and args.clip_id:
        print_samples(args.clip_id, args.samples)

    if args.json_out:
        args.json_out.write_text(json.dumps(cards, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
