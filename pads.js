// 키 하나 = 소리 하나 + 영상 하나.
// 패드를 늘리려면 아래에 줄을 추가하면 된다.
// flip: true 면 누를 때마다 영상을 좌우·상하로 무작위 반전한다 (직전과는 다른 방향으로).
// 영상은 1920x1080, 한지 배경 위 먹, 끝 프레임이 빈 종이인 클립을 쓴다.
window.PADS = [
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
];
