// 뱅크(악기 묶음) 여러 개. PC는 스페이스바, 터치는 오른쪽 아래 칸으로 뱅크를 바꾼다.
// 뱅크마다 배경 그림과 영상 겹치는 방식(blend)을 정한다:
//   darken  = 밝은 종이 위 먹·색 (흰 바탕·종이색은 사라지고 그림만 남는다)
//   lighten = 어두운 배경 위 색 (검은 바탕은 사라지고 색만 남는다) — 검은 바탕 클립을 쓸 때
// 패드 한 줄 = 키 하나. sound는 빼도 된다 (영상만 나온다).
// flip: true 면 누를 때마다 영상을 좌우·상하로 무작위 반전한다 (직전과는 다른 방향으로).
// 영상은 1920x1080, 밝은 바탕(한지·흰색) 위 그림이고, 끝 프레임은 빈 바탕이어야 한다.
window.BANKS = [
  {
    name: "수묵",
    background: "assets/hanji.jpg",
    blend: "darken",
    pads: [
      { key: "a", name: "꽹과리 지 (강)",      sound: "sounds/kkwaenggwari_ji_strong.wav",   clip: "clips/v2/ink09b_splat.mp4", flip: true },
      { key: "s", name: "꽹과리 게르르르 (강)", sound: "sounds/kkwaenggwari_roll_strong.wav", clip: "clips/v2/ink07_slashes.mp4", flip: true },
      { key: "d", name: "징 (강)",             sound: "sounds/jing_strong.wav",              clip: "clips/v2/ink20_gray_enso.mp4", flip: true },
      { key: "f", name: "징 (약)",             sound: "sounds/jing_soft.wav",                clip: "clips/v2/ink08_enso_wash.mp4", flip: true },
      { key: "g", name: "장구 덩 (강)", sound: "sounds/janggu_deong_strong.wav", clip: "clips/v2/ink13_slash.mp4", flip: true },
      { key: "t", name: "장구 덩 (중)", sound: "sounds/janggu_deong_mid.wav", clip: "clips/v2/ink15_gray_arc.mp4", flip: true },
      { key: "h", name: "장구 쿵 (강)", sound: "sounds/janggu_kung_strong.wav", clip: "clips/v2/ink01_bloom.mp4", flip: true },
      { key: "y", name: "장구 쿵 (중)", sound: "sounds/janggu_kung_mid.wav", clip: "clips/v2/ink06_wash.mp4", flip: true },
      { key: "j", name: "장구 덕 (강)", sound: "sounds/janggu_deok_strong.wav", clip: "clips/v2/ink09c_splat_tendril.mp4", flip: true },
      { key: "u", name: "장구 덕 (중)", sound: "sounds/janggu_deok_mid.wav", clip: "clips/v2/ink05_splash.mp4", flip: true },
      { key: "k", name: "장구 기덕 (강)", sound: "sounds/janggu_gideok_strong.wav", clip: "clips/v2/ink12_arch.mp4", flip: true },
      { key: "i", name: "장구 기덕 (중)", sound: "sounds/janggu_gideok_mid.wav", clip: "clips/v2/ink09a_stains.mp4", flip: true },
      { key: "l", name: "장구 더 (강)", sound: "sounds/janggu_deo_strong.wav", clip: "clips/v2/ink03_stroke.mp4", flip: true },
      { key: "o", name: "장구 더 (중)", sound: "sounds/janggu_deo_mid.wav", clip: "clips/v2/ink09d_wash_drip.mp4", flip: true },
      { key: "p", name: "장구 더러러러 (강)", sound: "sounds/janggu_deororeo_strong.wav", clip: "clips/v2/ink02_scatter.mp4", flip: true },
      { key: "z", name: "추임새 얼쑤", sound: "sounds/chuimsae_eolssu.wav", clip: "clips/v2/ink10_dry_loop.mp4", flip: true },
      { key: "x", name: "추임새 얼씨구", sound: "sounds/chuimsae_eolssigu.wav", clip: "clips/v2/ink11_zigzag.mp4", flip: true },
      { key: "c", name: "추임새 좋다", sound: "sounds/chuimsae_jota.wav", clip: "clips/v2/ink14_swirl.mp4", flip: true },
      { key: "q", name: "꽹과리 객 (강)", sound: "sounds/kkwaenggwari_gaek_strong.wav", clip: "clips/v2/ink19_c_enso.mp4", flip: true },
      { key: "w", name: "꽹과리 갯 (강)", sound: "sounds/kkwaenggwari_gaet_strong.wav", clip: "clips/v2/ink04_enso.mp4", flip: true },
      { key: "e", name: "북 노고 (중)", sound: "sounds/buk_nogo_mid.wav", clip: "clips/v3/ink22_peony_bloom.mp4", flip: true },
      { key: "r", name: "북 절고 (중)", sound: "sounds/buk_jeolgo_mid.wav", clip: "clips/v3/ink21_mountain_mist.mp4", flip: true },
      { key: "v", name: "북 노고 (강)", sound: "sounds/buk_nogo_strong.wav", clip: "clips/v3/ink23_ink_circles.mp4", flip: true },
      { key: "b", name: "북 절고 (강)", sound: "sounds/buk_jeolgo_strong.wav", clip: "clips/v2/ink17_landscape.mp4", flip: true },
      { key: "n", name: "추임새 쑤", sound: "sounds/chuimsae_ssu.wav", clip: "clips/v2/ink16_stains.mp4", flip: true },
      { key: "m", name: "추임새 어이", sound: "sounds/chuimsae_eoi.wav", clip: "clips/v2/ink18_mist.mp4", flip: true },
    ],
  },
  {
    name: "단청",
    background: "assets/hanji_aged.jpg",
    blend: "darken",
    pads: [
      { key: "a", name: "연꽃",      clip: "clips/dancheong/dc01_lotus_bloom.mp4", flip: true },
      { key: "s", name: "물결",      clip: "clips/dancheong/dc02_wave_sweep.mp4", flip: true },
      { key: "d", name: "기와 문양", clip: "clips/dancheong/dc03_tile_medallions.mp4", flip: true },
      { key: "f", name: "머리초 띠", clip: "clips/dancheong/dc04_meoricho_band.mp4", flip: true },
    ],
  },
];
