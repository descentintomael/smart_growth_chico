#!/usr/bin/env zsh
# Parallel download orchestrator for council-meeting-analyzer.
#
# Maintains N concurrent ffmpeg streams pulling Granicus HLS into MP3.
# Picks the next pending clip from meetings.db, marks it 'downloading',
# spawns ffmpeg, watches for completion, then marks 'downloaded' (or
# 'failed') and picks the next one. Honors a priority order so the
# most recent 2026 City Council meetings download first.
#
# Designed to run ON macstudio. Invoke as:
#   ./parallel-download-meetings.sh <concurrency>
# Defaults to concurrency=2 (caller should manually spawn the first 1-2
# downloads if any are already in flight).

set -uo pipefail

DB="$HOME/Projects/council-meeting-analyzer/data/meetings.db"
AUDIO_DIR="$HOME/Projects/council-meeting-analyzer/data/audio"
LOG_DIR="/tmp/parallel-dl-logs"
CONCURRENCY="${1:-2}"

# As of Aug 2026 archive-stream.granicus.com returns 403 Forbidden to ffmpeg's
# default User-Agent. A browser UA gets 200. Without this every download fails.
BROWSER_UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

mkdir -p "$LOG_DIR"

# Priority SQL: dated 2026 City Council meetings, newest first; then anything
# else in 'discovered' status.
PRIORITY_SQL="
SELECT clip_id, video_url
  FROM meetings
 WHERE status = 'discovered'
   AND video_url IS NOT NULL
   AND video_url <> ''
 ORDER BY
   CASE
     WHEN meeting_date >= '2026-01-01' AND meeting_type = 'City Council' THEN 0
     WHEN meeting_date >= '2025-12-01' AND meeting_type = 'City Council' THEN 1
     WHEN meeting_type = 'Special Meeting' AND meeting_date >= '2026-01-01' THEN 2
     ELSE 3
   END,
   meeting_date DESC NULLS LAST,
   clip_id DESC
"

claim_next() {
  # Atomically claim the next pending clip. Returns "clip_id|url" or empty.
  local row
  row=$(sqlite3 "$DB" "$PRIORITY_SQL LIMIT 1;")
  if [[ -z "$row" ]]; then
    return 1
  fi
  local clip_id="${row%%|*}"
  # Mark it 'downloading' before we spawn ffmpeg.
  sqlite3 "$DB" "UPDATE meetings SET status='downloading' WHERE clip_id=$clip_id AND status='discovered';"
  print -- "$row"
  return 0
}

start_download() {
  local clip_id="$1" url="$2"
  local out="$AUDIO_DIR/$clip_id.mp3"
  local log="$LOG_DIR/$clip_id.log"
  # Progress chatter goes to stderr: this function's stdout IS its return
  # value, and the caller reads only the first line of it.
  print -u2 -- ">> spawning ffmpeg for clip $clip_id -> $out"
  nohup ffmpeg -y -user_agent "$BROWSER_UA" -i "$url" \
    -vn -acodec libmp3lame -q:a 2 -map 0:a:0 \
    "$out" > "$log" 2>&1 &
  local pid=$!
  print -- "$clip_id $pid $out"
}

mark_done() {
  local clip_id="$1" out="$2"
  if [[ -s "$out" ]]; then
    sqlite3 "$DB" "UPDATE meetings SET status='downloaded' WHERE clip_id=$clip_id;"
    print -- "<< clip $clip_id downloaded ($(du -h "$out" | cut -f1))"
  else
    sqlite3 "$DB" "UPDATE meetings SET status='failed' WHERE clip_id=$clip_id;"
    print -- "<< clip $clip_id FAILED (empty file)"
  fi
}

# Track active downloads as parallel arrays:
#   active_clips[i] / active_pids[i] / active_paths[i]
typeset -a active_clips active_pids active_paths

# Seed concurrency. The caller is responsible for handling any pre-existing
# downloads they spawned (e.g. via run_download.py) — this orchestrator only
# claims clips that are still in 'discovered' status.
while (( ${#active_clips[@]} < CONCURRENCY )); do
  row=$(claim_next) || break
  read -r clip_id url <<<"${row//|/ }"
  result=$(start_download "$clip_id" "$url")
  # NB: never name a variable `path` here — in zsh it is tied to $PATH, so
  # assigning a filename to it wipes the command search path mid-run.
  read -r cid pid out_path <<<"$result"
  active_clips+=("$cid")
  active_pids+=("$pid")
  active_paths+=("$out_path")
done

# Main loop: when any active ffmpeg exits, mark it done and queue the next.
while (( ${#active_clips[@]} > 0 )); do
  # Poll once per 15 sec
  sleep 15
  local i=1
  while (( i <= ${#active_clips[@]} )); do
    pid=${active_pids[$i]}
    if ! kill -0 "$pid" 2>/dev/null; then
      # Process exited
      cid=${active_clips[$i]}
      out_path=${active_paths[$i]}
      mark_done "$cid" "$out_path"
      # Remove from arrays
      active_clips[$i]=()
      active_pids[$i]=()
      active_paths[$i]=()
      # Try to claim a new one
      if row=$(claim_next); then
        read -r new_cid new_url <<<"${row//|/ }"
        result=$(start_download "$new_cid" "$new_url")
        read -r new_cid2 new_pid new_path <<<"$result"
        active_clips+=("$new_cid2")
        active_pids+=("$new_pid")
        active_paths+=("$new_path")
      fi
    else
      ((i++))
    fi
  done
done

print -- "Queue drained. All downloads complete."
