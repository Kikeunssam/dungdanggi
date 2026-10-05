"""pads.js에 적힌 음원을 sounds.js 하나에 담는다.

index.html을 더블클릭해서(서버 없이) 열 때 브라우저는 음원 파일을 직접 읽지 못하므로,
음원을 바꾸거나 추가했으면 이 스크립트를 한 번 실행한다:  python3 make_sounds_js.py
"""
import base64
import json
import pathlib
import re

root = pathlib.Path(__file__).parent
paths = re.findall(r'^\s*\{[^\n]*?sound:\s*"([^"]+)"', (root / "pads.js").read_text(encoding="utf-8"), re.M)
data = {p: base64.b64encode((root / p).read_bytes()).decode("ascii") for p in paths}
(root / "sounds.js").write_text("window.SOUND_DATA = " + json.dumps(data, indent=0) + ";\n", encoding="utf-8")
print("sounds.js:", ", ".join(paths))
