"""
Composite text, film grade and soundtrack onto the three.js frames, and encode the teaser.

Usage:
  python post.py --frames frames_dir --out neural_sudoku_teaser.mp4 [--fps 30]
  python post.py --frames frames_dir --still 20.0 --png check.png

Edit the TITLE block below to set the project name, tagline and byline.
"""

import argparse
import glob
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- editable title card
TITLE = "NEURAL × DISCRETE"
SUBTITLE = "NEURAL NETWORKS FOR HARD DISCRETE PROBLEMS"
SUBTITLE_ZH = "神经网络 · 求解极难离散问题"
TAGLINE = "COMING SOON"
TAGLINE_ZH = "即将发布"
BYLINE = "Zhongpan Tang  ·  github.com/simonFelix-Ai"

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "web", "fonts")
FONTS = {
    "thin": os.path.join(FONT_DIR, "SourceSansPro-ExtraLight.ttf"),
    "light": os.path.join(FONT_DIR, "SourceSansPro-Light.ttf"),
    "rlight": os.path.join(FONT_DIR, "Roboto-Light.ttf"),
    "cjk": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
}
W, H = 1920, 1080
LETTERBOX = 64
DUR = 45.0

# (start, end, english, chinese, y, size)
CAPTIONS = [
    (0.15, 4.8, "THE WORLD'S HARDEST SUDOKU", "“世界最难数独”", 0.80, 50),
    (1.2, 4.8, "21 CLUES  ·  ONE ANSWER", "21 个提示数 · 唯一解", 0.905, 24),
    (5.4, 8.5, "CLASSIC SOLVERS SEARCH", "传统求解器：搜索", 0.84, 46),
    (8.8, 12.2, "BRANCH.  FAIL.  BACKTRACK.", "分支 · 失败 · 回溯", 0.84, 46),
    (12.7, 14.9, "WHAT IF A NEURAL NETWORK COULD REASON THROUGH IT?", "如果，神经网络能直接推理出答案？", 0.50, 44),
    (16.2, 21.4, "EVERY CELL HOLDS NINE POSSIBILITIES", "每一格，九种可能", 0.84, 44),
    (22.4, 27.6, "UNCERTAINTY HARDENS INTO CERTAINTY", "不确定，逐渐凝结为确定", 0.84, 44),
    (28.4, 32.2, "CONTINUOUS THOUGHT.  DISCRETE ANSWER.", "连续的思考，离散的答案", 0.84, 44),
    (33.0, 37.3, "EVERY ROW  ·  EVERY COLUMN  ·  EVERY BOX", "每一行 · 每一列 · 每一宫", 0.84, 40),
]


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def window(t, a, b, fi=0.5, fo=0.5):
    if t < a or t > b:
        return 0.0
    return min(smooth((t - a) / fi), smooth((b - t) / fo))


@lru_cache(maxsize=256)
def mask(s, font, size, tracking):
    path = FONTS[font]
    f = ImageFont.truetype(path, size, index=2) if path.endswith(".ttc") else ImageFont.truetype(path, size)
    widths = [f.getlength(ch) for ch in s]
    extra = tracking * size
    w = int(sum(widths) + extra * max(0, len(s) - 1)) + 8
    asc, desc = f.getmetrics()
    img = Image.new("L", (max(w, 1), asc + desc + 8), 0)
    d = ImageDraw.Draw(img)
    x = 4.0
    for ch, cw in zip(s, widths):
        d.text((x, 4), ch, font=f, fill=255)
        x += cw + extra
    return np.asarray(img, np.float32) / 255.0


def put(layer, s, x, y, size, font="light", col=(1, 1, 1), alpha=1.0, tracking=0.0):
    if alpha <= 0.003 or not s:
        return
    m = mask(s, font, int(size), float(tracking))
    h, w = m.shape
    x0, y0 = int(x - w / 2), int(y - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb > xa and yb > ya:
        layer[ya:yb, xa:xb] += m[ya - y0:yb - y0, xa - x0:xb - x0, None] * np.array(col, np.float32) * alpha


def text_layer(t):
    L = np.zeros((H, W, 3), np.float32)
    for a, b, en, zh, y, size in CAPTIONS:
        al = window(t, a, b, 0.5, 0.45)
        if al <= 0:
            continue
        put(L, en, W / 2, H * y, size, "thin" if size >= 40 else "light", (1, 1, 1), al, 0.22 if size < 50 else 0.26)
        put(L, zh, W / 2, H * y + size * 1.05, max(20, int(size * 0.55)), "cjk", (0.75, 0.82, 0.95), al, 0.15)
    # title card
    a = smooth((t - 38.2) / 0.9) * (1 - smooth((t - 44.0) / 0.9))
    if a > 0:
        put(L, TITLE, W / 2, H * 0.36, 118, "thin", (1, 1, 1), a, 0.2)
        put(L, SUBTITLE, W / 2, H * 0.47, 28, "light", (0.85, 0.88, 0.95), a, 0.35)
        put(L, SUBTITLE_ZH, W / 2, H * 0.515, 24, "cjk", (0.7, 0.75, 0.85), a, 0.2)
    b = smooth((t - 39.6) / 0.8) * (1 - smooth((t - 44.0) / 0.9))
    if b > 0:
        put(L, TAGLINE, W / 2, H * 0.64, 44, "light", (1.0, 0.78, 0.35), b, 0.6)
        put(L, TAGLINE_ZH, W / 2, H * 0.69, 26, "cjk", (1.0, 0.8, 0.45), b, 0.5)
        put(L, BYLINE, W / 2, H * 0.85, 22, "rlight", (0.7, 0.72, 0.8), b, 0.08)
    return L


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.5).clip(0.3, 1)[..., None]
del yy, xx


def composite(args):
    path, t, idx = args
    img = cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255.0
    tl = text_layer(t)
    if tl.any():
        lum = tl.max(axis=2)
        shade = cv2.GaussianBlur(cv2.dilate(lum, np.ones((9, 9), np.uint8)), (0, 0), 22)
        img *= (1 - 0.72 * np.clip(shade * 1.6, 0, 1))[..., None]  # soft dark backdrop for legibility
        glow = cv2.GaussianBlur(tl, (0, 0), 6) * 0.55
        img = 1 - (1 - img) * (1 - np.clip(tl * 0.95 + glow, 0, 1))  # screen blend
    img *= VIGNETTE
    g = np.random.default_rng(idx).standard_normal((H // 2, W // 2)).astype(np.float32)
    img += cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.012
    out = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    out[:LETTERBOX] = 0
    out[H - LETTERBOX:] = 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", default="neural_sudoku_teaser.mp4")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--png", default="check.png")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.frames, "f_*.jpg")) + glob.glob(os.path.join(a.frames, "f_*.png")))
    fidx = [int(os.path.basename(f)[2:7]) for f in files]
    if a.still is not None:
        k = min(range(len(files)), key=lambda i: abs(fidx[i] / a.fps - a.still))
        cv2.imwrite(a.png, composite((files[k], fidx[k] / a.fps, fidx[k]))[..., ::-1])
        print("wrote", a.png)
        return
    wav = os.path.splitext(a.out)[0] + ".wav"
    subprocess.run([sys.executable, os.path.join(HERE, "music.py"), wav], check=True)
    t0 = fidx[0] / a.fps
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(a.fps), "-i", "-", "-ss", str(t0), "-i", wav, "-c:v", "libx264", "-preset", "slow",
           "-crf", "18", "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
           "-shortest", "-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for fr in pool.imap(composite, [(f, i / a.fps, i) for f, i in zip(files, fidx)], chunksize=4):
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
