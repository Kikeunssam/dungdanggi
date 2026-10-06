(() => {
  // 브라우저가 한꺼번에 열어 둘 수 있는 영상 수에는 한계가 있다 (Chrome 데스크톱은 1080p 약 25개를 컴퓨터 전체에서 나눠 쓰고,
  // 휴대폰·태블릿은 훨씬 적다). 그래서 영상 요소를 키마다 두지 않고, 전체에서 MAX_VIDEOS개만
  // 만들어 돌려 쓴다. 쉬는 영상이 없으면 가장 오래된 영상을 가져와 새 클립을 연다.
  const MOBILE = window.matchMedia("(pointer: coarse)").matches;
  // 화면 전체에 동시에 둘 수 있는 영상 수. 영상 디코더는 컴퓨터 전체가 나눠 쓰므로(다른 탭·앱 포함)
  // 데스크톱도 넉넉히 12개로 둔다 (22개일 때 다른 크롬 창이 열려 있으면 일부 키 영상이 안 나왔다).
  const MAX_VIDEOS = MOBILE ? 6 : 12;
  const VIDEOS_PER_PAD = 4; // 한 키에서 동시에 겹쳐 보일 수 있는 최대 개수
  const VOICES_PER_PAD = 8; // 같은 소리가 동시에 울릴 수 있는 최대 개수

  // 터치 화면 칸 순서 (가로 9x3, 세로 3x9). 27번째(오른쪽 아래) 칸은 뱅크 바꾸기.
  const GRID = "qwertyuiopasdfghjklzxcvbnm".split("").concat("switch");

  const stage = document.getElementById("stage");
  const notice = document.getElementById("notice");
  const audio = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: "interactive" });
  const master = audio.createGain();
  master.connect(audio.destination);

  // 뱅크마다 배경 그림 층을 하나씩 깔고, 지금 뱅크의 배경만 보이게 한다 (영상은 그 위에 겹친다)
  const banks = window.BANKS.map((b, i) => {
    const bg = document.createElement("div");
    bg.className = "bg";
    bg.style.backgroundImage = `url("${b.background}")`;
    bg.classList.toggle("on", i === 0);
    stage.appendChild(bg);
    return { ...b, defs: b.pads, index: i, bg, pads: new Map() }; // pads: key -> { def, bank, buffer, voices, lastFlip }
  });
  let bank = banks[0];
  const label = document.createElement("div");
  label.id = "bank-label";
  document.body.appendChild(label);
  const videos = []; // 전체 영상 요소 (최대 MAX_VIDEOS개)
  let zTop = 0;
  const stats = (window.dungdanggiStats = { triggers: 0, voices: 0, bank: 0 }); // 테스트용 숫자

  function showNotice(text) {
    notice.textContent = text;
    notice.hidden = false;
  }

  // 웹 서버(http)로 열면 음원 파일을 바로 받는다.
  // index.html을 파일로 바로 열면 브라우저가 fetch를 막으므로 sounds.js에 담아 둔 데이터를 쓴다.
  async function loadSoundBytes(path) {
    const b64 = location.protocol === "file:" && window.SOUND_DATA && window.SOUND_DATA[path];
    if (b64) return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer;
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${path} (${res.status})`);
    return res.arrayBuffer();
  }

  function decode(bytes) {
    // 옛 Safari는 Promise 형태의 decodeAudioData를 지원하지 않는다
    return new Promise((resolve, reject) => audio.decodeAudioData(bytes, resolve, reject));
  }

  async function loadPad(b, def) {
    const buffer = def.sound ? await decode(await loadSoundBytes(def.sound)) : null; // 소리 없는 패드도 된다
    b.pads.set(def.key, { def, bank: b, buffer, voices: [], lastFlip: 0 });
  }

  // ---- 영상 ----

  function createVideo() {
    const v = document.createElement("video");
    v.muted = true;
    v.playsInline = true;
    v.setAttribute("playsinline", "");
    v.setAttribute("muted", "");
    v.preload = MOBILE ? "metadata" : "auto";
    v.startedAt = 0;
    v.pad = null;
    v.addEventListener("ended", () => v.classList.remove("on"));
    v.addEventListener("error", () => {
      if (!v.getAttribute("src")) return;
      console.warn("영상을 열 수 없음:", v.pad && v.pad.def.key, v.getAttribute("src"), v.error);
      // 열지 못한 영상이 '재생 중'으로 남아 키가 먹통이 되지 않도록 비워 둔다 (다음에 다시 연다)
      v.classList.remove("on");
      v.pad = null;
      v.removeAttribute("src");
      v.load();
    });
    stage.appendChild(v);
    videos.push(v);
    return v;
  }

  function assign(v, pad) {
    if (v.pad === pad && v.getAttribute("src")) return;
    v.pad = pad;
    v.style.mixBlendMode = pad.bank.blend;
    v.src = pad.def.clip;
    v.load();
  }

  function oldest(list) {
    return list.reduce((a, b) => (a.startedAt <= b.startedAt ? a : b));
  }

  function pickVideo(pad) {
    const mine = videos.filter((v) => v.pad === pad);
    const idleMine = mine.find((v) => !v.classList.contains("on"));
    if (idleMine) return idleMine;
    if (mine.length >= VIDEOS_PER_PAD) return oldest(mine);
    if (videos.length < MAX_VIDEOS) return createVideo();
    const idle = videos.filter((v) => !v.classList.contains("on"));
    if (idle.length) return oldest(idle); // 다른 키가 쓰던 쉬는 영상을 가져온다
    return oldest(videos); // 모두 재생 중이면 가장 오래된 것을 끊는다
  }

  const FLIPS = ["none", "scaleX(-1)", "scaleY(-1)", "scale(-1, -1)"];

  function randomFlip(pad) {
    let i = Math.floor(Math.random() * (FLIPS.length - 1));
    if (i >= pad.lastFlip) i++; // 직전 방향은 건너뛴다
    pad.lastFlip = i;
    return FLIPS[i];
  }

  function playVideo(pad) {
    const v = pickVideo(pad);
    assign(v, pad);
    v.startedAt = performance.now();
    v.style.zIndex = String(++zTop);
    v.style.transform = pad.def.flip ? randomFlip(pad) : "none";
    try {
      v.currentTime = 0;
    } catch (e) {}
    v.classList.add("on");
    // 브라우저가 영상을 끝내 못 틀면 'ended'가 오지 않으므로, 클립 길이가 지나면 정리한다
    const startedAt = v.startedAt;
    setTimeout(() => {
      if (v.startedAt === startedAt && v.classList.contains("on") && (v.paused || v.readyState < 2)) v.classList.remove("on");
    }, ((v.duration || 4) + 1) * 1000);
    const p = v.play();
    if (p)
      p.catch((err) => {
        if (v.startedAt !== startedAt) return; // 다른 키가 이 영상을 가져가면서 끊긴 경우
        v.classList.remove("on");
        console.warn("영상 재생 실패:", pad.def.key, pad.def.clip, err);
      });
  }

  // 데스크톱은 키마다 하나씩 미리 열어 둔다 (한도까지). 휴대폰은 누를 때 연다.
  function warmUp() {
    if (MOBILE) return;
    for (const pad of banks[0].pads.values()) {
      if (videos.length >= MAX_VIDEOS) break;
      assign(createVideo(), pad);
    }
  }

  // ---- 소리 ----

  function playSound(pad) {
    if (!pad.buffer) return;
    const src = audio.createBufferSource();
    src.buffer = pad.buffer;
    src.connect(master);
    src.start();
    pad.voices.push(src);
    stats.voices++;
    src.onended = () => {
      const i = pad.voices.indexOf(src);
      if (i >= 0) pad.voices.splice(i, 1);
      stats.voices--;
    };
    if (pad.voices.length > VOICES_PER_PAD) pad.voices.shift().stop();
  }

  // iOS·안드로이드는 사용자가 처음 화면을 만질 때 소리를 켜 줘야 한다 (무음 한 번 재생)
  let unlocked = false;
  function unlockAudio() {
    if (audio.state !== "running") audio.resume();
    if (unlocked) return;
    unlocked = true;
    const s = audio.createBufferSource();
    s.buffer = audio.createBuffer(1, 1, 22050);
    s.connect(audio.destination);
    s.start(0);
  }

  function trigger(key) {
    const pad = bank.pads.get(key);
    if (!pad) return false;
    if (audio.state !== "running") audio.resume();
    stats.triggers++;
    playSound(pad);
    playVideo(pad);
    return true;
  }

  // ---- 뱅크 바꾸기 ----

  let labelTimer = 0;
  function switchBank() {
    bank = banks[(bank.index + 1) % banks.length];
    stats.bank = bank.index;
    for (const b of banks) b.bg.classList.toggle("on", b === bank);
    // 다른 뱅크 영상이 새 배경 위에 남지 않도록 바로 감춘다 (울리고 있는 소리는 끝까지 둔다)
    for (const v of videos) {
      if (v.pad && v.pad.bank !== bank && v.classList.contains("on")) {
        v.classList.remove("on");
        v.startedAt = 0;
        v.pause();
      }
    }
    label.textContent = bank.name;
    label.classList.add("on");
    clearTimeout(labelTimer);
    labelTimer = setTimeout(() => label.classList.remove("on"), 600);
  }

  // ---- 입력 ----

  window.addEventListener("keydown", (e) => {
    if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return; // 꾹 누르고 있을 때의 자동 반복은 무시
    if (e.code === "Space") {
      e.preventDefault();
      switchBank();
      return;
    }
    // e.code 기준이라 한글 입력 상태(ㅁㄴㅇㄹ)에서도 키 자리로 동작한다
    const key = e.code.startsWith("Key") ? e.code.slice(3).toLowerCase() : "";
    if (bank.pads.has(key)) {
      e.preventDefault();
      trigger(key);
    }
  });

  // 화면 전체를 보이지 않는 칸으로 나눈다: 가로 화면 9x3, 세로 화면 3x9
  function cellAt(x, y) {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const cols = w >= h ? 9 : 3;
    const rows = 27 / cols;
    const c = Math.min(cols - 1, Math.max(0, Math.floor((x / w) * cols)));
    const r = Math.min(rows - 1, Math.max(0, Math.floor((y / h) * rows)));
    return GRID[r * cols + c];
  }

  function ripple(x, y) {
    const d = document.createElement("div");
    d.className = "ripple";
    d.style.left = x + "px";
    d.style.top = y + "px";
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 600);
  }

  // 손가락마다 pointerdown이 따로 오므로 여러 손가락을 동시에 눌러도 각각 울린다
  window.addEventListener("pointerdown", (e) => {
    if (e.target.closest && e.target.closest("#notice")) return;
    e.preventDefault();
    unlockAudio();
    if (e.pointerType === "mouse") return; // 마우스 클릭은 소리만 켜고 연주는 키보드로
    const cell = cellAt(e.clientX, e.clientY);
    if (cell === "switch") {
      switchBank();
      return;
    }
    if (trigger(cell)) ripple(e.clientX, e.clientY);
  }, { passive: false });

  // 길게 누르기 메뉴·두 번 눌러 확대 막기
  window.addEventListener("contextmenu", (e) => e.preventDefault());
  document.addEventListener("dblclick", (e) => e.preventDefault());
  document.addEventListener("gesturestart", (e) => e.preventDefault());

  Promise.all(banks.flatMap((b) => b.defs.map((def) => loadPad(b, def))))
    .then(warmUp)
    .catch((err) => {
      const hint = location.protocol === "file:" ? " (소리를 바꿨다면 python3 make_sounds_js.py 를 한 번 실행해 주세요)" : "";
      showNotice(`불러오지 못한 파일이 있어요: ${err.message}${hint}`);
    });
})();
