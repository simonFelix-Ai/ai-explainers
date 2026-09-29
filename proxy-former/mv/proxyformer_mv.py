"""
ProxyFormer -- cinematic music video (procedural, no external assets besides open fonts).

A small particle renderer built on numpy + OpenCV: additive light splatting,
a perspective camera, multi-scale bloom, filmic tone mapping, vignette, grain,
letterbox and glitch. Every frame is a pure function of time, so frames render
in parallel and pipe straight into ffmpeg. The timeline is locked to the
soundtrack in music.py (100 BPM, one bar = 2.4 s).

Usage:
  python proxyformer_mv.py --out mv.mp4 [--fps 30] [--start 0 --end 72] [--scale 1.0]
  python proxyformer_mv.py --still 25.0 --png frame.png
"""

import argparse
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
CJK_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

W, H = 1920, 1080
CX, CY = W / 2, H / 2
DUR = 72.0
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT

# palette (linear-ish light values)
CYAN = np.array([0.25, 0.75, 1.0], np.float32)
BLUE = np.array([0.20, 0.45, 1.0], np.float32)
GOLD = np.array([1.0, 0.72, 0.28], np.float32)
WHITE = np.array([1.0, 1.0, 1.0], np.float32)
RED = np.array([1.0, 0.18, 0.12], np.float32)
MAGENTA = np.array([0.95, 0.25, 0.8], np.float32)
GREEN = np.array([0.35, 1.0, 0.55], np.float32)

SECTIONS = [  # (start, end, name)
    (0.0, 9.6, "river"),
    (9.6, 19.2, "web"),
    (19.2, 21.6, "question"),
    (21.6, 31.2, "proxy"),
    (31.2, 40.8, "layers"),
    (40.8, 52.8, "numbers"),
    (52.8, 60.0, "galaxy"),
    (60.0, 72.0, "title"),
]


# ------------------------------------------------------------------ easing / timing

def clamp01(x):
    return min(max(x, 0.0), 1.0)


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp01(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def window(t, a, b, fi=0.5, fo=0.5):
    """Fade in over [a, a+fi], hold, fade out over [b-fo, b]."""
    if t < a or t > b:
        return 0.0
    return min(smooth((t - a) / fi) if fi > 0 else 1.0, smooth((b - t) / fo) if fo > 0 else 1.0)


def kick_pulse(t, t0, t1, decay=0.16):
    """Decaying pulse on every beat between t0 and t1 (synced with the kick)."""
    if t < t0 or t > t1:
        return 0.0
    return math.exp(-((t - t0) % BEAT) / decay)


# ------------------------------------------------------------------ static assets (same seed in every worker)

RNG = np.random.default_rng(2608)


def _nebula():
    h, w = H // 8, (W + 400) // 8
    field = np.zeros((h, w, 3), np.float32)
    for sigma, col, amp in [(18, np.array([0.05, 0.12, 0.28]), 1.0), (9, np.array([0.18, 0.06, 0.22]), 0.7),
                            (30, np.array([0.02, 0.10, 0.14]), 1.0)]:
        n = cv2.GaussianBlur(RNG.standard_normal((h, w)).astype(np.float32), (0, 0), sigma)
        n = np.clip((n - n.mean()) / (n.std() + 1e-6), 0, None)
        field += n[..., None] * col[None, None, :] * amp
    field = cv2.resize(field, (W + 400, H), interpolation=cv2.INTER_CUBIC)
    return field * 0.35


NEBULA = _nebula()
STARS = np.column_stack([RNG.uniform(0, W + 400, 2200), RNG.uniform(0, H, 2200)]).astype(np.float32)
STAR_B = RNG.uniform(0.05, 0.5, 2200).astype(np.float32) ** 2 * 2.0
STAR_PH = RNG.uniform(0, 2 * np.pi, 2200).astype(np.float32)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.55 * (((xx - CX) / CX) ** 2 + ((yy - CY) / CY) ** 2) ** 1.4).clip(0.25, 1)[..., None]
del yy, xx
LETTERBOX = 64


# ------------------------------------------------------------------ drawing primitives

def splat(buf, x, y, col, inten=1.0):
    """Additive bilinear splat of points (x, y) with colors col (N,3) or (3,), intensity per point."""
    x = np.asarray(x, np.float32)
    y = np.asarray(y, np.float32)
    inten = np.broadcast_to(np.asarray(inten, np.float32), x.shape)
    m = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1) & (inten > 1e-4)
    if not m.any():
        return
    x, y, inten = x[m], y[m], inten[m]
    col = np.asarray(col, np.float32)
    col = col[m] if col.ndim == 2 else np.broadcast_to(col, (x.size, 3))
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    idx = np.concatenate([y0 * W + x0, y0 * W + x0 + 1, (y0 + 1) * W + x0, (y0 + 1) * W + x0 + 1])
    wts = np.concatenate([(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy]) * np.tile(inten, 4)
    flat = buf.reshape(-1, 3)
    for c in range(3):
        cw = wts * np.tile(col[:, c], 4)
        flat[:, c] += np.bincount(idx, weights=cw, minlength=W * H).astype(np.float32)


@lru_cache(maxsize=64)
def _gauss_stamp(r):
    s = int(math.ceil(r * 3))
    g = np.exp(-((np.arange(-s, s + 1)[:, None] ** 2 + np.arange(-s, s + 1)[None, :] ** 2) / (2 * r * r)))
    return g.astype(np.float32)


def stamp(buf, x, y, r, col, inten=1.0):
    """Soft gaussian sprite (for big glowing stars / proxies)."""
    r = max(0.6, round(float(r) * 2) / 2)
    g = _gauss_stamp(r)
    s = g.shape[0] // 2
    xi, yi = int(round(x)), int(round(y))
    x0, x1, y0, y1 = xi - s, xi + s + 1, yi - s, yi + s + 1
    gx0, gy0 = max(0, -x0), max(0, -y0)
    gx1, gy1 = g.shape[1] - max(0, x1 - W), g.shape[0] - max(0, y1 - H)
    if gx1 <= gx0 or gy1 <= gy0:
        return
    buf[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] += \
        g[gy0:gy1, gx0:gx1, None] * (np.asarray(col, np.float32) * inten)[None, None, :]


def draw_lines(buf, segs, col, inten, thickness=1):
    """Antialiased lines. segs: list/array of (x0, y0, x1, y1). Drawn on an 8-bit mask then added."""
    if len(segs) == 0 or inten <= 0:
        return
    mask = np.zeros((H, W), np.uint8)
    pts = [np.array([[[a, b]], [[c, d]]], np.int32) for a, b, c, d in np.asarray(segs) * 1]
    cv2.polylines(mask, pts, False, 255, thickness, cv2.LINE_AA)
    buf += (mask.astype(np.float32) / 255.0)[..., None] * (np.asarray(col, np.float32) * inten)


def draw_polyline(buf, pts_list, col, inten, thickness=1):
    if not pts_list or inten <= 0:
        return
    mask = np.zeros((H, W), np.uint8)
    cv2.polylines(mask, [np.asarray(p, np.int32).reshape(-1, 1, 2) for p in pts_list], False, 255, thickness,
                  cv2.LINE_AA)
    buf += (mask.astype(np.float32) / 255.0)[..., None] * (np.asarray(col, np.float32) * inten)


def rect_outline(buf, x0, y0, x1, y1, col, inten, thickness=2):
    mask = np.zeros((H, W), np.uint8)
    cv2.rectangle(mask, (int(x0), int(y0)), (int(x1), int(y1)), 255, thickness, cv2.LINE_AA)
    buf += (mask.astype(np.float32) / 255.0)[..., None] * (np.asarray(col, np.float32) * inten)


def rect_border(buf, x0, y0, x1, y1, col, inten, th=1):
    """Thin rectangle border via four strip fills (no full-frame mask)."""
    rect_fill(buf, x0, y0, x1, y0 + th, col, inten)
    rect_fill(buf, x0, y1 - th, x1, y1, col, inten)
    rect_fill(buf, x0, y0, x0 + th, y1, col, inten)
    rect_fill(buf, x1 - th, y0, x1, y1, col, inten)


def rect_fill(buf, x0, y0, x1, y1, col, inten):
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
    if x1 > x0 and y1 > y0:
        buf[y0:y1, x0:x1] += np.asarray(col, np.float32) * inten


# ------------------------------------------------------------------ text

FONTS = {
    "thin": os.path.join(FONT_DIR, "SourceSansPro-ExtraLight.ttf"),
    "light": os.path.join(FONT_DIR, "SourceSansPro-Light.ttf"),
    "semi": os.path.join(FONT_DIR, "SourceSansPro-Semibold.ttf"),
    "rthin": os.path.join(FONT_DIR, "Roboto-Thin.ttf"),
    "rlight": os.path.join(FONT_DIR, "Roboto-Light.ttf"),
    "cjk": CJK_FONT,
}


@lru_cache(maxsize=512)
def text_mask(s, font="light", size=48, tracking=0.0):
    """Render text to a float mask [0,1]. tracking is extra spacing in em."""
    path = FONTS[font]
    f = ImageFont.truetype(path, size, index=2) if path.endswith(".ttc") else ImageFont.truetype(path, size)
    widths = [f.getlength(ch) for ch in s]
    extra = tracking * size
    total = int(sum(widths) + extra * max(0, len(s) - 1)) + 8
    asc, desc = f.getmetrics()
    img = Image.new("L", (max(total, 1), asc + desc + 8), 0)
    d = ImageDraw.Draw(img)
    x = 4.0
    for ch, w in zip(s, widths):
        d.text((x, 4), ch, font=f, fill=255)
        x += w + extra
    return np.asarray(img, np.float32) / 255.0


def text(buf, s, x, y, size=48, font="light", col=WHITE, alpha=1.0, tracking=0.0, inten=1.2, anchor="c",
         sweep=None):
    """Composite text centred (anchor c), left (l) or right (r) at (x, y)."""
    if alpha <= 0.003 or not s:
        return
    m = text_mask(s, font, int(size), float(tracking))
    h, w = m.shape
    x0 = int(x - (w / 2 if anchor == "c" else (0 if anchor == "l" else w)))
    y0 = int(y - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return
    sub = m[ya - y0:yb - y0, xa - x0:xb - x0]
    gain = alpha * inten
    region = buf[ya:yb, xa:xb]
    if sweep is not None:  # moving light band across the text
        cols = np.arange(xa, xb, dtype=np.float32)
        band = 1 + 2.2 * np.exp(-((cols - sweep) / 70.0) ** 2)
        region += sub[..., None] * band[None, :, None] * (np.asarray(col, np.float32) * gain)
    else:
        region += sub[..., None] * (np.asarray(col, np.float32) * gain)


def fmt(n):
    return f"{int(n):,}"


# ------------------------------------------------------------------ camera

def project(P, cam, f=900.0, yaw=0.0, pitch=0.0):
    """Perspective projection. P (N,3) world; returns x, y, z (camera-space depth)."""
    Q = P - cam
    if yaw:
        c, s = math.cos(yaw), math.sin(yaw)
        Q = np.column_stack([c * Q[:, 0] - s * Q[:, 2], Q[:, 1], s * Q[:, 0] + c * Q[:, 2]])
    if pitch:
        c, s = math.cos(pitch), math.sin(pitch)
        Q = np.column_stack([Q[:, 0], c * Q[:, 1] - s * Q[:, 2], s * Q[:, 1] + c * Q[:, 2]])
    z = Q[:, 2]
    zs = np.where(z > 1e-3, z, 1e-3)
    return f * Q[:, 0] / zs + CX, -f * Q[:, 1] / zs + CY, z


# ------------------------------------------------------------------ background

def background(buf, t, amount=1.0, drift=0.0):
    if amount <= 0:
        return
    off = int((t * 6 + drift) % 400)
    buf += NEBULA[:, off:off + W] * (amount * 0.3)
    sx = (STARS[:, 0] - off) % (W + 400)
    tw = 0.6 + 0.4 * np.sin(STAR_PH + t * 2.3)
    splat(buf, sx, STARS[:, 1], np.array([0.8, 0.85, 1.0], np.float32), STAR_B * tw * amount)


# ================================================================== scenes
# Each scene draws into buf (float32 HxWx3) for global time t and local time lt.

RIV_N = 7000
_rz = RNG.uniform(0, 700, RIV_N).astype(np.float32)
_rang = RNG.uniform(0, 2 * np.pi, RIV_N).astype(np.float32)
_rrad = np.abs(RNG.normal(0, 1, RIV_N)).astype(np.float32) * 16
_rcol = (CYAN[None, :] * RNG.uniform(0.6, 1.0, (RIV_N, 1)) + WHITE[None, :] * RNG.uniform(0, 0.35, (RIV_N, 1))
         ).astype(np.float32)
_rb = RNG.uniform(0.5, 1.4, RIV_N).astype(np.float32)


def river_path(z):
    return 70 * np.sin(z * 0.011), 28 * np.sin(z * 0.019 + 1.0)


def river_points():
    px, py = river_path(_rz)
    return np.column_stack([px + _rrad * np.cos(_rang), py + _rrad * np.sin(_rang), _rz])


RIVER = river_points()


def cam_river(t):
    z = -80 + 260 * (1 - math.exp(-t / 2.6))
    px, py = river_path(np.array([z + 60]))
    return np.array([px[0] * 0.7, py[0] * 0.7 + 14, z], np.float32)


def s_river(buf, t, lt):
    background(buf, t, 0.8)
    for k in range(4):  # motion-blur samples along the camera path
        tc = max(0.0, lt - k * 0.012)
        x, y, z = project(RIVER, cam_river(tc), f=820)
        vis = z > 2
        depth = np.where(vis, z, 1)
        inten = _rb * np.clip(50 / depth, 0, 3.5) * np.exp(-depth / 420) * (1.0 - 0.18 * k)
        splat(buf, x[vis], y[vis], _rcol[vis], inten[vis] * 3.6)
    a = window(lt, 2.0, 8.6, 0.9, 0.8)
    text(buf, "EVERY TOKEN WANTS TO SEE EVERY OTHER TOKEN", CX, H * 0.78, 44, "thin", WHITE, a, 0.22, 1.4)
    text(buf, "每一个 token，都想看见其他所有 token", CX, H * 0.78 + 58, 26, "cjk", np.array([0.7, 0.8, 0.95]), a,
         0.12, 1.1)


WEB_MAX = 170
_wi, _wj = np.triu_indices(WEB_MAX, 1)


def s_web(buf, t, lt):
    background(buf, t, 0.5)
    p = lt / 9.6
    n = int(10 + (WEB_MAX - 10) * smooth(lt / 7.2) ** 1.25)
    ang = 2 * np.pi * np.arange(n) / n + lt * 0.06
    shake = 0.0 if lt < 6.0 else (lt - 6.0) * 3.2
    jx, jy = (RNG.standard_normal(2) * shake) if shake else (0, 0)
    R = 360 + 12 * math.sin(lt * 1.7)
    px = CX + jx + R * np.cos(ang)
    py = CY - 30 + jy + R * np.sin(ang) * 0.92
    sel = (_wi < n) & (_wj < n)
    total = int(sel.sum())
    stride = max(1, math.ceil(total / 2400))  # a stable subset keeps the woven texture visible
    sel &= ((_wi * 7919 + _wj * 104729) % stride) == 0
    segs = np.column_stack([px[_wi[sel]], py[_wi[sel]], px[_wj[sel]], py[_wj[sel]]])
    col = CYAN * (1 - smooth(p * 1.6)) + MAGENTA * smooth(p * 1.6) * (1 - smooth((p - 0.55) * 3)) \
        + RED * smooth((p - 0.55) * 3)
    li = 0.16 + 0.3 * smooth(p * 1.3)
    for part in np.array_split(segs, max(1, min(3, len(segs) // 700))):
        draw_lines(buf, part, col, li)
    for i in range(n):
        stamp(buf, px[i], py[i], 2.2, WHITE * 0.6 + col * 0.4, 1.6)
    # counters: real sequence scale grows to 2^20 tokens, pairs = tokens^2
    toks = 2 ** (10 + 10 * smooth(lt / 8.4))
    toks = 1048576 if lt >= 8.4 else toks
    a = window(lt, 0.8, 9.2, 0.6, 0.2)
    text(buf, "TOKENS", CX - 420, H * 0.83, 22, "light", GREY(0.7), a, 0.3, 1.0, "l")
    text(buf, fmt(toks), CX - 420, H * 0.83 + 40, 44, "rthin", WHITE, a, 0.02, 1.4, "l")
    text(buf, "PAIRS TO COMPUTE", CX + 420, H * 0.83, 22, "light", GREY(0.7), a, 0.3, 1.0, "r")
    text(buf, fmt(toks * toks), CX + 420, H * 0.83 + 40, 44, "rthin", col * 0.6 + WHITE * 0.4, a, 0.02, 1.6, "r")
    text(buf, "O(N²)", CX, CY - 30, 120, "rthin", WHITE, window(lt, 3.0, 8.4, 1.0, 0.4) * 0.55, 0.05, 1.2)
    if lt >= 8.6:
        flick = 1.0 if int(lt * 30) % 3 else 0.35
        text(buf, "OUT OF MEMORY", CX, CY - 30, 120, "semi", RED, flick, 0.08, 2.4)


def GREY(v):
    return np.array([v, v, v], np.float32)


def s_question(buf, t, lt):
    background(buf, t, 0.35)
    a = window(lt, 0.25, 2.25, 0.6, 0.3)
    text(buf, "WHAT IF ONLY THE REPRESENTATIVES SPOKE?", CX, CY - 10, 50, "thin", WHITE, a, 0.22, 1.4)
    text(buf, "如果，只让代表们对话？", CX, CY + 56, 28, "cjk", np.array([0.75, 0.8, 0.95]), a, 0.2, 1.1)
    g = smooth((lt - 1.6) / 0.8)  # a point of light gathers before the drop
    if g > 0:
        stamp(buf, CX, CY + 170, 2 + 6 * g, GOLD, 3.0 * g)


K_CH, M_TOK = 16, 150
_cx = np.linspace(-780, 780, K_CH).astype(np.float32)
_tx = (np.repeat(_cx, M_TOK) + RNG.normal(0, 20, K_CH * M_TOK)).astype(np.float32)
_ty = (175 + RNG.normal(0, 24, K_CH * M_TOK)).astype(np.float32)
_tgrp = np.repeat(np.arange(K_CH), M_TOK)
_tdel = RNG.uniform(0, 1.2, K_CH * M_TOK).astype(np.float32)
_tside = RNG.uniform(-1, 1, K_CH * M_TOK).astype(np.float32)
_tb = RNG.uniform(0.6, 1.3, K_CH * M_TOK).astype(np.float32)
PROXY_Y = -175
_pi, _pj = np.triu_indices(K_CH, 1)


def _bezier(p0, p1, p2, s):
    s = s[:, None] if np.ndim(s) else s
    return (1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s * s * p2


def s_proxy(buf, t, lt):
    background(buf, t, 0.45)
    kp = kick_pulse(lt, 0.0, 9.6)
    # tokens: burst from the centre into 16 chunks, then persist (the local stream)
    burst = ease_out(lt / 1.3)
    wob = 3 * np.sin(lt * 2 + _tdel * 9)
    tx = CX + _tx * burst
    ty = CY + 170 * (1 - burst) + (_ty + wob) * burst
    tint = smooth((lt - 7.6) / 1.5)
    tcol = CYAN[None, :] * (1 - tint) + (GOLD * 0.6 + WHITE * 0.4)[None, :] * tint
    splat(buf, tx, ty, np.broadcast_to(tcol, (tx.size, 3)), _tb * (2.0 + 0.9 * kp))
    # compression streams: token -> proxy (bars 2), inject streams proxy -> token (bar 4)
    for phase, t0, rev in ((0, 2.4, False), (1, 7.2, True)):
        s = (lt - t0 - _tdel) / 1.0
        act = (s > 0) & (s < 1)
        if act.any():
            p0 = np.column_stack([tx[act], ty[act]])
            p2 = np.column_stack([CX + _cx[_tgrp[act]], np.full(act.sum(), CY + PROXY_Y)])
            if rev:
                p0, p2 = p2, p0
            ctrl = (p0 + p2) / 2 + np.column_stack([_tside[act] * 110, np.zeros(act.sum())])
            for k in range(4):
                sk = np.clip(s[act] - k * 0.025, 0, 1)
                pos = _bezier(p0, ctrl, p2, ease_io_arr(sk))
                splat(buf, pos[:, 0], pos[:, 1], GOLD if not rev else GOLD * 0.7 + WHITE * 0.3,
                      (1.1 - 0.22 * k) * np.sin(np.pi * sk) + 0.05)
    # proxies
    pb = smooth((lt - 2.8) / 1.8)
    if pb > 0:
        for k in range(K_CH):
            x, y = CX + _cx[k], CY + PROXY_Y
            stamp(buf, x, y, 3.0 + 1.5 * kp, WHITE * 0.5 + GOLD * 0.5, 4.0 * pb)
            stamp(buf, x, y, 14, GOLD, 0.35 * pb * (1 + kp))
    # proxy-to-proxy arcs grow in by distance (bar 3), then stay
    if lt > 4.8:
        pts = []
        for a, b in zip(_pi, _pj):
            d = abs(b - a)
            f = clamp01((lt - 4.8 - d * 0.1) / 0.8)
            if f <= 0:
                continue
            p0 = np.array([CX + _cx[a], CY + PROXY_Y])
            p2 = np.array([CX + _cx[b], CY + PROXY_Y])
            p1 = (p0 + p2) / 2 - np.array([0, 28 * d])
            ss = np.linspace(0, f, max(3, int(30 * f)))
            pts.append(_bezier(p0, p1, p2, ss))
        draw_polyline(buf, pts, GOLD, 0.32 * (1 + 0.8 * kp))
    for word, zh, a0 in (("COMPRESS", "压缩", 2.4), ("CONNECT", "交互", 4.8), ("INJECT", "注入", 7.2)):
        a = window(lt, a0 + 0.05, a0 + 2.35, 0.25, 0.35)
        text(buf, word, CX, H * 0.855, 54, "thin", WHITE, a, 0.45, 1.6)
        text(buf, zh, CX, H * 0.855 + 54, 26, "cjk", np.array([0.95, 0.8, 0.55]), a, 0.6, 1.0)


def ease_io_arr(x):
    x = np.clip(x, 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * x)


N_LAYERS, N_COLS = 8, 40
LAYER_DZ = 90.0
_lx = np.linspace(-260, 260, N_COLS).astype(np.float32)
_prox_x = np.linspace(-208, 208, 5).astype(np.float32)


def s_layers(buf, t, lt):
    background(buf, t, 0.4)
    kp = kick_pulse(lt, 0.0, 9.6)
    cz = -170 + (N_LAYERS * LAYER_DZ - 40) * ease_io(lt / 9.6)
    cam = np.array([35 * math.sin(lt * 0.5), 18 + 10 * math.sin(lt * 0.33), cz], np.float32)
    yaw = 0.06 * math.sin(lt * 0.4)
    tok_pts, prox_pts, segs_up, segs_dn, segs_loc = [], [], [], [], []
    for k in range(N_LAYERS):
        z = k * LAYER_DZ
        for r in range(3):
            tok_pts.append(np.column_stack([_lx, np.full(N_COLS, -48.0 - 9 * r), np.full(N_COLS, z)]))
        prox_pts.append(np.column_stack([_prox_x, np.full(5, 55.0), np.full(5, z + 45)]))
    T = np.concatenate(tok_pts)
    P = np.concatenate(prox_pts)
    tx, ty, tz = project(T, cam, 900, yaw)
    px, py, pz = project(P, cam, 900, yaw)
    tv = tz > 5
    fade_t = np.exp(-np.maximum(tz, 1) / 520) * np.clip((tz - 5) / 40, 0, 1)
    splat(buf, tx[tv], ty[tv], CYAN, (fade_t * 4.0 * np.clip(300 / np.maximum(tz, 1), 0.6, 3) * (1 + 0.4 * kp))[tv])
    # beams: layer tokens (row 0) -> proxies -> next layer tokens; local stream straight through
    for k in range(N_LAYERS):
        base = k * 3 * N_COLS
        pb = k * 5
        for i in range(0, N_COLS, 2):
            g = pb + min(4, i * 5 // N_COLS)
            if tz[base + i] > 5 and pz[g] > 5:
                segs_up.append((tx[base + i], ty[base + i], px[g], py[g], min(tz[base + i], pz[g])))
            if k + 1 < N_LAYERS:
                nb = (k + 1) * 3 * N_COLS
                if pz[g] > 5 and tz[nb + i] > 5:
                    segs_dn.append((px[g], py[g], tx[nb + i], ty[nb + i], min(pz[g], tz[nb + i])))
                if tz[base + i] > 5 and tz[nb + i] > 5:
                    segs_loc.append((tx[base + i], ty[base + i], tx[nb + i], ty[nb + i], tz[base + i]))
    for segs, col, g in ((segs_up, CYAN * 0.5 + GOLD * 0.5, 0.35), (segs_dn, GOLD, 0.30), (segs_loc, BLUE, 0.22)):
        if not segs:
            continue
        arr = np.array(segs)
        for lo, hi, f in ((0, 200, 1.0), (200, 450, 0.55), (450, 1e9, 0.25)):
            m = (arr[:, 4] >= lo) & (arr[:, 4] < hi)
            if m.any():
                draw_lines(buf, arr[m, :4], col, g * f * (1 + 0.5 * kp))
    pv = pz > 5
    for i in np.where(pv)[0]:
        f = math.exp(-pz[i] / 520) * clamp01((pz[i] - 5) / 40)
        stamp(buf, px[i], py[i], max(1.5, 900 / max(pz[i], 1) * 0.9), WHITE * 0.4 + GOLD * 0.6, 3.5 * f * (1 + kp))
    # packets of light travelling up (compress) and down (inject) on the beat
    ph = (lt % BEAT) / BEAT
    if segs_up:
        a = np.array(segs_up)
        splat(buf, a[:, 0] + (a[:, 2] - a[:, 0]) * ph, a[:, 1] + (a[:, 3] - a[:, 1]) * ph, WHITE,
              2.0 * np.exp(-a[:, 4] / 400))
    if segs_dn:
        a = np.array(segs_dn)
        splat(buf, a[:, 0] + (a[:, 2] - a[:, 0]) * ph, a[:, 1] + (a[:, 3] - a[:, 1]) * ph, GOLD,
              2.0 * np.exp(-a[:, 4] / 400))
    a1 = window(lt, 0.6, 4.6, 0.5, 0.5)
    a2 = window(lt, 5.4, 9.3, 0.5, 0.5)
    text(buf, "MICRO GUIDES MACRO", CX, H * 0.84, 50, "thin", WHITE, a1, 0.4, 1.5)
    text(buf, "微观指导宏观 · 局部汇聚成代理", CX, H * 0.84 + 52, 26, "cjk", np.array([0.7, 0.85, 1.0]), a1, 0.2, 1.0)
    text(buf, "MACRO GUIDES MICRO", CX, H * 0.84, 50, "thin", WHITE, a2, 0.4, 1.5)
    text(buf, "宏观指导微观 · 全局视野注入回每一个 token", CX, H * 0.84 + 52, 26, "cjk", np.array([1.0, 0.85, 0.6]),
         a2, 0.2, 1.0)


NIAH_64K = [
    [.93, .98, .99, .99, 1.00, 1.00, 1.00, .99, .94],
    [.94, .98, .99, 1.00, 1.00, 1.00, 1.00, .99, .95],
    [.93, .98, .99, 1.00, 1.00, 1.00, 1.00, .98, .94],
    [.95, .98, .99, .99, 1.00, 1.00, 1.00, .99, .92],
    [.89, .98, .99, .99, 1.00, 1.00, 1.00, 1.00, .95],
    [.89, .98, 1.00, 1.00, .99, 1.00, 1.00, .98, .94],
    [.92, .97, .99, 1.00, 1.00, 1.00, 1.00, .99, .92],
    [.93, .98, 1.00, 1.00, 1.00, 1.00, .99, .98, .93],
    [.93, .98, 1.00, 1.00, 1.00, 1.00, 1.00, .99, .93],
    [.94, .99, 1.00, 1.00, 1.00, 1.00, 1.00, .99, .93],
]
LENGTHS = ["4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M"]


def heat(v):
    # dark red -> amber -> green -> bright cyan-green at 1.0, tuned for glow
    stops = [(0.85, np.array([1.0, 0.35, 0.15])), (0.93, np.array([1.0, 0.8, 0.25])),
             (0.97, np.array([0.45, 1.0, 0.45])), (1.0, np.array([0.3, 1.0, 0.75]))]
    if v <= stops[0][0]:
        return stops[0][1]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            return ca + (cb - ca) * (v - a) / (b - a)
    return stops[-1][1]


def s_numbers(buf, t, lt):
    background(buf, t, 0.35)
    kp = kick_pulse(lt, 0.0, 12.0)
    bar_i = int(lt // BAR)
    bl = lt - bar_i * BAR
    if bar_i <= 1:  # GPU capacity bar: full attention OOM, then ProxyFormer
        x0, x1, y0, y1 = CX - 620, CX + 620, CY - 26, CY + 26
        text(buf, "ONE 16 GB GPU", CX, CY - 110, 40, "thin", WHITE, 1.0, 0.45, 1.4)
        text(buf, "同一块 16 GB 显卡", CX, CY - 66, 24, "cjk", GREY(0.75), 1.0, 0.2, 1.0)
        rect_outline(buf, x0 - 6, y0 - 6, x1 + 6, y1 + 6, GREY(0.8), 0.7)
        if bar_i == 0:
            f = ease_out(bl / 1.5) * 0.975
            oom = bl > 1.5
            rect_fill(buf, x0, y0, x0 + (x1 - x0) * f, y1, RED if oom else CYAN, 0.55 + (0.4 if oom else 0))
            text(buf, f"{fmt(20992 * min(1, ease_out(bl / 1.5)))} TOKENS", CX, CY + 80, 46, "rthin",
                 RED if oom else CYAN, 1.0, 0.05, 1.6)
            text(buf, "FULL ATTENTION", CX, CY + 132, 22, "light", GREY(0.7), 1.0, 0.4, 1.0)
            if oom:
                text(buf, "OUT OF MEMORY", CX, CY, 34, "semi", WHITE, 1.0 if int(bl * 20) % 2 else 0.5, 0.3, 1.4)
        else:
            f = ease_io(bl / 1.7) * (15.1 / 16)
            rect_fill(buf, x0, y0, x0 + (x1 - x0) * f, y1, GOLD, 0.6)
            splat(buf, np.full(40, x0 + (x1 - x0) * f), np.linspace(y0, y1, 40), WHITE, 1.2)
            text(buf, f"{fmt(716800 * ease_io(bl / 1.7))} TOKENS", CX, CY + 80, 46, "rthin", GOLD, 1.0, 0.05, 1.7)
            text(buf, "PROXYFORMER · r = 64", CX, CY + 132, 22, "light", GREY(0.7), 1.0, 0.4, 1.0)
            a = smooth((bl - 1.8) / 0.25)
            text(buf, "35×", CX + 480, CY + 104, 96, "rthin", WHITE, a, 0.02, 2.0 * (1 + 0.5 * kp))
    elif bar_i == 2:  # same length: 1/5 memory, 12x speed
        text(buf, "SAME 21K-TOKEN HISTORY", CX, CY - 180, 30, "light", GREY(0.8), 1.0, 0.45, 1.2)
        text(buf, "同样 2.1 万 token 的历史", CX, CY - 140, 22, "cjk", GREY(0.7), 1.0, 0.2, 1.0)
        a1 = smooth((bl - 0.05) / 0.2)
        a2 = smooth((bl - BEAT - 0.05) / 0.2)
        text(buf, "1/5", CX - 330, CY + 10, 190, "rthin", GOLD, a1, 0.0, 1.8 * (1 + 0.3 * kp))
        text(buf, "MEMORY  ·  显存", CX - 330, CY + 130, 26, "cjk", GREY(0.8), a1, 0.25, 1.0)
        text(buf, "12×", CX + 330, CY + 10, 190, "rthin", CYAN, a2, 0.0, 1.8 * (1 + 0.3 * kp))
        text(buf, "FASTER  ·  速度", CX + 330, CY + 130, 26, "cjk", GREY(0.8), a2, 0.25, 1.0)
        text(buf, "15.6 GB → 2.9 GB", CX - 330, CY + 175, 22, "light", GREY(0.55), a1, 0.1, 1.0)
        text(buf, "1.3 → 16.1 it/s", CX + 330, CY + 175, 22, "light", GREY(0.55), a2, 0.1, 1.0)
    else:  # NIAH heatmap (bars 3-4)
        hl = lt - 3 * BAR
        cw, ch, gap = 118, 36, 6
        gx0 = CX - (9 * (cw + gap)) / 2 + 30
        gy0 = CY - (10 * (ch + gap)) / 2 + 10
        text(buf, "50 NEEDLES  ·  EVERY ONE QUERIED  ·  5,000 LOOKUPS PER LENGTH", CX, gy0 - 70, 24, "light",
             GREY(0.8), 1.0, 0.2, 1.1)
        text(buf, "每篇 50 根针 · 全部要找 · 训练窗口 64K", CX, gy0 - 36, 22, "cjk", GREY(0.65), 1.0, 0.2, 1.0)
        for c in range(9):
            rev = smooth((hl - 0.15 - c * 0.28) / 0.25)
            if rev <= 0:
                continue
            cx0 = gx0 + c * (cw + gap)
            text(buf, LENGTHS[c], cx0 + cw / 2, gy0 + 10 * (ch + gap) + 16, 22, "rlight", GREY(0.8), rev, 0.05, 1.0)
            for r in range(10):
                v = NIAH_64K[r][c]
                cy0 = gy0 + r * (ch + gap)
                col = heat(v)
                rect_fill(buf, cx0, cy0, cx0 + cw, cy0 + ch, col, 0.16 * rev)
                rect_border(buf, cx0, cy0, cx0 + cw, cy0 + ch, col, 0.45 * rev, 1)
                text(buf, f"{v:.2f}", cx0 + cw / 2, cy0 + ch / 2, 20, "rlight", WHITE, rev, 0.05, 1.0)
        for r in range(0, 10, 3):
            text(buf, f"{r * 10}%", gx0 - 20, gy0 + r * (ch + gap) + ch / 2, 18, "rlight", GREY(0.55), 1.0, 0, 1,
                 "r")
        a1 = smooth((hl - 2.6) / 0.3)
        a2 = smooth((hl - 3.8) / 0.3)
        if a1 > 0:
            bx0 = gx0 + 5 * (cw + gap) - 5
            rect_outline(buf, bx0, gy0 - 6, bx0 + 2 * (cw + gap) + 4, gy0 + 10 * (ch + gap), GREEN, 1.2 * a1, 2)
            text(buf, "4× BEYOND TRAINING: 99–100%", bx0 + cw + gap, gy0 + 10 * (ch + gap) + 58, 26, "light", GREEN,
                 a1 * (1 - a2), 0.1, 1.4)
        if a2 > 0:
            bx0 = gx0 + 8 * (cw + gap) - 5
            rect_outline(buf, bx0, gy0 - 6, bx0 + cw + 10, gy0 + 10 * (ch + gap), GOLD, 1.3 * a2, 2)
            text(buf, "1,048,576 TOKENS · 16×: 92–95%", bx0 - 180, gy0 + 10 * (ch + gap) + 58, 26, "light", GOLD, a2,
                 0.1, 1.5)


GAL_N = 42000
_gr = np.clip(RNG.gamma(2.0, 95, GAL_N), 5, 720).astype(np.float32)
_garm = RNG.integers(0, 3, GAL_N)
_gth = (_garm * 2 * np.pi / 3 + _gr * 0.0135 + RNG.normal(0, 0.28, GAL_N) * (0.4 + 60 / (_gr + 60))).astype(
    np.float32)
_gy = (RNG.normal(0, 1, GAL_N) * (4 + 26 * np.exp(-_gr / 90))).astype(np.float32)
_gmix = np.clip(1 - _gr / 260, 0, 1)[:, None]
_gcol = (GOLD[None, :] * _gmix + (CYAN * 0.7 + BLUE * 0.3)[None, :] * (1 - _gmix)).astype(np.float32)
_gcol[RNG.random(GAL_N) < 0.06] = MAGENTA * 0.8
_gb = RNG.uniform(0.25, 0.8, GAL_N).astype(np.float32)
_gprox = RNG.choice(GAL_N, 70, replace=False)


def s_galaxy(buf, t, lt):
    background(buf, t, 0.5)
    th = _gth + lt * 0.09
    P = np.column_stack([_gr * np.cos(th), _gy, _gr * np.sin(th)])
    dist = 520 + 900 * ease_io(lt / 7.2)
    elev = 1.15 - 0.75 * ease_io(lt / 7.2)
    cam = np.array([0, dist * math.sin(elev), -dist * math.cos(elev)], np.float32)
    x, y, z = project(P, cam, 950, 0.0, -elev)
    v = z > 5
    splat(buf, x[v], y[v], _gcol[v], (_gb * np.clip(700 / np.maximum(z, 1), 0, 2.5))[v])
    for i in _gprox:
        if z[i] > 5:
            stamp(buf, x[i], y[i], 2.5, GOLD * 0.7 + WHITE * 0.3, 2.2 * min(2, 900 / z[i]))
    stamp(buf, CX, y[np.argmin(_gr)], 40, GOLD, 0.25)
    a1 = window(lt, 0.8, 3.7, 0.5, 0.4)
    a2 = window(lt, 3.9, 7.0, 0.5, 0.4)
    text(buf, "TRAINED ON 64K", CX, H * 0.83, 52, "thin", WHITE, a1, 0.45, 1.5)
    text(buf, "只用 64K 窗口训练", CX, H * 0.83 + 52, 26, "cjk", GREY(0.75), a1, 0.2, 1.0)
    text(buf, "STILL FINDING NEEDLES AT ONE MILLION", CX, H * 0.83, 52, "thin", WHITE, a2, 0.3, 1.5)
    text(buf, "一百万 token，依然找得到", CX, H * 0.83 + 52, 26, "cjk", GREY(0.75), a2, 0.2, 1.0)


TITLE = "PROXYFORMER"
TITLE_SIZE, TITLE_TRACK = 150, 0.22
TITLE_Y = H * 0.40


def _title_targets(n=16000):
    m = text_mask(TITLE, "light", TITLE_SIZE, TITLE_TRACK)
    ys, xs = np.nonzero(m > 0.5)
    idx = RNG.choice(len(xs), n, replace=len(xs) < n)
    h, w = m.shape
    return (xs[idx] - w / 2 + CX).astype(np.float32), (ys[idx] - h / 2 + TITLE_Y).astype(np.float32)


TTX, TTY = _title_targets()
_tang = RNG.uniform(0, 2 * np.pi, TTX.size).astype(np.float32)
_trad = (RNG.gamma(2.0, 170, TTX.size)).astype(np.float32)
_tdl = RNG.uniform(0, 0.7, TTX.size).astype(np.float32)
_tcol = np.where(RNG.random(TTX.size)[:, None] < 0.5, GOLD[None, :], (CYAN * 0.6 + WHITE * 0.4)[None, :])


def s_title(buf, t, lt):
    background(buf, t, 0.45 * (1 - smooth((lt - 10.5) / 1.5)))
    # particles burst from the centre, then converge into the title
    burst = ease_out(lt / 0.7)
    sx = CX + np.cos(_tang) * _trad * burst
    sy = TITLE_Y + np.sin(_tang) * _trad * burst * 0.6
    s = ease_io_arr((lt - 0.6 - _tdl) / 1.5)
    px = sx + (TTX - sx) * s
    py = sy + (TTY - sy) * s
    pa = 1.0 - 0.8 * smooth((lt - 2.2) / 1.0)
    tw = 0.7 + 0.3 * np.sin(_tang * 7 + lt * 5)
    splat(buf, px, py, _tcol, 1.3 * pa * tw * (1 - smooth((lt - 10.8) / 1.0)))
    fade_all = 1 - smooth((lt - 10.6) / 1.2)
    ta = smooth((lt - 1.9) / 0.8) * fade_all
    sweep = CX - 900 + 1800 * clamp01((lt - 2.7) / 1.1) if 2.7 < lt < 3.8 else None
    text(buf, TITLE, CX, TITLE_Y, TITLE_SIZE, "light", WHITE, ta, TITLE_TRACK, 1.5, sweep=sweep)
    a = window(lt, 3.0, 12.0, 0.8, 1.2) * fade_all
    text(buf, "PROXY TOKENS FOR ULTRA-LONG CONTEXT", CX, TITLE_Y + 118, 34, "thin", GREY(0.9), a, 0.4, 1.3)
    text(buf, "代理 Token · 超长上下文与高分辨率生成", CX, TITLE_Y + 164, 24, "cjk", GREY(0.7), a, 0.25, 1.0)
    # end card
    b = smooth((lt - 5.0) / 0.8) * fade_all
    if b > 0:
        y = H * 0.67
        text(buf, "PATENT PENDING", CX, y, 40, "light", GOLD, b, 0.5, 1.8 * (1 + 0.15 * math.sin(lt * 3)))
        draw_lines(buf, [(CX - 330, y, CX - 200, y), (CX + 200, y, CX + 330, y)], GOLD, 0.6 * b)
        text(buf, "OPEN TO LICENSING  ·  COMPUTE  ·  RESEARCH COLLABORATION", CX, y + 56, 24, "light", GREY(0.85), b,
             0.25, 1.1)
        text(buf, "代理 Token 方法已提交专利申请 · 欢迎商业授权、算力与研究合作", CX, y + 94, 22, "cjk", GREY(0.7), b, 0.1,
             1.0)
        c = smooth((lt - 6.2) / 0.8) * fade_all
        text(buf, "arXiv:2608.23463   ·   github.com/simonFelix-Ai/proxy-former   ·   tangzhongp@qq.com", CX,
             H * 0.86, 22, "rlight", GREY(0.75), c, 0.05, 1.0)


SCENE_FN = {"river": s_river, "web": s_web, "question": s_question, "proxy": s_proxy, "layers": s_layers,
            "numbers": s_numbers, "galaxy": s_galaxy, "title": s_title}


# ------------------------------------------------------------------ post-processing

def flash(t):
    f = 1.2 * math.exp(-t / 0.3)
    for t0, amp in ((21.6, 3.0), (60.0, 4.0), (31.2, 0.6), (40.8, 0.5), (52.8, 0.6)):
        if t >= t0:
            f += amp * math.exp(-(t - t0) / 0.25)
    return f


def post(buf, t, fidx):
    small = cv2.resize(buf, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(buf, (0, 0), 1.6)
    g2 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3.0), (W, H), interpolation=cv2.INTER_LINEAR)
    g3 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 14.0), (W, H), interpolation=cv2.INTER_LINEAR)
    img = buf + 0.35 * g1 + 0.55 * g2 + 0.75 * g3
    exposure = 1.25 * (1 + flash(t))
    img = 1 - np.exp(-img * exposure)
    img = img * VIGNETTE
    img = np.clip(img ** 0.92, 0, 1)
    # subtle teal-orange grade: lift shadows toward teal
    img = img + (1 - img) * np.array([0.0, 0.012, 0.02], np.float32)
    grain = np.random.default_rng(fidx).standard_normal((H // 2, W // 2)).astype(np.float32)
    grain = cv2.resize(grain, (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.012
    img = np.clip(img + grain, 0, 1)
    out = (img * 255 + 0.5).astype(np.uint8)
    # glitch at the out-of-memory moment
    if 18.2 <= t < 19.2:
        g = np.random.default_rng(fidx + 99)
        amt = (t - 18.2) / 1.0
        for _ in range(int(6 + 18 * amt)):
            y0 = int(g.integers(0, H - 20))
            hgt = int(g.integers(4, 40))
            out[y0:y0 + hgt] = np.roll(out[y0:y0 + hgt], int(g.integers(-120, 120) * amt), axis=1)
        s = int(4 + 14 * amt)
        out[..., 0] = np.roll(out[..., 0], s, axis=1)
        out[..., 2] = np.roll(out[..., 2], -s, axis=1)
    if 19.2 <= t < 19.35:  # hard cut to black before the question
        out[:] = 0
    out[:LETTERBOX] = 0
    out[H - LETTERBOX:] = 0
    return out


def render_frame(args):
    fidx, fps = args
    t = fidx / fps
    buf = np.zeros((H, W, 3), np.float32)
    for a, b, name in SECTIONS:
        if a <= t < b or (name == "title" and t >= b):
            SCENE_FN[name](buf, t, t - a)
            break
    return post(buf, t, fidx)


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="proxyformer_mv.mp4")
    ap.add_argument("--audio", default=None, help="WAV to mux (default: generate with music.py)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=DUR)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--png", default="still.png")
    args = ap.parse_args()

    if args.still is not None:
        fr = render_frame((int(round(args.still * args.fps)), args.fps))
        cv2.imwrite(args.png, fr[..., ::-1])
        print(f"wrote {args.png}")
        return

    audio = args.audio
    if audio is None:
        audio = os.path.splitext(args.out)[0] + ".wav"
        subprocess.run([sys.executable, os.path.join(HERE, "music.py"), audio], check=True)

    f0, f1 = int(args.start * args.fps), int(args.end * args.fps)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(args.fps), "-i", "-", "-ss", str(args.start), "-t", str(args.end - args.start), "-i", audio,
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M",
           "-pix_fmt", "yuv420p", "-tune", "film",
           "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.workers) as pool:
        for i, fr in enumerate(pool.imap(render_frame, [(k, args.fps) for k in range(f0, f1)], chunksize=2)):
            ff.stdin.write(fr.tobytes())
            if i % (args.fps * 2) == 0:
                print(f"  t={(f0 + i) / args.fps:5.1f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
