// ============================================================================
// AdaptCode web frontend
// Mirrors game_visual.py's mechanics via the FastAPI backend (server.py),
// and posts questionnaire responses straight to Supabase (client-side),
// using the same question data as questionnaire.py.
// ============================================================================

const GRID_SIZE = 10;
let CELL = 70;

const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");

let sessionId = localStorage.getItem("adaptcode_session_id");
let state = null;
let supabaseUrl = "";
let supabaseKey = "";

// ── Question data (mirrors questionnaire.py exactly) ───────────────────────
const RATING_OPTIONS = [
  "1 - Strongly Disagree", "2 - Disagree", "3 - Neutral",
  "4 - Agree", "5 - Strongly Agree",
];

const PRE_QUESTIONS = [
  { id: "student_id", type: "text",
    label: "Student ID / Code (for matching pre & post):" },
  { id: "q1", type: "radio",
    label: "Q1. What is your current level of Python experience?",
    options: [
      "A) Complete beginner - I have never written Python code",
      "B) Beginner - I have seen Python but written very little",
      "C) Some experience - I can write simple programs",
      "D) Intermediate - I am comfortable with functions and loops",
    ]},
  { id: "q2", type: "radio",
    label: "Q2. How motivated do you feel to learn Python right now?",
    options: [
      "A) Very motivated", "B) Somewhat motivated",
      "C) Neutral - I do it because I have to", "D) Not very motivated",
    ]},
  { id: "q3", type: "radio",
    label: "Q3. When you get stuck on a Python problem, what do you usually do?",
    options: [
      "A) Search Google or Stack Overflow",
      "B) Re-read the material and try again",
      "C) Ask a friend or classmate",
      "D) Give up and move on",
    ]},
];

const POST_QUESTIONS = [
  { id: "student_id", type: "text",
    label: "Student ID / Code (for matching pre & post):" },
  { id: "q1", type: "radio",
    label: "Q1. How long were you able to stay focused while playing?",
    options: [
      "A) Less than 10 minutes", "B) 10-20 minutes",
      "C) 20-40 minutes", "D) More than 40 minutes - I lost track of time",
    ]},
  { id: "q2", type: "radio",
    label: "Q2. When you picked a wrong code snippet and saw the explanation, what did you do?",
    options: [
      "A) Read it carefully - it helped me understand my mistake",
      "B) Glanced at it and moved on",
      "C) Ignored it and just tried again",
      "D) Found the explanation confusing",
    ]},
  { id: "q3", type: "radio",
    label: "Q3. How useful were the adaptive hints when you were stuck?",
    options: [
      "A) Very useful - they guided me without giving the full answer",
      "B) Somewhat useful - they helped a little",
      "C) Neutral - I wasn't sure how to use them",
      "D) Not useful - I still felt stuck",
      "E) I did not use the hints",
    ]},
  { id: "r5", type: "radio", options: RATING_OPTIONS,
    label: "Rate: The hints felt personalised - they matched how much help I actually needed." },
  { id: "q4", type: "radio",
    label: "Q4. Did completing a problem in the game feel rewarding?",
    options: [
      "A) Yes - I immediately wanted to try the next one",
      "B) Somewhat - it was satisfying but not exciting",
      "C) Neutral - it felt like any normal exercise",
      "D) No difference",
    ]},
  { id: "overall_rating", type: "radio", options: RATING_OPTIONS,
    label: "Rate: I would recommend AdaptCode to a friend learning Python for the first time." },
];

// ── Toast ────────────────────────────────────────────────────────────────
let toastTimer = null;
function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  el.style.opacity = "1";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.style.opacity = "0";
    setTimeout(() => el.classList.add("hidden"), 300);
  }, 3500);
}

// ── API helpers ──────────────────────────────────────────────────────────
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 404) {
    // Session expired (server restarted) — start fresh automatically.
    sessionId = null;
    localStorage.removeItem("adaptcode_session_id");
    await initSession();
    return null;
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function initSession() {
  if (sessionId) {
    try {
      state = await api(`/api/${sessionId}/state`);
      if (state) { render(); return; }
    } catch (e) { /* fall through to new session */ }
  }
  const created = await fetch("/api/session", { method: "POST" }).then(r => r.json());
  sessionId = created.session_id;
  localStorage.setItem("adaptcode_session_id", sessionId);
  state = created;
  render();
}

async function loadConfig() {
  const cfg = await fetch("/api/config").then(r => r.json());
  supabaseUrl = cfg.supabase_url;
  supabaseKey = cfg.supabase_anon_key;
}

// ── Game actions ─────────────────────────────────────────────────────────
async function move(action) {
  if (!state || state.game_state !== "playing") return;
  const next = await api(`/api/${sessionId}/move`, {
    method: "POST", body: JSON.stringify({ action }),
  });
  if (next) { state = next; render(); }
}

async function requestHint() {
  const next = await api(`/api/${sessionId}/hint`, { method: "POST" });
  if (next) { state = next; render(); }
}

async function restart() {
  const next = await api(`/api/${sessionId}/reset`, { method: "POST" });
  if (next) { state = next; render(); }
}

async function selectProblem(idx) {
  const next = await api(`/api/${sessionId}/select/${idx}`, { method: "POST" });
  if (next) { state = next; render(); }
}

async function generateProblem(topic) {
  const btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.textContent = "⏳ Generating...";
  try {
    const result = await api(`/api/${sessionId}/generate`, {
      method: "POST", body: JSON.stringify({ topic }),
    });
    if (result) {
      state = result;
      render();
      if (!result.ok) toast(result.error || "Generation failed.");
    }
  } catch (e) {
    toast("Error generating problem: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "⚡ Generate";
  }
}

// ── Rendering: canvas board ──────────────────────────────────────────────
function resizeCanvas() {
  const wrap = document.getElementById("board-wrap");
  const maxSize = Math.min(wrap.clientWidth - 20, wrap.clientHeight - 60, 700);
  CELL = Math.max(30, Math.floor(maxSize / GRID_SIZE));
  const size = CELL * GRID_SIZE;
  canvas.width = size;
  canvas.height = size;
}

function drawBoard() {
  if (!state) return;
  const size = CELL * GRID_SIZE;
  ctx.clearRect(0, 0, size, size);

  // grid
  for (let gx = 0; gx < GRID_SIZE; gx++) {
    for (let gy = 0; gy < GRID_SIZE; gy++) {
      ctx.fillStyle = "#19192a";
      ctx.fillRect(gx * CELL, gy * CELL, CELL, CELL);
      ctx.strokeStyle = "#373737";
      ctx.strokeRect(gx * CELL, gy * CELL, CELL, CELL);
    }
  }

  // snippets (drawn before snake, so the snake visually sits on top)
  const fontSize = Math.max(8, Math.round(CELL * 0.13));
  ctx.font = `${fontSize}px Consolas, monospace`;
  ctx.fillStyle = "#232337";
  for (const [key, text] of Object.entries(state.snippets)) {
    const [gx, gy] = key.split(",").map(Number);
    ctx.fillStyle = "#232337";
    ctx.fillRect(gx * CELL + 1, gy * CELL + 1, CELL - 2, CELL - 2);
    wrapText(text.trim(), gx * CELL + CELL / 2, gy * CELL + CELL / 2, CELL - 8, fontSize);
  }

  // snake
  state.snake.forEach(([gx, gy], i) => {
    ctx.fillStyle = i === 0 ? "#00d264" : "#468cff";
    roundRect(gx * CELL + 1, gy * CELL + 1, CELL - 2, CELL - 2, 4);
    ctx.fill();
  });

  // eyes on head
  if (state.snake.length) {
    const [hx, hy] = state.snake[0];
    drawEyes(hx, hy, state.facing);
  }
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawEyes(gx, gy, facing) {
  const cx = gx * CELL + CELL / 2, cy = gy * CELL + CELL / 2;
  const [dx, dy] = facing;
  const px = -dy, py = dx;
  const fwd = CELL * 0.16, spread = CELL * 0.17, r = Math.max(2, CELL * 0.09);
  [-1, 1].forEach(sign => {
    const ex = cx + dx * fwd + px * spread * sign;
    const ey = cy + dy * fwd + py * spread * sign;
    ctx.fillStyle = "#fff";
    ctx.beginPath(); ctx.arc(ex, ey, r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#0a0a14";
    ctx.beginPath(); ctx.arc(ex + dx * r * 0.4, ey + dy * r * 0.4, r * 0.5, 0, Math.PI * 2); ctx.fill();
  });
}

function wrapText(text, cx, cy, maxWidth, fontSize) {
  const words = text.split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    const test = cur ? cur + " " + w : w;
    if (ctx.measureText(test).width <= maxWidth || !cur) cur = test;
    else { lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  const shown = lines.slice(0, 4);
  const lineH = fontSize + 3;
  const startY = cy - (shown.length * lineH) / 2 + lineH / 2;
  ctx.fillStyle = "#ffa51e";
  ctx.textAlign = "center";
  shown.forEach((ln, i) => ctx.fillText(ln, cx, startY + i * lineH));
}

// ── Rendering: sidebar ───────────────────────────────────────────────────
function renderSidebar() {
  if (!state) return;

  // Problem picker
  const sel = document.getElementById("problem-select");
  sel.innerHTML = "";
  state.problems.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.idx;
    opt.textContent = p.name;
    if (p.idx === state.problem_idx) opt.selected = true;
    sel.appendChild(opt);
  });

  document.getElementById("problem-name").textContent = state.problem_name;
  document.getElementById("problem-desc").textContent = state.description;

  // Collected
  const collectedList = document.getElementById("collected-list");
  if (state.collected.length === 0) {
    collectedList.textContent = "(none yet)";
    collectedList.className = "muted";
  } else {
    collectedList.className = "";
    collectedList.innerHTML = state.collected.map(l => `<div>${escapeHtml(l)}</div>`).join("");
  }

  // Progress
  const pct = state.total_lines ? (state.expected_idx / state.total_lines) * 100 : 0;
  document.getElementById("progress-bar-fill").style.width = pct + "%";
  document.getElementById("progress-label").textContent = `${state.expected_idx}/${state.total_lines}`;

  // Panels (hint / wrong / feedback) — priority order matches game_visual.py
  const slot = document.getElementById("panel-slot");
  slot.innerHTML = "";
  if (state.hint_active) {
    slot.innerHTML = `<div class="panel panel-hint">
      <span class="panel-title" style="color:#ffd23c">💡 Hint (${escapeHtml(state.hint_level)})</span>
      ${escapeHtml(state.hint_text)}</div>`;
  } else if (state.wrong_active) {
    slot.innerHTML = `<div class="panel panel-wrong">
      <span class="panel-title" style="color:#d23232">✗ Wrong pick — keep going!</span>
      ${escapeHtml(state.wrong_detail)}</div>`;
  } else if (state.fb_msg) {
    slot.innerHTML = `<div class="panel panel-fb">
      <span style="color:#00d264">${escapeHtml(state.fb_msg)}</span>
      ${state.fb_detail ? `<div style="color:#ffd23c;margin-top:4px">${escapeHtml(state.fb_detail)}</div>` : ""}</div>`;
  }

  // Suggestion
  const sugg = document.getElementById("suggestion-box");
  if (!state.hint_active && state.suggested_level && state.suggested_level !== "none") {
    sugg.classList.remove("hidden");
    sugg.textContent = `Hint suggests: ${state.suggested_level} — press H for help`;
  } else {
    sugg.classList.add("hidden");
  }

  // Stats
  const s = state.stats;
  document.getElementById("stat-success").textContent =
    `${Math.round(s.success_rate * 100)}%  (${s.correct}✓ / ${s.attempts})`;
  document.getElementById("stat-runs").textContent = s.runs;
  document.getElementById("stat-completed").textContent = s.completed;
  document.getElementById("stat-hints").textContent = state.run_hints_used;

  // Complete overlay
  const overlay = document.getElementById("complete-overlay");
  if (state.game_state === "complete") {
    overlay.classList.remove("hidden");
    document.getElementById("complete-stats").innerHTML = `
      Success rate: ${Math.round(s.success_rate * 100)}% (${s.correct}✓ / ${s.attempts})<br>
      Hints used this run: ${state.run_hints_used}<br>
      Runs completed: ${s.completed} / ${s.runs}`;
  } else {
    overlay.classList.add("hidden");
  }
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

function render() {
  resizeCanvas();
  drawBoard();
  renderSidebar();
}

// ── Questionnaire modal ──────────────────────────────────────────────────
let questForm = null; // { questions, title, table, idx, answers }

function openQuestionnaire(questions, title, table) {
  questForm = { questions, title, table, idx: 0, answers: {} };
  questions.forEach(q => (questForm.answers[q.id] = ""));
  document.getElementById("quest-overlay").classList.remove("hidden");
  document.getElementById("quest-title").textContent = title;
  renderQuestStep();
}

function closeQuestionnaire() {
  questForm = null;
  document.getElementById("quest-overlay").classList.add("hidden");
}

function renderQuestStep() {
  const { questions, idx, answers } = questForm;
  const q = questions[idx];
  document.getElementById("quest-progress").textContent =
    `Question ${idx + 1} / ${questions.length}`;

  const form = document.getElementById("quest-form");
  form.innerHTML = "";

  const label = document.createElement("div");
  label.className = "q-label";
  label.textContent = q.label;
  form.appendChild(label);

  if (q.type === "radio") {
    q.options.forEach(opt => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "q-option" + (answers[q.id] === opt ? " selected" : "");
      b.textContent = opt;
      b.onclick = () => {
        answers[q.id] = opt;
        document.getElementById("quest-error").classList.add("hidden");
        renderQuestStep();
      };
      form.appendChild(b);
    });
  } else if (q.type === "text") {
    const input = document.createElement("input");
    input.type = "text";
    input.value = answers[q.id];
    input.placeholder = "Type your answer...";
    input.oninput = () => (answers[q.id] = input.value);
    input.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); questNext(); } };
    form.appendChild(input);
    setTimeout(() => input.focus(), 0);
  }

  document.getElementById("quest-back").classList.toggle("hidden", idx === 0);
  document.getElementById("quest-next").textContent =
    idx === questions.length - 1 ? "Submit" : "Next >";
}

function questBack() {
  if (questForm.idx > 0) {
    questForm.idx -= 1;
    document.getElementById("quest-error").classList.add("hidden");
    renderQuestStep();
  }
}

async function questNext() {
  const { questions, idx, answers } = questForm;
  const q = questions[idx];
  const answer = (answers[q.id] || "").trim();
  const required = q.type === "radio" || q.id === "student_id";
  if (required && !answer) {
    const err = document.getElementById("quest-error");
    err.textContent = "Please answer before continuing.";
    err.classList.remove("hidden");
    return;
  }
  document.getElementById("quest-error").classList.add("hidden");

  if (idx === questions.length - 1) {
    await submitQuestionnaire();
    return;
  }
  questForm.idx += 1;
  renderQuestStep();
}

async function submitQuestionnaire() {
  const { answers, table } = questForm;
  const row = { timestamp: new Date().toISOString(), ...answers };

  const btn = document.getElementById("quest-next");
  btn.disabled = true;
  btn.textContent = "Submitting...";

  let synced = false;
  if (supabaseUrl && supabaseKey) {
    try {
      const res = await fetch(`${supabaseUrl.replace(/\/$/, "")}/rest/v1/${table}`, {
        method: "POST",
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
        },
        body: JSON.stringify(row),
      });
      synced = res.ok;
      if (!res.ok) console.error("Supabase insert failed:", await res.text());
    } catch (e) {
      console.error("Supabase unreachable:", e);
    }
  }

  btn.disabled = false;
  closeQuestionnaire();
  toast(synced
    ? "✓ Questionnaire submitted — synced to cloud!"
    : "✓ Questionnaire recorded, but cloud sync isn't configured/reachable — ask your instructor.");
}

// ── Event wiring ─────────────────────────────────────────────────────────
document.getElementById("btn-hint").onclick = requestHint;
document.getElementById("btn-restart").onclick = restart;
document.getElementById("problem-select").onchange = (e) => selectProblem(Number(e.target.value));
document.getElementById("btn-generate").onclick = () => {
  const input = document.getElementById("topic-input");
  const topic = input.value.trim();
  if (!topic) return;
  input.value = "";
  generateProblem(topic);
};
document.getElementById("topic-input").onkeydown = (e) => {
  if (e.key === "Enter") document.getElementById("btn-generate").click();
};

document.getElementById("btn-pre").onclick = () =>
  openQuestionnaire(PRE_QUESTIONS, "AdaptCode — Pre-Game Questionnaire", "pre_questionnaire_responses");
document.getElementById("btn-post").onclick = () =>
  openQuestionnaire(POST_QUESTIONS, "AdaptCode — Post-Game Questionnaire", "post_questionnaire_responses");
document.getElementById("quest-close").onclick = closeQuestionnaire;
document.getElementById("quest-back").onclick = questBack;
document.getElementById("quest-next").onclick = questNext;

document.addEventListener("keydown", (e) => {
  // Questionnaire modal open — Esc closes it, nothing else here should fire.
  if (questForm) {
    if (e.key === "Escape") closeQuestionnaire();
    return;
  }
  // Typing in the topic box — don't hijack keys as game shortcuts.
  if (document.activeElement === document.getElementById("topic-input")) return;

  switch (e.key) {
    case "ArrowLeft": move(0); e.preventDefault(); break;
    case "ArrowRight": move(1); e.preventDefault(); break;
    case "ArrowUp": move(2); e.preventDefault(); break;
    case "ArrowDown": move(3); e.preventDefault(); break;
    case "h": case "H": requestHint(); break;
    case "r": case "R": restart(); break;
  }
});

window.addEventListener("resize", () => { if (state) render(); });

// ── Boot ─────────────────────────────────────────────────────────────────
(async function boot() {
  await loadConfig();
  await initSession();
})();
