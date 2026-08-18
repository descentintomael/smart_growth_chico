#!/usr/bin/env python3
"""Remove Whisper silence hallucinations from the council corpus.

Whisper emits filler when it hears silence, music or room noise — most often a
short stock phrase like "Thank you." dropped into the dead air before a meeting
is gavelled in. The corpus carries 518 runs of three or more consecutive
"Thank you." spread evenly across 2020-2026, so this was never cleaned rather
than cleaned and regressed, and every new transcription adds more.

The naive fix — collapse any repeated phrase — is wrong, because a chair
thanking several speakers in a row is real content. This script instead keys on
evidence the segment records already carry:

  impossible speech rate  a 0.02s "Thank you." is 500 characters per second.
                          Sustained speech tops out around 25.
  model self-doubt        no_speech_prob >= 0.5 means Whisper itself thinks the
                          audio is more likely silence than speech.

Either signal, combined with the text being a stock filler phrase, is enough.
A genuine "Thank you." at conversational pace with low no_speech_prob is kept:
of 44,875 stock phrases in the corpus, this keeps 34,830 and removes 10,045.

Designed to be SCP'd to macstudio and run there:

    scp scripts/council-fix-hallucinations.py macstudio:/tmp/
    ssh macstudio "python3 /tmp/council-fix-hallucinations.py"            # dry run
    ssh macstudio "python3 /tmp/council-fix-hallucinations.py --apply"
    ssh macstudio "python3 /tmp/council-fix-hallucinations.py --clip-id 1321 --apply"

Dry run is the default. --apply backs up the database and every touched file
first, then verifies the JSON still parses and the database is intact.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import time
from collections import Counter
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~/Projects/council-meeting-analyzer/data"))

# Short phrases Whisper falls back on when it has nothing to transcribe. Only
# ever removed with corroborating evidence — these are all things people
# genuinely say in a council meeting.
STOCK_PHRASE = re.compile(
    r"^[\s\W]*(thank you( very much)?|thanks|okay|ok|all right|alright"
    r"|bye|you|yeah|mm-?hmm|uh|um|so|right)[\s\W]*$",
    re.I,
)

# Training-data bleed-through with no legitimate reading in this corpus. Note
# how specific these are: an earlier draft used "see you (in the )?next" and
# flagged "we will see you next year" and "see you next month", which are real
# council speech. The video/time qualifier is what makes the pattern safe.
ALWAYS_JUNK = re.compile(
    r"thank you for watching|please subscribe|like and subscribe"
    r"|amara\.org|subtitles by|see you (in the )?next (video|time)",
    re.I,
)

# Sustained speech runs well under this; anything faster is a collapsed
# timestamp, not a person talking.
MAX_CHARS_PER_SECOND = 25.0
# Whisper's own probability that the span contains no speech at all.
NO_SPEECH_THRESHOLD = 0.5
# A run of this many identical stock phrases in a text blob, with nothing in
# between, is filler. Timing signals are unavailable at blob level.
MIN_REPEAT_RUN = 3


def chars_per_second(text: str, start: float, end: float) -> float:
    """Speech rate implied by a segment's text and timestamps."""
    duration = max(float(end) - float(start), 1e-6)
    return len(text.strip()) / duration


def segment_is_hallucination(text: str, start: float, end: float,
                             no_speech_prob: float | None) -> str | None:
    """Return the reason this segment is filler, or None to keep it."""
    stripped = text.strip()
    if not stripped:
        return None
    if ALWAYS_JUNK.search(stripped):
        return "always-junk"
    if not STOCK_PHRASE.match(stripped):
        return None
    if no_speech_prob is not None and float(no_speech_prob) >= NO_SPEECH_THRESHOLD:
        return "stock+high-no-speech"
    if chars_per_second(stripped, start, end) > MAX_CHARS_PER_SECOND:
        return "stock+impossible-rate"
    return None


def clean_segment_list(segments: list, tally: Counter, has_no_speech: bool) -> list:
    """Drop hallucinated segments, keeping everything else untouched."""
    kept = []
    for segment in segments:
        if not isinstance(segment, dict):
            kept.append(segment)
            continue
        reason = segment_is_hallucination(
            str(segment.get("text") or ""),
            segment.get("start") or 0,
            segment.get("end") or 0,
            segment.get("no_speech_prob") if has_no_speech else None,
        )
        if reason:
            tally[reason] += 1
        else:
            kept.append(segment)
    return kept


def collapse_repeats(text: str, tally: Counter) -> str:
    """Collapse runs of identical stock phrases in a text blob to one instance.

    Text blobs carry no timing, so repetition is the only available signal.
    Requiring an unbroken run of MIN_REPEAT_RUN identical phrases keeps the
    ordinary case — a chair saying "Thank you." between two speakers — intact.
    """
    pattern = re.compile(
        r"(?:(?<=^)|(?<=[\s]))"
        r"((?:Thank you|Thanks|Okay|All right|Alright|Bye|Yeah)[.!]?)"
        r"(?:\s+\1){" + str(MIN_REPEAT_RUN - 1) + r",}",
        re.I,
    )

    def replace(match: re.Match) -> str:
        tally["collapsed-repeat-run"] += 1
        return match.group(1)

    text = pattern.sub(replace, text)

    def drop_junk(match: re.Match) -> str:
        tally["always-junk (text)"] += 1
        return ""

    return re.sub(r"[^.!?]*(?:thank you for watching|please subscribe"
                  r"|amara\.org|see you (?:in the )?next (?:video|time))[^.!?]*[.!?]?",
                  drop_junk, text, flags=re.I)


def transcript_paths(clip_id: int | None, suffix: str) -> list[Path]:
    """Transcript files of a given kind, optionally for one clip.

    Model transcripts are named <clip>_large_v3.json / <clip>_medium.json, but
    the diarization file is just <clip>_diarization.json — so a single
    "<clip>_*<suffix>" glob silently matches nothing for diarization and the
    clip-scoped run quietly skips it.
    """
    if clip_id is None:
        pattern = f"*{suffix}"
    elif suffix == ".json":
        pattern = f"{clip_id}_*{suffix}"
    else:
        pattern = f"{clip_id}{suffix}"
    return sorted((DATA_DIR / "transcripts").glob(pattern))


def clean_transcript_files(clip_id: int | None, tally: Counter,
                           backup: Path | None) -> tuple[int, int]:
    """Clean model transcripts, returning (files changed, segments removed)."""
    changed = removed = 0
    paths = [p for p in transcript_paths(clip_id, ".json")
             if "_diarization" not in p.name]

    for path in paths:
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        segments = payload.get("segments")
        if not isinstance(segments, list):
            continue

        before = len(segments)
        local: Counter = Counter()
        payload["segments"] = clean_segment_list(segments, local, has_no_speech=True)
        dropped = before - len(payload["segments"])

        top_text = payload.get("text")
        new_text = collapse_repeats(top_text, local) if isinstance(top_text, str) else top_text
        if isinstance(top_text, str) and new_text != top_text:
            payload["text"] = new_text

        if not dropped and (not isinstance(top_text, str) or new_text == top_text):
            continue

        tally.update(local)
        changed += 1
        removed += dropped
        if backup:
            if not (backup / path.name).exists():
                shutil.copy2(path, backup / path.name)
            path.write_text(json.dumps(payload, ensure_ascii=False))
    return changed, removed


def clean_diarization_files(clip_id: int | None, tally: Counter,
                            backup: Path | None) -> tuple[int, int]:
    """Clean speaker-annotated transcripts, which the public site renders.

    These carry no no_speech_prob, so only the speech-rate signal applies.
    """
    changed = removed = 0
    for path in transcript_paths(clip_id, "_diarization.json"):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        segments = payload.get("segments")
        if not isinstance(segments, list):
            continue

        before = len(segments)
        local: Counter = Counter()
        payload["segments"] = clean_segment_list(segments, local, has_no_speech=False)
        dropped = before - len(payload["segments"])
        if not dropped:
            continue

        tally.update({f"diarization/{k}": v for k, v in local.items()})
        changed += 1
        removed += dropped
        if backup:
            if not (backup / path.name).exists():
                shutil.copy2(path, backup / path.name)
            path.write_text(json.dumps(payload, ensure_ascii=False))
    return changed, removed


def clean_database(conn: sqlite3.Connection, clip_id: int | None,
                   tally: Counter, apply: bool) -> int:
    """Collapse repeat runs in transcripts.full_text, which the exporter reads.

    Rebuilding full_text from the cleaned segments would be simpler but lossy:
    the stored text holds several thousand characters per meeting that the
    segment list does not, so it is edited in place instead.
    """
    query = "SELECT clip_id, full_text FROM transcripts"
    params: tuple = ()
    if clip_id is not None:
        query += " WHERE clip_id = ?"
        params = (clip_id,)

    changed = 0
    for row in conn.execute(query, params).fetchall():
        text = row["full_text"]
        if not text:
            continue
        cleaned = collapse_repeats(text, tally)
        if cleaned == text:
            continue
        changed += 1
        if apply:
            conn.execute(
                "UPDATE transcripts SET full_text=? WHERE clip_id=?",
                (cleaned, row["clip_id"]),
            )
    return changed


def verify(clip_id: int | None, conn: sqlite3.Connection) -> tuple[int, str]:
    """Confirm every transcript still parses and the database is intact."""
    corrupt = 0
    for path in transcript_paths(clip_id, ".json"):
        try:
            json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            corrupt += 1
            print(f"  CORRUPT: {path}")
    return corrupt, conn.execute("PRAGMA integrity_check").fetchone()[0]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Write changes. Without this the script only reports.")
    parser.add_argument("--clip-id", type=int, default=None,
                        help="Restrict to one meeting, for post-transcription use.")
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    tally: Counter = Counter()
    scope = f"clip {args.clip_id}" if args.clip_id else "whole corpus"
    print(f"[{'APPLY' if args.apply else 'DRY RUN'}] hallucination cleanup over {scope}\n")

    backup = None
    if args.apply:
        backup = DATA_DIR / "_backups" / f"halluc-{time.strftime('%Y%m%dT%H%M%S')}"
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DATA_DIR / "meetings.db", backup / "meetings.db")

    files, removed = clean_transcript_files(args.clip_id, tally, backup)
    print(f"transcript files changed : {files}  (segments removed: {removed})")

    diar_files, diar_removed = clean_diarization_files(args.clip_id, tally, backup)
    print(f"diarization files changed: {diar_files}  (segments removed: {diar_removed})")

    conn = sqlite3.connect(DATA_DIR / "meetings.db")
    conn.row_factory = sqlite3.Row
    db_changed = clean_database(conn, args.clip_id, tally, args.apply)
    print(f"full_text rows changed   : {db_changed}")
    if args.apply:
        conn.commit()

    print(f"\n{'count':>8}  reason")
    for reason, count in tally.most_common():
        print(f"{count:>8}  {reason}")
    print(f"\nTOTAL {sum(tally.values())}")

    if args.apply:
        corrupt, integrity = verify(args.clip_id, conn)
        print(f"\nVERIFY: {corrupt} corrupt JSON | integrity_check: {integrity}")
        print(f"Backup: {backup}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
