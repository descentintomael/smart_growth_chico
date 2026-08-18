#!/usr/bin/env python3
"""Apply verified proper-noun corrections to the council-meeting corpus.

Whisper reliably mangles Chico place names and councilmember surnames, and it
produces a *family* of variants per name rather than one consistent error. The
rules below were adjudicated against city agendas, official minutes, Census
TIGER, city GIS and OSM in an earlier review pass; this script is the permanent
home for them, replacing the throwaway /tmp scripts that pass ran from.

Two reasons this must be re-runnable rather than one-and-done:

1. Every new transcription reintroduces the same errors, so this belongs in the
   post-transcription flow (see --clip-id).
2. The original pass wrote to the transcript JSON files, `analysis.result`,
   `agenda_items.title` and `meetings.title` but *not* to `transcripts.full_text`,
   leaving that column stale. This script covers all five.

Designed to be SCP'd to macstudio and run there (the corpus lives there):

    scp scripts/council-fix-proper-nouns.py macstudio:/tmp/
    ssh macstudio "python3 /tmp/council-fix-proper-nouns.py"            # dry run
    ssh macstudio "python3 /tmp/council-fix-proper-nouns.py --apply"
    ssh macstudio "python3 /tmp/council-fix-proper-nouns.py --clip-id 1311 --apply"

Dry run is the default. --apply backs up the database and every touched file to
data/_backups/nouns-<timestamp>/ before writing, then verifies that all
transcript JSON still parses and the database passes an integrity check.
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

# Speaker titles that appear before a surname. Used to restrict rules whose
# target string is also a legitimate word or a different real surname.
TITLE = (
    r"(?:Mayor|Vice\s+Mayor|Council\s?[Mm]ember|Councilor|Councilmember"
    r"|Mr\.|Ms\.|Miss|Mrs\.|City\s+Clerk|City\s+Manager|Dr\.)"
)

# Unambiguous one-to-one substitutions, safe to apply anywhere in the corpus.
FLAT_CORRECTIONS: list[tuple[str, str]] = [
    ("Denley", "Denlay"),
    ("Dinley", "Denlay"),
    ("Merriam Park", "Meriam Park"),
    ("Merion Park", "Meriam Park"),
    ("Veague", "Vieg"),
    ("Withoon", "Withuhn"),
    ("Lexapol", "Lexipol"),
    ("Tanden", "Tandon"),
    ("Torrey Shelter", "Torres Shelter"),
    ("Torre Shelter", "Torres Shelter"),
    ("Aeroflite", "Aero-Flite"),
    ("Bamlett", "Bamlet"),
    ("Hagen Lane", "Hegan Lane"),
    ("Stillson Canyon", "Stilson Canyon"),
    # Bibble/Bimble are not words in any other context here — they are always
    # Bidwell, whether the speaker meant the park, the mansion or the avenue.
    ("Bibble", "Bidwell"),
    ("Bimble", "Bidwell"),
    ("Bainey Lane", "Baney Lane"),
    ("Tiger Pond", "Teichert Pond"),
    ("Tigard Ponds", "Teichert Ponds"),
    ("Tigard Pond", "Teichert Pond"),
    ("Myers Street", "Meyers Street"),
    ("Cusick Avenue", "Cussick Avenue"),
    ("Cusick Apartments", "Cussick Apartments"),
    ("Hinshaw Avenue", "Henshaw Avenue"),
    ("Carling Place", "Carlene Place"),
    ("Velland-Brosia", "Vallombrosa"),
]

# Cheap substring probe so the regex battery only runs on text that could match.
TRIGGERS = tuple(
    word.lower()
    for word in (
        [wrong.split()[0] for wrong, _ in FLAT_CORRECTIONS]
        + [
            "overbe", "oberbe", "marion park", "miriam park", "mary park",
            "northern valley", "orry", "horry", "orrie", "preston", "orem",
            "sorenson", "byker", "bellmere", "ferris street", "dome hill",
            "linda channel", "kulich", "koolidge", "tannen", "kirk kauf",
        ]
    )
)


def keep_case(replacement: str, matched: str) -> str:
    """Preserve all-caps styling so headings keep their shout-case."""
    return replacement.upper() if matched.isupper() else replacement


def build_flat_pattern() -> tuple[re.Pattern, dict[str, str]]:
    """Compile the flat corrections into one alternation, longest match first."""
    ordered = sorted(FLAT_CORRECTIONS, key=lambda c: -len(c[0]))
    lookup = {wrong.lower(): right for wrong, right in ordered}
    alternation = "|".join(
        r"\s+".join(re.escape(part) for part in wrong.split()) for wrong, _ in ordered
    )
    return re.compile(r"\b(" + alternation + r")\b", re.I), lookup


FLAT_PATTERN, FLAT_LOOKUP = build_flat_pattern()


def build_context_rules() -> list[tuple[str, re.Pattern, callable]]:
    """Rules whose target is also a real word or surname elsewhere.

    Each carries a guard — a speaker title, a neighbouring word, or an explicit
    exclusion — so it cannot fire on the legitimate use.
    """
    rules: list[tuple[str, re.Pattern, callable]] = []

    def rule(name: str, pattern: str, replace) -> None:
        rules.append((name, re.compile(pattern, re.I), replace))

    # Repair the whole "van Overbeek" span, preserving heading capitalisation.
    rule(
        "van Overbeek (span)",
        r"\bva[nm]\s+O(?:ver|ber)be[ck]k?\b",
        lambda m: keep_case("van Overbeek", m.group(0)),
    )
    # Bare surname, only where "van" does not already precede it.
    rule(
        "van Overbeek (bare)",
        r"(?<!van )(?<!Van )(?<!VAN )\bO(?:ver|ber)be[ck]k\b",
        lambda m: keep_case("van Overbeek", m.group(0)),
    )
    rule(
        "Meriam Park",
        r"\b(?:Marion|Miriam|Mary)\s+Park\b",
        lambda m: keep_case("Meriam Park", m.group(0)),
    )
    # The flat "Merriam Park" rule joins words with \s+, so the hyphenated form
    # slips past it.
    rule(
        "Meriam Park (hyphenated)",
        r"\bMerriam[-–]Park\b",
        lambda m: keep_case("Meriam Park", m.group(0)),
    )
    # Speakers also say the name bare ("places like Merriam", "the Merriam
    # project"). Every bare occurrence in this corpus is the park; the only
    # realistic false positive is the dictionary, which is excluded.
    rule(
        "Meriam (bare)",
        r"\bMerriam(s?)\b(?![-\s]*Webster)",
        lambda m: keep_case("Meriam" + m.group(1), m.group(0)),
    )
    # Only these two orgs are really "North Valley" — Northern Valley Indian
    # Health is correct and is deliberately left alone.
    rule(
        "North Valley Harm Reduction",
        r"\bNorthern\s+Valley\s+Harm\s+Reduction\b",
        lambda m: keep_case("North Valley Harm Reduction", m.group(0)),
    )
    rule(
        "North Valley Property Owners",
        r"\bNorthern\s+Valley\s+Property\s+Owners\b",
        lambda m: keep_case("North Valley Property Owners", m.group(0)),
    )
    rule(
        "Ory (councilmember)",
        r"\b((?:Council\s?[Mm]ember|Councilor|Councilmember)\s+)(?:Orry|Horry|Orrie)\b",
        lambda m: m.group(1) + "Ory",
    )
    rule(
        "Presson (clerk)",
        rf"\b({TITLE}\s+|Debbie\s+)Preston\b",
        lambda m: m.group(1) + "Presson",
    )
    rule(
        "Orme (city manager)",
        rf"\b({TITLE}\s+|Mark\s+)Orem\b",
        lambda m: m.group(1) + "Orme",
    )
    rule(
        "Sorensen (city manager)",
        rf"\b({TITLE}\s+|Mark\s+)Sorenson\b",
        lambda m: m.group(1) + "Sorensen",
    )
    # The canonical form matches this pattern too, so without the lookahead the
    # rule rewrites its own output on every run and the tally reports hundreds
    # of "corrections" that changed nothing.
    rule(
        "Bykerk-Kauffman",
        r"\b(?!Bykerk-Kauffman\b)Byker[k]?[-\s]?Kau?f+man\b",
        lambda m: keep_case("Bykerk-Kauffman", m.group(0)),
    )
    rule(
        "Bykerk-Kauffman (Kirk variant)",
        r"\b(?:by\s+)?Kirk\s+Kau?f+man\b",
        lambda m: keep_case("Bykerk-Kauffman", m.group(0)),
    )
    rule(
        "Ann Bykerk",
        r"\bAnn\s+Byker\b(?![-\s]?Kau)",
        lambda m: keep_case("Ann Bykerk", m.group(0)),
    )
    rule("Bell-Muir", r"\bBellmere\b", lambda m: keep_case("Bell-Muir", m.group(0)))
    rule("Fair Street", r"\bFerris\s+Street\b", lambda m: keep_case("Fair Street", m.group(0)))
    rule("Doe Mill", r"\bDome\s+Hill\b", lambda m: keep_case("Doe Mill", m.group(0)))
    rule("Lindo Channel", r"\bLinda\s+Channel\b", lambda m: keep_case("Lindo Channel", m.group(0)))
    rule(
        "Coolidge",
        rf"\b({TITLE}\s+)K(?:ulich|oolidge)\b",
        lambda m: m.group(1) + "Coolidge",
    )
    rule(
        "Tandon (variant)",
        rf"\b({TITLE}\s+)Tannen\b",
        lambda m: m.group(1) + "Tandon",
    )
    # Deliberately NOT applied: Wolff -> Wolfe, held pending a roster check.
    return rules


CONTEXT_RULES = build_context_rules()


def might_match(text: str) -> bool:
    """Cheap containment test before running the full regex battery."""
    lowered = text.lower()
    return any(trigger in lowered for trigger in TRIGGERS)


def apply_corrections(text: str, tally: Counter) -> str:
    """Apply every flat and context rule to a blob of text."""
    if not might_match(text):
        return text

    def flat_sub(match: re.Match) -> str:
        key = re.sub(r"\s+", " ", match.group(0)).lower()
        replacement = FLAT_LOOKUP.get(key)
        if replacement is None:
            return match.group(0)
        tally[f"{key} -> {replacement}"] += 1
        return keep_case(replacement, match.group(0))

    text = FLAT_PATTERN.sub(flat_sub, text)

    for name, pattern, replace in CONTEXT_RULES:
        def context_sub(match: re.Match, _name=name, _replace=replace) -> str:
            tally[_name] += 1
            return _replace(match)

        text = pattern.sub(context_sub, text)

    return text


def phrase_replacements() -> list[tuple[list[str], list[str]]]:
    """Flat corrections expressed as token sequences, for word-level repair.

    Whisper stores each word of a segment as its own JSON string, so a phrase
    rule like "Hagen Lane" -> "Hegan Lane" matches the segment text but cannot
    span the separator between two word tokens. The result is a transcript
    whose text says "Hegan Lane" while its own word timestamps still say
    "Hagen". Every correction pass so far has left that mismatch in place.
    """
    pairs = []
    for wrong, right in FLAT_CORRECTIONS:
        wrong_tokens, right_tokens = wrong.split(), right.split()
        # Same-length only: replacing n tokens with m would desynchronise the
        # per-word timestamps that sit alongside them.
        if len(wrong_tokens) == len(right_tokens):
            pairs.append((wrong_tokens, right_tokens))
    return pairs


PHRASE_REPLACEMENTS = phrase_replacements()


def fix_word_tokens(payload: dict, tally: Counter) -> bool:
    """Repair proper nouns inside segments[].words[], returning True if changed.

    Matches whole token windows rather than bare words: "Hagen" is only
    corrected when the following token is "Lane", so a legitimate surname is
    never rewritten on the strength of one ambiguous token.
    """
    changed = False
    for segment in payload.get("segments") or []:
        words = segment.get("words")
        if not isinstance(words, list):
            continue

        for index, entry in enumerate(words):
            if not isinstance(entry, dict) or "word" not in entry:
                continue

            for wrong_tokens, right_tokens in PHRASE_REPLACEMENTS:
                span = len(wrong_tokens)
                if index + span > len(words):
                    continue
                window = words[index:index + span]
                if not all(isinstance(w, dict) and "word" in w for w in window):
                    continue

                # Compare on the bare word, ignoring the leading space and any
                # trailing punctuation Whisper attaches to the final token.
                actual = [str(w["word"]).strip() for w in window]
                stripped = [a.rstrip(".,;:!?") for a in actual]
                if [s.lower() for s in stripped] != [t.lower() for t in wrong_tokens]:
                    continue

                for offset, (target, replacement) in enumerate(zip(window, right_tokens)):
                    original = str(target["word"])
                    leading = original[: len(original) - len(original.lstrip())]
                    trailing = actual[offset][len(stripped[offset]):]
                    if stripped[offset].isupper():
                        replacement = replacement.upper()
                    target["word"] = f"{leading}{replacement}{trailing}"

                tally[f"words: {' '.join(wrong_tokens)} -> {' '.join(right_tokens)}"] += 1
                changed = True
                break

    return changed


def fix_word_token_files(paths: list[Path], tally: Counter, backup: Path | None) -> int:
    """Apply word-token repair across transcript JSON files."""
    touched = 0
    for path in paths:
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict) or not payload.get("segments"):
            continue
        if not fix_word_tokens(payload, tally):
            continue
        touched += 1
        if backup:
            if not (backup / path.name).exists():
                shutil.copy2(path, backup / path.name)
            path.write_text(json.dumps(payload, ensure_ascii=False))
    return touched


def transcript_files(clip_id: int | None) -> list[Path]:
    """Transcript JSON files, optionally narrowed to a single clip."""
    pattern = f"{clip_id}_*.json" if clip_id else "*.json"
    return sorted((DATA_DIR / "transcripts").glob(pattern))


# (table, text column, primary key column, clip filter column)
DB_TARGETS = [
    ("transcripts", "full_text", "clip_id", "clip_id"),
    ("analysis", "result", "id", "clip_id"),
    ("agenda_items", "title", "id", "clip_id"),
    ("meetings", "title", "clip_id", "clip_id"),
]


def fix_files(paths: list[Path], tally: Counter, backup: Path | None) -> int:
    """Rewrite transcript JSON in place as raw text.

    Raw substitution rather than JSON reserialization keeps each file
    byte-identical apart from the corrected spans — no reformatting, no key
    reordering, so diffs stay reviewable.
    """
    touched = 0
    for path in paths:
        raw = path.read_text()
        fixed = apply_corrections(raw, tally)
        if fixed == raw:
            continue
        touched += 1
        if backup:
            shutil.copy2(path, backup / path.name)
            path.write_text(fixed)
    return touched


def fix_database(
    conn: sqlite3.Connection, clip_id: int | None, tally: Counter, apply: bool
) -> dict[str, int]:
    """Correct every text-bearing column, returning per-table row counts."""
    counts: dict[str, int] = {}
    for table, column, key, clip_col in DB_TARGETS:
        query = f"SELECT {key} AS k, {column} AS v FROM {table}"
        params: tuple = ()
        if clip_id is not None:
            query += f" WHERE {clip_col} = ?"
            params = (clip_id,)

        changed = 0
        for row in conn.execute(query, params).fetchall():
            if not row["v"]:
                continue
            fixed = apply_corrections(row["v"], tally)
            if fixed == row["v"]:
                continue
            changed += 1
            if apply:
                conn.execute(
                    f"UPDATE {table} SET {column}=? WHERE {key}=?", (fixed, row["k"])
                )
        counts[table] = changed
    return counts


def verify(paths: list[Path], conn: sqlite3.Connection) -> tuple[int, str]:
    """Confirm every transcript still parses and the database is intact."""
    corrupt = 0
    for path in paths:
        try:
            json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            corrupt += 1
            print(f"  CORRUPT: {path}")
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    return corrupt, integrity


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Write changes. Without this the script reports and exits.",
    )
    parser.add_argument(
        "--clip-id", type=int, default=None,
        help="Restrict to a single meeting, for use as a post-transcription step.",
    )
    parser.add_argument(
        "--word-tokens", action="store_true",
        help="Also repair segments[].words[], which phrase rules cannot reach. "
             "Rewrites the JSON rather than patching raw text.",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    tally: Counter = Counter()
    mode = "APPLY" if args.apply else "DRY RUN"
    scope = f"clip {args.clip_id}" if args.clip_id else "whole corpus"
    rule_count = len(FLAT_CORRECTIONS) + len(CONTEXT_RULES)
    print(f"[{mode}] {rule_count} rules over {scope}\n")

    backup = None
    if args.apply:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        backup = DATA_DIR / "_backups" / f"nouns-{stamp}"
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DATA_DIR / "meetings.db", backup / "meetings.db")

    paths = transcript_files(args.clip_id)
    touched = fix_files(paths, tally, backup)
    print(f"transcript files changed: {touched} of {len(paths)}")

    if args.word_tokens:
        word_touched = fix_word_token_files(paths, tally, backup)
        print(f"word-token files changed: {word_touched} of {len(paths)}")

    conn = sqlite3.connect(DATA_DIR / "meetings.db")
    conn.row_factory = sqlite3.Row
    counts = fix_database(conn, args.clip_id, tally, args.apply)
    for table, changed in counts.items():
        print(f"  {table:<14} rows changed: {changed}")
    if args.apply:
        conn.commit()

    print(f"\n{'occurrences':>8}  rule")
    for name, count in tally.most_common():
        print(f"{count:>8}  {name}")
    print(f"\nTOTAL {sum(tally.values())}")

    if args.apply:
        corrupt, integrity = verify(paths, conn)
        print(f"\nVERIFY: {corrupt} corrupt JSON | integrity_check: {integrity}")
        print(f"Backup: {backup}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
