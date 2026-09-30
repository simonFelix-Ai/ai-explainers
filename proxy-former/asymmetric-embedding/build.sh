#!/usr/bin/env bash
# Render every scene and assemble the video + SRT + chapters.
# Usage: ./build.sh [l|m|h|k] [zh|en]    (default: h = 1080p60, zh)
set -euo pipefail
cd "$(dirname "$0")"
Q="${1:-h}"
export PF_LANG="${2:-zh}"
export CUE_DIR="$PWD/build/cues"
MEDIA="build/media_$PF_LANG"
OUT="asym_embedding.$PF_LANG"

SCENES=$(python -c "from asym_embedding import SCENES; print(' '.join(s.__name__ for s in SCENES))")
manim render -q"$Q" --media_dir "$MEDIA" asym_embedding.py $SCENES

case "$Q" in l) RES=480p15;; m) RES=720p30;; h) RES=1080p60;; k) RES=2160p60;; esac
LIST="build/list.$PF_LANG.txt"
: > "$LIST"
for s in $SCENES; do echo "file '$PWD/$MEDIA/videos/asym_embedding/$RES/$s.mp4'" >> "$LIST"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$OUT.mp4"
python make_srt.py "$CUE_DIR/$PF_LANG" "$OUT.srt"
echo "done -> $PWD/$OUT.mp4"
