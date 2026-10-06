"""단청 뱅크(뱅크 2)용 배경과 원샷 영상을 만든다.

    python3 tools/dancheong.py            # 배경 + 영상 4개 전부
    python3 tools/dancheong.py dc01 dc03  # 원하는 영상만

출력
- assets/hanji_aged.jpg : 수묵 뱅크보다 누렇고 바랜 한지 배경
- clips/dancheong/*.mp4 : 1920x1080, 30fps, 4초. 흰 바탕 위 단청 문양.
  화면에서는 한지 배경 위에 수묵과 같은 '어둡게(darken)'로 겹치므로 흰 부분은 한지가 되고 색만 남는다.
  첫 프레임과 마지막 프레임은 완전한 흰색이라 다시 눌러도 끊김이 없다.

참고 이미지를 베끼지 않고, 단청의 기본 요소(연화 꽃잎의 겹겹 빛넣기 띠, 물결 비늘, 네모 문양판,
머리초 무지개 반원과 매화점 줄)를 단청 색으로 새로 그렸다. numpy + OpenCV + ffmpeg 필요.
"""
import math
import pathlib
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS, DUR = 1920, 1080, 30, 4.0
N = int(FPS * DUR)
ROOT = pathlib.Path(__file__).resolve().parent.parent
SHIFT = 4
ONE = 1 << SHIFT


def rgb(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)  # OpenCV는 BGR


# 단청 색
WHITE = rgb("f4f1e8")
NOK = rgb("2f6b4f")      # 뇌록
YANGNOK = rgb("3fae6a")  # 양록
PALE_G = rgb("9fd8a8")
SAMCHEONG = rgb("2a55b0")  # 삼청
SKY = rgb("5fb8e0")
PALE_B = rgb("a9dcef")
NAVY = rgb("27306e")
JU = rgb("d8402c")       # 주홍
DAJA = rgb("8a2234")     # 다자
PINK = rgb("f39ab0")
HWANG = rgb("f2c22e")    # 황
ORANGE = rgb("f08a2a")
PURPLE = rgb("7a5bc4")


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def fade_env(t, out_start=2.6, out_end=3.75):
    """밝기 곱. 4초 전에 완전히 0이 된다."""
    if t >= out_end:
        return 0.0
    if t <= out_start:
        return 1.0
    return 1 - ease_in_out((t - out_start) / (out_end - out_start))


def poly(img, pts, color):
    p = np.round(np.asarray(pts) * ONE).astype(np.int32).reshape(-1, 1, 2)
    cv2.fillPoly(img, [p], color, lineType=cv2.LINE_AA, shift=SHIFT)


def disc(img, c, r, color):
    if r <= 0.5:
        return
    cv2.circle(img, (int(round(c[0] * ONE)), int(round(c[1] * ONE))), int(round(r * ONE)), color, -1,
               lineType=cv2.LINE_AA, shift=SHIFT)


def ring(img, c, r, thick, color):
    if r <= 0.5 or thick <= 0:
        return
    cv2.circle(img, (int(round(c[0] * ONE)), int(round(c[1] * ONE))), int(round(r * ONE)), color,
               max(1, int(round(thick))), lineType=cv2.LINE_AA, shift=SHIFT)


# ---------------------------------------------------------------- 꽃잎과 연화 문양

def petal_shape(length, width, n=40):
    """원점에서 +x 방향으로 뻗는 끝이 뾰족한 꽃잎 (로컬 좌표)."""
    t = np.linspace(0, 1, n)
    x = length * t
    w = width * np.sin(np.pi * t) ** 0.75 * (1 - 0.25 * t)
    upper = np.stack([x, w], 1)
    lower = np.stack([x[::-1], -w[::-1]], 1)
    return np.concatenate([upper, lower])


def draw_petal(img, center, angle, r0, length, width, bands):
    """bands: 바깥→안쪽 색 목록. 단청의 빛넣기처럼 같은 모양을 겹겹이 줄여 그린다."""
    base = petal_shape(length, width)
    pivot = np.array([length * 0.42, 0.0])
    ca, sa = math.cos(angle), math.sin(angle)
    rot = np.array([[ca, -sa], [sa, ca]])
    n = len(bands)
    for i, col in enumerate(bands):
        s = 1.0 - 0.8 * i / max(n, 1)
        shp = (base - pivot) * s + pivot
        shp = shp + np.array([r0, 0.0])
        pts = shp @ rot.T + np.asarray(center)
        poly(img, pts, col)


def draw_lotus(img, center, R, progress, rot, scheme):
    """연화문(연꽃 원형 문양). progress 0→1 로 안쪽부터 피어난다."""
    outer_bands, inner_bands, core = scheme
    # 바깥 꽃잎 (늦게 핀다)
    p_out = ease_out((progress - 0.25) / 0.75)
    if p_out > 0:
        n = 8
        for k in range(n):
            a = rot + 2 * math.pi * k / n
            draw_petal(img, center, a, R * 0.30 * p_out, R * 0.70 * p_out, R * 0.26 * p_out, outer_bands)
    # 안쪽 꽃잎 (반 칸 어긋나게)
    p_in = ease_out((progress - 0.08) / 0.7)
    if p_in > 0:
        n = 8
        for k in range(n):
            a = rot + 2 * math.pi * (k + 0.5) / n
            draw_petal(img, center, a, R * 0.18 * p_in, R * 0.46 * p_in, R * 0.17 * p_in, inner_bands)
    # 꽃술 (가운데 동그라미 겹)
    p_c = ease_out(progress / 0.5)
    if p_c > 0:
        rr = R * 0.24 * p_c
        for i, col in enumerate(core):
            disc(img, center, rr * (1 - i / (len(core) + 0.5)), col)
        # 꽃술 점 고리
        for k in range(12):
            a = rot * 2 + 2 * math.pi * k / 12
            disc(img, (center[0] + math.cos(a) * rr * 0.72, center[1] + math.sin(a) * rr * 0.72), rr * 0.08, WHITE)


SCHEMES = [
    ([WHITE, NOK, YANGNOK, PALE_G, WHITE], [WHITE, DAJA, JU, PINK, WHITE], [WHITE, HWANG, JU, HWANG]),
    ([WHITE, NAVY, SAMCHEONG, SKY, PALE_B, WHITE], [WHITE, JU, ORANGE, HWANG], [WHITE, YANGNOK, HWANG, JU]),
    ([WHITE, DAJA, JU, PINK, WHITE], [WHITE, NOK, YANGNOK, PALE_G], [WHITE, SAMCHEONG, SKY, WHITE]),
    ([WHITE, PURPLE, SAMCHEONG, PALE_B, WHITE], [WHITE, HWANG, ORANGE, WHITE], [WHITE, JU, HWANG, JU]),
]


MUK = rgb("23262b")       # 먹(검정)


def blank():
    return np.full((H, W, 3), 255, np.uint8)


def dim(img, k):
    """흰 바탕 쪽으로 옅어진다 (k=0 이면 완전한 흰색)."""
    if k >= 1:
        return img
    return (255 - (255 - img.astype(np.float32)) * k).astype(np.uint8)


def over_white(pattern, mask):
    """mask(0..1) 만큼만 무늬를 보이고 나머지는 흰 바탕."""
    m = mask[..., None] if np.ndim(mask) == 2 else mask
    return (255 - (255 - pattern.astype(np.float32)) * m).astype(np.uint8)


# ---------------------------------------------------------------- 1. 연화문: 가운데서 피었다 진다

def dc01_lotus_bloom(t):
    """끝이 뾰족한 연꽃잎 두 겹이 돌며 피었다가 살짝 커지며 옅어진다."""
    img = blank()
    if t < 0.02:
        return img
    prog = ease_out(t / 0.9)
    grow = 1 + 0.08 * max(0.0, t - 1.0) / 3
    rot = -0.6 * (1 - prog) + 0.04 * t
    draw_lotus(img, (W / 2, H / 2), 470 * grow, prog, rot, SCHEMES[0])
    return dim(img, fade_env(t))


# ---------------------------------------------------------------- 2. 물결 비늘: 띠가 '삭' 쓸고 지나간다

def wave_scales(cell=110):
    img = blank()
    bands = [WHITE, NAVY, WHITE, SAMCHEONG, WHITE, SKY, PALE_B]
    rows = int(H / (cell * 0.5)) + 3
    for row in range(rows):
        cy = row * cell * 0.5 - cell * 0.5
        off = (cell / 2) if row % 2 else 0
        for col in range(-1, int(W / cell) + 2):
            cx = col * cell + off
            for i, c in enumerate(bands):
                disc(img, (cx, cy), cell * 0.62 * (1 - i / (len(bands) + 1)), c)
    return img


_WAVES = None


def dc02_wave_sweep(t):
    global _WAVES
    if _WAVES is None:
        _WAVES = wave_scales()
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    skew = (y - H / 2) * 0.35
    soft = 140.0
    head = -300 + (W + 700) * ease_out(t / 0.55)
    tail = -300 + (W + 900) * ease_in_out((t - 1.1) / 1.4)
    m_in = np.clip((head - (x + skew)) / soft, 0, 1)
    m_out = np.clip(((x + skew) - tail) / soft, 0, 1) if t > 1.1 else 1.0
    band = np.clip(1 - np.abs(y - H / 2) / 330, 0, 1) ** 0.6
    mask = m_in * m_out * np.minimum(band * 1.6, 1.0)
    if t >= 3.0:
        mask = mask * 0
    return over_white(_WAVES, mask)


# ---------------------------------------------------------------- 3. 네모 문양판: 둥근 꽃잎 원판이 차례로 톡톡

def rounded_petals(img, c, n, r0, length, width, rot, bands):
    for k in range(n):
        a = rot + 2 * math.pi * k / n
        deg = math.degrees(a)
        for i, col in enumerate(bands):
            s = 1 - 0.78 * i / len(bands)
            mid = r0 + length / 2
            pc = (c[0] + math.cos(a) * mid, c[1] + math.sin(a) * mid)
            pts = cv2.ellipse2Poly((int(pc[0] * 8), int(pc[1] * 8)),
                                   (max(1, int(length / 2 * s * 8)), max(1, int(width / 2 * s * 8))),
                                   int(deg), 0, 360, 6)
            poly(img, pts / 8.0, col)


def square(img, c, half, rot, color):
    ca, sa = math.cos(rot), math.sin(rot)
    pts = [(c[0] + (dx * ca - dy * sa) * half, c[1] + (dx * sa + dy * ca) * half)
           for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    poly(img, pts, color)


TILES = [
    # 네모 테두리 띠, 원 띠, 꽃잎 띠, 꽃술, 꽃잎 수
    ([NOK, WHITE, YANGNOK, WHITE], [WHITE, NAVY, SKY], [WHITE, JU, PINK, WHITE], [WHITE, HWANG, JU], 8),
    ([DAJA, WHITE, JU, HWANG], [WHITE, NOK, PALE_G], [WHITE, SAMCHEONG, SKY, PALE_B], [WHITE, JU, WHITE], 6),
    ([SAMCHEONG, WHITE, SKY, WHITE], [WHITE, DAJA, PINK], [WHITE, YANGNOK, PALE_G, WHITE], [WHITE, ORANGE, HWANG], 12),
    ([MUK, WHITE, PURPLE, WHITE], [WHITE, HWANG, ORANGE], [WHITE, JU, PINK], [WHITE, SAMCHEONG, WHITE], 8),
    ([NOK, HWANG, YANGNOK, WHITE], [WHITE, JU, PINK], [WHITE, PURPLE, PALE_B, WHITE], [WHITE, HWANG, JU], 6),
]


def draw_tile(img, c, size, prog, rot, spec):
    sq, circ, petal, core, n = spec
    half = size / 2
    p1 = ease_out(prog / 0.45)
    if p1 <= 0:
        return
    for i, col in enumerate(sq):
        square(img, c, half * p1 * (1 - 0.07 * i), rot, col)
    # 네 귀퉁이 작은 점
    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        ca, sa = math.cos(rot), math.sin(rot)
        k = half * p1 * 0.70
        disc(img, (c[0] + (dx * ca - dy * sa) * k, c[1] + (dx * sa + dy * ca) * k), half * 0.07 * p1, sq[0])
    p2 = ease_out((prog - 0.12) / 0.55)
    if p2 > 0:
        R = half * 0.66 * p2
        for i, col in enumerate(circ):
            disc(img, c, R * (1 - 0.12 * i), col)
    p3 = ease_out((prog - 0.28) / 0.7)
    if p3 > 0:
        R = half * 0.62
        rounded_petals(img, c, n, R * 0.22 * p3, R * 0.72 * p3, R * (1.9 / n + 0.12) * p3 * 1.6, rot * 2, petal)
        for i, col in enumerate(core):
            disc(img, c, R * 0.26 * p3 * (1 - i / (len(core) + 0.6)), col)


def dc03_tile_medallions(t):
    """네모 문양판 다섯 장이 왼쪽부터 차례로 돌며 펼쳐졌다가 옅어진다."""
    img = blank()
    size, gap = 350, 22
    x0 = W / 2 - 2 * (size + gap)
    for i, spec in enumerate(TILES):
        lt = t - 0.09 * i
        if lt <= 0:
            continue
        prog = ease_out(lt / 0.7)
        y = H / 2 + (40 if i % 2 else -40)
        draw_tile(img, (x0 + i * (size + gap), y), size, prog, 0.6 * (1 - prog), spec)
    return dim(img, fade_env(t, 2.3, 3.6))


# ---------------------------------------------------------------- 4. 머리초 띠: 무지개 반원과 줄무늬가 펼쳐졌다 닫힌다

def meoricho_band():
    """가로 띠 한 장: 가운데 무지개 반원 줄, 위아래로 매화점 검은 줄과 색 줄무늬 (위아래 대칭)."""
    hb = 270  # 띠 반 높이
    half = np.full((hb, W, 3), 255, np.uint8)
    # 가운데 선(맨 아래 y=hb)에 걸친 무지개 반원
    cell = 230
    arcs = [JU, ORANGE, HWANG, YANGNOK, SKY, SAMCHEONG, PURPLE]
    for col in range(-1, W // cell + 2):
        cx = col * cell + cell / 2
        for i, c in enumerate(arcs):
            r = cell * 0.62 * (1 - i / (len(arcs) + 0.5))
            disc(half, (cx, hb + 2), r + 3, WHITE)
            disc(half, (cx, hb + 2), r, c)
    # 위쪽: 색 줄무늬 + 매화점 검은 줄
    y = 0
    for h, c in ((10, MUK), (14, JU), (6, WHITE), (14, YANGNOK), (6, WHITE), (12, HWANG), (6, WHITE)):
        half[y:y + h] = c
        y += h
    strip = 56
    half[y:y + strip] = MUK
    cy = y + strip / 2
    for k in range(W // 110 + 1):
        cx = k * 110 + 55
        for j in range(5):
            a = -math.pi / 2 + 2 * math.pi * j / 5
            disc(half, (cx + math.cos(a) * 11, cy + math.sin(a) * 11), 7, WHITE)
        disc(half, (cx, cy), 5, HWANG)
    y += strip
    for h, c in ((6, WHITE), (12, NAVY), (6, WHITE)):
        half[y:y + h] = c
        y += h
    return np.concatenate([half, half[::-1]], 0)


_BAND = None


def dc04_meoricho_band(t):
    global _BAND
    if _BAND is None:
        _BAND = meoricho_band()
    img = blank()
    bh = _BAND.shape[0]
    y0 = (H - bh) // 2
    # 가운데에서 좌우로 '삭' 펼쳐지고, 나중에 위아래로 접히며 닫힌다
    open_w = (W / 2 + 60) * ease_out(t / 0.45)
    close = ease_in_out((t - 1.7) / 0.9)
    x = np.arange(W, dtype=np.float32)[None, :]
    yy = np.arange(bh, dtype=np.float32)[:, None]
    m = np.clip((open_w - np.abs(x - W / 2)) / 40, 0, 1)
    vis_h = bh / 2 * (1 - close)
    m = m * np.clip((vis_h - np.abs(yy - bh / 2)) / 12, 0, 1)
    if t >= 2.7:
        m = m * 0
    img[y0:y0 + bh] = over_white(_BAND, m)
    return img


CLIPS = {
    "dc01_lotus_bloom": dc01_lotus_bloom,
    "dc02_wave_sweep": dc02_wave_sweep,
    "dc03_tile_medallions": dc03_tile_medallions,
    "dc04_meoricho_band": dc04_meoricho_band,
}


def render(name, fn, out_dir):
    out = out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
           "-g", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        t = i / FPS
        frame = fn(t) if i < N - 1 else blank()
        p.stdin.write(frame.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out.relative_to(ROOT))


# ---------------------------------------------------------------- 바랜 한지 배경

def aged_hanji():
    """수묵 뱅크의 한지(assets/hanji.jpg)를 더 누렇고 바랜 느낌으로."""
    src = cv2.imread(str(ROOT / "assets" / "hanji.jpg")).astype(np.float32)
    src = cv2.resize(src, (W, H))
    mean = src.mean((0, 1), keepdims=True)
    img = mean + (src - mean) * 0.8                     # 대비를 조금 낮춰 바랜 느낌
    img = img * np.array([0.80, 0.93, 0.99], np.float32)  # BGR: 파랑을 빼서 누렇게
    rng = np.random.default_rng(11)
    stain = cv2.resize(rng.normal(0, 1, (9, 16)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    stain = cv2.GaussianBlur(stain, (0, 0), 60)
    stain = (stain - stain.min()) / (stain.max() - stain.min())
    img = img * (1 - 0.07 * stain[..., None] * np.array([1.4, 1.0, 0.6], np.float32))  # 군데군데 누런 얼룩
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.12 * (((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    img = img * vig[..., None] * np.array([0.97, 0.99, 1.0], np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def main(names):
    out_dir = ROOT / "clips" / "dancheong"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not names:
        cv2.imwrite(str(ROOT / "assets" / "hanji_aged.jpg"), aged_hanji(), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("wrote assets/hanji_aged.jpg")
    for name, fn in CLIPS.items():
        if not names or any(name.startswith(n) for n in names):
            render(name, fn, out_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
