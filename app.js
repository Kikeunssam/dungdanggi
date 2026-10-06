(() => {
  // 브라우저는 한꺼번에 준비해 둘 수 있는 영상 수에 한계가 있어서(키가 많으면 일부가 안 나온다),
  // 키마다 영상은 1개만 미리 준비하고, 연타로 겹칠 때만 잠깐 더 만들었다가 끝나면 치운다.
  const VIDEOS_PER_PAD = 4; // 한 키에서 동시에 겹쳐 보일 수 있는 최대 개수
  const VOICES_PER_PAD = 8; // 같은 소리가 동시에 울릴 수 있는 최대 개수
  const MAX_VIDEOS = 22; // 화면 전체에 둘 수 있는 영상 수 (Chrome은 1080p 영상을 약 25개 넘게 동시에 열면 일부를 못 연다)

  const stage = document.getElementById("stage");
  const notice = document.getElementById("notice");
  const audio = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: "interactive" });
  const master = audio.createGain();
  master.connect(audio.destination);

  const pads = new Map(); // key -> { buffer, videos, voices }
  let zTop = 0;
  let videoCount = 0;

  function showNotice(text) {
    notice.textContent = text;
    notice.hidden = false;
  }

  // index.html을 파일로 바로 열면 브라우저가 fetch를 막으므로,
  // sounds.js에 미리 담아 둔 음원 데이터를 먼저 쓰고 없을 때만 fetch한다.
  async function loadSoundBytes(path) {
    const b64 = window.SOUND_DATA && window.SOUND_DATA[path];
    if (b64) return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer;
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${path} (${res.status})`);
    return res.arrayBuffer();
  }

  async function loadPad(def) {
    const buffer = await audio.decodeAudioData(await loadSoundBytes(def.sound));

    const pad = { def, buffer, videos: [], voices: [], lastFlip: 0 };
    addVideo(pad);
    pads.set(def.key, pad);
  }

  function addVideo(pad) {
    const v = document.createElement("video");
    v.src = pad.def.clip; // 영상은 파일로 열어도(file://) 바로 재생된다
    v.muted = true;
    v.playsInline = true;
    v.preload = "auto";
    v.startedAt = 0;
    // 첫 번째(미리 준비한) 영상만 남기고, 연타 때 더 만든 영상은 치워서 디코더를 돌려준다
    const release = () => {
      v.classList.remove("on");
      if (pad.videos[0] !== v && pad.videos.includes(v)) {
        pad.videos.splice(pad.videos.indexOf(v), 1);
        videoCount--;
        v.removeAttribute("src");
        v.load();
        v.remove();
      }
    };
    v.addEventListener("ended", release);
    v.addEventListener("error", () => {
      if (!v.getAttribute("src")) return; // 치우면서 src를 지운 경우
      console.warn("영상을 열 수 없음:", pad.def.key, pad.def.clip, v.error);
      // 열지 못한 영상이 화면에 '재생 중'으로 남아 키가 먹통이 되지 않도록 정리한다
      release();
      if (pad.videos[0] === v) setTimeout(() => v.load(), 500); // 미리 준비한 영상은 다시 연다
    });
    stage.appendChild(v);
    videoCount++;
    v.load();
    pad.videos.push(v);
    return v;
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

  const FLIPS = ["none", "scaleX(-1)", "scaleY(-1)", "scale(-1, -1)"];

  function randomFlip(pad) {
    let i = Math.floor(Math.random() * (FLIPS.length - 1));
    if (i >= pad.lastFlip) i++; // 직전 방향은 건너뛴다
    pad.lastFlip = i;
    return FLIPS[i];
  }

  function playVideo(pad) {
    // 쉬고 있는 영상을 먼저 쓰고, 모두 재생 중이면 가장 오래된 것을 처음부터 다시 튼다.
    let v = pad.videos.find((x) => !x.classList.contains("on"));
    if (!v && pad.videos.length < VIDEOS_PER_PAD && videoCount < MAX_VIDEOS) v = addVideo(pad);
    if (!v) v = pad.videos.reduce((a, b) => (a.startedAt <= b.startedAt ? a : b));
    v.startedAt = performance.now();
    v.style.zIndex = String(++zTop);
    if (pad.def.flip) v.style.transform = randomFlip(pad);
    v.currentTime = 0;
    v.classList.add("on");
    // 브라우저가 영상을 끝내 못 틀면 'ended'가 오지 않으므로, 클립 길이가 지나면 정리한다
    const startedAt = v.startedAt;
    setTimeout(() => {
      if (v.startedAt === startedAt && v.classList.contains("on") && (v.paused || v.readyState < 2)) v.dispatchEvent(new Event("ended"));
    }, ((v.duration || 4) + 1) * 1000);
    v.play().catch((err) => {
      v.classList.remove("on");
      console.warn("영상 재생 실패:", pad.def.key, pad.def.clip, err);
    });
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

  Promise.all(window.PADS.map(loadPad)).catch((err) => {
    const hint = location.protocol === "file:" ? " (소리를 바꿨다면 python3 make_sounds_js.py 를 한 번 실행해 주세요)" : "";
    showNotice(`불러오지 못한 파일이 있어요: ${err.message}${hint}`);
  });
})();
