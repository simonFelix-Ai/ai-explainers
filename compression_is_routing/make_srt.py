"""把各场景导出的字幕时间轴合并为一份 SRT（可用于后期配音/外挂字幕）。"""
import importlib
import json
import os
import sys

cue_dir = sys.argv[1]
out = sys.argv[2]
module = importlib.import_module(sys.argv[3] if len(sys.argv) > 3 else "compression_is_routing")
SCENES = module.SCENES
CHAPTERS = getattr(module, "CHAPTERS", {})


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


offset, idx, lines, chapters = 0.0, 1, [], []
for sc in SCENES:
    if sc.__name__ in CHAPTERS:
        m, sec = divmod(int(offset), 60)
        chapters.append(f"{m}:{sec:02d} {CHAPTERS[sc.__name__]}")
    with open(os.path.join(cue_dir, f"{sc.__name__}.json"), encoding="utf-8") as f:
        data = json.load(f)
    for t0, t1, text in data["cues"]:
        lines.append(f"{idx}\n{ts(offset + t0)} --> {ts(offset + t1)}\n{text}\n")
        idx += 1
    offset += data["duration"]

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
if chapters:
    with open(os.path.splitext(out)[0] + ".chapters.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(chapters) + "\n")
print(f"{idx - 1} cues, total {offset:.1f}s -> {out}")
