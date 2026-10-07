"""뱅크 4(섞음, 회색 바탕)용 영상 바꾸기. 모두 검은 바탕 + 밝은 무늬로 만들어 lighten 으로 겹친다.

    python3 tools/bank4_convert.py sumuk|dancheong [이름 ...]

- 수묵: 먹을 흰 먹으로 뒤집는다. 밝기만 뒤집고 담채의 빛깔(색상·채도)은 그대로 둔다.
- 단청: 흰 바탕만 검게 빼고 단청 빛깔은 그대로 둔다.
- 자개: 원래 검은 바탕이라 그대로 쓴다.
결과: clips/mix/<sumuk|dancheong>/<이름>.mp4
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1920, 1080, 30


def ink_white(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    lum = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    hsv[..., 2] = 255 - lum
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def dancheong_black(f):
    a = np.clip(((255 - f.astype(np.float32)).max(2) - 10) / 40.0, 0, 1)    # 종이(≈250)는 0
    return (f * a[..., None]).astype(np.uint8)


def convert(kind, src):
    fn = ink_white if kind == "sumuk" else dancheong_black
    out = ROOT / "clips" / "mix" / kind / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                            "-crf", "18", "-preset", "slow", "-g", "30", "-movflags", "+faststart", str(out)],
                           stdin=subprocess.PIPE)
    n = W * H * 3
    while True:
        buf = dec.stdout.read(n)
        if len(buf) < n:
            break
        enc.stdin.write(fn(np.frombuffer(buf, np.uint8).reshape(H, W, 3)).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("wrote", out.relative_to(ROOT), flush=True)


if __name__ == "__main__":
    kind, names = sys.argv[1], sys.argv[2:]
    srcs = [ROOT / "clips" / kind / f"{n}.mp4" for n in names] if names else sorted((ROOT / "clips" / kind).glob("*.mp4"))
    for s in srcs:
        convert(kind, s)
