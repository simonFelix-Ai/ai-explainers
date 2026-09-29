"""
Procedural soundtrack for the Neural Sudoku teaser (no samples, no third-party audio).

A minor, 96 BPM, 18 bars (45 s), locked to the timeline in web/scene.js and post.py:
  bars  0-1   hook          low pulse, glassy pad
  bars  2-4   search        ticking arpeggio, accelerating hats, riser, hard stop at 12.5 s
  bar   5     question      near silence, three plucks, swell
  bars  6-12  neural phase  impact at 15 s, kick, sub bass, warm pad, shimmering arp
  bars 13-14  verification  27 ascending chimes (one per row / column / box)
  bars 15-17  title         big impact, sustained Am(add9), long tail

Usage: python music.py out.wav
"""

import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 45.0
N = int(DUR * SR)
rng = np.random.default_rng(11)

CHORDS = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 60], [55, 59, 62, 67]]  # Am F C G
ROOTS = [45, 41, 48, 43]
PENTA = [57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86, 88, 91]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x)


def place(bus, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(bus):
        return
    n = min(len(sig), len(bus) - i)
    bus[i:i + n] += gain * sig[:n]


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def saw(f, n):
    t = np.arange(n) / SR
    return 2 * ((f * t + rng.random()) % 1.0) - 1


def pad_note(m, dur, bright):
    n = int(dur * SR)
    s = sum(saw(hz(m) * 2 ** (c / 1200), n) for c in (-8, 0, 7)) / 3
    return filt(s, "low", bright) * env(n, 0.4, 0.7)


def glass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.3)
    return s * env(n, 0.6, 0.8) * 0.5


def pluck(m, dur=0.5, decay=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t / decay) * env(n, 0.002, 0.02)


def chime(m):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / 0.15)) \
        * np.exp(-t / 0.5) * env(n, 0.001, 0.05)


def kick(s=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 44 + 90 * np.exp(-t / 0.035)
    return s * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
                + filt(rng.standard_normal(n), "high", 3000) * np.exp(-t / 0.004) * 0.25)


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), "high", 7500) * np.exp(-t / (0.07 if open_ else 0.015)) * 0.3


def sub(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * t) * env(n, 0.005, 0.05) * np.exp(-t / 0.35)


def boom(size=1.0):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * np.cumsum(36 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / (0.7 * size))
    return (low + filt(rng.standard_normal(n), "low", 800) * np.exp(-t / (0.25 * size)) * 0.6) * size


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = t / dur
    return (filt(rng.standard_normal(n), "high", 1500) * x ** 2.2 * 0.5
            + np.sin(2 * np.pi * np.cumsum(220 + 1500 * x ** 2) / SR) * x ** 3 * 0.22)


def ir(sec, seed):
    r = np.random.default_rng(seed)
    t = np.arange(int(sec * SR)) / SR
    return r.standard_normal(t.size) * np.exp(-t / (sec / 5)) * 0.02


def build():
    pad, bass, drums, arp, fx = (np.zeros(N) for _ in range(5))
    kenv = np.zeros(N)

    for b in range(18):
        t0 = b * BAR
        ch = CHORDS[b % 4]
        if b == 5:
            continue
        if b == 15:
            for m in [57, 64, 69, 71, 76]:
                place(pad, pad_note(m, 7.4, 1700), t0, 0.22)
                place(pad, glass(m + 12, 7.4), t0, 0.06)
            continue
        if b > 15:
            continue
        bright, gain = (800, 0.13) if b < 2 else ((1100, 0.14) if b < 6 else (1600, 0.16))
        for m in ch:
            place(pad, pad_note(m, BAR + 0.5, bright), t0, gain)
        if b < 2 or b >= 6:
            place(pad, glass(ch[-1] + 12, BAR), t0, 0.05)

    for b in range(0, 2):  # hook pulse
        for i in range(4):
            place(drums, kick(0.5 if i == 0 else 0.25), b * BAR + i * BEAT)
    for b in range(2, 5):  # search: ticking arpeggio + accelerating hats
        ch = CHORDS[b % 4]
        div = 2 if b == 2 else 4
        for i in range(4 * div):
            place(drums, hat(), b * BAR + i * BEAT / div, 0.5 + 0.2 * (b - 2))
        for i in range(8):
            place(arp, pluck(ch[i % 4] + 12, 0.3, 0.09), b * BAR + i * BEAT / 2, 0.12)
        place(drums, kick(0.6), b * BAR)
    place(fx, riser(3 * BAR), 2 * BAR, 0.75)
    stop = int(5 * BAR * SR)

    for k, m in enumerate([76, 72, 69]):  # question bar, beats 2-4
        place(arp, pluck(m, 1.2, 0.5), 5 * BAR + (k + 1) * BEAT, 0.3)
    place(fx, riser(BAR), 5 * BAR, 0.4)

    place(fx, boom(1.2), 6 * BAR, 0.9)
    for b in range(6, 13):  # neural phase groove
        root = ROOTS[b % 4]
        ch = CHORDS[b % 4]
        for i in range(4):
            t = b * BAR + i * BEAT
            place(drums, kick(0.95), t)
            place(kenv, np.exp(-np.arange(int(0.3 * SR)) / SR / 0.08), t)
            place(bass, sub(root, BEAT / 2), t, 0.45)
            place(bass, sub(root + 12, BEAT / 2), t + BEAT / 2, 0.5)
            if b >= 8:
                place(drums, hat(True), t + BEAT / 2, 0.45)
        tones = ch + [ch[1] + 12, ch[2] + 12]
        for i in range(16):
            m = tones[[0, 2, 3, 5, 4, 2, 3, 1][i % 8] % len(tones)] + 12
            place(arp, pluck(m, 0.4, 0.13), b * BAR + i * BEAT / 4, 0.12 + 0.03 * (b >= 9))

    for k in range(27):  # verification chimes: one per row / column / box
        place(arp, chime(PENTA[k % len(PENTA)] + (12 if k >= 15 else 0)), 32.7 + k * 0.17, 0.16)
    for b in (13, 14):
        for i in range(4):
            place(drums, kick(0.7), b * BAR + i * BEAT)
            place(kenv, np.exp(-np.arange(int(0.3 * SR)) / SR / 0.08), b * BAR + i * BEAT)
    place(fx, riser(2 * BAR), 13 * BAR, 0.55)
    place(fx, boom(1.7), 15 * BAR, 1.1)

    pad *= 1 - 0.5 * np.clip(kenv, 0, 1)
    send = pad + 0.8 * arp + 0.5 * fx
    wl = fftconvolve(send, ir(3.0, 1))[:N]
    wr = fftconvolve(send, ir(3.0, 2))[:N]
    dry = pad + arp + bass + drums + fx
    q0, q1 = stop, int(6 * BAR * SR)
    dry[q0:q1] = (arp + fx)[q0:q1]
    wg = np.ones(N)
    wg[q0:q1] = np.linspace(0.08, 0.6, q1 - q0) ** 1.5
    L, R = dry + 0.9 * wl * wg, dry + 0.9 * wr * wg
    d = int(0.012 * SR)
    R[d:] += 0.15 * arp[:-d]
    tail = np.ones(N)
    f0 = int(42.5 * SR)
    tail[f0:] = np.linspace(1, 0, N - f0) ** 1.5
    st = np.stack([L * tail, R * tail], axis=1)
    st = np.tanh(1.2 * st / (np.max(np.abs(st)) + 1e-9) * 1.4)
    return st / np.max(np.abs(st)) * 0.89


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "teaser.wav"
    a = build()
    wavfile.write(out, SR, (a * 32767).astype(np.int16))
    print(f"wrote {out}: {a.shape[0] / SR:.1f}s")
