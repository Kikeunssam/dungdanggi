# 둥당기 (Dungdanggi)

키 하나에 소리 하나와 수묵 영상 하나를 짝지은 MPC 방식 웹앱. 처음에는 빈 한지 화면만 보이고,
키를 누르면 그 키의 소리와 영상이 함께 나온다. 여러 키를 동시에 누르면 동시에 겹쳐 나오고,
같은 키를 다시 누르면 처음부터 새로 재생된다 (앞의 것도 끝까지 이어서 울리고 보인다).

## 실행 (로컬)

폴더를 받은 뒤 `index.html`을 Chrome으로 열고(더블클릭) 키를 누르면 된다. 서버는 필요 없다.
전체 화면은 F11 (macOS는 ⌃⌘F).

로컬 서버로 열어도 된다: 폴더에서 `python3 -m http.server 8000` 실행 후 http://localhost:8000

## 키 배치

가운데 줄 = 장구 강, 그 위 키 = 같은 장단 중, 아랫줄 = 추임새. a s d f는 꽹과리·징.

| 키 | 소리 | 영상 |
|---|---|---|
| a | 꽹과리 지 (강) | v2/ink09b_splat |
| s | 꽹과리 게르르르 (강) | v2/ink07_slashes |
| d | 징 (강) | v2/ink20_gray_enso |
| f | 징 (약) | v2/ink08_enso_wash |
| g | 장구 덩 (강) | v2/ink13_slash |
| t | 장구 덩 (중) | v2/ink15_gray_arc |
| h | 장구 쿵 (강) | v2/ink01_bloom |
| y | 장구 쿵 (중) | v2/ink06_wash |
| j | 장구 덕 (강) | v2/ink09c_splat_tendril |
| u | 장구 덕 (중) | v2/ink05_splash |
| k | 장구 기덕 (강) | v2/ink12_arch |
| i | 장구 기덕 (중) | v2/ink09a_stains |
| l | 장구 더 (강) | v2/ink03_stroke |
| o | 장구 더 (중) | v2/ink09d_wash_drip |
| p | 장구 더러러러 (강) | v2/ink02_scatter |
| z | 추임새 얼쑤 | v2/ink10_dry_loop |
| x | 추임새 얼씨구 | v2/ink11_zigzag |
| c | 추임새 좋다 | v2/ink14_swirl |

모든 키는 누를 때마다 영상이 좌우·상하로 무작위 반전된다 (`pads.js`의 `flip: true`).

한글 입력 상태에서도 키 자리 기준으로 동작한다.

## 소리·영상 바꾸기

`pads.js`의 한 줄이 패드 하나다. `sounds/`나 `clips/`에 파일을 넣고 경로만 바꾸면 된다.

- 영상: 1920x1080, 한지 배경 위 먹, 마지막 프레임이 빈 종이인 클립 (`clips/` ink01~06, `clips/v2/` ink01~20 모두 같은 형식).
  화면에서는 한지 배경(`assets/hanji.jpg`) 위에 '어둡게(darken)'로 겹쳐서 먹만 보이게 한다.
- 소리를 바꾸거나 추가했으면 `python3 make_sounds_js.py`를 한 번 실행한다. 파일로 바로 열 때는
  브라우저가 음원 파일을 직접 못 읽어서, 음원을 `sounds.js`에 담아 두고 쓰기 때문이다.
- 소리: wav/mp3 등 브라우저가 읽는 형식. 앞쪽 무음은 잘라 두어야 누르는 순간 바로 소리가 난다
  (지금 음원은 앞의 약 0.2초 무음을 잘라 두었다).
