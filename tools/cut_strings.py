"""뱅크 3(자개) 현악기 음원: 긴 녹음에서 한 음(또는 한 가락)씩 잘라 sounds/ 에 넣는다.

    python3 tools/cut_strings.py <압축 푼 폴더>

시작점은 소리가 들어오는 자리, 끝은 그 음의 여음이 피크보다 40dB 내려간 자리(최소 MIN, 최대 MAX초).
최대 길이에서 잘리면 끝을 페이드아웃한다. 피크는 -1dBFS 로 맞춘다. 44.1kHz 스테레오 16bit.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR, HOP = 44100, 441
MIN, MAX = 1.6, 4.0

# (출력 이름, 원본 파일, 시작 초, 최대 길이)
CUTS = [
    ("gayageum25_gliss",      "25string_gayageum_glissando_60.wav",           39.3, 3.6),
    ("gayageum25_nonghyun",   "25string_gayageum_nonghyun_loud_42.wav",        0.05, MAX),
    ("gayageum25_low",        "25string_gayageum_sus_loud_04.wav",            39.85, MAX),
    ("gayageum25_high",       "25string_gayageum_sus_loud_04.wav",           179.65, MAX),
    ("gayageum25_tremolo",    "25string_gayageum_tremolo_59.wav",            313.2, 3.0),
    ("sanjo_gayageum_break",  "sanjo_gayageum_break_nonghyon_loud_22.wav",    23.85, MAX),
    ("sanjo_gayageum_twigim", "sanjo_gayageum_eaontuigim_loud_40.wav",        51.35, MAX),
    ("sanjo_gayageum_gullim", "sanjo_gayageum_gullim_loud_24.wav",            40.15, MAX),
    ("sanjo_gayageum_nong",   "sanjo_gayageum_shallow_nonghyun_loud_08.wav",  77.15, MAX),
    ("sanjo_gayageum_note",   "sanjo_gayageum_sus_loud_03.wav",               41.85, MAX),
    ("geomungo_low",          "gumungo_D_scale_loud_81.wav",                  20.05, MAX),
    ("geomungo_high",         "gumungo_U_scale_loud_02.wav",                  35.15, MAX),
    ("geomungo_chusung",      "gumungo_D_chusung_loud_95.wav",                20.05, MAX),
    ("geomungo_junsung",      "gumungo_D_junsung_loud_98.wav",                 4.95, MAX),
    ("geomungo_toesung",      "gumungo_U_teasung_loud_28.wav",                 0.05, MAX),
    ("ajaeng_long",           "SanjoAjaeng_1.wav",                             0.15, 3.6),
    ("ajaeng_high",           "SanjoAjaeng_1.wav",                            35.25, 3.6),
    ("ajaeng_run",            "SanjoAjaeng_4.mp3",                            27.7,  3.8),
    ("yanggeum_trill",        "양금_트릴_강.wav",                              6.85, 3.4),
    ("yanggeum_staccato",     "양금_스타카토_강.wav",                          5.15, MAX),
    ("yanggeum_accent",       "양금_강세별음계_강.wav",                        41.55, MAX),
    ("yanggeum_accent2",      "양금_강세별음계_강.wav",                        80.95, MAX),
    ("jeongak_gayageum_flick", "jungak_gayageum_pluck_flick_loud_75_77.wav",  20.55, MAX),
    ("jeongak_gayageum_stacc", "jungak_gayageum_staccato_loud_16.wav",        41.95, MAX),
    ("jeongak_gayageum_jun",  "jungak_gayageum_junsung_loud_67.wav",          47.15, MAX),
    ("jeongak_gayageum_note", "jungak_gayageum_sus_loud_07.wav",              31.35, MAX),
]


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def env_db(x):
    m = x.mean(1)
    n = len(m) // HOP
    return 20 * np.log10(np.sqrt((m[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9)


def attack(x, start):
    """start 근처(-0.4~+0.6초)의 가장 센 자리에서 거슬러 올라가, 소리가 들어오기 직전(-25dB)을 찾는다."""
    a = max(0, int((start - 0.4) * SR))
    e = env_db(x[a:a + SR])
    p = int(e.argmax())
    i = p
    while i > 0 and e[i] > e[p] - 25:
        i -= 1
    return max(0.0, a / SR + i * HOP / SR - 0.01)


def cut(x, start, maxlen):
    if maxlen == MAX:          # 한 음: 시작점을 어택 직전으로 맞춘다 (가락·트레몰로는 적힌 자리 그대로)
        start = attack(x, start)
    s = int(start * SR)
    seg = x[s:s + int(maxlen * SR) + SR]
    e = env_db(seg)
    pk = e[:int(0.6 * SR / HOP)].max()
    # 여음이 피크 -40dB 아래로 0.15초 이상 머무는 첫 자리
    below = e < pk - 40
    end = len(e)
    for i in range(int(MIN * SR / HOP), len(e) - 15):
        if below[i:i + 15].all():
            end = i
            break
    n = min(end * HOP, int(maxlen * SR))
    n = max(n, int(MIN * SR))
    y = seg[:n].copy()
    fi = int(0.008 * SR)
    y[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(max(0.35, 0.3 * n / SR) * SR) if n >= int(maxlen * SR) - HOP else int(0.12 * SR)
    y[-fo:] *= (np.cos(np.linspace(0, np.pi, fo)) * 0.5 + 0.5)[:, None]
    return y * (10 ** (-1 / 20) / (np.abs(y).max() + 1e-9))


def save(y, path):
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", str(path)],
                   input=pcm, check=True)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    files = {p.name: p for p in src.rglob("*") if p.is_file()}
    cache = {}
    for name, fn, start, maxlen in CUTS:
        if fn not in cache:
            cache[fn] = load(files[fn])
        y = cut(cache[fn], start, maxlen)
        save(y, ROOT / "sounds" / f"{name}.wav")
        print(f"{name:26s} {len(y) / SR:.2f}s")
