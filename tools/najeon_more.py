#!/usr/bin/env python3
"""뱅크 3 (자개) 나머지 22개: 단순한 기하 반복과 화려한 그림 무늬를 섞었다.

단순: 줄무늬, 마름모 격자, 물방울, 빗살, 동심원, 귀갑(육각), 뇌문 띠, 칠보, 대나무, 별빛, 물결
화려: 학, 국화, 매화 가지, 모란, 구름, 연꽃, 물고기, 만화경 꽃, 포도 덩굴, 소나무 가지, 꽃 액자

자개 재질·바탕·형식은 najeon.py 와 같다 (검정 위에 그리고 옻칠 위에 lighten).

    python3 tools/najeon_more.py            # 22개 전부 → clips/najeon/
    python3 tools/najeon_more.py nj05 nj16  # 일부만
    python3 tools/najeon_more.py --preview out.jpg
"""
import subprocess
import sys
from math import cos, sin, pi, radians, atan2, hypot
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from najeon import (ROOT, W, H, FPS, N, SC, SHIFT, Pearl, smooth, ease_out, fade_io, P, fill, ell, line, rot,
                    draw_fan, draw_flower, lacquer)


def ring(mask, c, r, v, th, a0=0, a1=360, rot_deg=0):
    cv2.ellipse(mask, (int(c[0] * SC), int(c[1] * SC)), (max(1, int(r * SC)), max(1, int(r * SC))), rot_deg,
                a0, a1, int(v), max(1, int(th)), cv2.LINE_AA, SHIFT)


def poly(mask, pts, v, th, closed=False):
    cv2.polylines(mask, [P(pts)], closed, int(v), max(1, int(th)), cv2.LINE_AA, SHIFT)


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def partial(pts, f):
    """폴리라인의 앞쪽 f(0..1)만."""
    pts = np.asarray(pts, np.float64)
    if f <= 0 or len(pts) < 2:
        return pts[:0]
    seg = np.hypot(*np.diff(pts, axis=0).T)
    L = np.concatenate([[0], np.cumsum(seg)])
    target = f * L[-1]
    k = int(np.searchsorted(L, target))
    if k >= len(pts):
        return pts
    a = (target - L[k - 1]) / max(seg[k - 1], 1e-9)
    return np.vstack([pts[:k], pts[k - 1] + a * (pts[k] - pts[k - 1])])


def blank():
    return np.zeros((H, W), np.uint8)


# ================================================================ 단순한 반복

def nj05(t, st):   # 줄무늬: 굵고 가는 띠가 좌우에서 번갈아 미끄러져 들어온다
    m = blank()
    for j, (y, th) in enumerate(st):
        a = fade_io(t, 0.05 * j)
        if a <= 0:
            continue
        side = 1 if j % 2 else -1
        off = side * (1 - ease_out((t - 0.05 * j) / 0.6)) * W
        cv2.rectangle(m, (int(off - 10), int(y - th / 2)), (int(off + W + 10), int(y + th / 2)), int(255 * a), -1)
    return m


def nj05_s(rng):
    out, y, j = [], 30, 0
    while y < H + 20:
        th = 34 if j % 3 == 0 else 10
        out.append((y, th))
        y += th / 2 + 44 + (30 if j % 3 == 2 else 0)
        j += 1
        y += th / 2
    return out


def nj06(t, st):   # 마름모 격자: 빗선이 그어지고, 만나는 자리에 점이 박힌다
    m = blank()
    for k, (a0, b0, t_in) in enumerate(st["lines"]):
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        f = ease_out((t - t_in) / 0.7)
        p = partial([a0, b0], f)
        if len(p) > 1:
            line(m, p[0], p[-1], 255 * a, 7)
    for (x, y, t_in) in st["dots"]:
        a = fade_io(t, t_in)
        if a > 0:
            r = 14 * ease_back((t - t_in) / 0.3)
            ell(m, (x, y), (r, r), 45, 255 * a)
            ell(m, (x, y), (r * 0.45, r * 0.45), 0, 0)
    return m


def nj06_s(rng):
    lines, dots = [], []
    s, k = 150, 0.7
    for i, c in enumerate(np.arange(-H / k, W + H / k, s)):
        lines.append(((c, 0), (c + H / k, H), 0.04 * (i % 12)))
        lines.append(((c, H), (c + H / k, 0), 0.04 * (i % 12) + 0.15))
    for i in np.arange(-30, 30):
        for j in np.arange(-30, 30):
            x = i * s / 2 + j * s / 2 + s / 4
            y = (j - i) * (k * s / 2)
            x, y = x - 3 * s / 4 + s / 2, y + H / 2
            if -20 < x < W + 20 and -20 < y < H + 20:
                dots.append((x, y, 0.75 + 0.0004 * x))
    return {"lines": lines, "dots": dots}


def nj07(t, st):   # 물방울: 가운데서 물결처럼 동그라미가 퐁퐁
    m = blank()
    for x, y, r, d in st:
        t_in = 0.05 + d / 1500
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        rr = r * ease_back((t - t_in) / 0.35)
        ell(m, (x, y), (rr, rr), 0, 255 * a)
        if r > 20:
            ell(m, (x, y), (rr * 0.5, rr * 0.5), 0, 0)
            ell(m, (x, y), (rr * 0.3, rr * 0.3), 0, 255 * a)
    return m


def nj07_s(rng):
    out = []
    dx, dy = 120, 104
    for j, y in enumerate(np.arange(20, H + 60, dy)):
        for x in np.arange(20 + (dx / 2 if j % 2 else 0), W + 60, dx):
            r = 30 if (j + int(x // dx)) % 2 == 0 else 13
            out.append((x, y, r, hypot(x - W / 2, y - H / 2)))
    return out


def nj08(t, st):   # 빗살: 미리 그린 빗살을 사선으로 훑는 빛이 드러낸다
    front = -400 + (W + 1300) * ease_out((t - 0.05) / 1.4)
    ramp = np.clip((front - st["proj"]) / 220, 0, 1)
    a = fade_io(t, 0.0)
    return (st["mask"] * ramp * a).astype(np.uint8)


def nj08_s(rng):
    m = blank()
    for i, c in enumerate(np.arange(-H, W + H, 64)):
        th = 22 if i % 4 == 0 else 9
        line(m, (c, H + 10), (c + H * 0.58, -10), 255, th)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return {"mask": m.astype(np.float32), "proj": xx + 0.4 * yy}


def nj09(t, st):   # 동심원: 고리가 차례로 퍼지고 번갈아 반대로 돈다
    m = blank()
    c = (W / 2, H / 2)
    for k in range(1, 15):
        r = 68 * k
        t_in = 0.06 * k
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        rr = r * (0.85 + 0.15 * ease_out((t - t_in) / 0.4))
        spin = (40 if k % 2 else -40) * (t - t_in)
        th = 16 if k % 3 == 0 else 7
        gap = 18 if k % 2 else 40
        for s in range(0, 360, 90):
            ring(m, c, rr, 255 * a, th, s + gap / 2, s + 90 - gap / 2, spin)
    return m


def hexagon(c, r, rot0=0):
    return [(c[0] + r * cos(rot0 + i * pi / 3), c[1] + r * sin(rot0 + i * pi / 3)) for i in range(6)]


def nj10(t, st):   # 귀갑: 거북 등껍질 육각이 한쪽 모서리부터 번진다
    m = blank()
    for x, y, d, alt in st:
        t_in = 0.05 + d / 1800
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        g = ease_out((t - t_in) / 0.4)
        poly(m, hexagon((x, y), 66 * (0.7 + 0.3 * g)), 255 * a, 7, True)
        if alt:
            fill(m, hexagon((x, y), 34 * g), 255 * a)
            fill(m, hexagon((x, y), 16 * g), 0)
        else:
            ell(m, (x, y), (9 * g, 9 * g), 0, 255 * a)
    return m


def nj10_s(rng):
    out = []
    r = 72
    dx, dy = 1.5 * r, r * np.sqrt(3)
    for i, x in enumerate(np.arange(0, W + 2 * r, dx)):
        for y in np.arange(0 + (dy / 2 if i % 2 else 0), H + 2 * r, dy):
            out.append((x, y, hypot(x, y), (i + int(y // dy)) % 3 == 0))
    return out


def nj11(t, st):   # 뇌문 띠: 번개무늬 띠 세 줄이 왼쪽부터 이어 그려진다
    m = blank()
    for b, (yb, t0, sgn) in enumerate(st["bands"]):
        a = fade_io(t, t0)
        if a <= 0:
            continue
        front = -100 + (W + 200) * ease_out((t - t0) / 1.1)
        if sgn < 0:
            front = W + 100 - (W + 200) * ease_out((t - t0) / 1.1)
        u = 22
        for y in (yb - 5 * u, yb + 1.2 * u):
            x0, x1 = (0, front) if sgn > 0 else (front, W)
            line(m, (x0, y), (x1, y), 255 * a, 8)
        for x in np.arange(-4 * u, W + 4 * u, 5 * u):
            if (sgn > 0 and x > front) or (sgn < 0 and x < front):
                continue
            hook = [(x, yb), (x, yb - 4 * u), (x + 3 * u, yb - 4 * u), (x + 3 * u, yb - u), (x + u, yb - u),
                    (x + u, yb - 3 * u), (x + 2 * u, yb - 3 * u), (x + 2 * u, yb - 2 * u)]
            poly(m, hook, 255 * a, 8)
            line(m, (x, yb), (x + 5 * u, yb), 255 * a, 8)
    return m


def nj11_s(rng):
    return {"bands": [(250, 0.05, 1), (600, 0.3, -1), (950, 0.55, 1)]}


def nj12(t, st):   # 칠보: 겹친 동그라미 고리가 시계 방향으로 돌며 채워진다
    m = blank()
    for x, y, ang in st:
        t_in = 0.05 + ang / (2 * pi) * 1.1
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        sweep = 360 * ease_out((t - t_in) / 0.5)
        ring(m, (x, y), 64, 255 * a, 6, -90, -90 + sweep)
        if sweep > 300:
            ell(m, (x + 64, y), (7, 7), 0, 255 * a)
            ell(m, (x, y + 64), (7, 7), 0, 255 * a)
    return m


def nj12_s(rng):
    out = []
    for x in np.arange(0, W + 90, 90):
        for y in np.arange(0, H + 90, 90):
            out.append((x, y, (atan2(y - H / 2, x - W / 2) + pi / 2) % (2 * pi)))
    return out


def nj13(t, st):   # 대나무: 줄기가 아래서 위로 마디마디 자라고 잎이 돋는다
    m = blank()
    for x, wdt, t0, nodes, leaves in st:
        a = fade_io(t, t0)
        if a <= 0:
            continue
        top = H + 20 - (H + 80) * ease_out((t - t0) / 1.3)
        cv2.rectangle(m, (int(x - wdt / 2), int(top)), (int(x + wdt / 2), H + 20), int(255 * a), -1)
        for ny in nodes:
            if ny > top:
                line(m, (x - wdt / 2 - 3, ny), (x + wdt / 2 + 3, ny), 0, 4)
                line(m, (x - wdt / 2 - 4, ny + 7), (x + wdt / 2 + 4, ny + 7), 255 * a, 5)
        for ly, sg, ang in leaves:
            if ly > top + 40:
                g = ease_out((ly - top - 40) / 200)
                c = (x + sg * (wdt / 2 + 50 * g), ly - 20 * g)
                ell(m, c, (62 * g, 13 * g), np.degrees(ang) * sg, 255 * a)
                line(m, (c[0] - sg * 50 * g, c[1] + 4 * g * 0), (c[0] + sg * 45 * g, c[1]), 0, 2)
    return m


def nj13_s(rng):
    out = []
    for i, x in enumerate([150, 390, 560, 830, 1080, 1260, 1520, 1760]):
        wdt = rng.choice([22, 30, 38])
        nodes = list(np.arange(H - rng.uniform(80, 160), -40, -rng.uniform(140, 190)))
        leaves = [(ny + 6, rng.choice([-1, 1]), radians(rng.uniform(-30, -10))) for ny in nodes if rng.random() < 0.4]
        out.append((x, wdt, 0.05 + 0.08 * ((i * 3) % 8), nodes, leaves))
    return out


def nj14(t, st):   # 별빛: 작은 네 갈래 별들이 반짝반짝
    m = blank()
    for x, y, r, t_in, f, ph in st:
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        tw = 0.35 + 0.65 * abs(sin(2 * pi * f * (t - t_in) + ph))
        rr = r * (0.6 + 0.4 * tw)
        v = 255 * a * tw
        fill(m, [(x, y - rr), (x + rr * 0.22, y), (x, y + rr), (x - rr * 0.22, y)], v)
        fill(m, [(x - rr, y), (x, y + rr * 0.22), (x + rr, y), (x, y - rr * 0.22)], v)
        ell(m, (x, y), (rr * 0.18, rr * 0.18), 0, v)
    return m


def nj14_s(rng):
    out = []
    for _ in range(130):
        out.append((rng.uniform(0, W), rng.uniform(0, H), rng.choice([18, 26, 38, 64], p=[0.4, 0.3, 0.2, 0.1]),
                    rng.uniform(0, 1.2), rng.uniform(0.6, 1.4), rng.uniform(0, pi)))
    return out


def nj15(t, st):   # 물결: 비늘 같은 물결 줄이 아래서부터 차오르며 옆으로 흐른다
    m = blank()
    r = 46
    for j, y in enumerate(np.arange(H + 10, -60, -58)):
        t_in = 0.05 + 0.07 * j
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        drift = (1 if j % 2 else -1) * 60 * (t - t_in) + (r if j % 2 else 0)
        for x in np.arange(-3 * r, W + 3 * r, 2 * r):
            c = (x + drift % (2 * r), y)
            ring(m, c, r, 255 * a, 7, 180, 360)
            ring(m, c, r * 0.55, 255 * a, 4, 180, 360)
    return m


# ================================================================ 화려한 그림

def draw_crane(m, c, s, flap, v):
    fill(m, rot([(-60, 0), (-20, -14), (40, -10), (70, 0), (40, 12), (-20, 14)], c, 0, s), v)    # 몸통
    poly(m, rot([(60, -4), (100, -30), (140, -42)], c, 0, s), v, 7 * s)                          # 목
    ell(m, rot([(146, -44)], c, 0, s)[0], (11 * s, 9 * s), 0, v)
    fill(m, rot([(154, -46), (196, -40), (154, -40)], c, 0, s), v)                                  # 부리
    ell(m, rot([(144, -50)], c, 0, s)[0], (4 * s, 4 * s), 0, 0)                                    # 붉은 정수리 자리
    line(m, rot([(-50, 6)], c, 0, s)[0], rot([(-130, 18)], c, 0, s)[0], v, 5 * s)                  # 다리
    for sgn in (-1, 1):
        k = flap * sgn
        wing = [(-20, 0), (0, -70 * k), (30, -150 * k), (50, -120 * k), (40, -60 * k), (60, -90 * k), (50, -30 * k),
                (30, 0)]
        fill(m, rot(wing, c, 0, s), v)
        for i in range(3):
            line(m, rot([(10 + 10 * i, -20 * k)], c, 0, s)[0], rot([(30 + 8 * i, -120 * k)], c, 0, s)[0], 0, 2.5)


def nj16(t, st):   # 학: 날갯짓하며 무리 지어 화면을 가로지른다
    m = blank()
    for x0, y0, s, ph, t_in in st:
        a = fade_io(t, t_in, 2.9, 3.8)
        if a <= 0:
            continue
        x = x0 + 260 * (t - t_in)
        y = y0 - 50 * (t - t_in)
        flap = 0.25 + 0.75 * (0.5 + 0.5 * cos(2 * pi * 1.3 * (t - t_in) + ph))
        draw_crane(m, (x, y), s, flap, 255 * a)
    return m


def nj16_s(rng):
    out = []
    lead = (1150, 470)
    for i in range(9):
        k = (i + 1) // 2
        sg = 1 if i % 2 else -1
        out.append((lead[0] - 300 * k + rng.normal() * 20, lead[1] + sg * 190 * k + rng.normal() * 20,
                    1.25 - 0.06 * k, rng.uniform(0, pi), 0.05 + 0.1 * k))
    return out


def draw_mum(m, c, R, g, rot0, v):
    for layer, (n, rl, wl) in enumerate([(26, 1.0, 0.075), (20, 0.72, 0.09), (14, 0.45, 0.11)]):
        gl = smooth((g - 0.2 * layer) / 0.6)
        if gl <= 0:
            continue
        for i in range(n):
            a = rot0 + i * 2 * pi / n + layer * 0.12
            L = R * rl * gl
            ell(m, (c[0] + L * 0.55 * cos(a), c[1] + L * 0.55 * sin(a)), (L * 0.48, R * wl), np.degrees(a), v)
            line(m, (c[0] + L * 0.2 * cos(a), c[1] + L * 0.2 * sin(a)), (c[0] + L * 0.95 * cos(a), c[1] + L * 0.95 * sin(a)), 0, 2)
    ell(m, c, (R * 0.2 * g, R * 0.2 * g), 0, v)
    for i in range(8):
        a = i * pi / 4
        ell(m, (c[0] + R * 0.1 * g * cos(a), c[1] + R * 0.1 * g * sin(a)), (3, 3), 0, 0)


def nj17(t, st):   # 국화: 꽃잎이 겹겹이 펼쳐지는 국화 바둑판
    m = blank()
    for x, y, R, d in st:
        t_in = 0.05 + d / 2200
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        g = ease_out((t - t_in) / 1.0)
        draw_mum(m, (x, y), R, g, 0.3 * (t - t_in), 255 * a)
    return m


def nj17_s(rng):
    out = []
    for j, y in enumerate(np.arange(130, H + 100, 290)):
        for x in np.arange(150 + (210 if j % 2 else 0), W + 100, 420):
            out.append((x, y, 128, hypot(x - W / 2, y - H / 2)))
    return out


def branch(rng, start, ang, length, depth, out, t0, speed, noise=0.18):
    pts = [start]
    x, y = start
    n = int(length / 22)
    for _ in range(n):
        ang += rng.normal() * noise
        x, y = x + 22 * cos(ang), y + 22 * sin(ang)
        pts.append((x, y))
    out.append((np.array(pts), t0, depth))
    if depth < 2:
        for k in range(2 if depth == 0 else 1):
            i = int(rng.uniform(0.3, 0.8) * n)
            branch(rng, pts[i], ang + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9), length * 0.5, depth + 1, out,
                   t0 + i * 22 / speed, speed, noise)


def nj18(t, st):   # 매화: 가지가 뻗고 다섯 잎 매화가 톡톡 핀다
    m = blank()
    for pts, t0, depth, blossoms in st:
        a = fade_io(t, t0)
        if a <= 0:
            continue
        L = 900 * (t - t0)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        f = min(1.0, L / cum[-1])
        p = partial(pts, f)
        if len(p) > 1:
            poly(m, p, 255 * a, [18, 10, 6][depth])
        for (bx, by, at, r) in blossoms:
            if L > at:
                g = ease_back((L - at) / 260)
                for i in range(5):
                    aa = i * 2 * pi / 5 - pi / 2
                    ell(m, (bx + r * 0.6 * g * cos(aa), by + r * 0.6 * g * sin(aa)), (r * 0.45 * g, r * 0.45 * g), 0, 255 * a)
                ell(m, (bx, by), (r * 0.25 * g, r * 0.25 * g), 0, 0)
                for i in range(5):
                    aa = i * 2 * pi / 5 - pi / 2 + pi / 5
                    line(m, (bx, by), (bx + r * 0.4 * g * cos(aa), by + r * 0.4 * g * sin(aa)), 255 * a, 2)
    return m


def nj18_s(rng):
    raw = []
    branch(rng, (-40, 1000), radians(-36), 1700, 0, raw, 0.05, 900, 0.07)
    branch(rng, (W + 40, 60), radians(150), 1200, 0, raw, 0.3, 900, 0.07)
    out = []
    for pts, t0, depth in raw:
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        bl = []
        for i in range(3, len(pts), 4 if depth else 6):
            if rng.random() < 0.7:
                nx, ny = rng.normal(0, 26, 2)
                bl.append((pts[i][0] + nx, pts[i][1] + ny, cum[i], rng.choice([34, 44, 56])))
        out.append((pts, t0, depth, bl))
    return out


def draw_peony(m, c, R, g, v):
    """모란: 바깥 꽃잎부터 안쪽으로 겹겹이, 꽃잎마다 새긴 테두리와 결."""
    for layer, (n, rr, ww) in enumerate([(8, 1.0, 0.34), (7, 0.74, 0.3), (6, 0.5, 0.26), (5, 0.3, 0.2)]):
        gl = smooth((g - 0.18 * layer) / 0.5)
        if gl <= 0:
            continue
        for i in range(n):
            a = i * 2 * pi / n + layer * 0.4
            d = R * rr * 0.55 * gl
            pc = (c[0] + d * cos(a), c[1] + d * sin(a))
            ax = (R * rr * 0.45 * gl, R * ww * gl)
            ell(m, pc, ax, np.degrees(a), v)
            cv2.ellipse(m, (int(pc[0] * SC), int(pc[1] * SC)), (max(1, int(ax[0] * SC)), max(1, int(ax[1] * SC))),
                        np.degrees(a), 0, 360, 0, 3, cv2.LINE_AA, SHIFT)
            for k in (-0.35, 0, 0.35):    # 꽃잎 결
                e = (pc[0] + ax[0] * 0.8 * cos(a + k), pc[1] + ax[0] * 0.8 * sin(a + k))
                line(m, (pc[0] - ax[0] * 0.5 * cos(a), pc[1] - ax[0] * 0.5 * sin(a)), e, 0, 1.5)
    ell(m, c, (R * 0.12 * g, R * 0.12 * g), 0, v)
    for i in range(10):
        a = i * pi / 5
        ell(m, (c[0] + R * 0.08 * g * cos(a), c[1] + R * 0.08 * g * sin(a)), (3, 3), 0, 0)


def draw_leaf3(m, c, s, ang, v):
    for k in (-1, 0, 1):
        a = ang + k * 0.6
        pc = (c[0] + 40 * s * cos(a), c[1] + 40 * s * sin(a))
        ell(m, pc, (42 * s, 16 * s), np.degrees(a), v)
        line(m, c, (c[0] + 75 * s * cos(a), c[1] + 75 * s * sin(a)), 0, 2)


def nj19(t, st):   # 모란: 가운데 큰 모란이 겹겹이 피고 잎과 작은 모란이 둘러싼다
    m = blank()
    a = fade_io(t, 0.05)
    g = ease_out((t - 0.05) / 1.4)
    for (x, y, s, ang, d) in st["leaves"]:
        gl = ease_out((t - 0.3 - d) / 0.6)
        if gl > 0:
            draw_leaf3(m, (x, y), s * gl, ang, 255 * a)
    draw_peony(m, (W / 2, H / 2), 300, g, 255 * a)
    for (x, y, R, d) in st["small"]:
        gs = ease_out((t - 0.5 - d) / 1.0)
        if gs > 0:
            draw_peony(m, (x, y), R, gs, 255 * a)
    return m


def nj19_s(rng):
    leaves = []
    for i in range(12):
        ang = i * 2 * pi / 12 + rng.normal() * 0.1
        leaves.append((W / 2 + 330 * cos(ang), H / 2 + 300 * sin(ang), 1.2, ang, 0.03 * i))
    small = [(220, 200, 130, 0.0), (W - 220, 200, 130, 0.15), (220, H - 200, 130, 0.3), (W - 220, H - 200, 130, 0.45)]
    return {"leaves": leaves, "small": small}


def draw_cloud(m, c, s, flip, v):
    sx = -1 if flip else 1
    blobs = [(0, 0, 40), (46, -18, 34), (88, 0, 30), (40, 22, 30), (-40, 10, 28)]
    for x, y, r in blobs:
        ell(m, (c[0] + sx * x * s, c[1] + y * s), (r * s, r * s), 0, v)
    fill(m, [(c[0] - sx * 50 * s, c[1] + 22 * s), (c[0] - sx * 170 * s, c[1] + 44 * s), (c[0] - sx * 40 * s, c[1] + 34 * s)], v)
    for x, y, r in blobs[:4]:
        ring(m, (c[0] + sx * x * s, c[1] + y * s), r * 0.55 * s, 0, 3, 0, 270)
        ring(m, (c[0] + sx * x * s, c[1] + y * s), r * 0.25 * s, 0, 3, 0, 270)


def nj20(t, st):   # 구름: 말린 구름(운문) 줄이 좌우로 흘러간다
    m = blank()
    for j, items in enumerate(st):
        t_in = 0.05 + 0.12 * j
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        dirn = 1 if j % 2 else -1
        for x, y, s in items:
            draw_cloud(m, (x + dirn * 90 * (t - t_in), y), s * (0.8 + 0.2 * ease_out((t - t_in) / 0.5)), dirn < 0, 255 * a)
    return m


def nj20_s(rng):
    rows = []
    for j, y in enumerate(np.arange(110, H + 80, 210)):
        rows.append([(x + rng.normal() * 30, y + rng.normal() * 15, rng.uniform(0.8, 1.1))
                     for x in np.arange(-100 + (170 if j % 2 else 0), W + 200, 340)])
    return rows


def draw_lotus(m, c, s, g, v):
    for i, (ang, L, wd) in enumerate([(-90, 120, 34), (-60, 105, 30), (-120, 105, 30), (-30, 80, 26), (-150, 80, 26),
                                       (-75, 115, 22), (-105, 115, 22)]):
        a = radians(ang)
        Lg = L * s * g
        pc = (c[0] + Lg * 0.5 * cos(a), c[1] + Lg * 0.5 * sin(a))
        ell(m, pc, (Lg * 0.52, wd * s * g), ang, v)
        cv2.ellipse(m, (int(pc[0] * SC), int(pc[1] * SC)), (max(1, int(Lg * 0.52 * SC)), max(1, int(wd * s * g * SC))),
                    ang, 0, 360, 0, 3, cv2.LINE_AA, SHIFT)
        line(m, c, (c[0] + Lg * 0.8 * cos(a), c[1] + Lg * 0.8 * sin(a)), 0, 1.5)
    ell(m, (c[0], c[1] + 6 * s), (50 * s * g, 14 * s * g), 0, v)


def nj21(t, st):   # 연꽃: 연잎과 연꽃이 아래에서 떠오르며 핀다
    m = blank()
    for x, y, s, t_in, kind in st:
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        rise = (1 - ease_out((t - t_in) / 0.9)) * 260
        g = ease_out((t - t_in - 0.2) / 0.9)
        c = (x, y + rise)
        if kind == "leaf":
            ell(m, c, (110 * s, 40 * s), 0, 255 * a)
            for i in range(9):
                aa = pi + i * pi / 8
                line(m, c, (c[0] + 105 * s * cos(aa) * 1.0, c[1] + 36 * s * sin(aa) * -1), 0, 2)
            line(m, c, (c[0], H + 20), 255 * a, 6 * s)
        else:
            line(m, c, (c[0] + 10, H + 20), 255 * a, 6 * s)
            if g > 0:
                draw_lotus(m, c, s, g, 255 * a)
    return m


def nj21_s(rng):
    out = []
    for i, x in enumerate(np.arange(120, W, 210)):
        kind = "flower" if i % 2 == 0 else "leaf"
        y = rng.uniform(620, 860) if kind == "flower" else rng.uniform(780, 960)
        out.append((x + rng.normal() * 20, y, rng.uniform(0.9, 1.2), 0.05 + 0.07 * ((i * 5) % 9), kind))
    for i, x in enumerate(np.arange(220, W, 420)):
        out.append((x, rng.uniform(330, 480), 0.8, 0.5 + 0.06 * i, "flower"))
    return out


def draw_fish(m, c, s, ang, v):
    body = rot([(-70, 0), (-40, -26), (10, -32), (60, -16), (78, 0), (60, 16), (10, 32), (-40, 26)], c, ang, s)
    fill(m, body, v)
    fill(m, rot([(-62, 0), (-110, -34), (-96, 0), (-110, 34)], c, ang, s), v)
    fill(m, rot([(0, -30), (20, -54), (36, -28)], c, ang, s), v)
    ell(m, rot([(52, -4)], c, ang, s)[0], (6 * s, 6 * s), 0, 0)
    for i in range(4):
        for j in (-1, 1):
            p = rot([(-30 + 20 * i, j * 10)], c, ang, s)[0]
            ring(m, p, 10 * s, 0, 2, -60 + np.degrees(ang), 60 + np.degrees(ang))
    line(m, rot([(34, -20)], c, ang, s)[0], rot([(34, 20)], c, ang, s)[0], 0, 2)


def nj22(t, st):   # 물고기: 쌍쌍이 둥글게 돌며 헤엄치고 물결 고리가 퍼진다
    m = blank()
    a = fade_io(t, 0.05)
    for k in range(5):
        tr = 0.05 + 0.3 * k
        ar = fade_io(t, tr)
        if ar > 0:
            ring(m, (W / 2, H / 2), 60 + 340 * ease_out((t - tr) / 1.8), 255 * ar * 0.8, 4)
    for R, n, spd, s, ph in st:
        for i in range(n):
            th = ph + i * 2 * pi / n + spd * (t - 0.05)
            c = (W / 2 + R * cos(th), H / 2 + R * 0.62 * sin(th))
            ang = th + (pi / 2 if spd > 0 else -pi / 2)
            ang = atan2(0.62 * sin(ang) * 1, cos(ang))
            g = ease_out((t - 0.05 - 0.05 * i) / 0.5)
            if g > 0:
                draw_fish(m, c, s * g, ang, 255 * a)
    return m


def nj22_s(rng):
    return [(300, 6, 0.55, 0.9, 0.0), (620, 10, -0.4, 0.75, 0.3), (880, 14, 0.3, 0.62, 0.1)]


def nj23(t, st):   # 만화경 꽃: 겹겹의 꽃잎 고리가 번갈아 반대로 돌며 피어난다
    m = blank()
    c = (W / 2, H / 2)
    for k, (n, r, L, wd, kind) in enumerate(st):
        t_in = 0.05 + 0.1 * k
        a = fade_io(t, t_in)
        if a <= 0:
            continue
        g = ease_out((t - t_in) / 0.6)
        spin = (1 if k % 2 else -1) * 0.25 * (t - t_in)
        for i in range(n):
            th = spin + i * 2 * pi / n
            p = (c[0] + r * g * cos(th), c[1] + r * g * sin(th))
            if kind == "petal":
                ell(m, p, (L * g, wd * g), np.degrees(th), 255 * a)
                line(m, (p[0] - L * 0.7 * g * cos(th), p[1] - L * 0.7 * g * sin(th)),
                     (p[0] + L * 0.7 * g * cos(th), p[1] + L * 0.7 * g * sin(th)), 0, 2)
            elif kind == "dot":
                ell(m, p, (wd * g, wd * g), 0, 255 * a)
            else:
                fill(m, rot([(0, -wd), (L, 0), (0, wd), (-L * 0.4, 0)], p, th, g), 255 * a)
        if kind == "petal":
            ring(m, c, (r - L) * g, 255 * a, 4)
    ell(m, c, (40, 40), 0, 255 * fade_io(t, 0.05))
    ell(m, c, (20, 20), 0, 0)
    return m


def nj23_s(rng):
    return [(8, 80, 40, 18, "petal"), (16, 160, 46, 16, "petal"), (24, 240, 30, 9, "dot"),
            (24, 300, 48, 18, "petal"), (32, 380, 32, 12, "kite"), (40, 450, 12, 9, "dot"),
            (36, 520, 54, 14, "petal"), (48, 610, 34, 12, "kite"), (60, 690, 10, 8, "dot")]


def draw_grapes(m, c, s, g, v):
    k = 0
    for row in range(5):
        for i in range(5 - row):
            x = c[0] + (i - (4 - row) / 2) * 24 * s
            y = c[1] + row * 21 * s
            if smooth((g * 15 - k) / 2) > 0:
                r = 12 * s * smooth((g * 15 - k) / 2)
                ell(m, (x, y), (r, r), 0, v)
                ell(m, (x - 3 * s, y - 3 * s), (3 * s * (r > 4), 3 * s * (r > 4)), 0, 0)
            k += 1


def draw_vleaf(m, c, s, ang, v):
    for k in range(-2, 3):
        a = ang + k * 0.55
        ell(m, (c[0] + 26 * s * cos(a), c[1] + 26 * s * sin(a)), (30 * s, 20 * s), np.degrees(a), v)
    for k in range(-2, 3):
        a = ang + k * 0.55
        line(m, c, (c[0] + 50 * s * cos(a), c[1] + 50 * s * sin(a)), 0, 2)


def nj24(t, st):   # 포도 덩굴: 위아래 덩굴이 뻗고 잎과 포도송이가 맺힌다
    m = blank()
    for vine in st:
        pts, t0, items, tendrils = vine
        a = fade_io(t, t0)
        if a <= 0:
            continue
        L = 1300 * (t - t0)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        p = partial(pts, min(1, L / cum[-1]))
        if len(p) > 1:
            poly(m, p, 255 * a, 12)
        for at, kind, x, y, ang in items:
            if L <= at:
                continue
            g = ease_out((L - at) / 400)
            if kind == "leaf":
                draw_vleaf(m, (x, y), 1.4 * g, ang, 255 * a)
            else:
                line(m, (x, y - 30), (x, y), 255 * a, 4)
                draw_grapes(m, (x, y), 1.2, g, 255 * a)
        for at, x, y, sg in tendrils:
            if L > at:
                g = ease_out((L - at) / 300)
                th = np.linspace(0, 3.5 * pi * g, 50)
                rr = 30 * (1 - th / (4 * pi))
                poly(m, np.stack([x + sg * rr * np.cos(th), y - 30 + rr * np.sin(th)], 1), 255 * a, 3)
    return m


def nj24_s(rng):
    out = []
    for yb, t0, sg in ((200, 0.05, 1), (H - 260, 0.35, -1)):
        xs = np.arange(-40, W + 60, 8.0)
        ys = yb + 40 * np.sin(xs / 160)
        pts = np.stack([xs if sg > 0 else W - xs, ys], 1)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        items, tendrils = [], []
        for k, i in enumerate(range(20, len(pts), 26)):
            x, y = pts[i]
            if k % 2 == 0:
                items.append((cum[i], "leaf", x, y - 60, radians(-90 + rng.normal() * 15)))
            else:
                items.append((cum[i], "grape", x, y + 40, 0))
            if k % 3 == 1:
                tendrils.append((cum[i], x + 30, y, sg))
        out.append((pts, t0, items, tendrils))
    return out


def nj25(t, st):   # 소나무 가지: 굽은 가지가 뻗고 끝마다 솔잎 부채가 돋는다
    m = blank()
    for pts, t0, depth, fans in st:
        a = fade_io(t, t0)
        if a <= 0:
            continue
        L = 800 * (t - t0)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        p = partial(pts, min(1, L / cum[-1]))
        if len(p) > 1:
            poly(m, p, 255 * a, [26, 14, 8][depth])
            if depth == 0:
                poly(m, p + np.array([4, 2]), 0, 3)      # 줄기 껍질 결
        for at, x, y, ang, r in fans:
            if L > at:
                g = ease_out((L - at) / 300)
                draw_fan(m, (x, y), r * g, ang, 255 * a)
    return m


def nj25_s(rng):
    raw = []
    branch(rng, (120, H + 30), radians(-70), 1150, 0, raw, 0.05, 800)
    branch(rng, (W - 200, H + 30), radians(-105), 950, 0, raw, 0.25, 800)
    out = []
    for pts, t0, depth in raw:
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        fans = []
        for i in range(6, len(pts), 5):
            if rng.random() < 0.75:
                fans.append((cum[i], pts[i][0] + rng.normal() * 20, pts[i][1] - 25 + rng.normal() * 10,
                             radians(rng.normal() * 15), rng.uniform(55, 85)))
        out.append((pts, t0, depth, fans))
    return out


def nj26(t, st):   # 꽃 액자: 테두리가 한 바퀴 그려지고 모서리 부채꽃과 가운데 원문이 피어난다
    m = blank()
    a = fade_io(t, 0.05)
    f = ease_out((t - 0.05) / 1.3)
    for inset, th in ((50, 10), (88, 5)):
        rect = np.array([(inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset), (inset, inset)], float)
        p = partial(rect, f)
        if len(p) > 1:
            poly(m, p, 255 * a, th)
    per = 2 * (W + H - 4 * 69)
    for i, (x, y, at) in enumerate(st["dots"]):
        if f * per > at:
            for k in range(4):
                aa = pi / 4 + k * pi / 2
                ell(m, (x + 10 * cos(aa), y + 10 * sin(aa)), (10, 6), np.degrees(aa), 255 * a)
    for (cx, cy, ang, d) in st["corners"]:
        g = ease_out((t - 0.4 - d) / 0.8)
        if g > 0:
            for k in range(7):
                aa = ang + k * (pi / 2) / 6
                L = 190 * g
                ell(m, (cx + L * 0.5 * cos(aa), cy + L * 0.5 * sin(aa)), (L * 0.5, 20 * g), np.degrees(aa), 255 * a)
                line(m, (cx, cy), (cx + L * 0.95 * cos(aa), cy + L * 0.95 * sin(aa)), 0, 2)
            ring(m, (cx, cy), 60 * g, 0, 6, np.degrees(ang), np.degrees(ang) + 90)
    g = ease_out((t - 0.7) / 1.0)
    if g > 0:
        c = (W / 2, H / 2)
        ring(m, c, 250 * g, 255 * a, 8)
        ring(m, c, 228 * g, 255 * a, 3)
        draw_mum(m, c, 190, g, 0.15 * t, 255 * a)
    return m


def nj26_s(rng):
    inset = 69
    rect = [(inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset), (inset, inset)]
    dots, acc = [], 0.0
    for (x0, y0), (x1, y1) in zip(rect[:-1], rect[1:]):
        L = hypot(x1 - x0, y1 - y0)
        for d in np.arange(110, L - 90, 70):
            dots.append((x0 + (x1 - x0) * d / L, y0 + (y1 - y0) * d / L, acc + d))
        acc += L
    corners = [(50, 50, 0, 0), (W - 50, 50, pi / 2, 0.15), (W - 50, H - 50, pi, 0.3), (50, H - 50, 3 * pi / 2, 0.45)]
    return {"dots": dots, "corners": corners}


# ---------------------------------------------------------------- 목록: 단순(S) / 화려(F) 섞음, 자개빛도 다르게

CLIPS = {
    "nj05": ("nj05_stripes", nj05, nj05_s, dict(sweep_ang=90, hue_off=0.0, sat_k=0.6)),
    "nj06": ("nj06_diamond_lattice", nj06, nj06_s, dict(sweep_ang=35, hue_off=0.4, spread=0.25, sat_k=1.2)),
    "nj07": ("nj07_pearl_dots", nj07, nj07_s, dict(sweep_ang=0, hue_off=0.85, spread=0.2, sat_k=1.3)),
    "nj08": ("nj08_hatch_sweep", nj08, nj08_s, dict(sweep_ang=-30, sat_k=0.5)),
    "nj09": ("nj09_spinning_rings", nj09, None, dict(sweep_ang=45, hue_off=0.15, sat_k=1.1)),
    "nj10": ("nj10_tortoise_hex", nj10, nj10_s, dict(sweep_ang=60, hue_off=0.55, spread=0.25, sat_k=1.2)),
    "nj11": ("nj11_thunder_fret", nj11, nj11_s, dict(sweep_ang=10, sat_k=0.7)),
    "nj12": ("nj12_chilbo_rings", nj12, nj12_s, dict(sweep_ang=120, hue_off=0.7, sat_k=1.2)),
    "nj13": ("nj13_bamboo", nj13, nj13_s, dict(sweep_ang=80, hue_off=0.25, spread=0.2, sat_k=1.1)),
    "nj14": ("nj14_sparkles", nj14, nj14_s, dict(sweep_ang=30, sat_k=1.4)),
    "nj15": ("nj15_wave_scales", nj15, None, dict(sweep_ang=-10, hue_off=0.45, spread=0.2, sat_k=1.3)),
    "nj16": ("nj16_cranes", nj16, nj16_s, dict(sweep_ang=20, sat_k=0.8)),
    "nj17": ("nj17_chrysanthemums", nj17, nj17_s, dict(sweep_ang=40, hue_off=0.1, sat_k=1.2)),
    "nj18": ("nj18_plum_branch", nj18, nj18_s, dict(sweep_ang=-35, hue_off=0.9, spread=0.25, sat_k=1.3)),
    "nj19": ("nj19_peony", nj19, nj19_s, dict(sweep_ang=50, hue_off=0.85, sat_k=1.4)),
    "nj20": ("nj20_cloud_scrolls", nj20, nj20_s, dict(sweep_ang=0, hue_off=0.5, spread=0.3, sat_k=0.9)),
    "nj21": ("nj21_lotus_pond", nj21, nj21_s, dict(sweep_ang=-80, hue_off=0.3, sat_k=1.2)),
    "nj22": ("nj22_circling_fish", nj22, nj22_s, dict(sweep_ang=70, hue_off=0.55, sat_k=1.3)),
    "nj23": ("nj23_kaleidoscope", nj23, nj23_s, dict(sweep_ang=15, spread=0.5, sat_k=1.6)),
    "nj24": ("nj24_grape_vine", nj24, nj24_s, dict(sweep_ang=30, hue_off=0.65, sat_k=1.2)),
    "nj25": ("nj25_pine_branch", nj25, nj25_s, dict(sweep_ang=-60, hue_off=0.3, spread=0.25, sat_k=0.9)),
    "nj26": ("nj26_flower_frame", nj26, nj26_s, dict(sweep_ang=45, sat_k=1.1)),
}


def build(key):
    name, fn, setup, pk = CLIPS[key]
    seed = int(key[2:])
    st = setup(np.random.default_rng(seed)) if setup else None
    pearl = Pearl(seed + 10, **pk)

    def frame(t):
        m = fn(t, st)
        if m.max() == 0:
            return np.zeros((H, W, 3), np.uint8)
        m = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 0.5)
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


def preview(keys, path, times=(0.5, 1.2, 2.2)):
    bg = lacquer()
    tw, th = 480, 270
    rows = []
    for k in keys:
        _, frame = build(k)
        row = [cv2.resize(np.maximum(bg, frame(t)), (tw, th), interpolation=cv2.INTER_AREA) for t in times]
        r = np.hstack(row)
        cv2.putText(r, k, (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (230, 230, 230), 2)
        rows.append(r)
    cv2.imwrite(str(path), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", path, flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--preview":
        preview(args[2:] or list(CLIPS), Path(args[1]))
    else:
        out_dir = ROOT / "clips" / "najeon"
        out_dir.mkdir(parents=True, exist_ok=True)
        for k in args or list(CLIPS):
            render(k, out_dir)
