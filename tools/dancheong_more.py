"""단청 뱅크 영상 dc05~dc26 (22개). dancheong.py의 그리기 도구와 형식을 그대로 쓴다.

    python3 tools/dancheong_more.py             # 22개 전부
    python3 tools/dancheong_more.py dc07 dc12   # 원하는 것만

모두 1920x1080, 30fps, 4초, 흰 바탕(첫·끝 프레임은 완전한 흰색). 화면에서는 바랜 한지 위에 '어둡게'로 겹친다.
단청의 실제 어휘(육모 금단, 구름 당초, 亞자 살, 보주, 무지개 머리초, 팔모, 소란반자, 기둥 띠, 매화점,
물결, 뇌문, 보상화 빛살 등)를 참고해 새로 그렸고, 모양·움직임·색 조합이 서로 겹치지 않게 했다.
"""
import math
import pathlib
import sys

import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dancheong as d  # noqa: E402
from dancheong import (W, H, WHITE, NOK, YANGNOK, PALE_G, SAMCHEONG, SKY, PALE_B, NAVY, JU, DAJA, PINK, HWANG,  # noqa: E402
                       ORANGE, PURPLE, MUK, ease_out, ease_in_out, fade_env, poly, disc, ring, blank, dim, over_white,
                       draw_petal, draw_lotus, rounded_petals, square, wave_scales)

OCHRE = d.rgb("c98a2e")
TEAL = d.rgb("1f8a86")
ROSE = d.rgb("c2456a")


def rng(seed):
    return np.random.default_rng(seed)


def ease_back(x, k=1.7):
    """살짝 넘쳤다 돌아오는 튀어나오기."""
    x = min(max(x, 0.0), 1.0)
    x -= 1
    return x * x * ((k + 1) * x + k) + 1


def reg_poly(c, r, n, rot=0.0):
    return [(c[0] + r * math.cos(rot + 2 * math.pi * k / n), c[1] + r * math.sin(rot + 2 * math.pi * k / n))
            for k in range(n)]


def star_poly(c, r1, r2, n, rot=0.0):
    pts = []
    for k in range(2 * n):
        r = r1 if k % 2 == 0 else r2
        a = rot + math.pi * k / n
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts


def banded(img, shape_fn, colors, shrink=0.16):
    """같은 모양을 바깥→안쪽으로 줄여 가며 색 띠를 겹친다 (단청 빛넣기)."""
    n = len(colors)
    for i, col in enumerate(colors):
        s = 1 - shrink * i * (6 / max(n, 1))
        if s <= 0.02:
            break
        poly(img, shape_fn(s), col)


def path_line(img, pts, thick, color):
    if len(pts) < 2 or thick < 1:
        return
    p = np.round(np.asarray(pts) * 16).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(img, [p], False, color, int(round(thick)), lineType=cv2.LINE_AA, shift=4)


def paste_min(img, sprite, cx, cy, sx=1.0, sy=1.0, ang=0.0):
    """흰 바탕 스프라이트를 확대·회전해서 '어둡게'로 붙인다."""
    if sx <= 0.01 or sy <= 0.01:
        return
    h, w = sprite.shape[:2]
    ca, sa = math.cos(ang), math.sin(ang)
    hw = (abs(w * sx * ca) + abs(h * sy * sa)) / 2 + 2
    hh = (abs(w * sx * sa) + abs(h * sy * ca)) / 2 + 2
    x0, x1 = int(max(0, cx - hw)), int(min(W, cx + hw))
    y0, y1 = int(max(0, cy - hh)), int(min(H, cy + hh))
    if x1 <= x0 or y1 <= y0:
        return
    # 목적지(ROI 좌표) -> 스프라이트 좌표 역변환
    A = np.array([[ca * sx, -sa * sy], [sa * sx, ca * sy]], np.float64)
    t = np.array([cx - x0, cy - y0]) - A @ np.array([w / 2, h / 2])
    M = np.hstack([A, t[:, None]])
    out = cv2.warpAffine(sprite, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                         borderValue=(255, 255, 255))
    np.minimum(img[y0:y1, x0:x1], out, out=img[y0:y1, x0:x1])


_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ================================================================ 22개 영상

def dc05_hex_lattice(t):
    """육모 금단: 벌집 육각 무늬가 가운데에서 바깥으로 물결처럼 깔렸다 걷힌다. 청록 + 황."""
    img = blank()
    s = 62
    cols = [NOK, WHITE, YANGNOK, PALE_G]
    for q in range(-12, 13):
        for r in range(-8, 9):
            cx = W / 2 + s * 1.5 * q
            cy = H / 2 + s * math.sqrt(3) * (r + q / 2)
            dd = math.hypot(cx - W / 2, cy - H / 2)
            if dd > 560:
                continue
            p_in = ease_back((t - dd / 560 * 0.7) / 0.32)
            p_out = 1 - ease_in_out((t - 1.9 - dd / 560 * 0.6) / 0.5)
            k = max(0.0, min(p_in, p_out))
            if k <= 0.01:
                continue
            rr = s * 0.94 * k
            for i, col in enumerate(cols):
                poly(img, reg_poly((cx, cy), rr * (1 - 0.2 * i), 6), col)
            disc(img, (cx, cy), rr * 0.22, HWANG if (q + r) % 2 else OCHRE)
    return img


def cloud_curl(c, R, sgn, phase, n=90):
    pts = []
    tail = [(c[0] - sgn * R * 2.4, c[1] + R * 0.9), (c[0] - sgn * R * 1.2, c[1] + R * 0.95)]
    for k in range(n):
        th = 2.3 * math.pi * k / (n - 1)
        r = R * (1 - th / (2.7 * math.pi))
        a = phase + math.pi / 2 - sgn * th
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return tail + pts


def dc06_cloud_scroll(t):
    """구름 당초: 구름 꼬리가 그려지며 소용돌이로 말려 들어간다. 주홍·분홍."""
    img = blank()
    curls = [((380, 300), 120, 1), ((820, 620), 150, -1), ((1250, 330), 130, 1), ((1640, 700), 110, -1),
             ((620, 860), 90, 1), ((1480, 140), 80, -1)]
    for i, (c, R, sgn) in enumerate(curls):
        prog = ease_out((t - i * 0.1) / 0.9)
        if prog <= 0:
            continue
        pts = cloud_curl(c, R, sgn, 0.0)
        m = max(2, int(len(pts) * prog))
        p = pts[:m]
        path_line(img, p, R * 0.36, DAJA)
        path_line(img, p, R * 0.26, JU)
        path_line(img, p, R * 0.13, PINK)
        path_line(img, p, R * 0.04, WHITE)
        if prog > 0.95:
            disc(img, p[-1], R * 0.12, HWANG)
    return dim(img, fade_env(t, 2.4, 3.6))


def aja_pattern():
    """亞자살: 계단진 십자(亞) 테두리가 이어진 창살 무늬."""
    img = blank()
    cell = 120
    for gy in range(-1, H // cell + 2):
        for gx in range(-1, W // cell + 2):
            cx, cy = gx * cell + cell / 2, gy * cell + cell / 2
            a, b = cell * 0.42, cell * 0.2  # 바깥 반폭, 계단 반폭
            shape = [(cx - b, cy - a), (cx + b, cy - a), (cx + b, cy - b), (cx + a, cy - b), (cx + a, cy + b),
                     (cx + b, cy + b), (cx + b, cy + a), (cx - b, cy + a), (cx - b, cy + b), (cx - a, cy + b),
                     (cx - a, cy - b), (cx - b, cy - b)]
            poly(img, shape, HWANG)
            path_line(img, shape + [shape[0]], 8, MUK)
            disc(img, (cx, cy), 12, JU)
            disc(img, (cx, cy), 5, HWANG)
            # 칸 사이 귀퉁이 마름모
            k = cell / 2
            poly(img, [(cx + k, cy + k - 16), (cx + k + 16, cy + k), (cx + k, cy + k + 16), (cx + k - 16, cy + k)], OCHRE)
    return img


def dc07_aja_lattice(t):
    """亞자 창살: 먹선 亞자 무늬가 대각선으로 '삭' 쓸고 지나간다. 황·먹."""
    pat = cached("aja", aja_pattern)
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    u = x + y * 0.9  # 대각선 좌표
    umax = W + H * 0.9
    head = -200 + (umax + 400) * ease_out(t / 0.6)
    tail = -200 + (umax + 600) * ease_in_out((t - 1.0) / 1.3)
    m = np.clip((head - u) / 160, 0, 1)
    if t > 1.0:
        m = m * np.clip((u - tail) / 160, 0, 1)
    if t >= 2.9:
        m = m * 0
    return over_white(pat, m)


def dc08_jewel_spiral(t):
    """보주 나선: 오방색 구슬이 해바라기 씨처럼 나선으로 하나씩 돋는다."""
    img = blank()
    n = 150
    cols = [SAMCHEONG, JU, HWANG, NOK, MUK]
    rot = 0.25 * t
    for k in range(n):
        lt = t - k / n * 1.1
        if lt <= 0:
            break
        p = ease_back(lt / 0.25)
        r = 36 * math.sqrt(k + 1)
        a = k * math.radians(137.508) + rot
        c = (W / 2 + r * math.cos(a), H / 2 + r * math.sin(a))
        rr = (10 + 0.12 * math.sqrt(k + 1) * 9) * p
        col = cols[k % 5]
        disc(img, c, rr, col)
        disc(img, c, rr * 0.62, WHITE)
        disc(img, c, rr * 0.36, col)
    return dim(img, fade_env(t, 2.4, 3.6))


def dc09_rainbow_ripple(t):
    """무지개 머리초 띠가 동그란 물결로 두 번 퍼져 나간다. 오색."""
    img = blank()
    c = (W / 2, H / 2)
    bands = [JU, ORANGE, HWANG, YANGNOK, SKY, SAMCHEONG, PURPLE]
    bw, gap = 24, 8
    for wv in range(2):
        lt = t - wv * 0.4
        if lt <= 0:
            continue
        front = 30 + 1300 * ease_out(lt / 2.2)
        for i, col in enumerate(bands):
            r = front - i * (bw + gap)
            if r > 0:
                ring(img, c, r, bw, col)
    disc(img, c, 70 * ease_back(t / 0.4), DAJA)
    disc(img, c, 46 * ease_back(t / 0.4), HWANG)
    return dim(img, fade_env(t, 2.1, 3.5))


def dc10_twin_lotus(t):
    """쌍연화: 좌우 두 송이가 서로 반대로 돌며 핀다. 주홍 계열."""
    img = blank()
    prog = ease_out(t / 1.0)
    sch_a = ([WHITE, DAJA, JU, PINK, WHITE], [WHITE, HWANG, ORANGE, WHITE], [WHITE, JU, HWANG, DAJA])
    sch_b = ([WHITE, JU, ORANGE, HWANG, WHITE], [WHITE, DAJA, ROSE, PINK], [WHITE, HWANG, DAJA, HWANG])
    draw_lotus(img, (W * 0.3, H / 2), 360, prog, -0.8 * (1 - prog) + 0.05 * t, sch_a)
    draw_lotus(img, (W * 0.7, H / 2), 360, ease_out((t - 0.15) / 1.0), 0.8 * (1 - prog) - 0.05 * t, sch_b)
    return dim(img, fade_env(t, 2.5, 3.7))


def dc11_star_rosette(t):
    """팔모 별꽃: 여덟 모 별이 겹겹이 돌며 커지고 안쪽 별은 반대로 돈다. 청·남."""
    img = blank()
    c = (W / 2, H / 2)
    p = ease_back(t / 0.7, 1.2)
    rot = math.pi / 4 * (1 - ease_out(t / 0.9)) + 0.08 * t
    R = 470 * p
    if R > 1:
        banded(img, lambda s: star_poly(c, R * s, R * s * 0.62, 8, rot), [NAVY, WHITE, SAMCHEONG, SKY, WHITE, NAVY],
               shrink=0.12)
        R2 = 230 * ease_back((t - 0.2) / 0.6, 1.2)
        if R2 > 1:
            banded(img, lambda s: star_poly(c, R2 * s, R2 * s * 0.55, 8, -rot * 1.5 + math.pi / 8),
                   [JU, WHITE, HWANG, ORANGE], shrink=0.15)
            disc(img, c, R2 * 0.22, NAVY)
            disc(img, c, R2 * 0.12, HWANG)
    return dim(img, fade_env(t, 2.4, 3.6))


def soran_panel(size, pal):
    img = np.full((size, size, 3), 255, np.uint8)
    c = (size / 2, size / 2)
    frame, inner, petal, core = pal
    square(img, c, size / 2 - 2, 0, frame)
    square(img, c, size / 2 * 0.86, 0, WHITE)
    square(img, c, size / 2 * 0.80, 0, inner)
    disc(img, c, size * 0.34, WHITE)
    rounded_petals(img, c, 4, size * 0.05, size * 0.26, size * 0.16, math.pi / 4, [petal, WHITE, petal])
    rounded_petals(img, c, 4, size * 0.04, size * 0.2, size * 0.11, 0, [frame, WHITE])
    disc(img, c, size * 0.07, core)
    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        disc(img, (c[0] + dx * size * 0.33, c[1] + dy * size * 0.33), size * 0.035, core)
    return img


SORAN_PALS = [
    (NOK, PALE_G, JU, HWANG), (SAMCHEONG, PALE_B, ROSE, HWANG), (DAJA, PINK, NOK, HWANG),
    (TEAL, PALE_G, ORANGE, JU), (NAVY, SKY, JU, HWANG),
]


def dc12_soran_grid(t):
    """소란반자: 천장 반자틀 네모판들이 카드처럼 뒤집히며 차례로 나타난다. 가칠 파스텔."""
    img = blank()
    size, gap = 230, 26
    rows, cols = 3, 5
    x0 = W / 2 - (cols - 1) * (size + gap) / 2
    y0 = H / 2 - (rows - 1) * (size + gap) / 2
    for r in range(rows):
        for c in range(cols):
            k = r * cols + c
            sprite = cached(("soran", k % 5), lambda k=k: soran_panel(size, SORAN_PALS[k % 5]))
            lt = t - (r + c) * 0.07
            flip_in = ease_out(lt / 0.35)
            flip_out = 1 - ease_in_out((t - 2.0 - (r + c) * 0.06) / 0.35)
            sy = max(0.0, min(flip_in, flip_out))
            paste_min(img, sprite, x0 + c * (size + gap), y0 + r * (size + gap), 1.0, sy)
    return img


def pillar_sprite(w, pal):
    img = np.full((H, w, 3), 255, np.uint8)
    y = 0
    body, accent = pal
    for h, col in ((14, MUK), (10, WHITE), (26, JU), (8, WHITE), (22, HWANG), (8, WHITE), (30, accent), (8, WHITE),
                   (60, MUK), (8, WHITE), (20, accent), (10, WHITE)):
        img[y:y + h] = col
        y += h
    # 검은 띠 안의 매화점
    cy = 14 + 10 + 26 + 8 + 22 + 8 + 30 + 8 + 30
    for cx in (w * 0.25, w * 0.5, w * 0.75):
        for j in range(5):
            a = -math.pi / 2 + 2 * math.pi * j / 5
            disc(img, (cx + math.cos(a) * 8, cy + math.sin(a) * 8), 5, WHITE)
    img[y:] = body
    return img


def dc13_pillar_bands(t):
    """기둥 단청: 머리초 띠를 인 기둥들이 위에서 '촤르륵' 내려왔다가 다시 올라간다. 녹·주."""
    img = blank()
    n, w = 7, 130
    gap = (W - n * w) / (n + 1)
    for i in range(n):
        sp = cached(("pillar", i % 2), lambda i=i: pillar_sprite(w, (NOK, YANGNOK) if i % 2 == 0 else (JU, SAMCHEONG)))
        down = ease_out((t - abs(i - 3) * 0.06) / 0.55)
        up = ease_in_out((t - 1.8 - abs(i - 3) * 0.05) / 0.6)
        vis = int(H * down * (1 - up))
        if vis <= 0:
            continue
        x = int(gap + i * (w + gap))
        img[:vis, x:x + w] = sp[H - vis:]  # 아래 끝부터 내려오는 것처럼
    return img


def mae_flower(img, c, r, petal, core):
    for j in range(5):
        a = -math.pi / 2 + 2 * math.pi * j / 5
        disc(img, (c[0] + math.cos(a) * r * 0.55, c[1] + math.sin(a) * r * 0.55), r * 0.42, petal)
    disc(img, c, r * 0.3, WHITE)
    disc(img, c, r * 0.18, core)


def dc14_maehwa_scatter(t):
    """매화점: 작은 다섯 잎 꽃이 화면 가득 톡톡톡 튀어나온다."""
    img = blank()
    g = rng(21)
    spots = cached("mae", lambda: [((g.uniform(60, W - 60), g.uniform(60, H - 60)), g.uniform(16, 44),
                                    g.uniform(0, 1.1), int(g.integers(4))) for _ in range(90)])
    pals = [(JU, HWANG), (SAMCHEONG, HWANG), (NOK, JU), (DAJA, HWANG)]
    for c, r, t0, pi in spots:
        p = ease_back((t - t0) / 0.22, 2.2)
        if p <= 0.01:
            continue
        mae_flower(img, c, r * p, *pals[pi])
    return dim(img, fade_env(t, 2.3, 3.5))


def dc15_wave_rise(t):
    """물결 비늘이 아래에서 출렁이며 차올랐다가 가라앉는다. 녹색 물결."""
    pat = cached("wave_green", lambda: _green_waves())
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    level = H * 0.62 * ease_out(t / 0.8) * (1 - ease_in_out((t - 1.8) / 1.0))
    edge = H + 60 - level + 22 * np.sin(x / 120 + t * 5)
    m = np.clip((y - edge) / 30, 0, 1)
    if t >= 2.85:
        m = m * 0
    return over_white(pat, m)


def _green_waves():
    img = blank()
    cell = 130
    bands = [WHITE, NOK, WHITE, YANGNOK, WHITE, PALE_G, TEAL]
    rows = int(H / (cell * 0.5)) + 3
    for row in range(rows):
        cy = row * cell * 0.5 - cell * 0.5
        off = (cell / 2) if row % 2 else 0
        for col in range(-1, int(W / cell) + 2):
            for i, cc in enumerate(bands):
                disc(img, (col * cell + off, cy), cell * 0.62 * (1 - i / (len(bands) + 1)), cc)
    return img


def _garland():
    img = blank()
    cell = 200
    arcs = [DAJA, JU, ORANGE, HWANG, YANGNOK, SAMCHEONG, PURPLE]
    for col in range(-1, W // cell + 2):
        cx = col * cell + cell / 2
        for cy in (0, H):
            for i, c in enumerate(arcs):
                r = cell * 0.62 * (1 - i / (len(arcs) + 0.4))
                disc(img, (cx, cy), r + 4, WHITE)
                disc(img, (cx, cy), r, c)
    img[0:14] = MUK
    img[H - 14:] = MUK
    return img


def dc16_arch_garland(t):
    """무지개 반원 장식이 위아래 가장자리를 따라 왼쪽에서 오른쪽으로 펼쳐졌다 걷힌다."""
    pat = cached("garland", _garland)
    x = np.arange(W, dtype=np.float32)[None, :]
    head = -100 + (W + 200) * ease_out(t / 0.7)
    tail = -100 + (W + 300) * ease_in_out((t - 1.6) / 1.0)
    m = np.clip((head - x) / 80, 0, 1) * np.ones((H, 1), np.float32)
    if t > 1.6:
        m = m * np.clip((x - tail) / 80, 0, 1)
    if t >= 2.9:
        m = m * 0
    return over_white(pat, m)


def dc17_clock_petals(t):
    """꽃잎 시계: 뾰족 꽃잎이 시곗바늘처럼 한 장씩 돌아가며 피고 전체가 천천히 돈다. 보라·청."""
    img = blank()
    c = (W / 2, H / 2)
    rot = 0.35 * t - math.pi / 2
    n = 16
    for k in range(n):
        p = ease_out((t - k * 0.045) / 0.35)
        if p <= 0:
            continue
        a = rot + 2 * math.pi * k / n
        bands = [WHITE, PURPLE, SAMCHEONG, PALE_B, WHITE] if k % 2 == 0 else [WHITE, NAVY, SKY, WHITE]
        draw_petal(img, c, a, 90, 400 * p, 120 * p, bands)
    p2 = ease_out((t - 0.75) / 0.4)
    if p2 > 0:
        for k in range(8):
            a = -rot * 1.3 + 2 * math.pi * (k + 0.5) / 8
            draw_petal(img, c, a, 30, 160 * p2, 70 * p2, [WHITE, JU, PINK, WHITE])
        disc(img, c, 50 * p2, HWANG)
        disc(img, c, 28 * p2, JU)
    return dim(img, fade_env(t, 2.4, 3.6))


def dc18_octagon_ripple(t):
    """팔모 메달: 팔각 띠가 안에서 밖으로 차례로 퍼지며 번갈아 돈다. 주홍·황."""
    img = blank()
    c = (W / 2, H / 2)
    cols = [DAJA, JU, ORANGE, HWANG, JU, DAJA, OCHRE]
    n = len(cols)
    for i in range(n - 1, -1, -1):
        p = ease_back((t - i * 0.08) / 0.4, 1.0)
        if p <= 0:
            continue
        R = (90 + i * 62) * p
        rot = (0.15 if i % 2 else -0.15) * t + math.pi / 8
        poly(img, reg_poly(c, R + 44, 8, rot), cols[i])
        poly(img, reg_poly(c, R + 32, 8, rot), WHITE)
        poly(img, reg_poly(c, R + 24, 8, rot), cols[(i + 3) % n])
        poly(img, reg_poly(c, R + 14, 8, rot), WHITE)
    pc = ease_out((t - 0.2) / 0.5)
    if pc > 0:
        rounded_petals(img, c, 8, 10, 70 * pc, 34 * pc, 0.3 * t, [JU, PINK, WHITE])
        disc(img, c, 20 * pc, HWANG)
    return dim(img, fade_env(t, 2.4, 3.6))


def dc19_lotus_ring(t):
    """연화 고리: 작은 연꽃 여덟 송이가 원을 따라 시계 방향으로 차례로 피고 고리째 돈다. 청록."""
    img = blank()
    c = (W / 2, H / 2)
    sch = ([WHITE, NOK, YANGNOK, PALE_G, WHITE], [WHITE, SAMCHEONG, SKY, WHITE], [WHITE, HWANG, NOK, HWANG])
    spin = 0.3 * ease_in_out(t / 3.0)
    for k in range(8):
        p = ease_out((t - k * 0.08) / 0.55)
        if p <= 0:
            continue
        a = -math.pi / 2 + 2 * math.pi * k / 8 + spin
        draw_lotus(img, (c[0] + 340 * math.cos(a), c[1] + 340 * math.sin(a)), 130, p, a, sch)
    pr = ease_out(t / 0.6)
    ring(img, c, 200 * pr, 14, TEAL)
    ring(img, c, 170 * pr, 6, NOK)
    disc(img, c, 60 * pr, YANGNOK)
    disc(img, c, 34 * pr, HWANG)
    return dim(img, fade_env(t, 2.4, 3.6))


def dc20_diamond_chain(t):
    """금문 마름모 사슬: 겹 마름모들이 오른쪽에서 줄지어 미끄러져 들어왔다가 왼쪽으로 빠진다. 황·먹."""
    img = blank()
    n = 9
    w, h = 220, 300
    step = 200
    xs0 = W / 2 - (n - 1) * step / 2
    cols = [MUK, HWANG, MUK, OCHRE, WHITE, JU]
    for i in range(n):
        target = xs0 + i * step
        pin = ease_out((t - i * 0.05) / 0.5)
        pout = ease_in_out((t - 1.8 - i * 0.04) / 0.6)
        x = target + (W + 300 - target) * (1 - pin) - (target + 300) * pout
        cy = H / 2
        for j, col in enumerate(cols):
            s = 1 - 0.15 * j
            poly(img, [(x, cy - h / 2 * s), (x + w / 2 * s, cy), (x, cy + h / 2 * s), (x - w / 2 * s, cy)], col)
    return img


def _fret_strip(length, bw=96):
    img = np.full((bw, length, 3), 255, np.uint8)
    img[0:8] = MUK
    img[bw - 8:] = MUK
    unit = 96
    for k in range(-1, length // unit + 2):
        x = k * unit + 8
        u = unit * 0.8
        y0, y1 = 20, bw - 20
        pts = [(x, y1), (x, y0), (x + u * 0.8, y0), (x + u * 0.8, y1 - 18), (x + u * 0.3, y1 - 18),
               (x + u * 0.3, y0 + 18), (x + u * 0.55, y0 + 18)]
        path_line(img, pts, 9, JU)
        path_line(img, [(x + u * 0.8, y1), (x + unit, y1)], 9, JU)
    return img


def _fret_frame():
    bw = 96
    img = blank()
    img[:bw] = _fret_strip(W, bw)
    img[H - bw:] = _fret_strip(W, bw)[::-1, ::-1]
    side = np.rot90(_fret_strip(H, bw), -1)  # 세로 띠
    img[:, W - bw:] = np.minimum(img[:, W - bw:], side)
    img[:, :bw] = np.minimum(img[:, :bw], side[::-1, ::-1])
    return img


def dc21_fret_frame(t):
    """뇌문 테두리: 번개무늬 띠가 화면 가장자리를 따라 시계 방향으로 한 바퀴 그려졌다 사라진다. 먹·주홍."""
    pat = cached("fret", _fret_frame)
    sp = cached("fret_s", _perimeter_param)
    prog = ease_in_out(t / 1.1)
    m = (sp < prog).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 3) if prog < 1 else m
    k = fade_env(t, 2.3, 3.4)
    return over_white(pat, m * k)


def _perimeter_param():
    """가장자리 띠의 각 점이 왼쪽 위에서 시계 방향으로 몇 % 지점인지 (0..1). 가운데는 2."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    per = 2 * (W + H)
    s = np.full((H, W), 2.0, np.float32)
    bw = 96
    top = y < bw
    right = x >= W - bw
    bottom = y >= H - bw
    left = x < bw
    s = np.where(left, (W + H + W + (H - y)) / per, s)
    s = np.where(bottom, (W + H + (W - x)) / per, s)
    s = np.where(right, (W + y) / per, s)
    s = np.where(top, x / per, s)
    return s


def dc22_falling_petals(t):
    """꽃잎 비: 분홍·주홍 꽃잎이 위에서 빙글빙글 흩날리며 떨어진다."""
    img = blank()
    g = rng(5)
    petals = cached("fall", lambda: [(g.uniform(0, W), g.uniform(0, 0.8), g.uniform(420, 820), g.uniform(-4, 4),
                                      g.uniform(80, 150), int(g.integers(3)), g.uniform(0, 6.28)) for _ in range(60)])
    pals = [[WHITE, JU, PINK, WHITE], [WHITE, ROSE, PINK], [WHITE, ORANGE, HWANG, WHITE]]
    for x0, t0, v, spin, L, pi, ph in petals:
        lt = t - t0
        if lt <= 0:
            continue
        y = -80 + v * lt
        x = x0 + 60 * math.sin(lt * 2.2 + ph)
        if y > H + 100:
            continue
        a = ph + spin * lt
        draw_petal(img, (x, y), a, -L * 0.45, L, L * 0.38, pals[pi])
    return dim(img, fade_env(t, 2.8, 3.7))


def dc23_sun_rays(t):
    """보상화 빛살: 오방색 빛살이 가운데서 확 뻗었다가 다시 빨려 들어간다."""
    img = blank()
    c = (W / 2, H / 2)
    n = 28
    cols = [SAMCHEONG, JU, HWANG, NOK, DAJA, WHITE, ORANGE]
    R = 1250 * ease_out(t / 0.5) * (1 - ease_in_out((t - 1.6) / 0.8))
    rot = 0.2 * t
    if R > 140:
        for k in range(n):
            a0 = rot + 2 * math.pi * k / n
            a1 = rot + 2 * math.pi * (k + 0.6) / n
            pts = [(c[0] + 120 * math.cos(a0), c[1] + 120 * math.sin(a0)), (c[0] + R * math.cos(a0), c[1] + R * math.sin(a0)),
                   (c[0] + R * math.cos(a1), c[1] + R * math.sin(a1)), (c[0] + 120 * math.cos(a1), c[1] + 120 * math.sin(a1))]
            poly(img, pts, cols[k % len(cols)])
    pc = ease_back(t / 0.4)
    if 0.01 < pc and t < 2.6:
        disc(img, c, 130 * pc, MUK)
        disc(img, c, 110 * pc, WHITE)
        rounded_petals(img, c, 6, 6, 80 * pc, 46 * pc, -0.4 * t, [JU, HWANG, WHITE])
        disc(img, c, 22 * pc, SAMCHEONG)
    return dim(img, fade_env(t, 2.4, 3.3))


def cloud_shape(img, c, R, pal):
    """둥근 구름: 동그라미 다섯 개를 겹쳐 띠를 둔다."""
    offs = [(-1.0, 0.15, 0.55), (-0.45, -0.25, 0.7), (0.15, -0.35, 0.8), (0.75, -0.1, 0.65), (1.15, 0.2, 0.5),
            (0.1, 0.25, 0.75)]
    for i, col in enumerate(pal):
        k = 1 - 0.2 * i
        for ox, oy, rr in offs:
            disc(img, (c[0] + ox * R, c[1] + oy * R), rr * R * k, col)


def dc24_cloud_drift(t):
    """오색 구름: 겹 구름 송이들이 부풀어 오르며 왼쪽에서 오른쪽으로 흘러간다. 가칠 하늘빛."""
    img = blank()
    clouds = [(200, 260, 110, 520, 0.0, (NAVY, WHITE, SKY, PALE_B)), (-100, 560, 150, 420, 0.12, (TEAL, WHITE, PALE_G, WHITE)),
              (500, 820, 120, 480, 0.2, (PURPLE, WHITE, PALE_B, WHITE)), (900, 380, 100, 380, 0.3, (SAMCHEONG, WHITE, SKY, WHITE)),
              (1200, 720, 130, 450, 0.08, (NAVY, WHITE, PALE_B, SKY)), (1450, 220, 90, 500, 0.25, (TEAL, WHITE, SKY, WHITE))]
    for x0, y0, R, v, t0, pal in clouds:
        lt = t - t0
        if lt <= 0:
            continue
        p = ease_back(lt / 0.45)
        cloud_shape(img, (x0 + v * lt, y0 + 10 * math.sin(lt * 3)), R * p, pal)
    return dim(img, fade_env(t, 2.3, 3.5))


def dc25_hexa_cross(t):
    """육엽 십자 금단: 큰 여섯 잎 꽃에서 네 방향으로 줄무늬 팔이 쭉 뻗어 나간다. 녹화."""
    img = blank()
    c = (W / 2, H / 2)
    arm = ease_out((t - 0.25) / 0.6)
    if arm > 0:
        cols = [NOK, WHITE, YANGNOK, WHITE, HWANG]
        for i, col in enumerate(cols):
            hw = 70 - i * 13
            L = 1100 * arm
            poly(img, [(c[0] - L, c[1] - hw), (c[0] + L, c[1] - hw), (c[0] + L, c[1] + hw), (c[0] - L, c[1] + hw)], col)
            poly(img, [(c[0] - hw, c[1] - L), (c[0] + hw, c[1] - L), (c[0] + hw, c[1] + L), (c[0] - hw, c[1] + L)], col)
    p = ease_back(t / 0.6, 1.2)
    if p > 0:
        disc(img, c, 330 * p, WHITE)
        rounded_petals(img, c, 6, 40 * p, 270 * p, 190 * p, 0.2 * t, [NOK, WHITE, YANGNOK, PALE_G, WHITE])
        disc(img, c, 90 * p, JU)
        disc(img, c, 64 * p, WHITE)
        disc(img, c, 46 * p, HWANG)
    return dim(img, fade_env(t, 2.3, 3.5))


def dc26_corner_fans(t):
    """네 귀 부채: 화면 네 귀퉁이에서 부채꼴 무늬가 촤악 펼쳐졌다 접힌다. 주홍·청 번갈아."""
    img = blank()
    corners = [((0, 0), 0, (DAJA, JU, ORANGE, HWANG)), ((W, 0), 90, (NAVY, SAMCHEONG, SKY, PALE_B)),
               ((W, H), 180, (DAJA, JU, ORANGE, HWANG)), ((0, H), 270, (NAVY, SAMCHEONG, SKY, PALE_B))]
    for i, ((cx, cy), base, pal) in enumerate(corners):
        open_ = ease_out((t - i * 0.08) / 0.5) * (1 - ease_in_out((t - 1.9 - i * 0.05) / 0.6))
        if open_ <= 0.01:
            continue
        sweep = 90 * open_
        R = 560
        for j in range(6):
            col = pal[j % len(pal)]
            r = R - j * 80
            if r <= 0:
                break
            cv2.ellipse(img, (cx, cy), (r, r), 0, base, base + sweep, col, -1, cv2.LINE_AA)
            cv2.ellipse(img, (cx, cy), (r - 14, r - 14), 0, base, base + sweep, WHITE, -1, cv2.LINE_AA)
            cv2.ellipse(img, (cx, cy), (r - 22, r - 22), 0, base, base + sweep, col, -1, cv2.LINE_AA)
        # 부채살
        for k in range(7):
            a = math.radians(base + sweep * k / 6)
            path_line(img, [(cx, cy), (cx + R * math.cos(a), cy + R * math.sin(a))], 6, WHITE)
    return img


CLIPS = {
    "dc05_hex_lattice": dc05_hex_lattice,
    "dc06_cloud_scroll": dc06_cloud_scroll,
    "dc07_aja_lattice": dc07_aja_lattice,
    "dc08_jewel_spiral": dc08_jewel_spiral,
    "dc09_rainbow_ripple": dc09_rainbow_ripple,
    "dc10_twin_lotus": dc10_twin_lotus,
    "dc11_star_rosette": dc11_star_rosette,
    "dc12_soran_grid": dc12_soran_grid,
    "dc13_pillar_bands": dc13_pillar_bands,
    "dc14_maehwa_scatter": dc14_maehwa_scatter,
    "dc15_wave_rise": dc15_wave_rise,
    "dc16_arch_garland": dc16_arch_garland,
    "dc17_clock_petals": dc17_clock_petals,
    "dc18_octagon_ripple": dc18_octagon_ripple,
    "dc19_lotus_ring": dc19_lotus_ring,
    "dc20_diamond_chain": dc20_diamond_chain,
    "dc21_fret_frame": dc21_fret_frame,
    "dc22_falling_petals": dc22_falling_petals,
    "dc23_sun_rays": dc23_sun_rays,
    "dc24_cloud_drift": dc24_cloud_drift,
    "dc25_hexa_cross": dc25_hexa_cross,
    "dc26_corner_fans": dc26_corner_fans,
}


def main(names):
    out_dir = d.ROOT / "clips" / "dancheong"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, fn in CLIPS.items():
        if not names or any(name.startswith(n) for n in names):
            d.render(name, fn, out_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
