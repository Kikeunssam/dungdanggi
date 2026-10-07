#!/usr/bin/env python3
"""뱅크 3 (자개 나전칠기) 샘플 영상 4개.

검은 옻칠 바탕 위에 자개 조각으로 박은 무늬가 규칙적으로 되풀이되며 나타났다 사라진다.
자개는 작은 조각을 이어 붙인 모자이크(조각마다 조금씩 다른 무지갯빛, 조각 사이 가는 이음선)로 그리고,
빛이 비스듬히 훑고 지나가며 분홍·하늘·연두빛으로 반짝인다.

검은 바탕(0,0,0)에 그려서 화면에서는 옻칠 배경(assets/lacquer.jpg) 위에 '밝게(lighten)'로 겹친다.
1920x1080, 30fps, 4초, 첫·끝 프레임은 검정.

    python3 tools/najeon.py           # 4개 전부 → clips/najeon/, assets/lacquer.jpg
    python3 tools/najeon.py nj02      # 일부만
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
SHIFT = 4
SC = 1 << SHIFT


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def fbm(h, w, cell, rng, octaves=4):
    out = np.zeros((h, w), np.float32)
    a, tot, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        if c < 1.5:
            break
        gh, gw = int(h / c) + 3, int(w / c) + 3
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        out += a * cv2.resize(g, (int(gw * c), int(gh * c)), interpolation=cv2.INTER_CUBIC)[:h, :w]
        tot += a * a
        a *= 0.5
        c /= 2
    return out / np.sqrt(tot)


# ---------------------------------------------------------------- 자개 재질

class Pearl:
    """자개 모자이크: 조각(보로노이 셀)마다 색조·밝기가 다르고, 조각 사이에 가는 이음선."""

    def __init__(self, seed, cell=26, sweep_ang=25, sweep_t=(0.7, 2.9)):
        rng = np.random.default_rng(seed)
        pts = np.zeros((H, W), np.uint8) + 255
        n = int(W * H / cell ** 2)
        xs, ys = rng.integers(0, W, n), rng.integers(0, H, n)
        pts[ys, xs] = 0
        _, labels = cv2.distanceTransformWithLabels(pts, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_CCOMP)
        lab = labels.astype(np.int32)
        k = lab.max() + 1
        cell_h = rng.uniform(0, 1, k).astype(np.float32)
        cell_v = rng.uniform(0.8, 1.0, k).astype(np.float32)
        cell_a = rng.uniform(0, pi, k).astype(np.float32)
        cell_p = rng.uniform(0, 2 * pi, k).astype(np.float32)
        flow = fbm(H, W, 420, rng, 3)
        self.hue0 = (cell_h[lab] * 0.35 + 0.5 + 0.35 * flow) % 1.0       # 0..1
        yy0, xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
        ca, sa = np.cos(cell_a[lab]), np.sin(cell_a[lab])
        streak = np.sin((xx0 * ca + yy0 * sa) / 7.0 + cell_p[lab])        # 조개껍데기 결
        self.val = cell_v[lab] * (0.9 + 0.06 * streak + 0.04 * fbm(H, W, 8, rng, 2))
        self.streak = streak
        seam = (cv2.Sobel(lab.astype(np.float32), cv2.CV_32F, 1, 0) != 0) | \
               (cv2.Sobel(lab.astype(np.float32), cv2.CV_32F, 0, 1) != 0)
        self.seam = 1 - 0.38 * cv2.GaussianBlur(seam.astype(np.float32), (0, 0), 0.6)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        a = radians(sweep_ang)
        self.proj = (xx * cos(a) + yy * sin(a))
        self.pmin, self.pmax = float(self.proj.min()), float(self.proj.max())
        self.sweep_t = sweep_t

    def color(self, t):
        """t초의 자개 색 (BGR float 0..1)."""
        t0, t1 = self.sweep_t
        f = (t - t0) / (t1 - t0)
        pos = self.pmin - 500 + f * (self.pmax - self.pmin + 1000)
        band = np.exp(-((self.proj - pos) / 260.0) ** 2)
        hue = (self.hue0 + 0.25 * band + 0.05 * t + 0.04 * self.streak) % 1.0
        sat = 0.1 + 0.2 * band + 0.06 * np.sin(6.28 * self.hue0)
        val = np.clip(self.val * (0.86 + 0.3 * band), 0, 1)
        hsv = np.dstack([hue * 180, sat * 255, val * 255]).astype(np.uint8)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR).astype(np.float32) / 255
        warm = np.array([0.93, 0.97, 1.0], np.float32)   # 살짝 따뜻한 진주빛
        return rgb * warm * self.seam[..., None]


def fade_io(t, t_in, t_out0=2.7, t_out1=3.7):
    a = smooth((t - t_in) / 0.35)
    return a * (1 - smooth((t - t_out0) / (t_out1 - t_out0)))


def P(pts):
    return (np.asarray(pts, np.float64) * SC).astype(np.int32)


def fill(mask, pts, v):
    cv2.fillPoly(mask, [P(pts)], int(v), cv2.LINE_AA, SHIFT)


def ell(mask, c, ax, ang, v):
    cv2.ellipse(mask, (int(c[0] * SC), int(c[1] * SC)), (max(1, int(ax[0] * SC)), max(1, int(ax[1] * SC))),
                ang, 0, 360, int(v), -1, cv2.LINE_AA, SHIFT)


def line(mask, a, b, v, th):
    cv2.line(mask, (int(a[0] * SC), int(a[1] * SC)), (int(b[0] * SC), int(b[1] * SC)), int(v), max(1, int(th)),
             cv2.LINE_AA, SHIFT)


def rot(pts, c, ang, s=1.0, sx=1.0):
    ca, sa = cos(ang), sin(ang)
    out = []
    for x, y in pts:
        x, y = x * s * sx, y * s
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


# ---------------------------------------------------------------- nj01 솔잎 부채

def draw_fan(mask, c, r, ang, v):
    """솔잎 다발: 아래 꼭지에서 위로 부채처럼 퍼지는 가는 바늘들."""
    n = 15
    for i in range(n):
        a = radians(-155 + 130 * i / (n - 1)) + ang
        tip = (c[0] + r * cos(a), c[1] + r * sin(a))
        w = r * 0.045
        nx, ny = -sin(a) * w, cos(a) * w
        base = (c[0] + 0.12 * r * cos(a), c[1] + 0.12 * r * sin(a))
        fill(mask, [(base[0] + nx, base[1] + ny), (tip[0] + nx * 0.3, tip[1] + ny * 0.3),
                    (tip[0] - nx * 0.3, tip[1] - ny * 0.3), (base[0] - nx, base[1] - ny)], v)
    ell(mask, c, (r * 0.13, r * 0.09), np.degrees(ang), v)
    a = pi / 2 + ang
    line(mask, c, (c[0] + r * 0.32 * cos(a), c[1] + r * 0.32 * sin(a)), v, r * 0.05)


def nj01(t, st):
    mask = np.zeros((H, W), np.uint8)
    for (x, y, r, ang, row) in st["tiles"]:
        t_in = 0.08 * row + 0.03 * ((x // 170) % 3)
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        s = 0.6 + 0.4 * ease_out((t - t_in) / 0.45)
        draw_fan(mask, (x, y), r * s, ang, 255 * a)
    return mask


def nj01_setup(rng):
    tiles = []
    dx, dy = 175, 150
    for row, y in enumerate(np.arange(40, H + 120, dy)):
        off = dx / 2 if row % 2 else 0
        for x in np.arange(-40 + off, W + 100, dx):
            tiles.append((x + rng.normal() * 6, y + rng.normal() * 6, 78 + rng.normal() * 5,
                          radians(rng.normal() * 12 + (8 if row % 2 else -8)), row))
    return {"tiles": tiles}


# ---------------------------------------------------------------- nj02 나비와 꽃

def draw_butterfly(mask, c, s, ang, flap, v):
    for side in (-1, 1):
        sx = side * flap
        fore = rot([(0, -4), (30, -48), (78, -62), (96, -40), (70, -6), (8, 2)], c, ang, s, sx)
        hind = rot([(4, 4), (60, 6), (74, 34), (52, 66), (22, 56), (6, 18)], c, ang, s, sx)
        fill(mask, fore, v)
        fill(mask, hind, v)
        for a, b in [((8, -2), (80, -50)), ((10, 0), (86, -30)), ((8, 6), (60, 50)), ((8, 8), (34, 56))]:
            pa, pb = rot([a, b], c, ang, s, sx)
            line(mask, pa, pb, 0, 2.2 * s)   # 새긴 잎맥
        ant = rot([(2, -20), (14, -58)], c, ang, s, sx)
        line(mask, ant[0], ant[1], v, 2.5 * s)
    ell(mask, c, (6 * s, 34 * s), np.degrees(ang) + 90, v)


def draw_flower(mask, c, r, ang, v):
    for i in range(5):
        a = ang + i * 2 * pi / 5
        ell(mask, (c[0] + r * 0.55 * cos(a), c[1] + r * 0.55 * sin(a)), (r * 0.5, r * 0.3), np.degrees(a), v)
    ell(mask, c, (r * 0.22, r * 0.22), 0, 0)
    ell(mask, c, (r * 0.14, r * 0.14), 0, v)
    for i in range(5):
        a = ang + i * 2 * pi / 5
        line(mask, (c[0] + r * 0.25 * cos(a), c[1] + r * 0.25 * sin(a)),
             (c[0] + r * 0.85 * cos(a), c[1] + r * 0.85 * sin(a)), 0, max(2, r * 0.04))


def nj02(t, st):
    mask = np.zeros((H, W), np.uint8)
    for (kind, x, y, s, ang, d, ph) in st["items"]:
        t_in = 0.1 + d / 1400
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        g = 0.5 + 0.5 * ease_out((t - t_in) / 0.5)
        if kind == "b":
            flap = 0.55 + 0.45 * abs(cos(2.2 * pi * (t - t_in) + ph))
            draw_butterfly(mask, (x, y), s * g, ang, flap, 255 * a)
        else:
            draw_flower(mask, (x, y), s * g, ang + 0.4 * (t - t_in), 255 * a)
    return mask


def nj02_setup(rng):
    items = []
    dx, dy = 250, 210
    for j, y in enumerate(np.arange(100, H + 60, dy)):
        for i, x in enumerate(np.arange(130, W / 2, dx)):
            kind = "b" if (i + j) % 2 == 0 else "f"
            s = 0.9 if kind == "b" else 52
            ang = radians(rng.normal() * 10)
            ph = rng.uniform(0, pi)
            for mx, sg in ((x, 1), (W - x, -1)):       # 좌우 대칭 반복
                d = abs(mx - W / 2) + abs(y - H / 2) * 0.8
                items.append((kind, mx, y, s, sg * ang, d, ph))
    return {"items": items}


# ---------------------------------------------------------------- nj03 수복 원문과 박쥐

def draw_medallion(mask, c, r, v):
    ell(mask, c, (r, r), 0, v)
    ell(mask, c, (r * 0.84, r * 0.84), 0, 0)
    ell(mask, c, (r * 0.74, r * 0.74), 0, v)
    # 가운데 기하학 문(원형 안의 대칭 빗살 미로) — 새겨서 비운 선
    u = r * 0.13
    for k in (-2, 0, 2):
        line(mask, (c[0] - 4.2 * u, c[1] + k * u), (c[0] + 4.2 * u, c[1] + k * u), 0, u * 0.55)
    for k in (-3, 3):
        line(mask, (c[0] + k * u, c[1] - 2 * u), (c[0] + k * u, c[1] + 2 * u), 0, u * 0.55)
    line(mask, (c[0], c[1] - 4.3 * u), (c[0], c[1] - 2 * u), 0, u * 0.55)
    line(mask, (c[0], c[1] + 2 * u), (c[0], c[1] + 4.3 * u), 0, u * 0.55)
    for k in (-1, 1):
        line(mask, (c[0] + k * u, c[1] - 4 * u), (c[0] + k * 2.6 * u, c[1] - 3.2 * u), 0, u * 0.5)
        line(mask, (c[0] + k * u, c[1] + 4 * u), (c[0] + k * 2.6 * u, c[1] + 3.2 * u), 0, u * 0.5)
        line(mask, (c[0] + k * 3 * u, c[1]), (c[0] + k * 1 * u, c[1]), 0, u * 0.5)


def draw_bat(mask, c, s, ang, flip, v):
    wing = [(0, -8), (20, -30), (48, -42), (80, -38), (102, -18), (96, -2), (84, -6), (78, 10), (64, 2), (54, 18),
            (40, 8), (26, 20), (8, 12)]
    for side in (-1, 1):
        fill(mask, rot(wing, c, ang, s, side * flip), v)
    ell(mask, c, (9 * s, 15 * s), np.degrees(ang), v)
    for side in (-1, 1):
        ear = rot([(-3, -12), (-7 * side * -1, -24), (3, -14)], c, ang, s, side)
        fill(mask, ear, v)
    ell(mask, rot([(0, -4)], c, ang, s)[0], (2.4 * s, 2.4 * s), 0, 0)


def nj03(t, st):
    mask = np.zeros((H, W), np.uint8)
    for row in st["rows"]:
        side, t_in, items = row
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        off = side * (1 - ease_out((t - t_in) / 0.7)) * 900
        for kind, x, y, s, ang in items:
            if kind == "m":
                draw_medallion(mask, (x + off, y), s, 255 * a)
            else:
                draw_bat(mask, (x + off, y), s, ang, 1.0, 255 * a)
    return mask


def nj03_setup(rng):
    rows = []
    dx, dy = 300, 250
    for j, y in enumerate(np.arange(110, H + 140, dy)):
        items = []
        off = dx / 2 if j % 2 else 0
        for x in np.arange(-60 + off, W + 200, dx):
            items.append(("m", x, y, 72, 0))
            ang = radians(rng.uniform(-35, 35))
            items.append(("b", x + dx / 2, y - 30 + rng.normal() * 10, 0.72, ang))
            items.append(("b", x + dx / 2 + rng.normal() * 15, y + 80, 0.58, radians(rng.uniform(140, 220))))
        rows.append((1 if j % 2 else -1, 0.05 + 0.18 * j, items))
    return {"rows": rows}


# ---------------------------------------------------------------- nj04 넝쿨 당초 띠

def nj04_setup(rng):
    bands = []
    for b, cx in enumerate([330, 960, 1590]):
        ys = np.arange(-40, H + 40, 2.0)
        amp, per = 95, 420
        ph = b * pi
        xs = cx + amp * np.sin(2 * pi * ys / per + ph)
        stem = np.stack([xs, ys], 1)
        orn = []
        for k, yc in enumerate(np.arange(per / 4 - ph / (2 * pi) * per, H + per, per / 2)):
            sgn = 1 if k % 2 == 0 else -1
            i = int(np.clip((yc + 40) / 2, 0, len(ys) - 1))
            px, py = stem[i]
            orn.append(("curl", px, py, -sgn, yc))
            orn.append(("leaf", px - sgn * 40, py - 50, -sgn, yc - 30))
            orn.append(("flower", px - sgn * 92, py + 6, -sgn, yc + 10))
        dots = [(cx + s * 245, y) for s in (-1, 1) for y in np.arange(20, H, 54)]
        bands.append({"stem": stem, "orn": orn, "dots": dots, "t0": 0.05 + 0.22 * b})
    return {"bands": bands}


def nj04(t, st):
    mask = np.zeros((H, W), np.uint8)
    for bd in st["bands"]:
        t0 = bd["t0"]
        a = fade_io(t, t0)
        if a <= 0:
            continue
        v = 255 * a
        front = -40 + (H + 120) * ease_out((t - t0) / 1.3)     # 위에서 아래로 자라는 덩굴
        stem = bd["stem"][bd["stem"][:, 1] < front]
        if len(stem) > 1:
            cv2.polylines(mask, [P(stem)], False, int(v), 13, cv2.LINE_AA, SHIFT)
        for kind, x, y, sgn, yc in bd["orn"]:
            g = ease_out((front - yc) / 160)
            if g <= 0:
                continue
            if kind == "curl":
                th = np.linspace(0, 1.7 * pi * g, 60)
                rr = 62 * (1 - th / (2.2 * pi))
                pts = np.stack([x - sgn * 62 + sgn * rr * np.cos(th), y + rr * np.sin(th) * -1], 1)
                cv2.polylines(mask, [P(pts)], False, int(v), 9, cv2.LINE_AA, SHIFT)
            elif kind == "leaf":
                ell(mask, (x, y), (44 * g, 15 * g), -sgn * 35, v)
                line(mask, (x - 30 * g, y + sgn * 20 * g * 0), (x + 30 * g, y), 0, 2.5)
            else:
                for i in range(8):
                    aa = i * pi / 4
                    ell(mask, (x + 26 * g * cos(aa), y + 26 * g * sin(aa)), (22 * g, 11 * g), np.degrees(aa), v)
                ell(mask, (x, y), (14 * g, 14 * g), 0, 0)
                ell(mask, (x, y), (8 * g, 8 * g), 0, v)
        for x, y in bd["dots"]:
            if y > front:
                continue
            for i in range(4):
                aa = pi / 4 + i * pi / 2
                ell(mask, (x + 9 * cos(aa), y + 9 * sin(aa)), (8, 5), np.degrees(aa), v)
    return mask


CLIPS = {
    "nj01": ("nj01_pine_fans", nj01, nj01_setup, 25),
    "nj02": ("nj02_butterfly_flower", nj02, nj02_setup, -20),
    "nj03": ("nj03_longevity_bats", nj03, nj03_setup, 60),
    "nj04": ("nj04_flower_vine", nj04, nj04_setup, 15),
}


def build(key):
    name, fn, setup, sweep = CLIPS[key]
    seed = int(key[2:])
    rng = np.random.default_rng(seed)
    st = setup(rng)
    pearl = Pearl(seed + 10, sweep_ang=sweep)

    def frame(t):
        m = fn(t, st).astype(np.float32) / 255
        if m.max() == 0:
            return np.zeros((H, W, 3), np.uint8)
        m = cv2.GaussianBlur(m, (0, 0), 0.5)
        return np.clip(pearl.color(t) * m[..., None] * 255 + 0.5, 0, 255).astype(np.uint8)
    return name, frame


def render(key, out_dir):
    name, frame = build(key)
    out = out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
           "-g", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        img = frame(i / FPS) if 0 < i < N - 1 else np.zeros((H, W, 3), np.uint8)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out.relative_to(ROOT), flush=True)


def lacquer():
    """검은 옻칠 바탕: 거의 검정에 아주 옅은 자줏빛 윤기와 붓결."""
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sheen = np.exp(-(((xx - W * 0.3) / (W * 0.7)) ** 2 + ((yy - H * 0.25) / (H * 0.9)) ** 2))
    grain = cv2.resize(cv2.GaussianBlur(rng.standard_normal((H // 4, W)).astype(np.float32), (0, 0), 1.0), (W, H))
    base = np.array([16, 9, 12], np.float32)       # BGR: 자줏빛 도는 검정
    img = base * (0.7 + 0.6 * sheen[..., None]) + 1.2 * grain[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    keys = sys.argv[1:] or list(CLIPS)
    out_dir = ROOT / "clips" / "najeon"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not sys.argv[1:]:
        cv2.imwrite(str(ROOT / "assets" / "lacquer.jpg"), lacquer(), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("wrote assets/lacquer.jpg")
    for k in keys:
        render(k, out_dir)
