const gameArea = document.getElementById("gameArea");
const player = document.getElementById("player");
const scoreEl = document.getElementById("score");
const overlay = document.getElementById("overlay");

const state = {
  running: true,
  leftPressed: false,
  rightPressed: false,
  speed: 260,
  obstacleSpeed: 220,
  spawnEveryMs: 900,
  spawnTimer: 0,
  score: 0,
  playerX: 139,
  obstacles: [],
  lastTime: 0,
};

function makeObstacle() {
  const el = document.createElement("div");
  el.className = "car enemy";
  const x = Math.random() * (gameArea.clientWidth - 42);
  const y = -80;
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  gameArea.appendChild(el);
  state.obstacles.push({ el, x, y, w: 42, h: 72 });
}

function rectsOverlap(a, b) {
  return (
    a.x < b.x + b.w &&
    a.x + a.w > b.x &&
    a.y < b.y + b.h &&
    a.y + a.h > b.y
  );
}

function gameOver() {
  state.running = false;
  overlay.classList.remove("hidden");
}

function resetGame() {
  for (const obs of state.obstacles) obs.el.remove();
  state.obstacles = [];
  state.running = true;
  state.spawnTimer = 0;
  state.score = 0;
  state.playerX = 139;
  player.style.left = `${state.playerX}px`;
  scoreEl.textContent = "0";
  overlay.classList.add("hidden");
}

function update(dt) {
  if (!state.running) return;

  if (state.leftPressed) state.playerX -= state.speed * dt;
  if (state.rightPressed) state.playerX += state.speed * dt;

  const maxX = gameArea.clientWidth - player.offsetWidth;
  state.playerX = Math.max(0, Math.min(maxX, state.playerX));
  player.style.left = `${state.playerX}px`;

  state.spawnTimer += dt * 1000;
  if (state.spawnTimer >= state.spawnEveryMs) {
    state.spawnTimer = 0;
    makeObstacle();
  }

  const playerRect = {
    x: state.playerX,
    y: gameArea.clientHeight - player.offsetHeight - 16,
    w: player.offsetWidth,
    h: player.offsetHeight,
  };

  for (let i = state.obstacles.length - 1; i >= 0; i--) {
    const obs = state.obstacles[i];
    obs.y += state.obstacleSpeed * dt;
    obs.el.style.top = `${obs.y}px`;

    if (rectsOverlap(playerRect, obs)) {
      gameOver();
      return;
    }

    if (obs.y > gameArea.clientHeight + 80) {
      obs.el.remove();
      state.obstacles.splice(i, 1);
    }
  }

  state.score += dt * 10;
  scoreEl.textContent = Math.floor(state.score).toString();
}

function loop(ts) {
  if (!state.lastTime) state.lastTime = ts;
  const dt = (ts - state.lastTime) / 1000;
  state.lastTime = ts;

  update(Math.min(dt, 0.05));
  requestAnimationFrame(loop);
}

document.addEventListener("keydown", (e) => {
  if (e.code === "ArrowLeft") state.leftPressed = true;
  if (e.code === "ArrowRight") state.rightPressed = true;
  if (e.code === "Space" && !state.running) resetGame();
});

document.addEventListener("keyup", (e) => {
  if (e.code === "ArrowLeft") state.leftPressed = false;
  if (e.code === "ArrowRight") state.rightPressed = false;
});

requestAnimationFrame(loop);
