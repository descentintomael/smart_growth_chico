#!/usr/bin/env python3
"""Post-transcription pipeline runner.

Polls the council-meeting-analyzer DB for meetings that have reached
status='transcribed' and runs validate -> diarize -> identify_speakers ->
analyze on each, in the order they finished.

Designed to run on macstudio alongside the download + transcribe pipelines.
Exits when no meetings are in 'transcribed' or 'validated' state and the
caller passes --once. Without --once, polls indefinitely (Ctrl-C to stop).

Usage:
    nohup python3 scripts/post-transcription-pipeline.py > /tmp/post.log 2>&1 &
    nohup python3 scripts/post-transcription-pipeline.py --once > /tmp/post.log 2>&1 &
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path.home() / "Projects/council-meeting-analyzer"
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from council_analyzer.database import init_database, get_meetings_by_status  # noqa: E402
from council_analyzer.validator import validate_meeting  # noqa: E402
from council_analyzer.analyzer import analyze_meeting  # noqa: E402
from council_analyzer.diarization import diarize_meeting  # noqa: E402


POLL_SECONDS = 30


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_identify_speakers(clip_id: int) -> bool:
    """Invoke the identify_speakers script. It's a separate top-level script,
    not a library, so we shell out. Nice'd to coexist with other GPU work."""
    # sys.executable, not bare "python3": this pipeline runs under the project
    # venv, but "python3" resolves to the Homebrew interpreter, which has none
    # of the project's dependencies. That made every identify_speakers call die
    # with ModuleNotFoundError: rich, silently costing speaker attribution.
    cmd = [
        "nice", "-n", "19",
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "identify_speakers.py"),
        str(clip_id),
    ]
    log(f"  identify_speakers {clip_id}...")
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=600,
    )
    if result.returncode == 0:
        log(f"  identify_speakers {clip_id} OK")
        return True
    log(f"  identify_speakers {clip_id} FAILED: {result.stderr[:200]}")
    return False


def process_validated(
    clip_id: int,
    skip_diarize: bool = False,
    skip_analyze: bool = False,
) -> None:
    """Diarize -> identify -> analyze for a clip that's just been validated.

    Phase-1 invocation (--skip-analyze) is the right mode when Ollama is
    serving a different model for another GPU workload — defer analyze so we
    only thrash the model swap once, not 10 times.
    """
    if not skip_diarize:
        log(f"  diarize {clip_id}...")
        try:
            diar_result = diarize_meeting(clip_id)
            if not diar_result:
                log(f"  diarize {clip_id} FAILED (no result)")
                return
        except Exception as e:
            log(f"  diarize {clip_id} EXCEPTION: {e}")
            return

        # Speaker attribution depends on minutes JSON being present.
        minutes_json = PROJECT_ROOT / "data" / "minutes" / f"{clip_id}_minutes.json"
        if minutes_json.exists():
            run_identify_speakers(clip_id)
        else:
            log(f"  no minutes JSON for {clip_id}; skipping identify_speakers")

    if skip_analyze:
        log(f"  analyze {clip_id} deferred (--skip-analyze)")
        return

    log(f"  analyze {clip_id}...")
    try:
        analyze_meeting(clip_id)
        log(f"  analyze {clip_id} OK")
    except Exception as e:
        log(f"  analyze {clip_id} EXCEPTION: {e}")


def process_transcribed(
    clip_id: int,
    skip_diarize: bool = False,
    skip_analyze: bool = False,
) -> None:
    """Validate a clip; if it passes, kick into the post-validate chain."""
    log(f"validate {clip_id}...")
    try:
        result = validate_meeting(clip_id)
        if result is None:
            log(f"  validate {clip_id} returned None")
            return
        log(f"  validate {clip_id} OK")
    except Exception as e:
        log(f"  validate {clip_id} EXCEPTION: {e}")
        return

    process_validated(clip_id, skip_diarize=skip_diarize, skip_analyze=skip_analyze)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true",
                        help="Process current queue and exit (don't poll forever)")
    parser.add_argument("--skip-diarize", action="store_true",
                        help="Skip diarize+identify_speakers steps")
    parser.add_argument("--skip-analyze", action="store_true",
                        help="Skip analyze step (Phase 1 — defer until Ollama is idle)")
    args = parser.parse_args()

    init_database()
    log(
        f"post-transcription pipeline started "
        f"(skip_diarize={args.skip_diarize}, skip_analyze={args.skip_analyze})"
    )

    while True:
        # Pick up anything stuck at 'transcribed' (didn't get validated yet)
        # then anything stuck at 'validated' (didn't get analyzed yet).
        # We sort by clip_id descending so the newest meeting goes first.
        transcribed = sorted(
            get_meetings_by_status("transcribed"),
            key=lambda m: -m["clip_id"],
        )
        validated = sorted(
            get_meetings_by_status("validated"),
            key=lambda m: -m["clip_id"],
        )

        if not transcribed and not validated:
            if args.once:
                log("queue empty; --once requested; exiting")
                return 0
            log(f"queue empty; sleeping {POLL_SECONDS}s")
            time.sleep(POLL_SECONDS)
            continue

        for m in validated:
            process_validated(
                m["clip_id"],
                skip_diarize=args.skip_diarize,
                skip_analyze=args.skip_analyze,
            )
        for m in transcribed:
            process_transcribed(
                m["clip_id"],
                skip_diarize=args.skip_diarize,
                skip_analyze=args.skip_analyze,
            )


if __name__ == "__main__":
    raise SystemExit(main())
