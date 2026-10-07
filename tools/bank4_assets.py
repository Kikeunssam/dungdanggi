"""뱅크 4(섞음) 바탕 그림: 새 빛깔의 누런 한지와, 자개 영상을 얹을 옻칠 판 가장자리 마스크.

    python3 tools/bank4_assets.py [색이름]

한지 결은 hanji_aged.jpg 의 결(밝기 무늬)을 그대로 쓰고 바탕 빛깔만 바꾼다.
마스크(480x270, 화면에서 늘려 씀)는 가운데가 불투명하고 가장자리가 먹물 번지듯 흐려지는 옻칠 판 모양(흰색=보임).
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H = 1920, 1080

TONES = {                     # RGB
    "chija":   (226, 196, 118),   # 치자빛: 노란 금빛
    "songhwa": (233, 219, 152),   # 송홧빛: 연한 송화가루 노랑
    "salgu":   (231, 197, 152),   # 살굿빛: 살구 도는 누런빛
}


def hanji(tone):
    aged = cv2.imread(str(ROOT / "assets" / "hanji_aged.jpg")).astype(np.float32)
    lum = aged.mean(2)
    tex = lum / lum.mean()                         # 결만 남긴다 (평균 1)
    tex = 1 + (tex - 1) * 0.8
    rgb = np.array(TONES[tone], np.float32)
    img = tex[..., None] * rgb[::-1][None, None]
    return np.clip(img, 0, 255).astype(np.uint8)


def fbm(h, w, rng, cells=(6, 12, 24, 48), pers=0.55):
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    for c in cells:
        g = rng.standard_normal((c, int(c * w / h) + 1)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        amp *= pers
    return out / np.abs(out).max()


def panel_mask(seed=7):
    """가장자리에서 안쪽으로 약 6~12% 들어온 둥근 네모, 가장자리는 먹 번짐처럼 들쭉날쭉하고 흐리다."""
    w, h = W // 2, H // 2
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # 둥근 네모까지의 거리 (안쪽 +)
    mx, my = w * 0.075, h * 0.10
    r = h * 0.12
    dx = np.maximum(np.maximum(mx + r - xx, xx - (w - mx - r)), 0)
    dy = np.maximum(np.maximum(my + r - yy, yy - (h - my - r)), 0)
    d = r - np.sqrt(dx ** 2 + dy ** 2)
    d += fbm(h, w, rng) * h * 0.045               # 들쭉날쭉한 가장자리
    a = np.clip(d / (h * 0.06) + 0.5, 0, 1)        # 부드러운 번짐 폭
    a = a ** 1.4
    a = cv2.GaussianBlur(a, (0, 0), 2.0)
    return cv2.resize((a * 255).astype(np.uint8), (W // 4, H // 4), interpolation=cv2.INTER_AREA)   # 부드러워서 작게 둬도 된다


if __name__ == "__main__":
    tone = sys.argv[1] if len(sys.argv) > 1 else "chija"
    cv2.imwrite(str(ROOT / "assets" / "hanji_mix.jpg"), hanji(tone), [cv2.IMWRITE_JPEG_QUALITY, 90])
    cv2.imwrite(str(ROOT / "assets" / "panel_mask.png"), panel_mask(), [cv2.IMWRITE_PNG_COMPRESSION, 9])
    print("wrote assets/hanji_mix.jpg (", tone, ") and assets/panel_mask.png")
