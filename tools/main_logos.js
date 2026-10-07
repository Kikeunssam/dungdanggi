// 둥당기 로고: 글꼴 없이 획(stroke)으로 직접 그린다. 음절 상자 100x100.
// 가로획(h)과 세로·사선획(v)을 나눠 두께 대비를 준다
const GA = {
  dung: { h: ['M84 9 H17', 'M17 33 H84', 'M6 47 H94'], v: ['M17 4 V38', 'M50 47 V62'], circles: [[50, 80, 14]] },
  dang: { h: ['M64 9 H13', 'M13 47 H64', 'M82 28 H96'], v: ['M13 4 V52', 'M82 0 V60'], circles: [[46, 80, 14]] },
  gi: { h: ['M8 14 H62'], v: ['M62 9 V34 Q62 70 20 95', 'M84 0 V100'], circles: [] },
};
const G = {
  // 둥: ㄷ 위, ㅜ, ㅇ 아래
  dung: { lines: ['M84 9 H17 V33 H84', 'M6 47 H94', 'M50 47 V61'], circles: [[50, 80, 14]] },
  // 당: ㄷ 왼쪽 위, ㅏ 오른쪽, ㅇ 아래
  dang: { lines: ['M64 9 H13 V47 H64', 'M82 2 V58', 'M82 28 H96'], circles: [[46, 80, 14]] },
  // 기: ㄱ + ㅣ
  gi: { lines: ['M8 14 H62 V34 Q62 70 22 94', 'M84 2 V98'], circles: [] },
};

function glyph(g, x, y, s, st) {
  let out = `<g transform="translate(${x} ${y}) scale(${s})">`;
  for (const d of g.lines) out += `<path d="${d}" ${st.line}/>`;
  for (const [cx, cy, r] of g.circles) out += st.circle(cx, cy, r);
  return out + '</g>';
}

const INK = '#1f2124', RED = '#b8352a';

// A. 가로는 가늘고 세로는 굵은 반듯한 획 + 북면처럼 가운데 붉은 점이 찍힌 ㅇ + 붉은 낙관
function glyphA(g, x) {
  let o = `<g transform="translate(${x} 0)">`;
  for (const d of g.h) o += `<path d="${d}" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="square"/>`;
  for (const d of g.v) o += `<path d="${d}" fill="none" stroke="${INK}" stroke-width="11.5" stroke-linecap="butt"/>`;
  for (const [cx, cy, r] of g.circles) o += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${INK}" stroke-width="9"/>` +
      `<circle cx="${cx}" cy="${cy}" r="3.4" fill="${RED}"/>`;
  return o + '</g>';
}
function logoA() {
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 382 120">`;
  s += glyphA(GA.dung, 0) + glyphA(GA.dang, 112) + glyphA(GA.gi, 224);
  // 낙관: 붉은 네모 안에 흰 획 '둥'
  s += `<g transform="translate(336 58)"><rect width="34" height="34" rx="2" fill="${RED}"/>` +
       `<g transform="translate(5 5) scale(0.24)"><path d="M84 9 H17 V33 H84" fill="none" stroke="#f6efe4" stroke-width="12"/>` +
       `<path d="M6 47 H94 M50 47 V61" fill="none" stroke="#f6efe4" stroke-width="12"/><circle cx="50" cy="80" r="14" fill="none" stroke="#f6efe4" stroke-width="12"/></g></g>`;
  return s + '</svg>';
}

// B. 전각 낙관: 세로로 긴 붉은 인장, 획을 하얗게 파낸 백문인
function logoB() {
  const st = {
    line: `fill="none" stroke="#f6efe4" stroke-width="13" stroke-linecap="square" stroke-linejoin="miter"`,
    circle: (cx, cy, r) => `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#f6efe4" stroke-width="13"/>`,
  };
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 150 400">
  <defs><filter id="stamp"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="5"/></filter>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="1" seed="7"/>
  <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.4 1.05"/><feComposite in2="SourceGraphic" operator="in"/></filter></defs>
  <g filter="url(#stamp)"><rect x="8" y="8" width="134" height="384" rx="6" fill="${RED}"/>`;
  s += glyph(G.dung, 25, 24, 1, st) + glyph(G.dang, 25, 148, 1, st) + glyph(G.gi, 25, 272, 1, st);
  s += `</g></svg>`;
  return s;
}

// C. 주문인(朱文印): 한지 위에 붉은 획과 붉은 테두리, 네 귀를 亞자처럼 들인 가로 인장
function logoC() {
  const st = {
    line: `fill="none" stroke="${RED}" stroke-width="10" stroke-linecap="square" stroke-linejoin="miter"`,
    circle: (cx, cy, r) => `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${RED}" stroke-width="10"/>`,
  };
  const W = 400, H = 150, c = 14;
  const frame = `M${c} 0 H${W - c} V${c} H${W} V${H - c} H${W - c} V${H} H${c} V${H - c} H0 V${c} H${c} Z`;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 ${W + 16} ${H + 16}">
  <defs><filter id="stampC"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="9" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="4"/></filter></defs><g filter="url(#stampC)">
  <path d="${frame}" fill="none" stroke="${RED}" stroke-width="7"/>
  <path d="M${c + 9} 9 H${W - c - 9} M${c + 9} ${H - 9} H${W - c - 9}" stroke="${RED}" stroke-width="2"/>`;
  s += glyph(G.dung, 36, 25, 1, st) + glyph(G.dang, 150, 25, 1, st) + glyph(G.gi, 264, 25, 1, st);
  return s + '</g></svg>';
}
module.exports = { logoA, logoB, logoC };

// node tools/main_logos.js  ->  assets/logo_A.svg, logo_B.svg, logo_C.svg
if (require.main === module) {
  const fs = require('fs'), path = require('path');
  const out = path.join(__dirname, '..', 'assets');
  for (const [k, f] of Object.entries({ A: logoA, B: logoB, C: logoC })) fs.writeFileSync(path.join(out, `logo_${k}.svg`), f());
}
