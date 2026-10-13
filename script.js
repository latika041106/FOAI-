// script.js
// ---------
// Frontend logic. Talks to the Flask API (/api/*) and renders the
// board, stats, AI reasoning panel, and event log. No game logic
// lives here on purpose -- the server (Symbolic AI + rules) is the
// single source of truth.

const boardEl = document.getElementById("board");
const logEl = document.getElementById("log");

function el(id) { return document.getElementById(id); }

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
}

function renderBoard(state) {
  boardEl.innerHTML = "";
  const size = state.grid_size;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const cell = document.createElement("div");
      cell.className = "cell";

      const key = `${x},${y}`;
      const item = state.items[key];
      const isExit = state.exit_pos[0] === x && state.exit_pos[1] === y;
      const isPlayer = state.player.x === x && state.player.y === y;
      const isEnemy = state.enemy.alive && state.enemy.x === x && state.enemy.y === y;

      if (isExit) cell.classList.add("exit");
      else if (item === "health_pack") cell.classList.add("health_pack");
      else if (item === "key") cell.classList.add("key");

      let content = "";
      if (isPlayer && isEnemy) content = "🧑👾";
      else if (isPlayer) content = "🧑";
      else if (isEnemy) content = "👾";
      else if (isExit) content = "🚪";
      else if (item === "health_pack") content = "❤️";
      else if (item === "key") content = "🗝️";

      cell.textContent = content;
      boardEl.appendChild(cell);
    }
  }
}

function renderStats(state) {
  const p = state.player;
  const e = state.enemy;

  el("player-hp-text").textContent = `HP: ${p.health}/${p.max_health}`;
  el("player-hp-fill").style.width = `${(p.health / p.max_health) * 100}%`;
  el("player-key").textContent = p.has_key ? "✅" : "❌";
  el("player-potions").textContent = p.potions;

  el("enemy-hp-text").textContent = e.alive ? `HP: ${e.health}/${e.max_health}` : "Defeated";
  el("enemy-hp-fill").style.width = `${(e.health / e.max_health) * 100}%`;
  el("enemy-state").textContent = e.alive ? e.state : "defeated";
}

function renderAI(aiDecision) {
  if (!aiDecision) return;
  el("ai-rule").textContent = aiDecision.rule_name;
  el("ai-reason").textContent = `"${aiDecision.reason}"`;
}

function renderLog(logLines) {
  logEl.innerHTML = "";
  logLines.slice().reverse().forEach((line) => {
    const div = document.createElement("div");
    div.textContent = line;
    logEl.appendChild(div);
  });
}

function renderGameOver(state) {
  const overlay = el("overlay");
  if (!state.game_over) {
    overlay.classList.add("hidden");
    return;
  }
  overlay.classList.remove("hidden");
  el("overlay-title").textContent = state.won ? "🎉 Victory!" : "💀 Game Over";
  el("overlay-text").textContent = state.won
    ? "You escaped the dungeon with the key!"
    : "You were defeated by the enemy.";
}

function renderAll(state) {
  renderBoard(state);
  renderStats(state);
  renderLog(state.log);
  renderGameOver(state);
  if (state.ai_decision) renderAI(state.ai_decision);
}

async function sendAction(action, direction = null) {
  const body = { action };
  if (direction) body.direction = direction;
  const state = await api("/api/action", { method: "POST", body: JSON.stringify(body) });
  renderAll(state);
}

async function startNewGame() {
  const state = await api("/api/new_game", { method: "POST" });
  el("ai-rule").textContent = "—";
  el("ai-reason").textContent = "Waiting for your move...";
  renderAll(state);
}

// ---- wire up buttons ----
el("btn-up").addEventListener("click", () => sendAction("move", "up"));
el("btn-down").addEventListener("click", () => sendAction("move", "down"));
el("btn-left").addEventListener("click", () => sendAction("move", "left"));
el("btn-right").addEventListener("click", () => sendAction("move", "right"));
el("btn-attack").addEventListener("click", () => sendAction("attack"));
el("btn-potion").addEventListener("click", () => sendAction("use_potion"));
el("btn-newgame").addEventListener("click", startNewGame);
el("overlay-restart").addEventListener("click", startNewGame);

// keyboard support
window.addEventListener("keydown", (e) => {
  switch (e.key) {
    case "ArrowUp": sendAction("move", "up"); break;
    case "ArrowDown": sendAction("move", "down"); break;
    case "ArrowLeft": sendAction("move", "left"); break;
    case "ArrowRight": sendAction("move", "right"); break;
    case " ": e.preventDefault(); sendAction("attack"); break;
  }
});

// ---- initial load ----
(async function init() {
  const state = await api("/api/state");
  renderAll(state);
})();
