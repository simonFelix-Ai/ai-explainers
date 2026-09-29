"""
Procedural soundtrack for the ProxyFormer MV (no samples, no third-party audio).

D minor, 100 BPM, 30 bars (72 s). The section layout mirrors the visual timeline
in proxyformer_mv.py so every cut and impact lands on the beat:

  bars  0-3   intro        pad + heartbeat kick
  bars  4-7   build        hats accelerate, riser, hard stop at 19.2 s
  bar   8     question     sparse plucks + reverse swell into the drop
  bars  9-12  drop         impact, four-on-the-floor, sub bass, side-chained pad
  bars 13-16  layers       + arpeggio, claps, off-beat hats
  bars 17-21  numbers      + a boom on every downbeat
  bars 22-24  galaxy       breakdown, pad swell, riser
  bars 25-29  title        big impact, sustained Dm(add9), long tail

Usage: python music.py out.wav
"""

import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 72.0
N = int(DUR * SR)
rng = np.random.default_rng(7)

# Dm, Bb, F, C  (i - VI - III - VII)
CHORDS = [[50, 53, 57, 62], [46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60]]
ROOTS = [38, 34, 41, 36]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def place(bus, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(bus):
        return
    n = min(len(sig), len(bus) - i)
    bus[i:i + n] += gain * sig[:n]


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1.0) - 1


def pad_note(m, dur, bright=1200):
    n = int(dur * SR)
    s = sum(saw(hz(m) * 2 ** (c / 1200), n, rng.random()) for c in (-9, 0, 8))
    return lp(s / 3, bright) * env_adsr(n, 0.35, 0.6)


def kick(strength=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.004) * 0.3
    return strength * (s + click)


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t / (0.08 if open_ else 0.018)) * 0.35


def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    env = sum(np.exp(-np.clip(t - d, 0, None) / 0.012) * (t >= d) for d in (0, 0.011, 0.022)) \
        + 0.6 * np.exp(-t / 0.09)
    return bp(rng.standard_normal(n), 900, 2600) * env * 0.5


def sub(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * t) * env_adsr(n, 0.005, 0.05) * np.exp(-t / 0.35)


def pluck(m, dur=0.5, decay=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t / decay) * env_adsr(n, 0.002, 0.02)


def boom(size=1.0):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / (0.7 * size))
    air = lp(rng.standard_normal(n), 900) * np.exp(-t / (0.25 * size)) * 0.6
    return (low + air) * size


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = t / dur
    noise = hp(rng.standard_normal(n), 1500) * x ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1400 * x ** 2) / SR) * x ** 3 * 0.25
    return (noise * 0.5 + tone) * env_adsr(n, 0.0, 0.01)


def reverb_ir(sec=3.0, seed=1):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    return r.standard_normal(n) * np.exp(-t / (sec / 5)) * 0.02


def build():
    pad = np.zeros(N)
    bass = np.zeros(N)
    drums = np.zeros(N)
    arp = np.zeros(N)
    fx = np.zeros(N)
    kick_env = np.zeros(N)

    def chord(b):
        return CHORDS[b % 4]

    # ---- pad through almost everything (silent in the question bar)
    for b in range(30):
        t0 = b * BAR
        if b == 8:
            continue
        if b >= 25:
            if b == 25:  # final sustained Dm(add9), long tail
                for m in [50, 57, 62, 64, 69]:
                    place(pad, pad_note(m, 10.5, 1600), t0, 0.22)
            continue
        bright = 700 if b < 4 else (1000 if b < 9 else 1500)
        gain = 0.14 if b < 4 else (0.15 if b < 9 else 0.16)
        if 22 <= b <= 24:
            gain, bright = 0.2, 2200
        for m in chord(b):
            place(pad, pad_note(m, BAR + 0.5, bright), t0, gain)

    # ---- intro heartbeat
    for b in range(0, 4):
        place(drums, kick(0.55), b * BAR)
        place(drums, kick(0.3), b * BAR + BEAT * 0.6)

    # ---- build: hats accelerate, riser, hard stop at bar 8
    for b in range(4, 8):
        div = 2 if b < 6 else 4
        for i in range(4 * div):
            place(drums, hat(), b * BAR + i * BEAT / div, 0.6 + 0.4 * (b - 4) / 3)
        place(drums, kick(0.7), b * BAR)
    place(fx, riser(4 * BAR), 4 * BAR, 0.8)
    stop = int(8 * BAR * SR)

    # ---- question bar: sparse plucks, reverse swell into the drop
    for k, m in enumerate([74, 69, 65]):  # beats 2-4: leave the cut itself silent
        place(arp, pluck(m, 1.2, 0.5), 8 * BAR + (k + 1) * BEAT, 0.35)
    place(fx, riser(BAR), 8 * BAR, 0.45)

    # ---- drop and after: impacts
    place(fx, boom(1.3), 9 * BAR, 0.9)
    for b in range(17, 22):
        place(fx, boom(0.7), b * BAR, 0.55)
    place(fx, riser(3 * BAR), 22 * BAR, 0.7)
    place(fx, boom(1.8), 25 * BAR, 1.1)

    # ---- groove: bars 9-21
    for b in range(9, 22):
        root = ROOTS[b % 4]
        for i in range(4):
            t = b * BAR + i * BEAT
            place(drums, kick(1.0), t)
            place(kick_env, np.exp(-np.arange(int(0.3 * SR)) / SR / 0.08), t)
            for j in (0.5,):
                place(bass, sub(root + 12, BEAT / 2), t + j * BEAT, 0.55)
            place(bass, sub(root, BEAT / 2), t, 0.45)
        if b >= 13:
            for i in range(4):
                place(drums, hat(open_=True), b * BAR + (i + 0.5) * BEAT, 0.5)
            for i in (1, 3):
                place(drums, clap(), b * BAR + i * BEAT, 0.8)

    # ---- arpeggio: bars 13-24 (softer in the breakdown)
    for b in range(13, 25):
        tones = chord(b) + [chord(b)[1] + 12, chord(b)[2] + 12]
        pattern = [0, 2, 3, 5, 4, 2, 3, 1]
        for i in range(16):
            m = tones[pattern[i % 8] % len(tones)] + 12
            place(arp, pluck(m, 0.4, 0.14), b * BAR + i * BEAT / 4, 0.16 if b < 22 else 0.11)

    # ---- side-chain the pad to the kick
    duck = 1 - 0.55 * np.clip(kick_env, 0, 1)
    pad *= duck

    # ---- reverb sends
    wet_l = fftconvolve(pad + 0.7 * arp + 0.5 * fx, reverb_ir(3.2, 1))[:N]
    wet_r = fftconvolve(pad + 0.7 * arp + 0.5 * fx, reverb_ir(3.2, 2))[:N]
    dry = pad + arp + bass + drums + fx

    # hard stop at bar 8: in the question bar only the plucks, the swell and the
    # reverb tail remain (pad and drum tails from bar 7 are cut)
    dry_gate = dry.copy()
    q0, q1 = stop, int(9 * BAR * SR)
    dry_gate[q0:q1] = (arp + fx)[q0:q1]

    # duck the build's reverb tail so the question bar is near-silent
    wet_gain = np.ones(N)
    wet_gain[q0:q1] = np.linspace(0.08, 0.6, q1 - q0) ** 1.5
    L = dry_gate + 0.9 * wet_l * wet_gain
    R = dry_gate + 0.9 * wet_r * wet_gain
    # slight stereo width on the arp
    delay = int(0.012 * SR)
    R[delay:] += 0.15 * arp[:-delay]

    # master: fade tail, soft clip, normalise
    tail = np.ones(N)
    f0 = int(69.0 * SR)
    tail[f0:] = np.linspace(1, 0, N - f0) ** 1.5
    L *= tail
    R *= tail
    st = np.stack([L, R], axis=1)
    st = np.tanh(1.2 * st / (np.max(np.abs(st)) + 1e-9) * 1.4)
    st = st / np.max(np.abs(st)) * 0.89
    return st


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "proxyformer_mv.wav"
    audio = build()
    wavfile.write(out, SR, (audio * 32767).astype(np.int16))
    print(f"wrote {out}: {audio.shape[0] / SR:.1f}s")
