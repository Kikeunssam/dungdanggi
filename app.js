(() => {
  const VIDEOS_PER_PAD = 4; // 같은 키를 빠르게 연타해도 겹쳐 보이도록 키마다 영상 4개를 돌려 쓴다
  const VOICES_PER_PAD = 8; // 같은 소리가 동시에 울릴 수 있는 최대 개수

  const stage = document.getElementById("stage");
  const notice = document.getElementById("notice");
  const audio = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: "interactive" });
  const master = audio.createGain();
  master.connect(audio.destination);

  const pads = new Map(); // key -> { buffer, videos, voices }
  let zTop = 0;

  function showNotice(text) {
    notice.textContent = text;
    notice.hidden = false;
  }

  async function loadPad(def) {
    const [soundRes, clipRes] = await Promise.all([fetch(def.sound), fetch(def.clip)]);
    if (!soundRes.ok) throw new Error(`${def.sound} (${soundRes.status})`);
    if (!clipRes.ok) throw new Error(`${def.clip} (${clipRes.status})`);
    const buffer = await audio.decodeAudioData(await soundRes.arrayBuffer());
    const clipUrl = URL.createObjectURL(await clipRes.blob());

    const videos = [];
    for (let i = 0; i < VIDEOS_PER_PAD; i++) {
      const v = document.createElement("video");
      v.src = clipUrl;
      v.muted = true;
      v.playsInline = true;
      v.preload = "auto";
      v.startedAt = 0;
      v.addEventListener("ended", () => v.classList.remove("on"));
      stage.appendChild(v);
      v.load();
      videos.push(v);
    }
    pads.set(def.key, { def, buffer, videos, voices: [] });
  }

  function playSound(pad) {
    const src = audio.createBufferSource();
    src.buffer = pad.buffer;
    src.connect(master);
    src.start();
    pad.voices.push(src);
    src.onended = () => {
      const i = pad.voices.indexOf(src);
      if (i >= 0) pad.voices.splice(i, 1);
    };
    if (pad.voices.length > VOICES_PER_PAD) pad.voices.shift().stop();
  }

  function playVideo(pad) {
    // 쉬고 있는 영상을 먼저 쓰고, 모두 재생 중이면 가장 오래된 것을 처음부터 다시 튼다.
    let v = pad.videos.find((x) => !x.classList.contains("on"));
    if (!v) v = pad.videos.reduce((a, b) => (a.startedAt <= b.startedAt ? a : b));
    v.startedAt = performance.now();
    v.style.zIndex = String(++zTop);
    v.currentTime = 0;
    v.classList.add("on");
    v.play().catch(() => v.classList.remove("on"));
  }

  function trigger(key) {
    const pad = pads.get(key);
    if (!pad) return;
    if (audio.state !== "running") audio.resume();
    playSound(pad);
    playVideo(pad);
  }

  window.addEventListener("keydown", (e) => {
    if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return; // 꾹 누르고 있을 때의 자동 반복은 무시
    // e.code 기준이라 한글 입력 상태(ㅁㄴㅇㄹ)에서도 a s d f 자리로 동작한다
    const key = e.code.startsWith("Key") ? e.code.slice(3).toLowerCase() : "";
    if (pads.has(key)) {
      e.preventDefault();
      trigger(key);
    }
  });

  if (location.protocol === "file:") {
    showNotice("파일을 직접 열면 소리를 불러올 수 없어요. 폴더에서 python3 -m http.server 를 실행한 뒤 http://localhost:8000 으로 열어 주세요.");
    return;
  }

  Promise.all(window.PADS.map(loadPad)).catch((err) => {
    showNotice(`불러오지 못한 파일이 있어요: ${err.message}`);
  });
})();
