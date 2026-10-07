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
    if (b.background.startsWith("#")) bg.style.backgroundColor = b.background; // 단색 배경
    else bg.style.backgroundImage = `url("${b.background}")`;
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

  let noticeTimer = 0;
  function showNotice(text, sec = 0) {
    notice.textContent = text;
    notice.hidden = false;
    clearTimeout(noticeTimer);
    if (sec) noticeTimer = setTimeout(() => (notice.hidden = true), sec * 1000);
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
    v.src = pad.clip || pad.def.clip; // 섞음 뱅크 패드는 섞음용 영상(pad.clip)을 쓴다
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
  // 이미 만든 영상 중 쉬는 것은 새 뱅크의 클립으로 바꿔 열어, 영상 수가 한도를 넘지 않게 한다.
  function warmUp(b = banks[0]) {
    if (MOBILE) return;
    const idle = videos.filter((v) => !v.classList.contains("on"));
    for (const pad of b.pads.values()) {
      if (videos.some((v) => v.pad === pad)) continue;
      if (idle.length) assign(idle.shift(), pad);
      else if (videos.length < MAX_VIDEOS) assign(createVideo(), pad);
      else break;
    }
  }

  // ---- 섞음 뱅크 ----
  // 들어올 때마다 뱅크 1~3에서 서로 다른 패드 26개를 9/9/8개(8개 뱅크는 무작위)로 골라 키에 섞는다.
  // 고른 패드는 원래 소리·영상·반전을 그대로 쓴다.

  function shuffle(list) {
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    return list;
  }

  function buildMix(mix) {
    const sources = banks.filter((b) => !b.mix && b.pads.size);
    const keys = GRID.slice(0, 26);
    const counts = sources.map(() => Math.floor(keys.length / sources.length));
    shuffle(sources.map((_, i) => i))
      .slice(0, keys.length - counts.reduce((a, b) => a + b, 0))
      .forEach((i) => counts[i]++);
    const picked = sources.flatMap((b, i) => shuffle([...b.pads.values()]).slice(0, counts[i]));
    shuffle(picked);
    mix.pads = new Map();
    keys.forEach((key, i) => {
      const src = picked[i];
      if (!src) return;
      const look = (mix.looks && mix.looks[src.bank.index]) || {};
      const clip = look.dir ? look.dir + src.def.clip.split("/").pop() : src.def.clip;
      mix.pads.set(key, { def: src.def, clip, bank: mix, src, buffer: src.buffer, voices: [], lastFlip: 0 });
    });
    // 테스트용: 지금 섞인 배치
    window.dungdanggiMix = [...mix.pads].map(([key, p]) => ({ key, bank: p.src.bank.index, clip: p.clip, sound: p.def.sound || null }));
  }

  // ---- 소리 ----

  function playSound(pad) {
    if (!pad.buffer) return;
    stats.sounds = (stats.sounds || 0) + 1;
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
    if (bank.mix) buildMix(bank);
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
    warmUp(bank); // 쉬는 영상은 새 뱅크 클립으로 미리 열어 둔다
    label.classList.add("on");
    clearTimeout(labelTimer);
    labelTimer = setTimeout(() => label.classList.remove("on"), 600);
  }

  // ---- 녹화 (PC: Shift+R) ----
  // 화면에 보이는 것(배경 + 재생 중인 영상, 겹치기 방식·반전 그대로)을 캔버스 하나에 매 프레임 다시 그리고,
  // 앱 소리와 함께 MediaRecorder로 MP4 파일을 만든다. 최대 23초, 멈추면 바로 내려받는다.

  const REC_MAX_SEC = 23;
  const REC_TYPES = [
    "video/mp4;codecs=avc1.42E01F,mp4a.40.2",
    "video/mp4;codecs=avc1,mp4a.40.2",
    "video/mp4",
    "video/webm;codecs=vp9,opus",
    "video/webm",
  ];
  const BLENDS = { multiply: "multiply", darken: "darken", lighten: "lighten", screen: "screen" };
  const recBadge = document.createElement("div");
  recBadge.id = "rec";
  recBadge.hidden = true;
  document.body.appendChild(recBadge);
  const bgImages = new Map();
  let rec = null;

  function bgImage(b) {
    if (b.background.startsWith("#")) return null;
    if (!bgImages.has(b)) {
      const img = new Image();
      img.src = b.background;
      bgImages.set(b, img);
    }
    return bgImages.get(b);
  }

  // CSS object-fit: cover / background-size: cover 와 같은 자리 계산
  function cover(sw, sh, dw, dh) {
    const s = Math.max(dw / sw, dh / sh);
    return [(dw - sw * s) / 2, (dh - sh * s) / 2, sw * s, sh * s];
  }

  function flipOf(transform) {
    if (!transform || transform === "none") return [1, 1];
    if (transform.startsWith("scaleX")) return [-1, 1];
    if (transform.startsWith("scaleY")) return [1, -1];
    if (transform.startsWith("scale(")) return [-1, -1];
    return [1, 1];
  }

  function drawStage(ctx, W, H) {
    ctx.globalCompositeOperation = "source-over";
    const img = bgImage(bank);
    if (img && img.naturalWidth) ctx.drawImage(img, ...cover(img.naturalWidth, img.naturalHeight, W, H));
    else {
      ctx.fillStyle = bank.background.startsWith("#") ? bank.background : "#e8e3da";
      ctx.fillRect(0, 0, W, H);
    }
    const on = videos
      .filter((v) => v.classList.contains("on") && v.readyState >= 2 && v.videoWidth)
      .sort((a, b) => Number(a.style.zIndex) - Number(b.style.zIndex));
    for (const v of on) {
      ctx.globalCompositeOperation = BLENDS[v.style.mixBlendMode] || "source-over";
      const [fx, fy] = flipOf(v.style.transform);
      ctx.save();
      ctx.translate(W / 2, H / 2);
      ctx.scale(fx, fy);
      ctx.translate(-W / 2, -H / 2);
      ctx.drawImage(v, ...cover(v.videoWidth, v.videoHeight, W, H));
      ctx.restore();
    }
  }

  function stamp(d) {
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
  }

  function download(blob, name) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.hidden = true;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);
  }

  function toggleRecording() {
    if (rec) stopRecording();
    else startRecording();
  }

  function startRecording() {
    // 파일로 바로 연 화면은 브라우저 보안 때문에 영상을 캔버스로 옮길 수 없어 그림이 녹화되지 않는다
    if (location.protocol === "file:") {
      showNotice("녹화는 웹 서버로 열었을 때만 돼요: 앱 폴더에서 python3 -m http.server 8000 실행 후 http://localhost:8000 을 열어 주세요", 8);
      return;
    }
    const type = window.MediaRecorder && REC_TYPES.find((t) => MediaRecorder.isTypeSupported(t));
    if (!type) {
      showNotice("이 브라우저는 화면 녹화를 지원하지 않아요 (Chrome을 써 주세요)", 6);
      return;
    }
    if (audio.state !== "running") audio.resume();
    const W = 1920;
    const H = Math.round((W * window.innerHeight) / window.innerWidth / 2) * 2;
    const canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);
    let stream;
    try {
      stream = canvas.captureStream(30); // 그림을 그리기 전에 스트림을 연다
    } catch (err) {
      showNotice(`녹화를 시작할 수 없어요: ${err.message}`, 6);
      return;
    }
    const dest = audio.createMediaStreamDestination();
    master.connect(dest); // 듣는 소리는 그대로, 같은 소리를 녹화에도 보낸다
    for (const track of dest.stream.getAudioTracks()) stream.addTrack(track);
    const recorder = new MediaRecorder(stream, { mimeType: type, videoBitsPerSecond: 8000000, audioBitsPerSecond: 192000 });
    const chunks = [];
    const ext = type.startsWith("video/mp4") ? "mp4" : "webm";
    const name = `dungdanggi_${bank.name}_${stamp(new Date())}.${ext}`;
    const state = { recorder, startedAt: performance.now(), timer: 0 };
    recorder.ondataavailable = (e) => e.data && e.data.size && chunks.push(e.data);
    recorder.onstop = () => {
      master.disconnect(dest);
      for (const track of stream.getTracks()) track.stop();
      download(new Blob(chunks, { type: type.split(";")[0] }), name);
      stats.lastRecording = { name, type, bytes: chunks.reduce((n, c) => n + c.size, 0) };
    };
    const draw = () => {
      if (rec !== state) return;
      drawStage(ctx, W, H);
      requestAnimationFrame(draw);
    };
    state.timer = setInterval(() => {
      const sec = (performance.now() - state.startedAt) / 1000;
      recBadge.textContent = `${Math.min(REC_MAX_SEC, Math.floor(sec))}초`;
      if (sec >= REC_MAX_SEC) stopRecording(); // 23초가 되면 저절로 멈추고 내려받는다
    }, 100);
    rec = state;
    recorder.start(1000);
    draw();
    recBadge.textContent = "0초";
    recBadge.hidden = false;
    stats.recording = true;
    if (ext !== "mp4") showNotice("이 브라우저는 MP4 녹화를 못 해서 WebM으로 저장해요", 6);
  }

  function stopRecording() {
    if (!rec) return;
    const state = rec;
    rec = null;
    clearInterval(state.timer);
    recBadge.hidden = true;
    stats.recording = false;
    if (state.recorder.state !== "inactive") state.recorder.stop();
  }

  // ---- 입력 ----

  window.addEventListener("keydown", (e) => {
    if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return; // 꾹 누르고 있을 때의 자동 반복은 무시
    if (e.code === "Space") {
      e.preventDefault();
      switchBank();
      return;
    }
    // Shift를 누른 동안은 패드를 치지 않는다. Shift+R = 녹화 시작/멈춤
    if (e.shiftKey) {
      if (e.code === "KeyR") {
        e.preventDefault();
        toggleRecording();
      }
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
    .then(() => {
      stats.loadedMs = Math.round(performance.now()); // 모든 소리를 다 불러온 시각 (테스트용)
      warmUp();
    })
    .catch((err) => {
      const hint = location.protocol === "file:" ? " (소리를 바꿨다면 python3 make_sounds_js.py 를 한 번 실행해 주세요)" : "";
      showNotice(`불러오지 못한 파일이 있어요: ${err.message}${hint}`);
    });
})();
