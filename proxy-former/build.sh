#!/usr/bin/env bash
# Render every scene and assemble the full video + SRT + chapters.
# Usage: ./build.sh [l|m|h|k] [zh|en]    (default: h = 1080p60, zh)
set -euo pipefail
cd "$(dirname "$0")"
Q="${1:-h}"
export PF_LANG="${2:-zh}"
export CUE_DIR="$PWD/build/cues"
MEDIA="build/media_$PF_LANG"
OUT="proxyformer.$PF_LANG"

SCENES=$(python -c "from proxyformer_video import SCENES; print(' '.join(s.__name__ for s in SCENES))")
manim render -q"$Q" --media_dir "$MEDIA" proxyformer_video.py $SCENES

case "$Q" in l) RES=480p15;; m) RES=720p30;; h) RES=1080p60;; k) RES=2160p60;; esac
LIST="build/list.$PF_LANG.txt"
: > "$LIST"
for s in $SCENES; do echo "file '$PWD/$MEDIA/videos/proxyformer_video/$RES/$s.mp4'" >> "$LIST"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$OUT.mp4"
python make_srt.py "$CUE_DIR/$PF_LANG" "$OUT.srt"
manim render -s -qh --media_dir "$MEDIA" proxyformer_video.py Thumbnail > /dev/null
ffmpeg -y -loglevel error -i "$(find "$MEDIA/images" -name 'Thumbnail*.png' | head -1)" -vf scale=1280:720 "thumbnail.$PF_LANG.png"
echo "done -> $PWD/$OUT.mp4"
