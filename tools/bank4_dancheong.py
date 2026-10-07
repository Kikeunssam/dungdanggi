"""뱅크 4(섞음, 회색 바탕)용 단청 영상. 압축된 영상을 거르지 않고 그림 단계에서 바로 만든다.

    python3 tools/bank4_dancheong.py [dc01 ...]

단청 그림은 흰 종이(255) 위에 그려진다. 각 화소가 '어떤 단청 색이 얼마만큼(a) 종이 위에 칠해졌나'를
단청 색표에서 거꾸로 풀어(un-mix) 종이만 정확히 빼고, 가장자리 계단·얼룩 없이 검은 바탕 위로 옮긴다.
회색 위에서 lighten 으로 겹칠 때 짙은 색(먹·감청·다자)이 사라지지 않도록 밝기를 조금 들어 올린다.
결과: clips/mix/dancheong/<이름>.mp4 (4초, 첫·끝 프레임 검정)
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dancheong as d            # noqa: E402
import dancheong_more as dm      # noqa: E402

W, H, FPS, N = d.W, d.H, d.FPS, d.N
CLIPS = {**d.CLIPS, **dm.CLIPS}
PALETTE = np.array(sorted({v for m in (d, dm) for k, v in vars(m).items()
                           if k.isupper() and isinstance(v, tuple) and len(v) == 3}), np.float32)
DP = 255 - PALETTE                                   # 종이에서 각 색까지의 거리 벡터
DPN = np.linalg.norm(DP, axis=1)
LIFT_FLOOR, LIFT_K = 70.0, 0.73                       # 밝기 V' = 70 + 0.73 V


def unmix(frame):
    """흰 종이 위 그림 → (검은 바탕 위 색 × 덮인 정도)."""
    dlt = 255 - frame.astype(np.float32)               # H,W,3
    n = np.linalg.norm(dlt, axis=2)
    cos = np.einsum("hwc,kc->hwk", dlt, DP) / (n[..., None] * DPN[None, None] + 1e-6)
    k = cos.argmax(2)
    a = np.clip(n / DPN[k], 0, 1)
    a[n < 3] = 0
    col = 255 - dlt / np.maximum(a, 1e-3)[..., None]   # 종이를 뺀 실제 색
    col = np.clip(col, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(col, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 2] = LIFT_FLOOR + LIFT_K * hsv[..., 2]
    col = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    return np.clip(col * a[..., None] + 0.5, 0, 255).astype(np.uint8)


def render(name):
    fn = CLIPS[name]
    out = d.ROOT / "clips" / "mix" / "dancheong" / f"{name}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow",
           "-g", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        img = unmix(fn(i / FPS)) if 0 < i < N - 1 else np.zeros((H, W, 3), np.uint8)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out.relative_to(d.ROOT), flush=True)


if __name__ == "__main__":
    for name in CLIPS:
        if not sys.argv[1:] or any(name.startswith(a) for a in sys.argv[1:]):
            render(name)
