"""단청 뱅크(뱅크 2)용 배경과 원샷 영상을 만든다.

    python3 tools/dancheong.py            # 배경 + 영상 4개 전부
    python3 tools/dancheong.py dc01 dc03  # 원하는 영상만

출력
- assets/giwa.jpg       : 검회색 기와무늬 배경 (단순화)
- clips/dancheong/*.mp4 : 1920x1080, 30fps, 4초. 검은 바탕 위 단청 문양.
  화면에서는 기와 배경 위에 '밝게(lighten)'로 겹치므로 검은 부분은 사라지고 색만 남는다.
  첫 프레임과 마지막 프레임은 완전한 검정이라 다시 눌러도 끊김이 없다.

참고 이미지를 베끼지 않고, 단청의 기본 요소(연화 꽃잎의 겹겹 빛넣기 띠, 물결 비늘, 머리초 무지개 띠,
매화점)를 단청 색으로 새로 그렸다. numpy + OpenCV + ffmpeg 필요.
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
SS = 2  # 안티에일리어싱용 내부 배율은 쓰지 않고 LINE_AA로 처리, 좌표만 고정소수점
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


def blank():
    return np.zeros((H, W, 3), np.uint8)


def dim(img, k):
    if k >= 1:
        return img
    return (img.astype(np.float32) * k).astype(np.uint8)


# ---------------------------------------------------------------- 영상 4개

def dc01_lotus_bloom(t):
    """가운데에서 큰 연화문이 돌며 피었다가 살짝 커지며 사라진다."""
    img = blank()
    if t < 0.02:
        return img
    prog = ease_out(t / 0.9)
    grow = 1 + 0.08 * max(0.0, t - 1.0) / 3
    rot = -0.6 * (1 - prog) + 0.04 * t
    draw_lotus(img, (W / 2, H / 2), 470 * grow, prog, rot, SCHEMES[0])
    return dim(img, fade_env(t))


def wave_scales(cell=110):
    """물결 비늘 무늬 한 장 (전체 화면 크기)."""
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
    """물결 비늘 띠가 왼쪽에서 오른쪽으로 '삭' 쓸고 지나간다."""
    global _WAVES
    if _WAVES is None:
        _WAVES = wave_scales()
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    skew = (y - H / 2) * 0.35  # 살짝 기울어진 쓸기
    soft = 140.0
    head = -300 + (W + 700) * ease_out(t / 0.55)          # 나타나는 앞쪽 경계
    tail = -300 + (W + 900) * ease_in_out((t - 1.1) / 1.4)  # 사라지는 뒤쪽 경계
    m_in = np.clip((head - (x + skew)) / soft, 0, 1)
    m_out = np.clip(((x + skew) - tail) / soft, 0, 1) if t > 1.1 else 1.0
    band = np.clip(1 - np.abs(y - H / 2) / 330, 0, 1) ** 0.6  # 가운데 가로 띠
    mask = (m_in * m_out * np.minimum(band * 1.6, 1.0))
    if t >= 3.0:
        mask = mask * 0
    out = (_WAVES.astype(np.float32) * mask[..., None]).astype(np.uint8)
    return out


_SPOTS = None


def dc03_scatter_blooms(t):
    """작은 연화·매화가 여기저기 차례로 톡톡 피었다가 진다."""
    global _SPOTS
    if _SPOTS is None:
        rng = np.random.default_rng(7)
        spots = []
        tries = 0
        while len(spots) < 11 and tries < 2000:
            tries += 1
            r = rng.uniform(90, 190)
            c = (rng.uniform(r + 40, W - r - 40), rng.uniform(r + 30, H - r - 30))
            if all(math.hypot(c[0] - s[0][0], c[1] - s[0][1]) > (r + s[1]) * 0.95 for s in spots):
                spots.append((c, r, len(spots) * 0.075 + rng.uniform(0, 0.03), rng.uniform(0, 6.28), rng.integers(4)))
        _SPOTS = spots
    img = blank()
    for c, r, t0, rot0, sch in _SPOTS:
        lt = t - t0
        if lt <= 0:
            continue
        prog = ease_out(lt / 0.45)
        draw_lotus(img, c, r, prog, rot0 + 0.3 * (1 - prog), SCHEMES[int(sch)])
    return dim(img, fade_env(t, 2.3, 3.6))


def dc04_rainbow_ripple(t):
    """머리초의 무지개 띠가 동그란 물결처럼 바깥으로 퍼져 나간다."""
    img = blank()
    c = (W / 2, H / 2)
    bands = [JU, ORANGE, HWANG, YANGNOK, SKY, SAMCHEONG, PURPLE]
    band_w = 26
    gap = 6
    stack = len(bands) * (band_w + gap)
    for wave in range(2):
        lt = t - wave * 0.35
        if lt <= 0:
            continue
        r_front = 40 + 1250 * ease_out(lt / 2.2)
        for i, col in enumerate(bands):
            r = r_front - i * (band_w + gap)
            if r > 0:
                ring(img, c, r, band_w + 2, WHITE)
                ring(img, c, r, band_w - 4, col)
    # 가운데 작은 꽃
    prog = ease_out(t / 0.5)
    draw_lotus(img, c, 150, prog, 0.2 * t, SCHEMES[1])
    return dim(img, fade_env(t, 2.2, 3.6))


CLIPS = {
    "dc01_lotus_bloom": dc01_lotus_bloom,
    "dc02_wave_sweep": dc02_wave_sweep,
    "dc03_scatter_blooms": dc03_scatter_blooms,
    "dc04_rainbow_ripple": dc04_rainbow_ripple,
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


# ---------------------------------------------------------------- 기와 배경

def giwa_background():
    """검회색 기와 지붕을 위에서 본 단순한 무늬: 둥근 골이 세로로 늘어서고 가로 줄마다 이음새."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    row_h = 216.0
    col_w = 92.0
    row = np.floor(y / row_h)
    fy = (y - row * row_h) / row_h  # 줄 안에서 0..1
    # 기와골이 줄마다 살짝 휘어진다
    bend = 26 * np.sin(fy * np.pi) * np.where(row % 2 == 0, 1, -1) + 14 * np.sin(x / 300 + row * 1.7)
    u = ((x + bend + (row % 2) * col_w * 0.5) / col_w) % 1.0
    # 수키와(볼록)와 암키와(오목)를 번갈아: 원통 음영
    shade = np.sin(u * np.pi) ** 0.7
    # 아래쪽 이음새 그림자 + 위쪽 끝 하이라이트
    seam = np.clip((fy - 0.88) / 0.12, 0, 1) ** 1.5
    lip = np.clip((0.06 - fy) / 0.06, 0, 1)
    v = 34 + 42 * shade - 16 * seam + 6 * lip
    # 아주 약한 결
    rng = np.random.default_rng(3)
    grain = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2)
    v = v + grain * 2.5
    # 가장자리 비네팅
    vig = 1 - 0.25 * (((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    v = np.clip(v * vig, 0, 255)
    img = np.stack([v * 1.02, v * 1.0, v * 0.97], -1)  # 아주 살짝 푸른 먹빛
    return np.clip(img, 0, 255).astype(np.uint8)


def main(names):
    out_dir = ROOT / "clips" / "dancheong"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not names:
        cv2.imwrite(str(ROOT / "assets" / "giwa.jpg"), giwa_background(), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("wrote assets/giwa.jpg")
    for name, fn in CLIPS.items():
        if not names or any(name.startswith(n) for n in names):
            render(name, fn, out_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
