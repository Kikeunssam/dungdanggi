// 키 하나 = 소리 하나 + 영상 하나.
// 패드를 늘리려면 아래에 줄을 추가하면 된다 (g h j k l 자리 비워 둠).
// flip: true 면 누를 때마다 영상을 좌우·상하로 무작위 반전한다 (직전과는 다른 방향으로).
// 영상은 1920x1080, 한지 배경 위 먹, 끝 프레임이 빈 종이인 클립을 쓴다.
window.PADS = [
  { key: "a", name: "꽹과리 지 (강)",      sound: "sounds/kkwaenggwari_ji_strong.wav",   clip: "clips/ink05_splash.mp4", flip: true },
  { key: "s", name: "꽹과리 게르르르 (강)", sound: "sounds/kkwaenggwari_roll_strong.wav", clip: "clips/ink02_scatter.mp4", flip: true },
  { key: "d", name: "징 (강)",             sound: "sounds/jing_strong.wav",              clip: "clips/ink04_enso.mp4", flip: true },
  { key: "f", name: "징 (약)",             sound: "sounds/jing_soft.wav",                clip: "clips/ink01_bloom.mp4", flip: true },
  // { key: "g", name: "", sound: "sounds/....wav", clip: "clips/ink03_stroke.mp4" },
  // { key: "h", name: "", sound: "sounds/....wav", clip: "clips/ink06_wash.mp4" },
];
