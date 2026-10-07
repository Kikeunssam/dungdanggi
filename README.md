# 둥당기 (Dungdanggi)

키 하나에 소리 하나와 수묵 영상 하나를 짝지은 MPC 방식 웹앱. 처음에는 빈 한지 화면만 보이고,
키를 누르면 그 키의 소리와 영상이 함께 나온다. 여러 키를 동시에 누르면 동시에 겹쳐 나오고,
같은 키를 다시 누르면 처음부터 새로 재생된다 (앞의 것도 끝까지 이어서 울리고 보인다).

## 실행 (로컬)

폴더를 받은 뒤 `index.html`을 Chrome으로 열고(더블클릭) 키를 누르면 된다. 서버는 필요 없다.
전체 화면은 F11 (macOS는 ⌃⌘F).

로컬 서버로 열어도 된다: 폴더에서 `python3 -m http.server 8000` 실행 후 http://localhost:8000

## 녹화 (PC, Chrome)

**Shift+R**로 녹화를 시작하고, 다시 **Shift+R**을 누르면 멈추면서 바로 MP4 파일로 내려받는다.
최대 23초이고, 23초가 되면 저절로 멈추고 내려받는다. 녹화하는 동안 왼쪽 위에 빨간 점과 초가 보인다
(이 표시는 녹화 파일에는 들어가지 않는다). 파일 이름은 `dungdanggi_<뱅크 이름>_<날짜-시각>.mp4`.

- 화면(배경 + 재생 중인 영상, 겹치기 방식·반전 그대로)과 앱 소리가 함께 녹화된다. 1920px 폭, 초당 약 30장.
- **웹 서버로 열었을 때만 녹화된다** (`python3 -m http.server 8000` 후 http://localhost:8000).
  `index.html`을 파일로 바로 열면 브라우저 보안 때문에 영상을 녹화용 캔버스로 옮길 수 없어서, 안내 문구만 나온다.
- Shift를 누르고 있는 동안은 글자 키가 연주되지 않는다.
- Chrome 설정의 '다운로드 전에 각 파일의 저장 위치 확인'이 켜져 있으면 저장할 때마다 저장 창이 뜬다
  (페이지에서 끌 수 없다. 끄려면 Chrome 설정 → 다운로드).

## 휴대폰·태블릿 (터치)

맥과 같은 Wi-Fi에서, 앱 폴더에서 아래 명령을 실행한 뒤 휴대폰 브라우저로 `http://<맥 IP>:8000/` 을 연다
(맥 IP는 `ipconfig getifaddr en0`).

```
python3 -m http.server 8000 --bind 0.0.0.0
```

화면 전체가 보이지 않는 27칸으로 나뉜다 (가로 화면 9x3, 세로 화면 3x9). 칸 순서는 자판 순서
q w e r t y u i o p / a s d f g h j k l / z x c v b n m 이고, 마지막 27번째 칸(오른쪽 아래)은 다음 뱅크로 넘어가기.
여러 손가락으로 동시에 눌러도 각각 울린다. 휴대폰은 동시에 보이는 영상 수를 6개로 줄여 둔다.

## 시작 화면

열면 바랜 한지 위에 제목 **둥당기**와 '우리 소리로 그리는 한 폭의 그림'이 보이고, 아래에 '아무 키나 누르거나 화면을 터치하세요'가 천천히 깜빡인다.
처음 누른 키(또는 터치)는 소리를 켜는 데만 쓰이고(소리·영상은 나오지 않는다), 시작 화면이 0.7초 동안 사라진 뒤 뱅크 1 빈 화면이 된다.
글꼴은 나눔손글씨 붓·나눔명조(SIL OFL)에서 쓰는 글자만 담아 `assets/fonts/fonts.css`에 넣어 두었다.

## 뱅크 (악기 묶음)

뱅크가 넷이다. PC는 **스페이스바**, 터치 화면은 **오른쪽 아래 칸**(27번째 칸)을 누를 때마다 1 수묵 → 2 단청 → 3 자개 → 4 섞음 → 1 수묵 순서로 넘어간다.
바꾸면 배경이 0.3초 동안 겹쳐 바뀌고, 오른쪽 아래에 뱅크 이름이 잠깐 보였다 사라진다.
이전 뱅크의 영상은 바로 감추고, 울리고 있던 소리는 끝까지 둔다.

| 뱅크 | 배경 | 영상 겹치기 | 패드 |
|---|---|---|---|
| 1 수묵 | 누렇게 바랜 한지 (`assets/hanji_aged.jpg`) | multiply (종이에 먹이 스미듯 겹침) | 아래 26개 키, 소리+영상 |
| 2 단청 | 한지 (`assets/hanji.jpg`) | darken (흰 바탕은 사라지고 색만 남음) | 26개 키 모두 관악기·대금 소리 + 단청 문양 영상 (`clips/dancheong/` dc01~dc26) — 아래 표 |
| 3 자개 | 검은 옻칠 (`assets/lacquer.jpg`) | lighten (검은 바탕은 사라지고 자개 빛만 남음) | 26개 키 모두 현악기(가야금·거문고·아쟁·양금) 소리 + 자개 문양 영상 (`clips/najeon/` nj01~nj26, 영상 길이 = 소리 길이) — 아래 표 |
| 4 섞음 | 회색 (`assets/gray_mix.jpg`) | lighten (검은 바탕은 사라짐) | 들어올 때마다 뱅크 1·2·3 패드를 9·9·8개(8개 뱅크는 무작위) 서로 다르게 골라 26개 키에 무작위로 섞는다. 소리는 원래 패드 그대로, 영상은 회색 바탕용(수묵 `clips/mix/sumuk/` 흰 먹, 단청 `clips/mix/dancheong/` 검은 바탕, 자개는 원래 영상) |

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

관악기 12개(단소·소금·피리·나발·나각·산조대금)와 대금 니나 한 음 14개. 대금 니나는 아랫줄(z x n m) → 가운데 줄(d f h j k) → 윗줄(q e u i o)로 갈수록 음이 높아진다.

| 키 | 소리 | 영상 |
|---|---|---|
| q | 대금 니나 10 (`daegeum_nina_10`) | dc05_hex_lattice |
| w | 소금 노니로 (`sogeum_noniro`) | dc06_cloud_scroll |
| e | 대금 니나 11 (`daegeum_nina_11`) | dc07_aja_lattice |
| r | 나각 (`nagak`) | dc08_jewel_spiral |
| t | 소금 깊은농음 (`sogeum_gipeun_nongeum`) | dc09_rainbow_ripple |
| y | 산조대금 (`sanjo_daegeum`) | dc10_twin_lotus |
| u | 대금 니나 12 (`daegeum_nina_12`) | dc11_star_rosette |
| i | 대금 니나 13 (`daegeum_nina_13`) | dc12_soran_grid |
| o | 대금 니나 14 (`daegeum_nina_14`) | dc13_pillar_bands |
| p | 소금 노르니르 (`sogeum_noreunireu`) | dc14_maehwa_scatter |
| a | 단소 8 (`danso_8`) | dc01_lotus_bloom |
| s | 단소 6 (`danso_6`) | dc02_wave_sweep |
| d | 대금 니나 5 (`daegeum_nina_05`) | dc03_tile_medallions |
| f | 대금 니나 6 (`daegeum_nina_06`) | dc04_meoricho_band |
| g | 피리 (`piri_14`) | dc15_wave_rise |
| h | 대금 니나 7 (`daegeum_nina_07`) | dc16_arch_garland |
| j | 대금 니나 8 (`daegeum_nina_08`) | dc17_clock_petals |
| k | 대금 니나 9 (`daegeum_nina_09`) | dc18_octagon_ripple |
| l | 단소 9 (`danso_9`) | dc19_lotus_ring |
| z | 대금 니나 1 (`daegeum_nina_01`) | dc20_diamond_chain |
| x | 대금 니나 2 (`daegeum_nina_02`) | dc21_fret_frame |
| c | 소금 나니루 (`sogeum_naniru`) | dc22_falling_petals |
| v | 나발 (`nabal`) | dc23_sun_rays |
| b | 단소 7 (`danso_7`) | dc24_cloud_drift |
| n | 대금 니나 3 (`daegeum_nina_03`) | dc25_hexa_cross |
| m | 대금 니나 4 (`daegeum_nina_04`) | dc26_corner_fans |

## 키 배치 (뱅크 3 자개)

현악기 소리 26개. 영상은 소리 길이(1.6~4초)에 맞춰 만들어 두어서, 소리가 끝날 때 무늬도 함께 사라진다.

| 키 | 소리 | 영상 |
|---|---|---|
| a | 산조가야금 튕김 (`sanjo_gayageum_twigim`) | nj01_pine_fans (솔잎 부채) |
| s | 정악가야금 튕기기 (`jeongak_gayageum_flick`) | nj02_butterfly_flower (나비와 꽃) |
| d | 거문고 퇴성 (`geomungo_toesung`) | nj03_longevity_bats (수복 원문과 박쥐) |
| f | 산조가야금 굴림 (`sanjo_gayageum_gullim`) | nj04_flower_vine (넝쿨 띠) |
| q | 정악가야금 짧게 뜯기 (`jeongak_gayageum_stacc`) | nj05_stripes (줄무늬) |
| w | 양금 짧게 치기 (`yanggeum_staccato`) | nj06_diamond_lattice (마름모 격자) |
| e | 양금 트릴 (`yanggeum_trill`) | nj07_pearl_dots (자개 점) |
| r | 25현 가야금 글리산도 (`gayageum25_gliss`) | nj08_hatch_sweep (빗살) |
| t | 거문고 추성 (`geomungo_chusung`) | nj09_spinning_rings (도는 고리) |
| y | 거문고 낮은 음 (`geomungo_low`) | nj10_tortoise_hex (거북등) |
| u | 거문고 전성 (`geomungo_junsung`) | nj11_thunder_fret (뇌문 띠) |
| i | 산조가야금 한 음 (`sanjo_gayageum_note`) | nj12_chilbo_rings (칠보 고리) |
| o | 아쟁 빠른 가락 (`ajaeng_run`) | nj13_bamboo (대나무) |
| p | 25현 가야금 트레몰로 (`gayageum25_tremolo`) | nj14_sparkles (반짝이 별) |
| g | 25현 가야금 농현 (`gayageum25_nonghyun`) | nj15_wave_scales (물결 비늘) |
| h | 아쟁 긴 음 (`ajaeng_long`) | nj16_cranes (학 떼) |
| j | 양금 강세 (`yanggeum_accent`) | nj17_chrysanthemums (국화) |
| k | 아쟁 높은 음 (`ajaeng_high`) | nj18_plum_branch (매화 가지) |
| l | 25현 가야금 높은 음 (`gayageum25_high`) | nj19_peony (모란) |
| z | 산조가야금 농현 (`sanjo_gayageum_nong`) | nj20_cloud_scrolls (구름) |
| x | 정악가야금 한 음 (`jeongak_gayageum_note`) | nj21_lotus_pond (연못 연꽃) |
| c | 산조가야금 꺾는 소리 (`sanjo_gayageum_break`) | nj22_circling_fish (맴도는 물고기) |
| v | 양금 강세 2 (`yanggeum_accent2`) | nj23_kaleidoscope (만화경) |
| b | 정악가야금 전성 (`jeongak_gayageum_jun`) | nj24_grape_vine (포도 넝쿨) |
| n | 거문고 높은 음 (`geomungo_high`) | nj25_pine_branch (소나무 가지) |
| m | 25현 가야금 낮은 음 (`gayageum25_low`) | nj26_flower_frame (꽃 테두리) |

## 소리·영상 바꾸기

`pads.js`의 한 줄이 패드 하나다 (뱅크마다 `pads` 목록이 따로 있다). `sounds/`나 `clips/`에 파일을 넣고 경로만 바꾸면 된다.

- 영상: 1920x1080, 한지 배경 위 먹, 마지막 프레임이 빈 종이인 클립 (`clips/` ink01~06, `clips/v2/` ink01~20, `clips/v3/` ink21~23, `clips/sumuk/` 모두 같은 형식). 뱅크 1은 지금 `clips/sumuk/`(소리 파형으로 만든 영상)을 쓴다.
  화면에서는 뱅크의 배경 위에 뱅크의 겹치기 방식(수묵: 곱하기 multiply, 단청: 어둡게 darken)으로 겹쳐서 그림만 보이게 한다.
- 소리를 바꾸거나 추가했으면 `python3 make_sounds_js.py`를 한 번 실행한다. 파일로 바로 열 때는
  브라우저가 음원 파일을 직접 못 읽어서, 음원을 `sounds.js`에 담아 두고 쓰기 때문이다.
- 소리: wav/mp3 등 브라우저가 읽는 형식. 앞쪽 무음은 잘라 두어야 누르는 순간 바로 소리가 난다
  (지금 음원은 앞의 약 0.2초 무음을 잘라 두었다).
