/* ── Config ──────────────────────────────────────────────────────── */
const WS_URL = "ws://localhost:8000/ws";

/* ── Agent registry (order matches HTML / nth-child) ─────────────── */
const AGENTS = [
  { name: "Diff Parser",    id: 0 },
  { name: "Logic Analyzer", id: 1 },
  { name: "Code Quality",   id: 2 },
  { name: "Performance",    id: 3 },
  { name: "Report Writer",  id: 4 },
];

// name → { msgs, badge, card }
const agentEl = {};
AGENTS.forEach(({ name, id }) => {
  agentEl[name] = {
    msgs:  document.getElementById(`msgs-${id}`),
    badge: document.getElementById(`badge-${id}`),
    card:  document.getElementById(`msgs-${id}`)?.closest(".agent-card"),
  };
});

/* ── DOM refs ─────────────────────────────────────────────────────── */
const repoUrlInput  = document.getElementById("repoUrl");
const analyzeBtn    = document.getElementById("analyzeBtn");
const statusMsg     = document.getElementById("statusMsg");
const scrollHint    = document.getElementById("scrollHint");
const reportSection = document.getElementById("reportSection");
const reportContent = document.getElementById("reportContent");
const copyBtn       = document.getElementById("copyBtn");
const backBtn       = document.getElementById("backBtn");

/* ── State ───────────────────────────────────────────────────────── */
let socket      = null;
let rawMarkdown = "";

/* ── Event listeners ─────────────────────────────────────────────── */
analyzeBtn.addEventListener("click", startAnalysis);
repoUrlInput.addEventListener("keydown", e => { if (e.key === "Enter") startAnalysis(); });

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(rawMarkdown).then(() => {
    copyBtn.textContent = "Copied!";
    setTimeout(() => (copyBtn.textContent = "Copy Markdown"), 2000);
  });
});

backBtn.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
});

/* ── Main ────────────────────────────────────────────────────────── */
function startAnalysis() {
  const url = repoUrlInput.value.trim();
  if (!url) { setStatus("Please enter a GitHub repo URL."); return; }

  resetUI();
  analyzeBtn.disabled = true;
  setStatus("Connecting...");

  if (socket) socket.close();
  socket = new WebSocket(WS_URL);

  socket.addEventListener("open", () => {
    setStatus(`Analyzing ${url.split("/").slice(-2).join("/")}…`);
    socket.send(JSON.stringify({ repo_url: url }));
  });

  socket.addEventListener("message", e => handleMessage(JSON.parse(e.data)));

  socket.addEventListener("error", () => {
    setStatus("Connection failed — is the backend running on :8000?");
    analyzeBtn.disabled = false;
  });

  socket.addEventListener("close", () => {
    analyzeBtn.disabled = false;
  });
}

/* ── Message dispatcher ──────────────────────────────────────────── */
function handleMessage(msg) {
  switch (msg.type) {
    case "status":
      setStatus(msg.message);
      break;

    case "agent_message":
      appendMsg(msg.agent, msg.message);
      setBadge(msg.agent, "active", "working…");
      setCardActive(msg.agent, true);
      break;

    case "agent_done":
      appendMsg(msg.agent, msg.message);
      setBadge(msg.agent, "done", "✓ done");
      setCardActive(msg.agent, false);
      break;

    case "report_ready":
      rawMarkdown = msg.report;
      renderReport(msg.report);
      scrollHint.classList.remove("hidden");
      setStatus("Analysis complete.");
      break;

    case "error":
      setStatus(`Error: ${msg.message}`);
      break;
  }
}

/* ── Agent helpers ───────────────────────────────────────────────── */
function appendMsg(agentName, text) {
  const { msgs } = agentEl[agentName] || {};
  if (!msgs) return;

  // Remove idle placeholder on first real message
  const idle = msgs.querySelector(".idle");
  if (idle) idle.remove();

  // Dim previous "latest" message
  msgs.querySelectorAll(".msg.latest").forEach(el => el.classList.remove("latest"));

  const el = document.createElement("div");
  el.className = "msg latest";
  el.textContent = `› ${text}`;
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function setBadge(agentName, cls, label) {
  const { badge } = agentEl[agentName] || {};
  if (!badge) return;
  badge.className = `badge ${cls}`;
  badge.textContent = label;
}

function setCardActive(agentName, active) {
  const { card } = agentEl[agentName] || {};
  if (!card) return;
  card.classList.toggle("active", active);
}

/* ── Report ──────────────────────────────────────────────────────── */
function renderReport(markdown) {
  reportContent.innerHTML = marked.parse(markdown);
  // Small delay so the DOM is painted before scrolling
  setTimeout(() => {
    reportSection.scrollIntoView({ behavior: "smooth" });
  }, 300);
}

/* ── UI helpers ──────────────────────────────────────────────────── */
function resetUI() {
  rawMarkdown = "";
  scrollHint.classList.add("hidden");
  reportContent.innerHTML = "";
  setStatus("");

  AGENTS.forEach(({ name }) => {
    const { msgs, badge, card } = agentEl[name];
    msgs.innerHTML  = '<span class="idle">waiting for analysis...</span>';
    badge.className = "badge";
    badge.textContent = "waiting";
    card?.classList.remove("active");
  });
}

function setStatus(text) {
  statusMsg.textContent = text;
}
