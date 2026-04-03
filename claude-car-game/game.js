const gameArea = document.getElementById("gameArea");
const player = document.getElementById("player");
const scoreEl = document.getElementById("score");
const energyFill = document.getElementById("energyFill");
const energyValue = document.getElementById("energyValue");
const laneStreaks = document.querySelector(".lane-streaks");
const speedLines = document.querySelector(".speed-lines");
const parallaxFar = document.querySelector(".parallax.far");
const parallaxNear = document.querySelector(".parallax.near");
const impactFlash = document.getElementById("impactFlash");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlayTitle");
const overlayText = document.getElementById("overlayText");

const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.engineOsc = null;
    this.engineGain = null;
    this.engineFilter = null;
  }

  ensure() {
    if (this.ctx) return;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    this.ctx = new Ctx();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.14;
    this.master.connect(this.ctx.destination);

    this.engineOsc = this.ctx.createOscillator();
    this.engineOsc.type = "sawtooth";
    this.engineGain = this.ctx.createGain();
    this.engineFilter = this.ctx.createBiquadFilter();
    this.engineFilter.type = "lowpass";
    this.engineFilter.frequency.value = 420;

    this.engineGain.gain.value = 0;
    this.engineOsc.frequency.value = 86;

    this.engineOsc.connect(this.engineFilter);
    this.engineFilter.connect(this.engineGain);
    this.engineGain.connect(this.master);
    this.engineOsc.start();
  }

  resume() {
    this.ensure();
    if (this.ctx.state === "suspended") this.ctx.resume();
  }

  startTone() {
    this.resume();
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(150, t);
    osc.frequency.exponentialRampToValueAtTime(460, t + 0.22);

    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(0.085, t + 0.04);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.24);

    osc.connect(gain);
    gain.connect(this.master);
    osc.start(t);
    osc.stop(t + 0.26);
  }

  setEngine(level, steerAmount) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const rpm = 86 + level * 120 + Math.abs(steerAmount) * 12;
    const throttle = 0.03 + level * 0.055;
    const cutoff = 320 + level * 780;

    this.engineOsc.frequency.setTargetAtTime(rpm, t, 0.05);
    this.engineGain.gain.setTargetAtTime(throttle, t, 0.08);
    this.engineFilter.frequency.setTargetAtTime(cutoff, t, 0.08);
  }

  idleEngine() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    this.engineOsc.frequency.setTargetAtTime(84, t, 0.1);
    this.engineGain.gain.setTargetAtTime(0.012, t, 0.12);
    this.engineFilter.frequency.setTargetAtTime(280, t, 0.12);
  }

  crash() {
    this.resume();
    const t = this.ctx.currentTime;

    const noiseBuffer = this.ctx.createBuffer(1, this.ctx.sampleRate * 0.24, this.ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < data.length; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / data.length);
    }

    const src = this.ctx.createBufferSource();
    src.buffer = noiseBuffer;

    const noiseFilter = this.ctx.createBiquadFilter();
    noiseFilter.type = "bandpass";
    noiseFilter.frequency.value = 210;

    const noiseGain = this.ctx.createGain();
    noiseGain.gain.setValueAtTime(0.001, t);
    noiseGain.gain.exponentialRampToValueAtTime(0.12, t + 0.012);
    noiseGain.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);

    src.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(this.master);

    const dropOsc = this.ctx.createOscillator();
    const dropGain = this.ctx.createGain();
    dropOsc.type = "square";
    dropOsc.frequency.setValueAtTime(220, t);
    dropOsc.frequency.exponentialRampToValueAtTime(52, t + 0.24);

    dropGain.gain.setValueAtTime(0.0001, t);
    dropGain.gain.exponentialRampToValueAtTime(0.06, t + 0.03);
    dropGain.gain.exponentialRampToValueAtTime(0.0001, t + 0.25);

    dropOsc.connect(dropGain);
    dropGain.connect(this.master);

    src.start(t);
    dropOsc.start(t);
    dropOsc.stop(t + 0.28);

    this.engineGain.gain.setTargetAtTime(0.004, t, 0.05);
  }
}

const audio = new AudioEngine();

const state = {
  running: false,
  started: false,
  leftPressed: false,
  rightPressed: false,
  speed: 290,
  obstacleSpeed: 200,
  spawnEveryMs: 760,
  spawnTimer: 0,
  score: 0,
  playerX: 160,
  obstacles: [],
  lastTime: 0,
  roadScroll: 0,
  farScrollX: 0,
  nearScrollX: 0,
  impactTimer: 0,
};

function showOverlay(mode) {
  overlay.classList.remove("hidden");
  overlay.dataset.state = mode;

  if (mode === "start") {
    overlayTitle.textContent = "Ready to Drive?";
    overlayText.textContent = "Press Space to start";
    return;
  }

  overlayTitle.textContent = "Game Over";
  overlayText.textContent = "Press Space to restart";
}

function hideOverlay() {
  overlay.classList.add("hidden");
}

function makeObstacle() {
  const el = document.createElement("div");
  el.className = "car enemy";
  const x = 42 + Math.random() * (gameArea.clientWidth - 84);
  const y = -70;
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  el.style.transform = "translateX(-50%) scale(0.56)";
  gameArea.appendChild(el);
  state.obstacles.push({ el, x, y, w: 42, h: 72, scale: 0.56 });
}

function rectsOverlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function setImpact() {
  gameArea.classList.remove("crash");
  void gameArea.offsetWidth;
  gameArea.classList.add("crash");

  impactFlash.classList.remove("active");
  void impactFlash.offsetWidth;
  impactFlash.classList.add("active");
}

function gameOver() {
  state.running = false;
  state.impactTimer = 0.26;
  setImpact();
  audio.crash();
  showOverlay("gameover");
}

function resetGame() {
  for (const obs of state.obstacles) obs.el.remove();
  state.obstacles = [];
  state.running = true;
  state.started = true;
  state.spawnTimer = 0;
  state.score = 0;
  state.roadScroll = 0;
  state.farScrollX = 0;
  state.nearScrollX = 0;
  state.impactTimer = 0;
  state.playerX = gameArea.clientWidth / 2;
  player.style.left = `${state.playerX}px`;
  scoreEl.textContent = "0";
  energyFill.style.width = "0%";
  energyValue.textContent = "0%";
  hideOverlay();
  audio.startTone();
}

function updateRoadAndParallax(dt, speedFactor, steerDir) {
  const roadRate = 420 + speedFactor * 420;
  state.roadScroll += dt * roadRate;
  laneStreaks.style.backgroundPositionY = `${state.roadScroll}px`;

  const streakWidth = 12 + speedFactor * 16;
  laneStreaks.style.width = `${streakWidth}px`;
  speedLines.style.opacity = (0.16 + speedFactor * 0.44).toFixed(3);

  state.farScrollX += dt * (12 + speedFactor * 26) * steerDir;
  state.nearScrollX += dt * (25 + speedFactor * 58) * steerDir;

  parallaxFar.style.backgroundPosition = `0 0, ${state.farScrollX}px 0`;
  parallaxNear.style.backgroundPosition = `0 0, ${state.nearScrollX}px 0`;
}

function updateObstacles(dt) {
  const center = gameArea.clientWidth / 2;

  for (let i = state.obstacles.length - 1; i >= 0; i--) {
    const obs = state.obstacles[i];
    const approachBoost = 1 + Math.max(0, obs.y) / gameArea.clientHeight;
    const speed = (state.obstacleSpeed + state.score * 0.5) * approachBoost;
    obs.y += speed * dt;

    const depth = clamp(obs.y / gameArea.clientHeight, 0, 1);
    const spread = 0.56 + depth * 0.9;
    const scaledX = center + (obs.x - center) * spread;
    const scale = 0.56 + depth * 0.95;

    obs.scale = scale;
    obs.w = 42 * scale;
    obs.h = 72 * scale;

    obs.el.style.left = `${scaledX}px`;
    obs.el.style.top = `${obs.y}px`;
    obs.el.style.transform = `translateX(-50%) scale(${scale.toFixed(3)})`;

    obs.rect = {
      x: scaledX - obs.w / 2,
      y: obs.y,
      w: obs.w,
      h: obs.h,
    };

    if (obs.y > gameArea.clientHeight + 90) {
      obs.el.remove();
      state.obstacles.splice(i, 1);
    }
  }
}

function update(dt) {
  if (!state.running) {
    audio.idleEngine();
    return;
  }

  const steerDir = (state.rightPressed ? 1 : 0) - (state.leftPressed ? 1 : 0);

  if (state.leftPressed) state.playerX -= state.speed * dt;
  if (state.rightPressed) state.playerX += state.speed * dt;

  const maxX = gameArea.clientWidth - player.offsetWidth / 2;
  const minX = player.offsetWidth / 2;
  state.playerX = clamp(state.playerX, minX, maxX);

  const tilt = steerDir * 7;
  gameArea.style.setProperty("--player-tilt", `${tilt}deg`);
  player.style.left = `${state.playerX}px`;

  const speedFactor = clamp(state.score / 180, 0, 1);

  state.spawnTimer += dt * 1000;
  const dynamicSpawn = state.spawnEveryMs - speedFactor * 220;
  if (state.spawnTimer >= dynamicSpawn) {
    state.spawnTimer = 0;
    makeObstacle();
  }

  updateRoadAndParallax(dt, speedFactor, steerDir);
  updateObstacles(dt);

  const playerRect = {
    x: state.playerX - player.offsetWidth / 2,
    y: gameArea.clientHeight - player.offsetHeight - 16,
    w: player.offsetWidth,
    h: player.offsetHeight,
  };

  for (const obs of state.obstacles) {
    if (obs.rect && rectsOverlap(playerRect, obs.rect)) {
      gameOver();
      return;
    }
  }

  state.score += dt * (10 + speedFactor * 9);
  scoreEl.textContent = Math.floor(state.score).toString();

  const energy = Math.floor(speedFactor * 100);
  energyFill.style.width = `${energy}%`;
  energyValue.textContent = `${energy}%`;

  audio.setEngine(speedFactor, steerDir);
}

function loop(ts) {
  if (!state.lastTime) state.lastTime = ts;
  const dt = (ts - state.lastTime) / 1000;
  state.lastTime = ts;

  if (state.impactTimer > 0) {
    state.impactTimer -= dt;
    if (state.impactTimer <= 0) {
      gameArea.classList.remove("crash");
      impactFlash.classList.remove("active");
    }
  }

  update(Math.min(dt, 0.05));
  requestAnimationFrame(loop);
}

document.addEventListener("keydown", (e) => {
  if (e.code === "ArrowLeft") {
    state.leftPressed = true;
    audio.resume();
  }
  if (e.code === "ArrowRight") {
    state.rightPressed = true;
    audio.resume();
  }

  if (e.code === "Space") {
    e.preventDefault();
    audio.resume();
    if (!state.started || !state.running) resetGame();
  }
});

document.addEventListener("keyup", (e) => {
  if (e.code === "ArrowLeft") state.leftPressed = false;
  if (e.code === "ArrowRight") state.rightPressed = false;
});

showOverlay("start");
requestAnimationFrame(loop);
