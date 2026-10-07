// 뱅크(악기 묶음) 여러 개. PC는 스페이스바, 터치는 오른쪽 아래 칸으로 다음 뱅크로 넘어간다 (1→2→3→4→1).
// 뱅크마다 배경 그림과 영상 겹치는 방식(blend)을 정한다:
//   multiply = 종이에 먹이 스미듯 겹친다 (흰 바탕은 사라지고, 옅은 담묵·담채도 종이색과 섞여 자연스럽다)
//   darken  = 밝은 종이 위 먹·색 (흰 바탕·종이색은 사라지고 그림만 남는다)
//   lighten = 어두운 배경 위 색 (검은 바탕은 사라지고 색만 남는다) — 검은 바탕 클립을 쓸 때
// 패드 한 줄 = 키 하나. sound는 빼도 된다 (영상만 나온다).
// flip: true 면 누를 때마다 영상을 좌우·상하로 무작위 반전한다 (직전과는 다른 방향으로).
// 영상은 1920x1080, 밝은 바탕(한지·흰색) 위 그림이고, 끝 프레임은 빈 바탕이어야 한다.
window.BANKS = [
  {
    name: "수묵",
    background: "assets/hanji_aged.jpg",
    blend: "multiply",
    pads: [
      { key: "a", name: "꽹과리 지 (강)",      sound: "sounds/kkwaenggwari_ji_strong.m4a",   clip: "clips/sumuk/ji_a.mp4", flip: true },
      { key: "s", name: "꽹과리 게르르르 (강)", sound: "sounds/kkwaenggwari_roll_strong.m4a", clip: "clips/sumuk/roll_s.mp4", flip: true },
      { key: "d", name: "징 (강)",             sound: "sounds/jing_strong.m4a",              clip: "clips/sumuk/jing_d.mp4", flip: true },
      { key: "f", name: "징 (약)",             sound: "sounds/jing_soft.m4a",                clip: "clips/sumuk/jing_f.mp4", flip: true },
      { key: "g", name: "장구 덩 (강)", sound: "sounds/janggu_deong_strong.m4a", clip: "clips/sumuk/deong_g.mp4", flip: true },
      { key: "t", name: "장구 덩 (중)", sound: "sounds/janggu_deong_mid.m4a", clip: "clips/sumuk/deong_t.mp4", flip: true },
      { key: "h", name: "장구 쿵 (강)", sound: "sounds/janggu_kung_strong.m4a", clip: "clips/sumuk/kung_h.mp4", flip: true },
      { key: "y", name: "장구 쿵 (중)", sound: "sounds/janggu_kung_mid.m4a", clip: "clips/sumuk/kung_y.mp4", flip: true },
      { key: "j", name: "장구 덕 (강)", sound: "sounds/janggu_deok_strong.m4a", clip: "clips/sumuk/deok_j.mp4", flip: true },
      { key: "u", name: "장구 덕 (중)", sound: "sounds/janggu_deok_mid.m4a", clip: "clips/sumuk/deok_u.mp4", flip: true },
      { key: "k", name: "장구 기덕 (강)", sound: "sounds/janggu_gideok_strong.m4a", clip: "clips/sumuk/gideok_k.mp4", flip: true },
      { key: "i", name: "장구 기덕 (중)", sound: "sounds/janggu_gideok_mid.m4a", clip: "clips/sumuk/gideok_i.mp4", flip: true },
      { key: "l", name: "장구 더 (강)", sound: "sounds/janggu_deo_strong.m4a", clip: "clips/sumuk/deo_l.mp4", flip: true },
      { key: "o", name: "장구 더 (중)", sound: "sounds/janggu_deo_mid.m4a", clip: "clips/sumuk/deo_o.mp4", flip: true },
      { key: "p", name: "장구 더러러러 (강)", sound: "sounds/janggu_deororeo_strong.m4a", clip: "clips/sumuk/deororeo_p.mp4", flip: true },
      { key: "z", name: "추임새 얼쑤", sound: "sounds/chuimsae_eolssu.m4a", clip: "clips/sumuk/eolssu_z.mp4", flip: true },
      { key: "x", name: "추임새 얼씨구", sound: "sounds/chuimsae_eolssigu.m4a", clip: "clips/sumuk/eolssigu_x.mp4", flip: true },
      { key: "c", name: "추임새 좋다", sound: "sounds/chuimsae_jota.m4a", clip: "clips/sumuk/jota_c.mp4", flip: true },
      { key: "q", name: "꽹과리 객 (강)", sound: "sounds/kkwaenggwari_gaek_strong.m4a", clip: "clips/sumuk/gaek_q.mp4", flip: true },
      { key: "w", name: "꽹과리 갯 (강)", sound: "sounds/kkwaenggwari_gaet_strong.m4a", clip: "clips/sumuk/gaet_w.mp4", flip: true },
      { key: "e", name: "북 노고 (중)", sound: "sounds/buk_nogo_mid.m4a", clip: "clips/sumuk/nogo_e.mp4", flip: true },
      { key: "r", name: "북 절고 (중)", sound: "sounds/buk_jeolgo_mid.m4a", clip: "clips/sumuk/jeolgo_r.mp4", flip: true },
      { key: "v", name: "북 노고 (강)", sound: "sounds/buk_nogo_strong.m4a", clip: "clips/sumuk/nogo_v.mp4", flip: true },
      { key: "b", name: "북 절고 (강)", sound: "sounds/buk_jeolgo_strong.m4a", clip: "clips/sumuk/jeolgo_b.mp4", flip: true },
      { key: "n", name: "추임새 쑤", sound: "sounds/chuimsae_ssu.m4a", clip: "clips/sumuk/ssu_n.mp4", flip: true },
      { key: "m", name: "추임새 어이", sound: "sounds/chuimsae_eoi.m4a", clip: "clips/sumuk/eoi_m.mp4", flip: true },
    ],
  },
  {
    name: "단청",
    background: "assets/hanji.jpg",
    blend: "darken",
    pads: [
      { key: "a", name: "단소 8 · 연꽃", sound: "sounds/danso_8.m4a", clip: "clips/dancheong/dc01_lotus_bloom.mp4", flip: true },
      { key: "s", name: "단소 6 · 물결", sound: "sounds/danso_6.m4a", clip: "clips/dancheong/dc02_wave_sweep.mp4", flip: true },
      { key: "d", name: "대금 니나 5 · 기와 문양", sound: "sounds/daegeum_nina_05.m4a", clip: "clips/dancheong/dc03_tile_medallions.mp4", flip: true },
      { key: "f", name: "대금 니나 6 · 머리초 띠", sound: "sounds/daegeum_nina_06.m4a", clip: "clips/dancheong/dc04_meoricho_band.mp4", flip: true },
      { key: "q", name: "대금 니나 10 · 육각 살창", sound: "sounds/daegeum_nina_10.m4a", clip: "clips/dancheong/dc05_hex_lattice.mp4", flip: true },
      { key: "w", name: "소금 노니로 · 구름 무늬", sound: "sounds/sogeum_noniro.m4a", clip: "clips/dancheong/dc06_cloud_scroll.mp4", flip: true },
      { key: "e", name: "대금 니나 11 · 아자 살창", sound: "sounds/daegeum_nina_11.m4a", clip: "clips/dancheong/dc07_aja_lattice.mp4", flip: true },
      { key: "r", name: "나각 · 보주 소용돌이", sound: "sounds/nagak.m4a", clip: "clips/dancheong/dc08_jewel_spiral.mp4", flip: true },
      { key: "t", name: "소금 깊은농음 · 오색 물결무늬", sound: "sounds/sogeum_gipeun_nongeum.m4a", clip: "clips/dancheong/dc09_rainbow_ripple.mp4", flip: true },
      { key: "y", name: "산조대금 · 쌍 연꽃", sound: "sounds/sanjo_daegeum.m4a", clip: "clips/dancheong/dc10_twin_lotus.mp4", flip: true },
      { key: "u", name: "대금 니나 12 · 별꽃", sound: "sounds/daegeum_nina_12.m4a", clip: "clips/dancheong/dc11_star_rosette.mp4", flip: true },
      { key: "i", name: "대금 니나 13 · 소란 격자", sound: "sounds/daegeum_nina_13.m4a", clip: "clips/dancheong/dc12_soran_grid.mp4", flip: true },
      { key: "o", name: "대금 니나 14 · 기둥 띠", sound: "sounds/daegeum_nina_14.m4a", clip: "clips/dancheong/dc13_pillar_bands.mp4", flip: true },
      { key: "p", name: "소금 노르니르 · 매화 흩날림", sound: "sounds/sogeum_noreunireu.m4a", clip: "clips/dancheong/dc14_maehwa_scatter.mp4", flip: true },
      { key: "g", name: "피리 · 솟는 물결", sound: "sounds/piri_14.m4a", clip: "clips/dancheong/dc15_wave_rise.mp4", flip: true },
      { key: "h", name: "대금 니나 7 · 아치 꽃줄", sound: "sounds/daegeum_nina_07.m4a", clip: "clips/dancheong/dc16_arch_garland.mp4", flip: true },
      { key: "j", name: "대금 니나 8 · 꽃잎 바퀴", sound: "sounds/daegeum_nina_08.m4a", clip: "clips/dancheong/dc17_clock_petals.mp4", flip: true },
      { key: "k", name: "대금 니나 9 · 팔각 물결", sound: "sounds/daegeum_nina_09.m4a", clip: "clips/dancheong/dc18_octagon_ripple.mp4", flip: true },
      { key: "l", name: "단소 9 · 연꽃 고리", sound: "sounds/danso_9.m4a", clip: "clips/dancheong/dc19_lotus_ring.mp4", flip: true },
      { key: "z", name: "대금 니나 1 · 마름모 사슬", sound: "sounds/daegeum_nina_01.m4a", clip: "clips/dancheong/dc20_diamond_chain.mp4", flip: true },
      { key: "x", name: "대금 니나 2 · 뇌문 틀", sound: "sounds/daegeum_nina_02.m4a", clip: "clips/dancheong/dc21_fret_frame.mp4", flip: true },
      { key: "c", name: "소금 나니루 · 떨어지는 꽃잎", sound: "sounds/sogeum_naniru.m4a", clip: "clips/dancheong/dc22_falling_petals.mp4", flip: true },
      { key: "v", name: "나발 · 햇살", sound: "sounds/nabal.m4a", clip: "clips/dancheong/dc23_sun_rays.mp4", flip: true },
      { key: "b", name: "단소 7 · 흐르는 구름", sound: "sounds/danso_7.m4a", clip: "clips/dancheong/dc24_cloud_drift.mp4", flip: true },
      { key: "n", name: "대금 니나 3 · 육각 십자", sound: "sounds/daegeum_nina_03.m4a", clip: "clips/dancheong/dc25_hexa_cross.mp4", flip: true },
      { key: "m", name: "대금 니나 4 · 모서리 부채", sound: "sounds/daegeum_nina_04.m4a", clip: "clips/dancheong/dc26_corner_fans.mp4", flip: true },
    ],
  },
  {
    name: "자개",
    background: "assets/lacquer.jpg",
    blend: "lighten", // 검은 바탕 영상: 검정은 사라지고 자개 빛만 남는다
    pads: [
      { key: "a", name: "산조가야금 튕김 · 솔잎 부채", sound: "sounds/sanjo_gayageum_twigim.m4a", clip: "clips/najeon/nj01_pine_fans.mp4", flip: true },
      { key: "s", name: "정악가야금 튕기기 · 나비와 꽃", sound: "sounds/jeongak_gayageum_flick.m4a", clip: "clips/najeon/nj02_butterfly_flower.mp4", flip: true },
      { key: "d", name: "거문고 퇴성 · 수복 원문과 박쥐", sound: "sounds/geomungo_toesung.m4a", clip: "clips/najeon/nj03_longevity_bats.mp4", flip: true },
      { key: "f", name: "산조가야금 굴림 · 넝쿨 띠", sound: "sounds/sanjo_gayageum_gullim.m4a", clip: "clips/najeon/nj04_flower_vine.mp4", flip: true },
      { key: "q", name: "정악가야금 짧게 뜯기 · 줄무늬", sound: "sounds/jeongak_gayageum_stacc.m4a", clip: "clips/najeon/nj05_stripes.mp4", flip: true },
      { key: "w", name: "양금 짧게 치기 · 마름모 격자", sound: "sounds/yanggeum_staccato.m4a", clip: "clips/najeon/nj06_diamond_lattice.mp4", flip: true },
      { key: "e", name: "양금 트릴 · 자개 점", sound: "sounds/yanggeum_trill.m4a", clip: "clips/najeon/nj07_pearl_dots.mp4", flip: true },
      { key: "r", name: "25현 가야금 글리산도 · 빗살", sound: "sounds/gayageum25_gliss.m4a", clip: "clips/najeon/nj08_hatch_sweep.mp4", flip: true },
      { key: "t", name: "거문고 추성 · 도는 고리", sound: "sounds/geomungo_chusung.m4a", clip: "clips/najeon/nj09_spinning_rings.mp4", flip: true },
      { key: "y", name: "거문고 낮은 음 · 거북등", sound: "sounds/geomungo_low.m4a", clip: "clips/najeon/nj10_tortoise_hex.mp4", flip: true },
      { key: "u", name: "거문고 전성 · 뇌문 띠", sound: "sounds/geomungo_junsung.m4a", clip: "clips/najeon/nj11_thunder_fret.mp4", flip: true },
      { key: "i", name: "산조가야금 한 음 · 칠보 고리", sound: "sounds/sanjo_gayageum_note.m4a", clip: "clips/najeon/nj12_chilbo_rings.mp4", flip: true },
      { key: "o", name: "아쟁 빠른 가락 · 대나무", sound: "sounds/ajaeng_run.m4a", clip: "clips/najeon/nj13_bamboo.mp4", flip: true },
      { key: "p", name: "25현 가야금 트레몰로 · 반짝이 별", sound: "sounds/gayageum25_tremolo.m4a", clip: "clips/najeon/nj14_sparkles.mp4", flip: true },
      { key: "g", name: "25현 가야금 농현 · 물결 비늘", sound: "sounds/gayageum25_nonghyun.m4a", clip: "clips/najeon/nj15_wave_scales.mp4", flip: true },
      { key: "h", name: "아쟁 긴 음 · 학 떼", sound: "sounds/ajaeng_long.m4a", clip: "clips/najeon/nj16_cranes.mp4", flip: true },
      { key: "j", name: "양금 강세 · 국화", sound: "sounds/yanggeum_accent.m4a", clip: "clips/najeon/nj17_chrysanthemums.mp4", flip: true },
      { key: "k", name: "아쟁 높은 음 · 매화 가지", sound: "sounds/ajaeng_high.m4a", clip: "clips/najeon/nj18_plum_branch.mp4", flip: true },
      { key: "l", name: "25현 가야금 높은 음 · 모란", sound: "sounds/gayageum25_high.m4a", clip: "clips/najeon/nj19_peony.mp4", flip: true },
      { key: "z", name: "산조가야금 농현 · 구름", sound: "sounds/sanjo_gayageum_nong.m4a", clip: "clips/najeon/nj20_cloud_scrolls.mp4", flip: true },
      { key: "x", name: "정악가야금 한 음 · 연못 연꽃", sound: "sounds/jeongak_gayageum_note.m4a", clip: "clips/najeon/nj21_lotus_pond.mp4", flip: true },
      { key: "c", name: "산조가야금 꺾는 소리 · 맴도는 물고기", sound: "sounds/sanjo_gayageum_break.m4a", clip: "clips/najeon/nj22_circling_fish.mp4", flip: true },
      { key: "v", name: "양금 강세 2 · 만화경", sound: "sounds/yanggeum_accent2.m4a", clip: "clips/najeon/nj23_kaleidoscope.mp4", flip: true },
      { key: "b", name: "정악가야금 전성 · 포도 넝쿨", sound: "sounds/jeongak_gayageum_jun.m4a", clip: "clips/najeon/nj24_grape_vine.mp4", flip: true },
      { key: "n", name: "거문고 높은 음 · 소나무 가지", sound: "sounds/geomungo_high.m4a", clip: "clips/najeon/nj25_pine_branch.mp4", flip: true },
      { key: "m", name: "25현 가야금 낮은 음 · 꽃 테두리", sound: "sounds/gayageum25_low.m4a", clip: "clips/najeon/nj26_flower_frame.mp4", flip: true },
    ],
  },
  {
    // 섞음: 이 뱅크로 들어올 때마다 뱅크 1~3 패드 26개를 9/9/8개씩 무작위로 골라 키에 섞어 놓는다.
    // 회색 바탕 위에 모두 lighten 으로 겹친다. 뱅크 1·2 패드는 검은 바탕용으로 다시 만든 영상을 쓴다
    // (looks: 뱅크 1, 2, 3 순서. dir 이 있으면 같은 파일 이름을 그 폴더에서 찾는다).
    name: "섞음",
    background: "assets/gray_mix.jpg",
    blend: "lighten",
    mix: true,
    looks: [
      { dir: "clips/mix/sumuk/" },     // 수묵: 먹을 흰색으로 반전, 검은 바탕
      { dir: "clips/mix/dancheong/" }, // 단청: 흰 종이를 검게, 색은 그대로
      {},                              // 자개: 원래 영상 그대로 (검은 바탕)
    ],
    pads: [],
  },
];
