# 둥당기 (Dungdanggi)

키 하나에 소리 하나와 수묵 영상 하나를 짝지은 MPC 방식 웹앱. 처음에는 빈 한지 화면만 보이고,
키를 누르면 그 키의 소리와 영상이 함께 나온다. 여러 키를 동시에 누르면 동시에 겹쳐 나오고,
같은 키를 다시 누르면 처음부터 새로 재생된다 (앞의 것도 끝까지 이어서 울리고 보인다).

## 실행 (로컬)

폴더를 받은 뒤 `index.html`을 Chrome으로 열고(더블클릭) 키를 누르면 된다. 서버는 필요 없다.
전체 화면은 F11 (macOS는 ⌃⌘F).

로컬 서버로 열어도 된다: 폴더에서 `python3 -m http.server 8000` 실행 후 http://localhost:8000

## 휴대폰·태블릿 (터치)

맥과 같은 Wi-Fi에서, 앱 폴더에서 아래 명령을 실행한 뒤 휴대폰 브라우저로 `http://<맥 IP>:8000/` 을 연다
(맥 IP는 `ipconfig getifaddr en0`).

```
python3 -m http.server 8000 --bind 0.0.0.0
```

화면 전체가 보이지 않는 27칸으로 나뉜다 (가로 화면 9x3, 세로 화면 3x9). 칸 순서는 자판 순서
q w e r t y u i o p / a s d f g h j k l / z x c v b n m 이고, 마지막 27번째 칸(오른쪽 아래)은 뱅크 바꾸기.
여러 손가락으로 동시에 눌러도 각각 울린다. 휴대폰은 동시에 보이는 영상 수를 6개로 줄여 둔다.

## 뱅크 (악기 묶음)

뱅크가 둘이다. PC는 **스페이스바**, 터치 화면은 **오른쪽 아래 칸**(27번째 칸)으로 바꾼다.
바꾸면 배경이 0.3초 동안 겹쳐 바뀌고, 오른쪽 아래에 뱅크 이름이 잠깐 보였다 사라진다.
이전 뱅크의 영상은 바로 감추고, 울리고 있던 소리는 끝까지 둔다.

| 뱅크 | 배경 | 영상 겹치기 | 패드 |
|---|---|---|---|
| 1 수묵 | 한지 (`assets/hanji.jpg`) | darken (먹만 남음) | 아래 26개 키, 소리+영상 |
| 2 단청 | 누렇게 바랜 한지 (`assets/hanji_aged.jpg`) | darken (흰 바탕은 사라지고 색만 남음) | 26개 키 모두 단청 문양 영상 (`clips/dancheong/` dc01~dc26, 아직 소리 없음) — 아래 표 |

`pads.js`의 `window.BANKS`에서 뱅크별로 패드를 적고,
`sound`를 빼면 영상만 나오는 패드가 된다.

## 키 배치 (뱅크 1 수묵)

가운데 줄 = 장구 강, 그 위 키 = 같은 장단 중, 아랫줄 = 추임새·북. a s d f q w는 꽹과리·징, e r(중)·v b(강)는 북, z x c n m은 추임새.

| 키 | 소리 | 영상 |
|---|---|---|
| a | 꽹과리 지 (강) | sumuk/ji_a |
| s | 꽹과리 게르르르 (강) | sumuk/roll_s |
| d | 징 (강) | sumuk/jing_d |
| f | 징 (약) | sumuk/jing_f |
| g | 장구 덩 (강) | sumuk/deong_g |
| t | 장구 덩 (중) | sumuk/deong_t |
| h | 장구 쿵 (강) | sumuk/kung_h |
| y | 장구 쿵 (중) | sumuk/kung_y |
| j | 장구 덕 (강) | sumuk/deok_j |
| u | 장구 덕 (중) | sumuk/deok_u |
| k | 장구 기덕 (강) | sumuk/gideok_k |
| i | 장구 기덕 (중) | sumuk/gideok_i |
| l | 장구 더 (강) | sumuk/deo_l |
| o | 장구 더 (중) | sumuk/deo_o |
| p | 장구 더러러러 (강) | sumuk/deororeo_p |
| z | 추임새 얼쑤 | sumuk/eolssu_z |
| x | 추임새 얼씨구 | sumuk/eolssigu_x |
| c | 추임새 좋다 | sumuk/jota_c |
| q | 꽹과리 객 (강) | sumuk/gaek_q |
| w | 꽹과리 갯 (강) | sumuk/gaet_w |
| e | 북 노고 (중) | sumuk/nogo_e |
| r | 북 절고 (중) | sumuk/jeolgo_r |
| v | 북 노고 (강) | sumuk/nogo_v |
| b | 북 절고 (강) | sumuk/jeolgo_b |
| n | 추임새 쑤 | sumuk/ssu_n |
| m | 추임새 어이 | sumuk/eoi_m |

모든 키는 누를 때마다 영상이 좌우·상하로 무작위 반전된다 (`pads.js`의 `flip: true`).

한글 입력 상태에서도 키 자리 기준으로 동작한다.

## 키 배치 (뱅크 2 단청)

| 키 | 영상 |
|---|---|
| a | dc01_lotus_bloom (연꽃) |
| s | dc02_wave_sweep (물결) |
| d | dc03_tile_medallions (기와 문양) |
| f | dc04_meoricho_band (머리초 띠) |
| q | dc05_hex_lattice (육각 살창) |
| w | dc06_cloud_scroll (구름 무늬) |
| e | dc07_aja_lattice (아자 살창) |
| r | dc08_jewel_spiral (보주 소용돌이) |
| t | dc09_rainbow_ripple (오색 물결무늬) |
| y | dc10_twin_lotus (쌍 연꽃) |
| u | dc11_star_rosette (별꽃) |
| i | dc12_soran_grid (소란 격자) |
| o | dc13_pillar_bands (기둥 띠) |
| p | dc14_maehwa_scatter (매화 흩날림) |
| g | dc15_wave_rise (솟는 물결) |
| h | dc16_arch_garland (아치 꽃줄) |
| j | dc17_clock_petals (꽃잎 바퀴) |
| k | dc18_octagon_ripple (팔각 물결) |
| l | dc19_lotus_ring (연꽃 고리) |
| z | dc20_diamond_chain (마름모 사슬) |
| x | dc21_fret_frame (뇌문 틀) |
| c | dc22_falling_petals (떨어지는 꽃잎) |
| v | dc23_sun_rays (햇살) |
| b | dc24_cloud_drift (흐르는 구름) |
| n | dc25_hexa_cross (육각 십자) |
| m | dc26_corner_fans (모서리 부채) |

## 소리·영상 바꾸기

`pads.js`의 한 줄이 패드 하나다 (뱅크마다 `pads` 목록이 따로 있다). `sounds/`나 `clips/`에 파일을 넣고 경로만 바꾸면 된다.

- 영상: 1920x1080, 한지 배경 위 먹, 마지막 프레임이 빈 종이인 클립 (`clips/` ink01~06, `clips/v2/` ink01~20, `clips/v3/` ink21~23, `clips/sumuk/` 모두 같은 형식). 뱅크 1은 지금 `clips/sumuk/`(소리 파형으로 만든 영상)을 쓴다.
  화면에서는 한지 배경(`assets/hanji.jpg`) 위에 '어둡게(darken)'로 겹쳐서 먹만 보이게 한다.
- 소리를 바꾸거나 추가했으면 `python3 make_sounds_js.py`를 한 번 실행한다. 파일로 바로 열 때는
  브라우저가 음원 파일을 직접 못 읽어서, 음원을 `sounds.js`에 담아 두고 쓰기 때문이다.
- 소리: wav/mp3 등 브라우저가 읽는 형식. 앞쪽 무음은 잘라 두어야 누르는 순간 바로 소리가 난다
  (지금 음원은 앞의 약 0.2초 무음을 잘라 두었다).
