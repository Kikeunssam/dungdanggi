#!/usr/bin/env python3
"""수묵 뱅크(뱅크 1) 영상: 각 키의 음원 파형을 읽어서 그 소리 모양대로 먹을 그린다.

- 소리의 세기(포락선)가 붓의 굵기, 번짐의 크기, 먹의 농담이 된다.
- 소리가 터지는 순간(온셋)마다 새 획이나 점이 찍힌다 (게르르르, 더러러러 등).
- 붓이 지나가는 속도는 소리 에너지가 쌓이는 속도를 따른다: 셀 때 빠르게, 잦아들 때 느리게.
- 강은 진한 농묵, 중은 옅은 담묵. 몇몇 키에는 옅은 담채(쪽빛, 주홍, 황토, 초록, 분홍)를 깐다.

1920x1080, 30fps, 4초, 흰 바탕(화면에서는 한지 위에 '어둡게'로 겹친다), 첫·끝 프레임은 빈 종이.
옅은 먹부터 마르듯 사라진다.

    python3 tools/ink_sound.py            # 26개 전부 → clips/sumuk/
    python3 tools/ink_sound.py a s d      # 일부 키만
    python3 tools/ink_sound.py --preview  # 미리보기 시트만 (outputs/)
"""
import subprocess
import sys
from math import cos, sin, pi, radians
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS, DUR = 1920, 1080, 30, 4.0
N = int(FPS * DUR)
SR, ER = 22050, 200          # 분석 샘플레이트, 포락선 해상도(Hz)
SHIFT = 4                    # cv2 그리기 고정소수점
SC = 1 << SHIFT


def bgr(r, g, b):
    return np.array([b, g, r], np.float32) / 255


MUK = bgr(24, 22, 28)        # 먹
INDIGO = bgr(64, 94, 140)    # 쪽빛
VERM = bgr(206, 84, 56)      # 주홍
OCHRE = bgr(200, 150, 80)    # 황토
GREEN = bgr(98, 136, 96)     # 초록
ROSE = bgr(214, 118, 126)    # 연분홍
UMBER = bgr(128, 98, 74)     # 갈색 담묵


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- 소리 분석

class Sound:
    def __init__(self, name):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "sounds" / f"{name}.wav"),
                              "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32)
        hop = SR // ER
        n = len(x) // hop
        rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
        rms = np.convolve(rms, np.ones(3) / 3, "same")
        self.name = name
        self.peak = float(rms.max())
        self.env = (rms / self.peak).astype(np.float32)
        self.t = np.arange(n) / ER
        above = np.nonzero(self.env > 0.05)[0]
        self.len = max((above[-1] + 1) / ER, 0.05)
        e = self.env ** 2
        c = np.cumsum(e[: int(self.len * ER) + 1])
        self.cum = c / c[-1]
        self.cum_t = np.arange(len(c)) / ER
        # 온셋: 25ms 사이 세기가 확 오르는 지점
        flux = np.maximum(rms - np.concatenate([np.full(5, rms[0]), rms[:-5]]), 0) / self.peak
        ons = [0.0]
        for i in range(1, n - 1):
            lo, hi = max(0, i - 12), min(n, i + 13)
            if flux[i] > 0.12 and flux[i] == flux[lo:hi].max() and i / ER - ons[-1] > 0.06:
                ons.append(i / ER)
        self.onsets = ons

    def env_at(self, ts):
        return np.interp(ts, self.t, self.env, right=0.0).astype(np.float32)

    def time_of(self, frac):
        """에너지가 frac만큼 쌓인 시각 (초)."""
        return np.interp(frac, self.cum, self.cum_t).astype(np.float32)


# ---------------------------------------------------------------- 질감

def fbm(h, w, cell, rng, octaves=4, pers=0.5):
    out = np.zeros((h, w), np.float32)
    a, tot, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        if c < 1.5:
            break
        gh, gw = int(h / c) + 3, int(w / c) + 3
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (int(gw * c), int(gh * c)), interpolation=cv2.INTER_CUBIC)[:h, :w]
        out += a * up
        tot += a * a
        a *= pers
        c /= 2
    return out / np.sqrt(tot)


_rng0 = np.random.default_rng(7)
GRAIN = fbm(H, W, 6, _rng0, 3)                                    # 종이 결
TONE = fbm(H, W, 60, _rng0, 3)                                    # 먹빛의 큰 얼룩
FIBRE = cv2.GaussianBlur(_rng0.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
FIBRE = cv2.resize(cv2.resize(FIBRE, (W // 3, H)), (W, H))        # 가로로 늘어진 섬유
FIBRE /= FIBRE.std()


def noise1d(n, rng, cell):
    k = max(2, int(n / cell) + 2)
    v = rng.standard_normal(k)
    return np.interp(np.linspace(0, k - 1, n) * (n / max(n, 1)), np.arange(k), v).astype(np.float32)


# ---------------------------------------------------------------- 레이어

class Layer:
    """먹 한 겹: 밀도 D(0..1)와 먹이 닿는 시각 T(초)."""

    def __init__(self, D, T, col=MUK, tau=0.05, x0=0, y0=0):
        m = D > 0.004
        self.empty = not m.any()
        if self.empty:
            return
        ys, xs = np.nonzero(m)
        a, b, c, d = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        self.D = np.clip(D[a:b, c:d], 0, 1).astype(np.float32)
        self.T = np.where(m[a:b, c:d], T[a:b, c:d], 99).astype(np.float32)
        self.sl = (slice(y0 + a, y0 + b), slice(x0 + c, x0 + d))
        self.tmin = float(self.T.min())
        self.k = (1 - col).astype(np.float32)
        self.tau = tau


def frame(layers, t, fade):
    img = np.ones((H, W, 3), np.float32)
    f = float(smooth((t - fade[0]) / (fade[1] - fade[0])))
    if f >= 1:
        return np.full((H, W, 3), 255, np.uint8)
    for L in layers:
        if L.empty or t <= L.tmin:
            continue
        s = smooth((t - L.T) / L.tau)
        a = L.D * s
        if f > 0:   # 옅은 먹부터 마르듯 사라진다
            a = np.clip((a - 0.9 * f) / (1 - 0.9 * f), 0, 1) * (1 - f) ** 0.35
        img[L.sl] *= 1 - a[..., None] * L.k
    return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- 붓질 재료

def blob(cx, cy, R, dens, seed, T=None, rough=0.22, rim=0.35, halo=0.3, inner=0.3,
         mod=None, col=MUK, tau=0.07, aspect=1.0, ang=0.0, bleed=1.2, core=0.0):
    """번지는 먹 덩어리. T(d): 중심에서 d(반지름=1) 떨어진 곳에 먹이 닿는 시각."""
    rng = np.random.default_rng(seed)
    ext = int(R * (1 + rough + halo * 3) * max(aspect, 1 / aspect)) + 24
    x0, y0 = max(0, int(cx - ext)), max(0, int(cy - ext))
    x1, y1 = min(W, int(cx + ext)), min(H, int(cy + ext))
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    ca, sa = cos(ang), sin(ang)
    u, v = (dx * ca + dy * sa) / aspect, (-dx * sa + dy * ca) * aspect
    n1 = fbm(h, w, max(R * 0.55, 8), rng, 4, 0.55)
    n2 = fbm(h, w, max(R * 0.25, 12), rng, 3)
    d = np.hypot(u, v) / (R * (1 + rough * 0.5 * n1))
    edge = smooth((1.0 - d) / 0.02 + 0.5)
    body = dens * (1 - inner + inner * np.clip(0.55 + 0.35 * n2, 0, 1))
    if core:
        body = body + core * dens * np.exp(-(d / 0.35) ** 2)
    D = body * edge + rim * dens * np.exp(-((d - 0.975) / 0.03) ** 2)
    if halo:
        fib = np.clip(0.55 + 0.45 * FIBRE[y0:y1, x0:x1] + 0.3 * n2, 0, 1)
        hal = 0.4 * dens * np.exp(-np.maximum(d - 1, 0) / halo) * fib * (d > 0.97)
        D = np.maximum(D, hal)
    if mod is not None:
        D = D * mod(d)
    D *= 0.95 + 0.04 * GRAIN[y0:y1, x0:x1] + 0.05 * TONE[y0:y1, x0:x1]
    if T is None:
        Tm = 0.25 * np.clip(d, 0, 1) ** 1.5
    else:
        Tm = T(np.clip(d, 0, 1))
    Tm = Tm + np.maximum(d - 1, 0) * bleed     # 테두리 밖으로 천천히 스미는 번짐
    return Layer(D.astype(np.float32), Tm.astype(np.float32), col, tau, x0, y0)


def spline(ctrl, step=3.0):
    P = np.array(ctrl, np.float64)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    ts = np.linspace(0, 1, 48, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1:i + 3]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * ts + (2 * p0 - 5 * p1 + 4 * p2 - p3) * ts ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * ts ** 3))
    out.append(P[-2][None])
    pts = np.vstack(out)
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    n = max(3, int(L[-1] / step))
    u = np.linspace(0, L[-1], n)
    return np.stack([np.interp(u, L, pts[:, 0]), np.interp(u, L, pts[:, 1])], 1), u / L[-1]


def stroke(ctrl, width, times, dens, seed, nb=40, dry=0.4, wet=0.0, col=MUK, tau=0.04,
           start=0.05, end=0.25):
    """붓 한 획. width(s), times(s): 획 위치 s(0..1)의 굵기(px)와 붓이 지나는 시각(초).
    dry가 클수록 먹이 빨리 떨어져 갈필(비백)이 생긴다. wet>0이면 획 둘레로 먹이 스민다."""
    rng = np.random.default_rng(seed)
    P, s = spline(ctrl)
    # 붓머리는 뭉툭하게 눌러 시작하고, 끝은 뾰족해지기보다 갈라지며 빠진다
    w = np.asarray(width(s), np.float32) * (0.55 + 0.45 * smooth(s / start)) * (0.3 + 0.7 * smooth((1 - s) / end))
    w *= 1 + 0.15 * noise1d(len(s), rng, 30)
    T = np.asarray(times(s), np.float32)
    tan = np.gradient(P, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    D = np.zeros((H, W), np.float32)
    Tm = np.full((H, W), 99, np.float32)
    offs = np.sort(rng.uniform(-1, 1, nb))
    strength = rng.uniform(0.55, 1.0, nb) * (1 - 0.55 * np.abs(offs) ** 3)
    load = np.exp(-dry * 3.2 * s)
    th = np.maximum(1, w / nb * 3.4)
    # 먹을 머금은 동안은 붓 안쪽이 고르게 차고, 먹이 떨어질수록 붓털 결(비백)이 드러난다
    B = np.zeros((H, W), np.float32)
    body = dens * 0.95 * smooth((load - 0.3) / 0.35)
    C = (P * SC).astype(np.int32)
    for i in range(len(s) - 1):
        if body[i] > 0.01 and w[i] > 2:
            cv2.line(B, (int(C[i, 0]), int(C[i, 1])), (int(C[i + 1, 0]), int(C[i + 1, 1])), float(body[i]),
                     max(1, int(w[i] * 0.95)), cv2.LINE_AA, SHIFT)
            cv2.line(Tm, (int(C[i, 0]), int(C[i, 1])), (int(C[i + 1, 0]), int(C[i + 1, 1])), float(T[i]),
                     max(1, int(w[i] * 0.95)) + 2, cv2.LINE_8, SHIFT)
    for j in range(nb):
        nz = noise1d(len(s), rng, rng.uniform(6, 30))
        alive = load * strength[j] + 0.22 * nz > 0.3 + 0.35 * dry * rng.random()
        off = offs[j] * (1 + 0.12 * noise1d(len(s), rng, 50)) + 0.05 * noise1d(len(s), rng, 25)
        Q = ((P + nrm * (off * w / 2)[:, None]) * SC).astype(np.int32)
        val = dens * (0.55 + 0.35 * np.clip(load * strength[j] * 1.3, 0, 1)) * rng.uniform(0.85, 1.0)
        for i in range(len(s) - 1):
            if alive[i] and w[i] > 0.6:
                p, q, t_ = (int(Q[i, 0]), int(Q[i, 1])), (int(Q[i + 1, 0]), int(Q[i + 1, 1])), int(th[i])
                cv2.line(D, p, q, float(val[i]), t_, cv2.LINE_AA, SHIFT)
                cv2.line(Tm, p, q, float(T[i]), t_ + 2, cv2.LINE_8, SHIFT)
    D = np.maximum(cv2.GaussianBlur(D, (0, 0), 0.8), cv2.GaussianBlur(B, (0, 0), 1.5))
    D *= 0.93 + 0.04 * GRAIN + 0.06 * TONE
    layers = [Layer(D, Tm, col, tau)]
    if wet:
        r = int(wet)
        hal = cv2.GaussianBlur(D, (0, 0), wet) * 0.55
        hal *= np.clip(0.6 + 0.4 * FIBRE + 0.3 * GRAIN, 0, 1)
        Th = cv2.erode(Tm, np.ones((2 * r + 1, 2 * r + 1), np.uint8)) + 0.12
        layers.append(Layer(hal, Th, col, 0.35))
    return layers


def splatter(cx, cy, n, rmin, rmax, smin, smax, dens, seed, T0=0.0, speed=2600, ang=None, spread=pi,
             col=MUK, tau=0.04, sat=0.35):
    """튀는 먹 방울. ang 방향(없으면 사방)으로 흩뿌린다. 멀수록 작고 길쭉하고 늦게 닿는다."""
    rng = np.random.default_rng(seed)
    D = np.zeros((H, W), np.float32)
    Tm = np.full((H, W), 99, np.float32)

    def drop(x, y, a, b, deg, val, t):
        c = (int(x * SC), int(y * SC))
        ax = (max(1, int(a * SC)), max(1, int(b * SC)))
        cv2.ellipse(D, c, ax, deg, 0, 360, float(val), -1, cv2.LINE_AA, SHIFT)
        cv2.ellipse(Tm, c, (ax[0] + 2 * SC, ax[1] + 2 * SC), deg, 0, 360, float(t), -1, cv2.LINE_8, SHIFT)

    for _ in range(n):
        th = rng.uniform(0, 2 * pi) if ang is None else ang + rng.normal() * spread
        fr = rng.random() ** 1.5
        dist = rmin + (rmax - rmin) * fr
        size = smin * (smax / smin) ** (rng.random() ** 2.5) * (1.15 - 0.6 * fr)
        x, y = cx + dist * cos(th), cy + dist * sin(th)
        e = 1 + 2.2 * rng.random() * fr
        val = dens * rng.uniform(0.65, 1.0) * (1 - 0.35 * fr)
        t = T0 + dist / speed
        drop(x, y, size * e, size / np.sqrt(e), np.degrees(th), val, t)
        if rng.random() < sat:
            for _ in range(rng.integers(1, 4)):
                d2 = size * rng.uniform(1.5, 4)
                drop(x + d2 * cos(th) + rng.normal() * size, y + d2 * sin(th) + rng.normal() * size,
                     size * 0.3, size * 0.25, np.degrees(th), val * 0.9, t + 0.02)
    D = cv2.GaussianBlur(D, (0, 0), 0.7)
    D *= 0.88 + 0.12 * GRAIN
    return Layer(D, Tm, col, tau)


def wash(cx, cy, R, dens, seed, col=MUK, T0=0.0, grow=0.6, aspect=1.0, ang=0.0, rough=0.4):
    """옅은 담묵·담채 바림: 테두리가 살짝 진하고 안은 고르지 않게."""
    return blob(cx, cy, R, dens, seed, T=lambda d: T0 + grow * d ** 1.4, rough=rough, rim=0.25,
                halo=0.45, inner=0.6, col=col, tau=0.3, aspect=aspect, ang=ang, bleed=1.0)


# ---------------------------------------------------------------- 소리 → 획 시간/굵기

def brush_time(S, T0=0.0, stretch=1.0, min_dur=0.12, mix=0.35):
    """붓이 획의 s 지점을 지나는 시각: 에너지가 s만큼 쌓인 때 (너무 순식간이면 min_dur로 늘림)."""
    dur = max(S.len * stretch, min_dur)

    def f(s):
        tn = S.time_of(s) / S.len
        return T0 + dur * ((1 - mix) * tn + mix * s)
    return f


def brush_width(S, w0, w1, stretch=1.0, gamma=0.7):
    """붓이 s 지점을 지날 때의 소리 세기가 굵기."""
    def f(s):
        return w0 + w1 * S.env_at(S.time_of(s) * 1.0) ** gamma
    return f


def bloom_time(S, T0=0.0, stretch=1.0, grow=0.12):
    """번짐의 넓이가 쌓인 에너지를 따른다: 반지름 d에 닿는 시각."""
    def f(d):
        return T0 + grow * d ** 1.3 + stretch * S.time_of(np.clip(d, 0, 1) ** 2) * min(1.0, 1.2 / max(S.len, 1e-3))
    return f


def pol(cx, cy, r, deg):
    return (cx + r * cos(radians(deg)), cy + r * sin(radians(deg)))


# ---------------------------------------------------------------- 레시피

def r_ji(S, k):      # a 꽹과리 지: 한가운데서 터지는 쇳소리 → 짙은 점과 사방으로 튀는 방울, 내던진 갈필
    cx, cy = 900, 520
    L = [wash(cx, cy, 260, 0.13, 1, T0=0.05, grow=0.7)]
    L.append(blob(cx, cy, 135, 0.95, 2, T=bloom_time(S, grow=0.06), rough=0.35, rim=0.3, halo=0.2, core=0.2))
    L.append(splatter(cx, cy, 200, 100, 760, 2, 30, 0.9, 3, T0=0.02, speed=3200))
    rng = np.random.default_rng(4)
    for i, a in enumerate([-150, -40, 25, 110, 200]):
        a += rng.normal() * 12
        ln = rng.uniform(320, 600)
        pts = [pol(cx, cy, 80, a), pol(cx, cy, 80 + ln * 0.5, a + 6), pol(cx, cy, 80 + ln, a + 4)]
        L += stroke(pts, lambda s: 34 * (1 - 0.7 * s), lambda s, i=i: 0.02 + 0.03 * i + 0.14 * s,
                    0.85, 10 + i, nb=14, dry=0.75, start=0.02, end=0.4)
    return L


def r_roll(S, k):    # s 꽹과리 게르르르: 소리 알갱이마다 짧은 갈필 + 방울이 화면을 가로질러 행진
    rng = np.random.default_rng(20)
    L = [wash(960, 560, 520, 0.09, 21, T0=0.05, grow=1.2, aspect=2.2, ang=-0.3)]
    ons = S.onsets
    for i, t in enumerate(ons):
        fr = i / max(len(ons) - 1, 1)
        x, y = 330 + 1300 * fr + rng.normal() * 30, 720 - 380 * fr + rng.normal() * 40
        e = float(S.env_at(t + 0.02))
        dv = 0.35 + 0.6 * e
        a = -60 + rng.normal() * 18
        ln = 260 + 220 * e
        pts = [pol(x, y, -ln / 2, a), pol(x, y, 0, a + 5), pol(x, y, ln / 2, a)]
        L += stroke(pts, lambda s, e=e: 40 + 80 * e, lambda s, t=t: t + 0.08 * s, dv, 30 + i,
                    nb=26, dry=0.6, start=0.05, end=0.45)
        L.append(splatter(x, y, 40, 40, 260, 2, 13, dv, 50 + i, T0=t, speed=2200))
    return L


def r_gaek(S, k):    # q 꽹과리 객: 막아 친 짧은 소리 → 오므린 짙은 점과 바짝 붙은 방울
    cx, cy = 1060, 470
    L = [wash(cx, cy, 200, 0.12, 60, T0=0.04, grow=0.5, col=UMBER)]
    L.append(blob(cx, cy, 105, 0.95, 61, T=bloom_time(S, grow=0.05), rough=0.4, rim=0.25, halo=0.15))
    L.append(splatter(cx, cy, 90, 70, 360, 2, 18, 0.9, 62, T0=0.01, speed=2400))
    L += stroke([(cx - 40, cy + 30), (cx - 170, cy + 120), (cx - 250, cy + 210)], lambda s: 46 * (1 - 0.6 * s),
                lambda s: 0.02 + 0.1 * s, 0.85, 63, nb=24, dry=0.65)
    return L


def r_gaet(S, k):    # w 꽹과리 갯: 높고 밝은 소리 → 가늘고 빠른 세 획이 엇갈리고 먹 안개가 뿌려진다
    L = [wash(960, 540, 300, 0.11, 70, col=INDIGO, T0=0.05, grow=0.8)]
    paths = [[(380, 820), (900, 520), (1560, 230)], [(520, 260), (1000, 520), (1500, 860)],
             [(300, 500), (980, 470), (1650, 560)]]
    for i, p in enumerate(paths):
        t0 = 0.05 * i
        L += stroke(p, lambda s: 16 * (1 - 0.7 * s) + 4, lambda s, t0=t0: t0 + 0.13 * s, 0.9 - 0.15 * i,
                    71 + i, nb=12, dry=0.8, start=0.02, end=0.5)
        a = np.degrees(np.arctan2(p[2][1] - p[0][1], p[2][0] - p[0][0]))
        L.append(splatter(p[1][0], p[1][1], 180, 0, 520, 1, 5, 0.75, 75 + i, T0=t0, speed=3500,
                          ang=radians(a), spread=0.25))
    return L


def r_jing(S, k, cx=960, cy=540, R=470, wcol=INDIGO, seed=100):   # d/f 징: 소리의 울림이 나이테처럼 퍼지는 동심원
    span = min(S.len, 7.0)
    tvis = 2.6

    def T(d):
        return tvis * d ** 1.6

    def stime(d):
        return span * d ** 1.25

    # 맥놀이: 큰 감쇠를 걷어낸 잔물결이 나이테의 진하고 옅은 띠가 된다
    e = np.convolve(S.env, np.ones(9) / 9, "same")
    trend = np.convolve(e, np.ones(81) / 81, "same") + 1e-3
    ripple = np.clip(e / trend - 1, -0.5, 0.5)
    ts = np.arange(len(e)) / ER

    peaks = [ts[i] for i in range(10, int(span * ER)) if ripple[i] == ripple[max(0, i - 30):i + 30].max()
             and ripple[i] > 0.02]
    ring_d = [(p / span) ** 0.8 for p in peaks]     # stime의 역함수

    def mod(d):
        st = stime(np.clip(d, 0, 1))
        m = 0.25 + 0.6 * np.interp(st, ts, trend) ** 0.6 + 2.2 * np.interp(st, ts, ripple)
        for rd in ring_d:
            m = m + 0.5 * np.exp(-((d - rd) / 0.01) ** 2)
        return np.clip(m, 0.08, 1.4)

    L = [wash(cx, cy, R * 1.12, 0.12 * k, seed, col=wcol, T0=0.4, grow=2.0, rough=0.2)]
    L.append(blob(cx, cy, R, 0.8 * k, seed + 1, T=T, rough=0.08, rim=0.5, halo=0.25, inner=0.15, mod=mod,
                  tau=0.18, bleed=1.5))
    L.append(blob(cx, cy, R * 0.12, 0.95 * k, seed + 2, T=lambda d: 0.06 * d, rough=0.3, rim=0.2, halo=0.2))
    return L


def r_jing_soft(S, k):
    return r_jing(S, k, cx=1080, cy=580, R=360, wcol=OCHRE, seed=120)


def r_kung(S, k, cx=960, cy=600, R=330, seed=200):   # h/y 쿵: 낮게 울리는 북통 → 크게 번지는 젖은 먹
    L = [blob(cx, cy, R, 0.78 * k, seed, T=bloom_time(S, grow=0.2, stretch=0.6), rough=0.3, rim=0.45,
              halo=0.6, inner=0.35, tau=0.12, bleed=1.6)]
    L.append(blob(cx - R * 0.15, cy - R * 0.1, R * 0.4, 0.9 * k, seed + 1, T=bloom_time(S, grow=0.06),
                  rough=0.45, rim=0.2, halo=0.4))
    return L


def r_deong(S, k, cx=820, cy=560, R=260, ang=-35, seed=300):   # g/t 덩: 궁편 울림(번짐) + 채편(날카로운 획)
    L = [blob(cx, cy, R, 0.72 * k, seed, T=bloom_time(S, grow=0.18, stretch=0.6), rough=0.3, rim=0.4,
              halo=0.5, inner=0.35, tau=0.12)]
    ln = 900 * (0.8 + 0.2 * k)
    p = [pol(cx + 80, cy - 20, -ln / 2, ang), pol(cx + 80, cy - 20, 0, ang + 4), pol(cx + 80, cy - 20, ln / 2, ang)]
    L += stroke(p, brush_width(S, 10, 70 * k), brush_time(S, min_dur=0.14), 0.95 * k ** 0.6, seed + 1,
                nb=40, dry=0.45, wet=6)
    return L


def r_deok(S, k, p0=(800, 300), p1=(1060, 640), p2=(1320, 900), seed=400):   # j/u 덕: 채로 딱 → 굵고 짧은 점획
    L = [blob(p0[0] + 50, p0[1] + 50, 100 * k, 0.95 * k ** 0.6, seed, T=lambda d: 0.04 * d, rough=0.35, rim=0.2,
              halo=0.25)]
    L += stroke([p0, p1, p2], brush_width(S, 10, 170 * k, gamma=0.8), brush_time(S, min_dur=0.16),
                0.95 * k ** 0.6, seed + 1, nb=44, dry=0.55, wet=5, start=0.03, end=0.5)
    L.append(splatter(p1[0], p1[1], 40, 80, 420, 2, 14, 0.85 * k, seed + 2, T0=0.03))
    return L


def r_gideok(S, k, cx=860, cy=520, seed=500):   # k/i 기덕: 앞꾸밈 '기'(가벼운 획) + '덕'(굵은 획)
    t2 = S.onsets[1] if len(S.onsets) > 1 else 0.07
    t2 = max(t2, 0.08)
    L = [wash(cx + 130, cy + 40, 300, 0.08 * k, seed, T0=0.1, grow=0.9)]
    L += stroke([(cx - 380, cy - 200), (cx - 240, cy - 60), (cx - 180, cy + 120)], lambda s: 55 * (1 - 0.4 * s),
                lambda s: 0.1 * s, 0.6 * k, seed + 1, nb=22, dry=0.6)
    L += stroke([(cx + 20, cy - 250), (cx + 230, cy + 20), (cx + 450, cy + 330)],
                brush_width(S, 12, 165 * k), lambda s: t2 + 0.16 * s, 0.95 * k ** 0.6, seed + 2, nb=44,
                dry=0.45, wet=5)
    L.append(splatter(cx + 230, cy + 20, 32, 100, 400, 2, 13, 0.8 * k, seed + 3, T0=t2))
    return L


def r_deo(S, k, pts=((380, 600), (900, 470), (1540, 520)), seed=600):   # l/o 더: 가볍게 끄는 소리 → 가로로 쓸어낸 획
    L = [wash(960, 540, 420, 0.07 * k, seed, T0=0.1, grow=1.0, aspect=2.4, ang=-0.08)]
    L += stroke(list(pts), brush_width(S, 14, 80 * k), brush_time(S, stretch=1.5, min_dur=0.3, mix=0.6),
                0.82 * k ** 0.7, seed + 1, nb=46, dry=0.7, wet=7, end=0.4)
    return L


def r_deororeo(S, k):   # p 더러러러: 굴린 소리 → 알갱이마다 점이 한 줄로 떨어지고 갈필이 이어 준다
    rng = np.random.default_rng(700)
    ons = S.onsets
    L = []
    centers = []
    for i, t in enumerate(ons):
        fr = i / max(len(ons) - 1, 1)
        x, y = 470 + 1000 * fr + rng.normal() * 25, 330 + 420 * fr ** 0.8 + 160 * sin(fr * pi) + rng.normal() * 25
        centers.append((x, y))
        e = float(S.env_at(t + 0.02))
        L.append(blob(x, y, 65 + 75 * e, 0.4 + 0.55 * e, 701 + i, T=lambda d, t=t: t + 0.07 * d, rough=0.35,
                      rim=0.35, halo=0.35, tau=0.06))
    span = ons[-1] + 0.15
    L += stroke(centers, lambda s: 10 + 18 * S.env_at(s * span), lambda s: s * span, 0.55, 720, nb=16, dry=0.85,
                start=0.02, end=0.1)
    return L


def r_nogo(S, k, cx=960, cy=700, R=290, seed=800):   # v/e 북 노고: 깊은 북 → 낮게 깔린 짙은 번짐 위로 산처럼 오르는 담묵
    L = [wash(cx + 60, cy - 160, 560 * (0.8 + 0.2 * k), 0.1, seed, col=GREEN, T0=0.35, grow=1.4, aspect=1.9,
              rough=0.5)]
    L.append(blob(cx - 40, cy - 120, R * 1.6, 0.2 * k, seed + 1, T=lambda d: 0.15 + 0.9 * d ** 1.2, rough=0.55,
                  rim=0.4, halo=0.5, inner=0.5, aspect=1.8, tau=0.2))
    L.append(blob(cx, cy, R * (0.8 + 0.2 * k), 0.85 * k, seed + 2, T=bloom_time(S, grow=0.2, stretch=0.5),
                  rough=0.3, rim=0.45, halo=0.45, aspect=1.5, tau=0.12, core=0.15))
    for i, t in enumerate(S.onsets[1:3]):
        L.append(blob(cx + (230 if i == 0 else -260), cy + 30, R * 0.4, 0.7 * k, seed + 5 + i,
                      T=lambda d, t=t: t + 0.12 * d, rough=0.35, rim=0.4, halo=0.4, aspect=1.3))
    return L


def r_jeolgo(S, k, y=520, seed=900):   # b/r 북 절고: 북 테를 끊어 치는 소리 → 화면을 가르는 마른 붓
    L = [stroke([(200, y + 30), (900, y - 10), (1720, y - 60)], brush_width(S, 30, 150 * k, gamma=0.5),
                brush_time(S, stretch=0.6, min_dur=0.22), 0.92 * k ** 0.6, seed, nb=70, dry=0.7, end=0.35)]
    L = L[0]
    if len(S.onsets) > 1 and k > 0.8:
        t = S.onsets[1]
        L += stroke([(620, y + 150), (1020, y + 135), (1420, y + 115)], lambda s: 70, lambda s: t + 0.15 * s, 0.6,
                    seed + 1, nb=40, dry=0.8)
    L.append(splatter(220, y + 30, 18, 20, 180, 2, 10, 0.8 * k, seed + 2, ang=pi, spread=0.6))
    return L


def r_call(S, k, pts, w0, w1, wcol, wpos, seed, dot=None, dry=0.35, nb=44, stretch=1.4):
    """추임새: 목소리 세기를 따라 굵어졌다 가늘어지는 한 획 + 옅은 담채."""
    L = [wash(wpos[0], wpos[1], wpos[2], 0.28, seed, col=wcol, T0=0.0, grow=0.8, rough=0.45)]
    L += stroke(pts, brush_width(S, w0, w1, gamma=0.8), brush_time(S, stretch=stretch, min_dur=0.35, mix=0.5),
                0.88, seed + 1, nb=nb, dry=dry, wet=6, end=0.3)
    if dot:
        x, y, r, t = dot
        L.append(blob(x, y, r, 0.95, seed + 2, T=lambda d: t + 0.1 * d, rough=0.35, rim=0.3, halo=0.35, core=0.1))
    return L


RECIPES = {
    "a": ("ji_a", "kkwaenggwari_ji_strong", r_ji),
    "s": ("roll_s", "kkwaenggwari_roll_strong", r_roll),
    "q": ("gaek_q", "kkwaenggwari_gaek_strong", r_gaek),
    "w": ("gaet_w", "kkwaenggwari_gaet_strong", r_gaet),
    "d": ("jing_d", "jing_strong", r_jing),
    "f": ("jing_f", "jing_soft", r_jing_soft),
    "g": ("deong_g", "janggu_deong_strong", r_deong),
    "t": ("deong_t", "janggu_deong_mid",
          lambda S, k: r_deong(S, k, cx=1080, cy=500, R=210, ang=-110, seed=320)),
    "h": ("kung_h", "janggu_kung_strong", r_kung),
    "y": ("kung_y", "janggu_kung_mid", lambda S, k: r_kung(S, k, cx=860, cy=480, R=250, seed=220)),
    "j": ("deok_j", "janggu_deok_strong", r_deok),
    "u": ("deok_u", "janggu_deok_mid",
          lambda S, k: r_deok(S, k, p0=(1200, 280), p1=(940, 620), p2=(720, 860), seed=420)),
    "k": ("gideok_k", "janggu_gideok_strong", r_gideok),
    "i": ("gideok_i", "janggu_gideok_mid", lambda S, k: r_gideok(S, k, cx=1040, cy=560, seed=520)),
    "l": ("deo_l", "janggu_deo_strong", r_deo),
    "o": ("deo_o", "janggu_deo_mid",
          lambda S, k: r_deo(S, k, pts=((560, 330), (1000, 520), (1380, 780)), seed=620)),
    "p": ("deororeo_p", "janggu_deororeo_strong", r_deororeo),
    "v": ("nogo_v", "buk_nogo_strong", r_nogo),
    "e": ("nogo_e", "buk_nogo_mid", lambda S, k: r_nogo(S, k, cx=900, cy=640, R=240, seed=820)),
    "b": ("jeolgo_b", "buk_jeolgo_strong", r_jeolgo),
    "r": ("jeolgo_r", "buk_jeolgo_mid", lambda S, k: r_jeolgo(S, k, y=470, seed=920)),
    "z": ("eolssu_z", "chuimsae_eolssu",
          lambda S, k: r_call(S, k, [(500, 780), (820, 430), (1180, 640), (1480, 300)], 12, 95, VERM,
                              (1000, 560, 330), 1000)),
    "x": ("eolssigu_x", "chuimsae_eolssigu",
          lambda S, k: r_call(S, k, [(330, 640), (560, 360), (700, 640), (520, 600), (900, 380), (1060, 660),
                                     (880, 600), (1300, 400), (1560, 560)], 10, 80, OCHRE, (950, 520, 380), 1010,
                              stretch=1.2)),
    "c": ("jota_c", "chuimsae_jota",
          lambda S, k: r_call(S, k, [(560, 380), (880, 340), (980, 420), (820, 760)], 12, 90, ROSE,
                              (1260, 560, 300), 1020, dot=(1260, 560, 80, S.onsets[1] if len(S.onsets) > 1 else 0.6),
                              stretch=0.9)),
    "n": ("ssu_n", "chuimsae_ssu",
          lambda S, k: r_call(S, k, [(700, 840), (980, 560), (1360, 240)], 6, 60, INDIGO, (1000, 560, 300), 1030,
                              dry=0.85, nb=30)),
    "m": ("eoi_m", "chuimsae_eoi",
          lambda S, k: r_call(S, k, [(480, 420), (960, 720), (1440, 400)], 14, 70, GREEN, (960, 560, 340), 1040,
                              dry=0.5)),
}

# 강/중 짝: 중은 강보다 옅고 작게 (실제 소리 크기 비율로)
PAIRS = {"t": "g", "y": "h", "u": "j", "i": "k", "o": "l", "e": "v", "r": "b"}
FADE = {"d": (2.9, 3.85), "f": (2.9, 3.85)}


def build(key):
    name, sound, fn = RECIPES[key]
    S = Sound(sound)
    k = 1.0
    if key in PAIRS:
        k = float(np.clip((S.peak / Sound(RECIPES[PAIRS[key]][1]).peak) ** 0.8, 0.5, 1.0))
    return name, [L for L in fn(S, k) if not L.empty], FADE.get(key, (2.4, 3.75))


def render(key, out_dir):
    name, layers, fade = build(key)
    out = out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
           "-g", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        img = frame(layers, i / FPS, fade) if 0 < i < N - 1 else np.full((H, W, 3), 255, np.uint8)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out.relative_to(ROOT), flush=True)


def preview(keys, path, times=(0.1, 0.3, 0.8, 2.0, 3.2)):
    """키마다 한 줄: 몇 시점의 장면을 한지 위에 겹쳐 본다."""
    paper = cv2.resize(cv2.imread(str(ROOT / "assets" / "hanji.jpg")), (W, H)).astype(np.float32)
    tw, th = 384, 216
    sheet = np.full((th * len(keys), tw * len(times) + 60, 3), 255, np.uint8)
    for r, key in enumerate(keys):
        _, layers, fade = build(key)
        cv2.putText(sheet, key, (15, r * th + 120), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 2)
        for c, t in enumerate(times):
            img = np.minimum(frame(layers, t, fade).astype(np.float32), paper).astype(np.uint8)
            sheet[r * th:(r + 1) * th, 60 + c * tw:60 + (c + 1) * tw] = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", path, flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--preview":
        keys = args[2:] or list(RECIPES)
        preview(keys, Path(args[1]))
    else:
        out_dir = ROOT / "clips" / "sumuk"
        out_dir.mkdir(parents=True, exist_ok=True)
        for key in args or list(RECIPES):
            render(key, out_dir)
