#!/usr/bin/env python3
"""ASR engine bake-off harness for the council-meeting corpus.

Compares candidate speech-to-text engines on the same council meeting audio so
we can decide whether to replace the current dual-model mlx-whisper setup
(large-v3 + medium) plus separate pyannote diarization with a single
speaker-attributed model.

Designed to be SCP'd to macstudio and run there (the audio and the Apple
Silicon GPU both live there):

    scp scripts/asr-bakeoff.py macstudio:/tmp/asr-bakeoff.py
    ssh macstudio "python3 /tmp/asr-bakeoff.py --plan"          # no GPU work
    ssh macstudio "python3 /tmp/asr-bakeoff.py --run --engines baseline,vibevoice-bf16"

SAFETY: --plan is the default. Nothing downloads models or touches the GPU
until --run is passed explicitly, because macstudio's GPU is frequently busy
with other experiments. --run also refuses to start if another process is
holding a large resident set unless --force is given.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path.home() / "Projects/council-meeting-analyzer"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
MINUTES_DIR = PROJECT_ROOT / "data" / "minutes"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "analysis" / "asr-bakeoff"

# Excerpt defaults: 10 minutes starting 45 minutes in. Council meetings open
# with ceremonial items; 45 minutes in usually lands in substantive discussion
# or public comment, which is where speaker attribution actually matters.
DEFAULT_OFFSET_MINUTES = 45
DEFAULT_EXCERPT_MINUTES = 10

# Another MLX job resident above this is a strong signal the GPU is busy.
BUSY_RSS_GB = 8.0


@dataclass
class Engine:
    """A candidate ASR engine and how to invoke it."""

    key: str
    model_id: str
    runner: str  # "mlx_whisper" | "mlx_audio"
    diarizes: bool
    notes: str
    approx_weights_gb: float
    # mlx-audio CLI flags vary by version; --plan prints the command so the
    # flags can be checked against the installed version before running.
    extra_args: list[str] = field(default_factory=list)


CANDIDATES: list[Engine] = [
    Engine(
        key="baseline",
        model_id="mlx-community/whisper-large-v3-mlx",
        runner="mlx_whisper",
        diarizes=False,
        notes="Current production primary model. Already cached on macstudio.",
        approx_weights_gb=3.1,
    ),
    Engine(
        key="whisper-turbo",
        model_id="mlx-community/whisper-large-v3-turbo-asr-fp16",
        runner="mlx_audio",
        diarizes=False,
        notes="Drop-in speed upgrade over large-v3, same family, no diarization.",
        approx_weights_gb=1.6,
    ),
    Engine(
        key="vibevoice-bf16",
        model_id="mlx-community/VibeVoice-ASR-bf16",
        runner="mlx_audio",
        diarizes=True,
        notes=(
            "Microsoft VibeVoice-ASR 9B, MIT. Speaker-attributed + timestamps "
            "in one pass, up to 60 min of audio. Reported DER 4.28% / cpWER "
            "11.48% on the MLC multi-speaker benchmark. Supports hotwords."
        ),
        approx_weights_gb=18.0,
        extra_args=["--format", "json", "--max-tokens", "8192"],
    ),
    Engine(
        key="vibevoice-8bit",
        model_id="mlx-community/VibeVoice-ASR-8bit",
        runner="mlx_audio",
        diarizes=True,
        notes="Quantized VibeVoice — check whether the accuracy delta is worth the speed.",
        approx_weights_gb=9.5,
        extra_args=["--format", "json", "--max-tokens", "8192"],
    ),
    Engine(
        key="moss-diarize-8bit",
        model_id="majentik/MOSS-Transcribe-Diarize-MLX-8bit",
        runner="mlx_audio",
        diarizes=True,
        notes=(
            "MOSS-Transcribe-Diarize 0.9B, Apache 2.0, 90-min single pass. "
            "Tiny and fast, but published benchmarks are CER/Chinese-leaning "
            "and the MLX conversions are community repos, not mlx-community."
        ),
        approx_weights_gb=1.1,
        extra_args=["--format", "json"],
    ),
    Engine(
        key="parakeet-v3",
        model_id="mlx-community/parakeet-tdt-0.6b-v3",
        runner="mlx_audio",
        diarizes=False,
        notes="Speed reference: ~100x faster than Whisper, slightly worse WER, no diarization.",
        approx_weights_gb=1.2,
        extra_args=["--format", "json"],
    ),
]

# Domain vocabulary. Recall of these terms is a usable accuracy proxy when we
# have no verbatim ground truth — these are the words a generic model gets
# wrong and the words the downstream analysis actually keys on.
DOMAIN_TERMS = [
    "Bidwell", "Esplanade", "Valley's Edge", "Chico", "Butte", "Enloe",
    "Oroville", "Paradise", "CARD", "CUSD", "Coolidge", "Reynolds", "Huber",
    "Morgan", "Tandon", "Overbeek", "Winslow", "infill", "zoning", "setback",
    "variance", "General Plan", "CEQA", "mitigated negative declaration",
    "parking minimum", "accessory dwelling", "groundwater", "Measure",
]

# Whisper's characteristic long-form failure modes. The existing pipeline has a
# whole cleanup script for these; a replacement engine should produce fewer.
HALLUCINATION_MARKERS = [
    "thank you for watching",
    "subscribe to",
    "www.",
    ".com",
    "amara.org",
    "transcription by",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare ASR engines on council meeting audio.",
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Actually run inference. Without this, only prints the plan.",
    )
    parser.add_argument(
        "--plan", action="store_true",
        help="Print the plan and readiness checks, then exit (default).",
    )
    parser.add_argument(
        "--clip-id", type=int, default=None,
        help="Clip ID to benchmark; audio is read from data/audio/<id>.mp3.",
    )
    parser.add_argument(
        "--audio", type=Path, default=None,
        help="Explicit audio path, overrides --clip-id.",
    )
    parser.add_argument(
        "--engines", default="all",
        help=f"Comma-separated engine keys, or 'all'. Known: {[e.key for e in CANDIDATES]}",
    )
    parser.add_argument(
        "--offset-minutes", type=int, default=DEFAULT_OFFSET_MINUTES,
        help="Start of the excerpt within the meeting.",
    )
    parser.add_argument(
        "--minutes", type=int, default=DEFAULT_EXCERPT_MINUTES,
        help="Excerpt length. Use 0 for the full meeting (slow).",
    )
    parser.add_argument(
        "--reference", type=Path, default=None,
        help="Optional hand-corrected transcript for the excerpt; enables WER.",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR,
        help="Where to write transcripts and the results table.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Run even if another large process looks like it is using the GPU.",
    )
    return parser.parse_args()


def select_engines(spec: str) -> list[Engine]:
    """Resolve an --engines spec into Engine objects."""
    if spec == "all":
        return list(CANDIDATES)

    by_key = {engine.key: engine for engine in CANDIDATES}
    selected = []
    for key in (part.strip() for part in spec.split(",")):
        if key not in by_key:
            raise SystemExit(f"Unknown engine '{key}'. Known: {sorted(by_key)}")
        selected.append(by_key[key])
    return selected


def resolve_audio(args: argparse.Namespace) -> Path:
    """Locate the source audio file."""
    if args.audio:
        return args.audio
    if args.clip_id:
        return AUDIO_DIR / f"{args.clip_id}.mp3"
    raise SystemExit("Provide --clip-id or --audio.")


def hf_cache_has(model_id: str) -> bool:
    """Check whether a model is already in the local HuggingFace cache."""
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    folder = "models--" + model_id.replace("/", "--")
    return (cache_dir / folder).exists()


def find_busy_processes() -> list[str]:
    """Return descriptions of processes with a large resident set.

    macstudio shares its GPU with other experiments; this is a courtesy check
    so a bake-off does not evict someone else's model mid-run.
    """
    try:
        output = subprocess.run(
            ["ps", "-axo", "pid,rss,comm"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []

    busy = []
    for line in output.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        pid, rss_kb, comm = parts
        try:
            rss_gb = int(rss_kb) / (1024 * 1024)
        except ValueError:
            continue
        if rss_gb >= BUSY_RSS_GB and "python" in comm.lower():
            busy.append(f"pid {pid}: {rss_gb:.1f} GB — {comm}")
    return busy


def make_excerpt(source: Path, out_dir: Path, offset_min: int, length_min: int) -> Path:
    """Cut a 16 kHz mono WAV excerpt so every engine sees identical input.

    Returns the source path unchanged when length_min is 0 (full meeting).
    """
    if length_min == 0:
        return source

    out_path = out_dir / f"{source.stem}_excerpt_{offset_min}m_{length_min}m.wav"
    if out_path.exists():
        return out_path

    cmd = [
        "ffmpeg", "-nostdin", "-y",
        "-ss", str(offset_min * 60),
        "-t", str(length_min * 60),
        "-i", str(source),
        "-ac", "1", "-ar", "16000",
        str(out_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True, timeout=600)
    return out_path


def build_command(engine: Engine, audio: Path, out_dir: Path) -> list[str]:
    """Build the shell command that runs one engine.

    Nice'd to 19 throughout so a bake-off yields to interactive GPU work.
    """
    out_stem = out_dir / f"{audio.stem}__{engine.key}"

    if engine.runner == "mlx_whisper":
        # Uses the same API the production transcriber calls, so the baseline
        # measures what the pipeline actually does today.
        snippet = (
            "import json, mlx_whisper, sys;"
            "r = mlx_whisper.transcribe("
            f"{str(audio)!r}, path_or_hf_repo={engine.model_id!r},"
            " word_timestamps=False, verbose=False);"
            f"open({str(out_stem) + '.json'!r}, 'w').write(json.dumps(r))"
        )
        return ["nice", "-n", "19", "python3", "-c", snippet]

    return [
        "nice", "-n", "19",
        "python3", "-m", "mlx_audio.stt.generate",
        "--model", engine.model_id,
        "--audio", str(audio),
        "--output-path", str(out_stem),
        *engine.extra_args,
    ]


def load_output_text(engine: Engine, audio: Path, out_dir: Path) -> tuple[str, list[str]]:
    """Read an engine's output back as (full_text, speaker_labels).

    Output shapes differ per engine, so this probes the plausible layouts
    rather than assuming one schema.
    """
    stem = out_dir / f"{audio.stem}__{engine.key}"
    candidates = [Path(f"{stem}.json"), stem / "output.json", Path(f"{stem}.txt")]
    payload = next((p for p in candidates if p.exists()), None)
    if payload is None:
        return "", []

    if payload.suffix == ".txt":
        return payload.read_text(), []

    data = json.loads(payload.read_text())
    if isinstance(data, dict) and isinstance(data.get("text"), str):
        text = data["text"]
    else:
        text = ""

    segments = []
    if isinstance(data, dict):
        for key in ("segments", "results", "transcript"):
            if isinstance(data.get(key), list):
                segments = data[key]
                break

    speakers = []
    if segments:
        parts = []
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            parts.append(str(segment.get("text", "")))
            speaker = segment.get("speaker") or segment.get("speaker_id")
            if speaker:
                speakers.append(str(speaker))
        if not text:
            text = " ".join(parts)

    # Some speaker-attributed models emit inline [S01] tags instead of fields.
    if not speakers:
        speakers = re.findall(r"\[S\d{1,2}\]", text)

    return text, speakers


def score_transcript(text: str, speakers: list[str], reference: str | None) -> dict:
    """Score a transcript on proxy metrics, plus WER when a reference exists."""
    lowered = text.lower()
    found_terms = [term for term in DOMAIN_TERMS if term.lower() in lowered]
    markers = [m for m in HALLUCINATION_MARKERS if m in lowered]

    words = lowered.split()
    # A repeated 8-gram is the classic Whisper long-form loop.
    eight_grams = Counter(
        " ".join(words[i:i + 8]) for i in range(max(0, len(words) - 7))
    )
    loops = sum(1 for _, count in eight_grams.items() if count >= 3)

    result = {
        "word_count": len(words),
        "domain_terms_found": len(found_terms),
        "domain_terms_total": len(DOMAIN_TERMS),
        "domain_terms_missing": [t for t in DOMAIN_TERMS if t.lower() not in lowered],
        "hallucination_markers": markers,
        "repeated_8gram_loops": loops,
        "distinct_speakers": len(set(speakers)),
        "speaker_turns": len(speakers),
    }

    if reference:
        result["wer"] = compute_wer(reference, text)
    return result


def compute_wer(reference: str, hypothesis: str) -> float | None:
    """Word error rate via jiwer, or None when jiwer is unavailable."""
    try:
        import jiwer
    except ImportError:
        return None

    transform = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
        jiwer.ReduceToListOfListOfWords(),
    ])
    return jiwer.wer(
        reference, hypothesis,
        truth_transform=transform, hypothesis_transform=transform,
    )


def print_plan(engines: list[Engine], audio: Path, args: argparse.Namespace) -> None:
    """Print readiness checks and the exact commands --run would execute."""
    print("=" * 78)
    print("ASR BAKE-OFF — PLAN ONLY (no GPU work performed)")
    print("=" * 78)

    print(f"\nSource audio:  {audio}  {'[MISSING]' if not audio.exists() else ''}")
    if args.minutes:
        print(f"Excerpt:       {args.minutes} min starting at {args.offset_minutes} min, 16 kHz mono WAV")
    else:
        print("Excerpt:       full meeting (slow)")
    print(f"Output dir:    {args.out_dir}")
    print(f"Reference:     {args.reference or 'none — WER will be skipped'}")

    print("\nTooling:")
    for tool, probe in (("ffmpeg", shutil.which("ffmpeg")), ("python3", sys.executable)):
        print(f"  {tool:<12} {probe or 'NOT FOUND'}")
    for module in ("mlx_whisper", "mlx_audio", "jiwer"):
        try:
            __import__(module)
            status = "installed"
        except ImportError:
            status = "NOT INSTALLED"
        print(f"  {module:<12} {status}")

    print("\nCandidates:")
    total_download = 0.0
    for engine in engines:
        cached = hf_cache_has(engine.model_id)
        if not cached:
            total_download += engine.approx_weights_gb
        print(f"\n  [{engine.key}] {engine.model_id}")
        print(f"    diarizes: {'yes' if engine.diarizes else 'no'}"
              f"   weights: ~{engine.approx_weights_gb} GB"
              f"   cached: {'yes' if cached else 'NO — will download'}")
        print(f"    {engine.notes}")
        print(f"    $ {' '.join(build_command(engine, audio, args.out_dir))}")

    print(f"\nTotal weights to download: ~{total_download:.1f} GB")

    busy = find_busy_processes()
    if busy:
        print("\nGPU courtesy check — large processes currently resident:")
        for line in busy:
            print(f"  {line}")
        print("  --run will refuse to start unless --force is passed.")
    else:
        print("\nGPU courtesy check: no large Python processes resident.")

    print("\nRe-run with --run to execute.")


def run_engine(engine: Engine, audio: Path, out_dir: Path) -> dict:
    """Execute one engine and return timing plus scoring inputs."""
    cmd = build_command(engine, audio, out_dir)
    print(f"\n[{engine.key}] {' '.join(cmd[:6])} ...")

    started = time.time()
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
    elapsed = time.time() - started

    if completed.returncode != 0:
        print(f"[{engine.key}] FAILED after {elapsed:.0f}s")
        print(completed.stderr[-1500:])
        return {"engine": engine.key, "ok": False, "seconds": elapsed,
                "error": completed.stderr[-1500:]}

    print(f"[{engine.key}] done in {elapsed:.0f}s")
    return {"engine": engine.key, "ok": True, "seconds": elapsed}


def audio_duration_seconds(audio: Path) -> float | None:
    """Probe audio duration with ffprobe."""
    try:
        output = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip()
        return float(output)
    except (subprocess.SubprocessError, ValueError, OSError):
        return None


def write_summary(results: list[dict], out_dir: Path) -> Path:
    """Write a markdown comparison table alongside the raw JSON results."""
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    header = (
        "| engine | ok | secs | RTF | words | domain terms | loops | markers | speakers | WER |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    rows = []
    for r in results:
        scores = r.get("scores", {})
        wer = scores.get("wer")
        rows.append(
            f"| {r['engine']} | {'y' if r.get('ok') else 'n'} "
            f"| {r.get('seconds', 0):.0f} "
            f"| {r.get('rtf', float('nan')):.3f} "
            f"| {scores.get('word_count', 0)} "
            f"| {scores.get('domain_terms_found', 0)}/{scores.get('domain_terms_total', 0)} "
            f"| {scores.get('repeated_8gram_loops', 0)} "
            f"| {len(scores.get('hallucination_markers', []))} "
            f"| {scores.get('distinct_speakers', 0)} "
            f"| {f'{wer:.3f}' if isinstance(wer, float) else '—'} |"
        )

    summary_path = out_dir / "summary.md"
    summary_path.write_text("# ASR bake-off results\n\n" + header + "\n".join(rows) + "\n")
    return summary_path


def main() -> int:
    """Entry point."""
    args = parse_args()
    engines = select_engines(args.engines)
    audio = resolve_audio(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.run:
        print_plan(engines, audio, args)
        return 0

    if not audio.exists():
        raise SystemExit(f"Audio not found: {audio}")

    busy = find_busy_processes()
    if busy and not args.force:
        print("Refusing to run — these processes look like active GPU work:")
        for line in busy:
            print(f"  {line}")
        print("Pass --force to override.")
        return 1

    clip = make_excerpt(audio, args.out_dir, args.offset_minutes, args.minutes)
    duration = audio_duration_seconds(clip)
    reference = args.reference.read_text() if args.reference else None

    results = []
    for engine in engines:
        result = run_engine(engine, clip, args.out_dir)
        if result.get("ok"):
            text, speakers = load_output_text(engine, clip, args.out_dir)
            result["scores"] = score_transcript(text, speakers, reference)
            if duration:
                result["rtf"] = result["seconds"] / duration
        results.append(result)

    summary_path = write_summary(results, args.out_dir)
    print(f"\nWrote {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
