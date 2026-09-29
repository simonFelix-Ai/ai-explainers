#!/usr/bin/env bash
# 渲染全部场景并合成完整视频 + SRT 字幕。
# 用法：./build.sh [l|m|h|k] [zh|en]   （默认 h = 1080p60，zh = 中文版）
set -euo pipefail
cd "$(dirname "$0")"
Q="${1:-h}"
LANG_CODE="${2:-zh}"
case "$LANG_CODE" in
  zh) MODULE=compression_is_routing;;
  en) MODULE=compression_is_routing_en;;
  *) echo "unknown language: $LANG_CODE" >&2; exit 1;;
esac
OUT="compression_is_routing.$LANG_CODE"
export CUE_DIR="$PWD/build/cues"
mkdir -p build "$CUE_DIR"

SCENES=$(python -c "from $MODULE import SCENES; print(' '.join(s.__name__ for s in SCENES))")
manim render -q"$Q" --media_dir build/media "$MODULE.py" $SCENES

case "$Q" in l) RES=480p15;; m) RES=720p30;; h) RES=1080p60;; k) RES=2160p60;; esac
VID_DIR="build/media/videos/$MODULE/$RES"
LIST="build/list.$LANG_CODE.txt"
: > "$LIST"
for s in $SCENES; do echo "file '$PWD/$VID_DIR/$s.mp4'" >> "$LIST"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$OUT.mp4"
python make_srt.py "$CUE_DIR" "$OUT.srt" "$MODULE"
echo "done -> $PWD/$OUT.mp4"
