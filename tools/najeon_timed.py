"""뱅크 3(자개) 영상을 각 키 음원 길이에 맞춰 다시 뽑는다.

    python3 tools/najeon_timed.py [키 ...]

영상을 느리게 돌리거나 멈춰 두지 않고, 4초짜리 무늬의 시간표를 음원 길이에 맞게 다시 짜서
매 프레임을 새로 그린다(30fps 그대로라 떨림이 없다). 무늬가 피어나는 앞부분은 거의 원래 빠르기로,
머무름과 사라짐을 소리 길이에 맞게 줄이거나 늘려서 소리가 끝날 때 화면도 비게 한다.
"""
import subprocess
import sys

import numpy as np

import najeon
import najeon_more
from najeon import ROOT, W, H, FPS

# 키: (무늬, 음원)
PADS = {
    "q": ("nj05", "jeongak_gayageum_stacc"), "w": ("nj06", "yanggeum_staccato"),
    "e": ("nj07", "yanggeum_trill"),         "r": ("nj08", "gayageum25_gliss"),
    "t": ("nj09", "geomungo_chusung"),       "y": ("nj10", "geomungo_low"),
    "u": ("nj11", "geomungo_junsung"),       "i": ("nj12", "sanjo_gayageum_note"),
    "o": ("nj13", "ajaeng_run"),             "p": ("nj14", "gayageum25_tremolo"),
    "a": ("nj01", "sanjo_gayageum_twigim"),  "s": ("nj02", "jeongak_gayageum_flick"),
    "d": ("nj03", "geomungo_toesung"),       "f": ("nj04", "sanjo_gayageum_gullim"),
    "g": ("nj15", "gayageum25_nonghyun"),    "h": ("nj16", "ajaeng_long"),
    "j": ("nj17", "yanggeum_accent"),        "k": ("nj18", "ajaeng_high"),
    "l": ("nj19", "gayageum25_high"),        "z": ("nj20", "sanjo_gayageum_nong"),
    "x": ("nj21", "jeongak_gayageum_note"),  "c": ("nj22", "sanjo_gayageum_break"),
    "v": ("nj23", "yanggeum_accent2"),       "b": ("nj24", "jeongak_gayageum_jun"),
    "n": ("nj25", "geomungo_high"),          "m": ("nj26", "gayageum25_low"),
}

ENTER, END = 1.0, 3.9     # 원래 시간표: 0~1초 피어남, 3.8초까지 다 사라짐


def duration(sound):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(ROOT / "sounds" / f"{sound}.wav")], capture_output=True, text=True, check=True).stdout
    return float(out)


def warp(t, dur):
    """실제 시각 t(0~dur) → 원래 4초 시간표의 시각."""
    a = min(ENTER, 0.4 * dur)
    if t < a:
        return t * ENTER / a
    return ENTER + (t - a) * (END - ENTER) / (dur - a)


def build(clip):
    mod = najeon if clip in najeon.CLIPS else najeon_more
    return mod.build(clip)


def render(key):
    clip, sound = PADS[key]
    dur = duration(sound)
    name, frame = build(clip)
    out = ROOT / "clips" / "najeon" / f"{name}.mp4"
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
           "-g", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        img = frame(warp(i / FPS, dur)) if 0 < i < n - 1 else np.zeros((H, W, 3), np.uint8)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    print(f"{key} {out.relative_to(ROOT)} {n / FPS:.2f}s  ({sound} {dur:.2f}s)", flush=True)


if __name__ == "__main__":
    for k in sys.argv[1:] or list(PADS):
        render(k)
