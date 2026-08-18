#!/usr/bin/env python3
"""Transcribe council meetings as their downloads finish.

The download stage streams several meetings in parallel and takes hours, while
transcription is a single-GPU job that must run one meeting at a time. This
driver bridges the two: it watches a set of clip IDs and transcribes each one
the moment it reaches status='downloaded', in completion order, so the GPU is
never idle waiting for a specific download.

Deliberately does NOT run validate/diarize/analyze — those use Ollama and
pyannote and would contend with MLX for the GPU. Run
scripts/post-transcription-pipeline.py once this finishes.

Designed to be SCP'd to macstudio and run there:

    scp scripts/council-transcribe-driver.py macstudio:/tmp/
    ssh macstudio "cd ~/Projects/council-meeting-analyzer && \\
        nohup .venv/bin/python /tmp/council-transcribe-driver.py \\
        --clip-ids 1309,1311,1316,1321,1322,1325 > /tmp/transcribe.log 2>&1 &"
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path.home() / "Projects/council-meeting-analyzer"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from council_analyzer.database import get_meeting, init_database  # noqa: E402
from council_analyzer.transcriber import transcribe_meeting  # noqa: E402

POLL_SECONDS = 60
# A 4-hour meeting downloads in roughly 2.5 hours; allow generous headroom
# before declaring a clip stuck.
MAX_WAIT_SECONDS = 6 * 60 * 60


def log(message: str) -> None:
    """Timestamped progress line."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def pending_states(clip_ids: list[int]) -> dict[int, str]:
    """Current status for each clip we are waiting on."""
    states = {}
    for clip_id in clip_ids:
        meeting = get_meeting(clip_id)
        states[clip_id] = meeting["status"] if meeting else "missing"
    return states


def next_ready(clip_ids: list[int], done: set[int]) -> int | None:
    """Return a clip that has finished downloading and still needs transcribing."""
    for clip_id in clip_ids:
        if clip_id in done:
            continue
        meeting = get_meeting(clip_id)
        if meeting and meeting["status"] == "downloaded":
            return clip_id
    return None


def unreachable(clip_ids: list[int], done: set[int]) -> bool:
    """True when no remaining clip can still become transcribable."""
    for clip_id in clip_ids:
        if clip_id in done:
            continue
        meeting = get_meeting(clip_id)
        if meeting and meeting["status"] in ("discovered", "downloading", "downloaded"):
            return False
    return True


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clip-ids", required=True,
        help="Comma-separated clip IDs to transcribe as they become available.",
    )
    parser.add_argument(
        "--single-model", action="store_true",
        help="Transcribe with large-v3 only, skipping the medium cross-check.",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    clip_ids = [int(part) for part in args.clip_ids.split(",") if part.strip()]

    # Yield to any interactive work on this shared box.
    try:
        os.nice(19)
    except OSError:
        pass

    init_database()
    log(f"driver started for {len(clip_ids)} clips: {clip_ids}")
    log(f"initial states: {pending_states(clip_ids)}")

    done: set[int] = set()
    waited = 0

    while len(done) < len(clip_ids):
        clip_id = next_ready(clip_ids, done)

        if clip_id is None:
            if unreachable(clip_ids, done):
                remaining = [c for c in clip_ids if c not in done]
                log(f"no remaining clip can become ready; giving up on {remaining}")
                log(f"final states: {pending_states(remaining)}")
                break
            if waited >= MAX_WAIT_SECONDS:
                log(f"waited {waited // 3600}h with no progress; stopping")
                break
            time.sleep(POLL_SECONDS)
            waited += POLL_SECONDS
            continue

        waited = 0
        meeting = get_meeting(clip_id)
        log(f"transcribing {clip_id}: {meeting['title'][:60]}")
        started = time.time()
        try:
            result = transcribe_meeting(clip_id, dual_model=not args.single_model)
            elapsed = (time.time() - started) / 60
            if result:
                log(f"  {clip_id} transcribed in {elapsed:.1f} min")
            else:
                log(f"  {clip_id} FAILED after {elapsed:.1f} min")
        except Exception as exc:  # keep the queue moving past one bad meeting
            log(f"  {clip_id} EXCEPTION: {exc}")
        done.add(clip_id)

    log(f"driver finished; transcribed/attempted {len(done)} of {len(clip_ids)}")
    log(f"final states: {pending_states(clip_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
