"""메인 화면 바탕 그림: 닥섬유가 보이는 밝은 한지, 연한 회보랏빛 넝쿨(당초) 문양지 타일.

    python3 tools/main_textures.py

참고 사진을 쓰지 않고 numpy + OpenCV 로 새로 그린다.
- assets/hanji_dak.jpg   : 1920x1080 아이보리 한지. 닥 섬유 가닥과 티끌.
- assets/dangcho_tile.jpg: 480x480 이음매 없는 타일. 회보랏빛 바탕에 흰 넝쿨·잎.
"""
from math import cos, sin, pi
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SHIFT = 4


def P(pts):
    return (np.asarray(pts) * (1 << SHIFT)).astype(np.int32)


def blur_noise(h, w, s, rng):
    return cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), s)


def hanji_dak(w=1920, h=1080, seed=5):
    rng = np.random.default_rng(seed)
    base = np.array([230, 241, 247], np.float32)          # BGR 아이보리
    mott = blur_noise(h, w, 40, rng)
    mott = mott / np.abs(mott).max()
    pulp = blur_noise(h, w, 1.2, rng)
    pulp = pulp / np.abs(pulp).max()
    img = base[None, None] * (1 + 0.018 * mott[..., None] + 0.012 * pulp[..., None])
    # 섬유: 가늘고 길게 휜 가닥. 대부분 옅은 황갈색, 일부 회색.
    fib = np.zeros((h, w, 3), np.float32)
    acc = np.zeros((h, w), np.float32)
    for i in range(2600):
        x, y = rng.uniform(-50, w + 50), rng.uniform(-50, h + 50)
        L = rng.lognormal(3.6, 0.55)
        a = rng.uniform(0, pi)
        k = rng.normal(0, 0.02)
        pts = []
        for s in np.linspace(0, L, max(4, int(L / 4))):
            a += k * 4 + rng.normal(0, 0.05)
            x += cos(a) * L / max(4, int(L / 4))
            y += sin(a) * L / max(4, int(L / 4))
            pts.append((x, y))
        col = np.array([118, 160, 196], np.float32) if rng.random() < 0.8 else np.array([150, 150, 150], np.float32)
        layer = np.zeros((h, w), np.uint8)
        cv2.polylines(layer, [P(pts)], False, 255, 1, cv2.LINE_AA, SHIFT)
        al = layer.astype(np.float32) / 255 * rng.uniform(0.05, 0.22)
        fib += al[..., None] * col[None, None]
        acc += al
    fcol = np.clip(fib / np.maximum(acc, 1e-4)[..., None], 0, 255)   # 겹친 섬유의 평균 색
    acc = np.clip(acc, 0, 0.8)
    img = img * (1 - acc[..., None]) + fcol * acc[..., None]
    # 티끌
    specks = np.zeros((h, w), np.float32)
    for i in range(140):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        cv2.circle(specks, (int(cx * 16), int(cy * 16)), int(rng.uniform(1.0, 3.0) * 16), rng.uniform(0.08, 0.25),
                   -1, cv2.LINE_AA, SHIFT)
    specks = cv2.GaussianBlur(specks, (0, 0), 1.2)
    img = img * (1 - specks[..., None]) + np.array([120, 150, 175], np.float32) * specks[..., None]
    img = cv2.GaussianBlur(img, (0, 0), 0.5)
    return np.clip(img, 0, 255).astype(np.uint8)


def leaf(img, p, ang, L, W, col):
    """끝이 뾰족하고 한쪽이 톱니처럼 갈라진 당초 잎."""
    pts = []
    for s in np.linspace(0, 1, 30):
        r = W * np.sin(pi * s) ** 0.8 * (1 - 0.35 * s)
        pts.append((s * L, r * (1 + 0.15 * np.sin(s * 18))))
    for s in np.linspace(1, 0, 30):
        r = W * np.sin(pi * s) ** 0.9 * 0.7
        pts.append((s * L, -r))
    c, s_ = cos(ang), sin(ang)
    q = [(p[0] + x * c - y * s_, p[1] + x * s_ + y * c) for x, y in pts]
    cv2.fillPoly(img, [P(q)], col, cv2.LINE_AA, SHIFT)


def scroll(img, c, R, ang0, turns, width, col, rng, leaves=True):
    """바깥에서 안으로 말려 들어가는 덩굴 줄기 + 줄기를 따라 난 잎."""
    pts = []
    n = 140
    for i in range(n):
        t = i / (n - 1)
        a = ang0 + t * turns * 2 * pi
        r = R * (1 - 0.82 * t)
        pts.append((c[0] + r * cos(a), c[1] + r * sin(a)))
    for i in range(n - 1):
        wdt = max(1, int(width * (1 - 0.6 * i / n)))
        cv2.line(img, tuple((np.array(pts[i]) * 16).astype(int)), tuple((np.array(pts[i + 1]) * 16).astype(int)),
                 col, wdt, cv2.LINE_AA, SHIFT)
    if leaves:
        for i in range(6, n - 25, 9):
            a = ang0 + i / (n - 1) * turns * 2 * pi
            side = 1 if (i // 9) % 2 else -1
            r = R * (1 - 0.82 * i / n)
            leaf(img, pts[i], a + pi / 2 + side * 1.0, max(10, r * rng.uniform(0.45, 0.7)), max(4, r * 0.16), col)


def dangcho_tile(T=480, seed=9):
    rng = np.random.default_rng(seed)
    big = np.zeros((T * 3, T * 3, 3), np.uint8)
    white = (246, 244, 245)
    # 크고 작은 덩굴을 고르게 촘촘히: 큰 것 3x3 격자, 작은 것은 그 사이 4x4 격자 (조금씩 흔들어서)
    j = lambda: rng.uniform(-0.06, 0.06)
    motifs = [(((i + 0.5) / 3 + j(), (k + 0.5) / 3 + j()), rng.uniform(0.13, 0.17), rng.uniform(0, 2 * pi),
               rng.uniform(1.1, 1.4)) for i in range(3) for k in range(3)]
    motifs += [(((i + 0.0) / 4 + j(), (k + 0.0) / 4 + j()), rng.uniform(0.05, 0.08), rng.uniform(0, 2 * pi),
                rng.uniform(1.3, 1.7)) for i in range(4) for k in range(4)]
    for (fx, fy), fr, a0, tr in motifs:
        for ox in (0, 1, 2):
            for oy in (0, 1, 2):
                c = ((fx + ox) * T, (fy + oy) * T)
                scroll(big, c, fr * T, a0, tr, 6 if fr > 0.15 else 4, white, np.random.default_rng(int(fx * 100 + fy * 10)))
    pat = big[T:2 * T, T:2 * T].astype(np.float32) / 255
    m = pat.max(2)
    base = np.array([214, 204, 212], np.float32)   # BGR 연한 회보라
    noise = blur_noise(T, T, 3, rng)
    paper = base[None, None] * (1 + 0.025 * (noise / np.abs(noise).max())[..., None])
    img = paper * (1 - m[..., None] * 0.9) + np.array(white, np.float32)[None, None] * m[..., None] * 0.9
    return np.clip(img, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    cv2.imwrite(str(ROOT / "assets" / "hanji_dak.jpg"), hanji_dak(), [cv2.IMWRITE_JPEG_QUALITY, 88])
    cv2.imwrite(str(ROOT / "assets" / "dangcho_tile.jpg"), dangcho_tile(), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("wrote assets/hanji_dak.jpg, assets/dangcho_tile.jpg")
