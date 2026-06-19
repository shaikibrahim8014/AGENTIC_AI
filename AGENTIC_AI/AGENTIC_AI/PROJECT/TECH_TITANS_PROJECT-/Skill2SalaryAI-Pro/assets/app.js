const ROLES = ["AI Engineer", "Data Scientist", "ML Engineer", "Full-Stack Developer", "Data Analyst", "Product Manager"];
const SKILLS = ["Python", "SQL", "Machine Learning", "Generative AI", "NLP", "MLOps", "Docker", "Kubernetes", "AWS", "React", "FastAPI", "Power BI", "Statistics", "Leadership"];
const ROLE_SKILLS = {
  "AI Engineer": ["Python", "Generative AI", "NLP", "MLOps", "Docker", "AWS", "FastAPI"],
  "Data Scientist": ["Python", "SQL", "Machine Learning", "Statistics", "NLP", "Power BI"],
  "ML Engineer": ["Python", "Machine Learning", "MLOps", "Docker", "Kubernetes", "AWS"],
  "Full-Stack Developer": ["React", "SQL", "Docker", "AWS", "FastAPI", "Python"],
  "Data Analyst": ["SQL", "Python", "Power BI", "Statistics"],
  "Product Manager": ["Leadership", "SQL", "Statistics", "Power BI"]
};
const SKILL_ALIASES = {
  Python: ["python"], SQL: ["sql"], "Machine Learning": ["machine learning", "scikit-learn", "sklearn"],
  "Generative AI": ["generative ai", "large language model", "llm", "prompt engineering"], NLP: ["nlp", "natural language processing"],
  MLOps: ["mlops", "model deployment", "model monitoring"], Docker: ["docker"], Kubernetes: ["kubernetes", "k8s"],
  AWS: ["aws", "amazon web services"], React: ["react", "reactjs", "react.js"], FastAPI: ["fastapi"],
  "Power BI": ["power bi", "powerbi"], Statistics: ["statistics", "statistical analysis"], Leadership: ["leadership", "mentored", "stakeholder management"]
};
const MODEL_LABELS = { linear: "Linear Regression", decision_tree: "Decision Tree", random_forest: "Random Forest", gradient_boosting: "Gradient Boosting", neural_network: "Neural Network" };
const MODEL_ORDER = ["linear", "decision_tree", "random_forest", "gradient_boosting", "neural_network"];

const state = { username: "", authMode: "login", resumeSkills: [], ats: 0, roleMatch: 0, lastProfile: null, prediction: null };
const $ = (id) => document.getElementById(id);
const formatLpa = (value) => `Rs. ${Number(value).toFixed(1)} LPA`;
const escapeRegex = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 2800);
}

function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll(".auth-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.auth === mode));
  $("loginCopy").classList.toggle("hidden", mode !== "login");
  $("signupCopy").classList.toggle("hidden", mode !== "signup");
  $("authSubmit").textContent = mode === "login" ? "Sign in" : "Create account";
  $("passwordInput").autocomplete = mode === "login" ? "current-password" : "new-password";
  $("authSwitch").innerHTML = mode === "login"
    ? 'New to Skill2Salary? <button type="button" data-switch-auth="signup">Create an account</button>'
    : 'Already have an account? <button type="button" data-switch-auth="login">Sign in</button>';
  $("authError").textContent = "";
}

function showDashboard(username, profile = {}) {
  state.username = username;
  $("authView").classList.add("hidden");
  $("dashboardView").classList.remove("hidden");
  $("chatWidget").classList.remove("hidden");
  $("sidebarUser").textContent = username;
  $("userAvatar").textContent = username.charAt(0).toUpperCase();
  $("welcomeText").textContent = `Welcome back, ${username}. Build a clearer path from your skills to your salary.`;
  if (Object.keys(profile).length) restoreProfile(profile);
  renderRoadmap();
}

function restoreProfile(profile) {
  const fieldMap = { role: "roleInput", experience: "experienceInput", education: "educationInput", city: "cityInput", industry: "industryInput", current_lpa: "currentLpaInput" };
  Object.entries(fieldMap).forEach(([key, id]) => { if (profile[key] !== undefined) $(id).value = profile[key]; });
  document.querySelectorAll('#salarySkills input').forEach((input) => { input.checked = (profile.skills || []).includes(input.value); });
}

function navigate(panel) {
  document.querySelectorAll(".panel").forEach((node) => node.classList.remove("active-panel"));
  document.querySelectorAll(".nav-btn").forEach((node) => node.classList.toggle("active", node.dataset.panel === panel));
  $(panel).classList.add("active-panel");
  const titles = { overview: "Your career overview", resume: "Resume intelligence", salary: "Salary prediction lab", roadmap: "Your career roadmap" };
  $("pageTitle").textContent = titles[panel];
  document.querySelector(".sidebar").classList.remove("open");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (panel === "roadmap") renderRoadmap();
}

function populateControls() {
  $("roleInput").innerHTML = ROLES.map((role) => `<option>${role}</option>`).join("");
  const skillChecks = SKILLS.map((skill) => `<label class="check-pill"><input type="checkbox" value="${skill}" /><span>${skill}</span></label>`).join("");
  $("salarySkills").innerHTML = skillChecks;
  $("whatIfSkills").innerHTML = skillChecks;
}

function extractSkills(text) {
  const clean = text.toLowerCase();
  return Object.entries(SKILL_ALIASES).filter(([, aliases]) => aliases.some((alias) => new RegExp(`(^|[^a-z0-9])${escapeRegex(alias)}([^a-z0-9]|$)`, "i").test(clean))).map(([skill]) => skill);
}

function scoreResume(text, skills) {
  const checks = [
    { weight: 12, pass: /[\w.+-]+@[\w.-]+\.[a-z]{2,}/i.test(text), tip: "Add a professional email address." },
    { weight: 10, pass: /linkedin\.com|github\.com|portfolio/i.test(text), tip: "Add LinkedIn, GitHub, or portfolio links." },
    { weight: 14, pass: /\b\d+(?:\.\d+)?%|rs\.?|inr|\$|\b\d+\+\b/i.test(text), tip: "Quantify achievements with percentages, scale, time, or revenue." },
    { weight: 12, pass: /experience|employment|work history|internship/i.test(text), tip: "Add a clearly labelled experience section." },
    { weight: 12, pass: /project|case study|application|platform/i.test(text), tip: "Include relevant projects with links and outcomes." },
    { weight: 14, pass: /improved|reduced|increased|built|launched|designed|led|automated/i.test(text), tip: "Start bullets with strong action verbs." },
    { weight: 14, pass: skills.length >= 5, tip: "Add a focused technical skills section with at least five relevant skills." },
    { weight: 12, pass: text.trim().split(/\s+/).length >= 90, tip: "Add enough evidence: responsibilities, decisions, tools, and results." }
  ];
  return { score: checks.filter((item) => item.pass).reduce((sum, item) => sum + item.weight, 0), tips: checks.filter((item) => !item.pass).map((item) => item.tip) };
}

function analyzeResume() {
  const text = $("resumeText").value.trim();
  if (text.length < 40) { toast("Please add more resume content before analysis."); return; }
  state.resumeSkills = extractSkills(text);
  const result = scoreResume(text, state.resumeSkills);
  state.ats = result.score;
  const role = $("roleInput").value;
  const required = ROLE_SKILLS[role];
  state.roleMatch = Math.round(required.filter((skill) => state.resumeSkills.includes(skill)).length / required.length * 100);
  $("atsScore").textContent = state.ats;
  $("atsRing").style.strokeDashoffset = 314 - 3.14 * state.ats;
  $("roleMatch").textContent = `${state.roleMatch}%`;
  $("resumeStatus").textContent = state.ats >= 75 ? "Strong foundation" : state.ats >= 55 ? "Good start" : "Needs attention";
  $("skillSummary").textContent = `${state.resumeSkills.length} skills found for your profile.`;
  $("skillCloud").innerHTML = state.resumeSkills.length ? state.resumeSkills.map((skill) => `<span>${skill}</span>`).join("") : '<span class="empty-chip">No catalog skills detected</span>';
  const missing = required.filter((skill) => !state.resumeSkills.includes(skill));
  const tips = [...result.tips.slice(0, 4), ...(missing.length ? [`Build evidence for role-critical skills: ${missing.slice(0, 3).join(", ")}.`] : ["Your core role skills are present. Strengthen ownership and business-impact language."] )];
  $("resumeTips").innerHTML = tips.map((tip, index) => `<div class="tip-item"><span>${String(index + 1).padStart(2, "0")}</span><p>${tip}</p></div>`).join("");
  document.querySelectorAll('#salarySkills input').forEach((input) => { if (state.resumeSkills.includes(input.value)) input.checked = true; });
  renderRoadmap();
  toast("Resume analysis complete.");
}

function salaryProfile(extraSkills = []) {
  const selected = [...document.querySelectorAll('#salarySkills input:checked')].map((input) => input.value);
  return {
    role: $("roleInput").value,
    experience: Number($("experienceInput").value),
    education: $("educationInput").value,
    city: $("cityInput").value,
    industry: $("industryInput").value,
    current_lpa: Number($("currentLpaInput").value),
    resume_score: state.ats || 55,
    skills: [...new Set([...selected, ...extraSkills])]
  };
}

async function predictSalary(event) {
  event.preventDefault();
  const button = event.submitter || $("salaryForm").querySelector('button[type="submit"]');
  button.disabled = true; button.textContent = "Running ML models..."; $("predictionError").textContent = "";
  try {
    state.lastProfile = salaryProfile();
    state.prediction = await api("/api/predict", { method: "POST", body: JSON.stringify(state.lastProfile) });
    renderPrediction(state.prediction);
    toast("Linear Regression, Decision Tree, Random Forest, Neural Network, and Ensemble predictions are ready.");
  } catch (error) { $("predictionError").textContent = error.message; }
  finally { button.disabled = false; button.textContent = "Generate salary prediction"; }
}

function modelCards(result) {
  const cards = MODEL_ORDER.map((name) => `
    <div class="model-card">
      <small>${MODEL_LABELS[name]}</small>
      <strong>${formatLpa(result.predictions[name])}</strong>
      <span>Weight ${Math.round(result.weights[name] * 100)}% | R2 ${result.metrics[name].r2}</span>
    </div>`).join("");
  return `${cards}
    <div class="model-card ensemble-mini">
      <small>Final Weighted Ensemble</small>
      <strong>${formatLpa(result.ensemble_lpa)}</strong>
      <span>Shown as the final salary to users</span>
    </div>`;
}

function renderPrediction(result) {
  $("salaryResults").innerHTML = `
    <article class="glass card prediction-card">
      <div class="card-head"><div><p class="eyebrow">FINAL ENSEMBLE ESTIMATE</p><h4>Estimated annual salary</h4></div><span class="confidence">${result.confidence}% confidence</span></div>
      <div class="gauge-wrap"><canvas id="salaryGauge" width="440" height="250"></canvas><div class="gauge-value"><strong>${formatLpa(result.ensemble_lpa)}</strong><span>Expected range ${formatLpa(result.range[0])} - ${formatLpa(result.range[1])}</span></div></div>
    </article>
    <article class="glass card model-visible-card">
      <div class="card-head"><div><p class="eyebrow">MODEL PREDICTIONS</p><h4>Linear Regression, Decision Tree, Random Forest, Gradient Boosting, Neural Network</h4></div><span>Final = Ensemble</span></div>
      <div class="model-card-grid">${modelCards(result)}</div>
    </article>
    <article class="glass card"><div class="card-head"><h4>Career insights</h4><span>Based on your profile</span></div><div class="insight-list">${result.insights.map((item) => `<div><span>+</span><p>${item}</p></div>`).join("")}</div></article>
    <article class="glass card"><div class="card-head"><h4>Top skills to increase salary</h4><span>Modeled uplift</span></div><div class="uplift-list">${result.top_skills.length ? result.top_skills.map((item) => `<div><span>${item.skill}</span><strong>+${item.impact_lpa.toFixed(1)} LPA</strong></div>`).join("") : '<p class="muted">You already cover the core role skill set.</p>'}</div></article>`;
  $("analysisArea").classList.remove("hidden");
  $("dataDisclaimer").textContent = result.disclaimer;
  renderWhatIfOptions(result.top_skills);
  requestAnimationFrame(() => {
    drawGauge("salaryGauge", result.ensemble_lpa, result.range);
    drawLineChart("growthChart", result.growth, ["Now", "Y1", "Y2", "Y3", "Y4", "Y5"], "#8b5cf6");
    drawBarChart("skillChart", result.top_skills.map((item) => item.impact_lpa), result.top_skills.map((item) => item.skill), "#22d3ee");
    renderAdvanced(result);
  });
}

function renderWhatIfOptions(topSkills) {
  const suggested = new Set(topSkills.map((item) => item.skill));
  document.querySelectorAll('#whatIfSkills input').forEach((input) => {
    input.checked = false;
    input.closest("label").classList.toggle("recommended", suggested.has(input.value));
    input.disabled = state.lastProfile.skills.includes(input.value);
  });
  $("whatIfResult").classList.add("hidden");
}

async function runWhatIf() {
  const selected = [...document.querySelectorAll('#whatIfSkills input:checked')].map((input) => input.value);
  if (!selected.length) { toast("Select at least one new skill."); return; }
  const button = $("whatIfBtn"); button.disabled = true; button.textContent = "Calculating...";
  try {
    const future = await api("/api/what-if", { method: "POST", body: JSON.stringify(salaryProfile(selected)) });
    const increase = future.ensemble_lpa - state.prediction.ensemble_lpa;
    $("whatIfResult").innerHTML = `<div><span>Current estimate</span><strong>${formatLpa(state.prediction.ensemble_lpa)}</strong></div><span class="change-arrow">to</span><div><span>After new skills</span><strong>${formatLpa(future.ensemble_lpa)}</strong></div><b class="uplift-badge">${increase >= 0 ? "+" : ""}${increase.toFixed(1)} LPA</b>`;
    $("whatIfResult").classList.remove("hidden");
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "Calculate future salary"; }
}

function renderAdvanced(result) {
  const names = MODEL_ORDER.filter((name) => result.predictions[name] !== undefined);
  const values = names.map((name) => result.predictions[name]);
  drawBarChart("modelChart", [...values, result.ensemble_lpa], [...names.map((name) => MODEL_LABELS[name]), "Ensemble"], "#8b5cf6");
  $("modelTable").innerHTML = `<table><thead><tr><th>Model</th><th>Prediction</th><th>Weight</th><th>MAE</th><th>RMSE</th><th>R2</th></tr></thead><tbody>${names.map((name) => `<tr><td>${MODEL_LABELS[name]}</td><td>${formatLpa(result.predictions[name])}</td><td>${Math.round(result.weights[name] * 100)}%</td><td>${result.metrics[name].mae}</td><td>${result.metrics[name].rmse}</td><td>${result.metrics[name].r2}</td></tr>`).join("")}<tr class="ensemble-row"><td>Weighted Ensemble</td><td>${formatLpa(result.ensemble_lpa)}</td><td>100%</td><td colspan="3">Final user prediction</td></tr></tbody></table>`;
}

function canvasContext(id) {
  const canvas = $(id); const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height); return { canvas, ctx };
}

function drawGauge(id, value, range) {
  const { canvas, ctx } = canvasContext(id); const cx = canvas.width / 2; const cy = 220; const radius = 170;
  ctx.lineCap = "round"; ctx.lineWidth = 25; ctx.strokeStyle = "rgba(148,163,184,.14)"; ctx.beginPath(); ctx.arc(cx, cy, radius, Math.PI, 0); ctx.stroke();
  const max = Math.max(40, range[1] * 1.25); const end = Math.PI + Math.min(1, value / max) * Math.PI;
  const grad = ctx.createLinearGradient(50, 0, 390, 0); grad.addColorStop(0, "#8b5cf6"); grad.addColorStop(1, "#22d3ee"); ctx.strokeStyle = grad; ctx.beginPath(); ctx.arc(cx, cy, radius, Math.PI, end); ctx.stroke();
  ctx.fillStyle = "#94a3b8"; ctx.font = "13px Segoe UI"; ctx.fillText("0", 37, 235); ctx.fillText(`${Math.round(max)} LPA`, 350, 235);
}

function drawLineChart(id, values, labels, color) {
  const { canvas, ctx } = canvasContext(id); const pad = 48; const min = Math.min(...values) * .9; const max = Math.max(...values) * 1.08;
  ctx.font = "13px Segoe UI"; ctx.strokeStyle = "rgba(148,163,184,.14)"; ctx.fillStyle = "#94a3b8";
  for (let i = 0; i < 5; i++) { const y = pad + i * (canvas.height - 2 * pad) / 4; ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(canvas.width - pad, y); ctx.stroke(); }
  const points = values.map((value, i) => ({ x: pad + i * (canvas.width - 2 * pad) / (values.length - 1), y: canvas.height - pad - (value - min) / (max - min) * (canvas.height - 2 * pad) }));
  const grad = ctx.createLinearGradient(0, 0, canvas.width, 0); grad.addColorStop(0, color); grad.addColorStop(1, "#22d3ee"); ctx.strokeStyle = grad; ctx.lineWidth = 4; ctx.beginPath(); points.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.stroke();
  points.forEach((p, i) => { ctx.fillStyle = "#080a12"; ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.fillStyle = "#94a3b8"; ctx.fillText(labels[i], p.x - 12, canvas.height - 14); ctx.fillStyle = "#e2e8f0"; ctx.fillText(values[i].toFixed(1), p.x - 12, p.y - 13); });
}

function drawBarChart(id, values, labels, color) {
  const { canvas, ctx } = canvasContext(id); if (!values.length) { ctx.fillStyle = "#94a3b8"; ctx.font = "15px Segoe UI"; ctx.fillText("No missing skills to visualize.", 30, 60); return; }
  const pad = 48; const max = Math.max(...values) * 1.22; const slot = (canvas.width - 2 * pad) / values.length; const bar = Math.min(74, slot * .58);
  values.forEach((value, i) => { const height = value / max * (canvas.height - 110); const x = pad + i * slot + (slot - bar) / 2; const y = canvas.height - 55 - height; const grad = ctx.createLinearGradient(0, y, 0, canvas.height); grad.addColorStop(0, color); grad.addColorStop(1, "#3b82f6"); ctx.fillStyle = grad; roundRect(ctx, x, y, bar, height, 8); ctx.fill(); ctx.fillStyle = "#e2e8f0"; ctx.font = "13px Segoe UI"; ctx.textAlign = "center"; ctx.fillText(value.toFixed(1), x + bar / 2, y - 10); ctx.fillStyle = "#94a3b8"; const label = labels[i].length > 15 ? `${labels[i].slice(0, 13)}...` : labels[i]; ctx.fillText(label, x + bar / 2, canvas.height - 24); }); ctx.textAlign = "start";
}

function roundRect(ctx, x, y, width, height, radius) { ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); }

function renderRoadmap() {
  const role = $("roleInput")?.value || "AI Engineer"; const current = new Set(state.resumeSkills); const missing = ROLE_SKILLS[role].filter((skill) => !current.has(skill));
  const steps = [
    ["Days 01-15", missing[0] || "Profile positioning", `Learn the foundations of ${missing[0] || role} and define one measurable project outcome.`],
    ["Days 16-35", missing[1] || "Portfolio evidence", `Build a practical ${missing[1] || "portfolio"} feature and document your decisions and tradeoffs.`],
    ["Days 36-60", missing[2] || "Resume refinement", "Rewrite resume bullets with action, technical method, scale, and measurable outcome."],
    ["Days 61-90", "Market execution", `Publish the case study, practice ${role} interviews, and track applications and callbacks weekly.`]
  ];
  $("roadmapList").innerHTML = steps.map((step, index) => `<article class="glass roadmap-item"><span>${String(index + 1).padStart(2, "0")}</span><div><small>${step[0]}</small><h4>${step[1]}</h4><p>${step[2]}</p></div><b>${index === 0 ? "Start here" : "Next"}</b></article>`).join("");
}

function initNetwork() {
  const canvas = $("network"), ctx = canvas.getContext("2d");
  const nodeCount = Math.min(95, Math.max(58, Math.floor(innerWidth / 18)));
  const nodes = Array.from({ length: nodeCount }, (_, i) => ({
    x: Math.random(), y: Math.random(),
    vx: (Math.random() - .5) * .00085, vy: (Math.random() - .5) * .00085,
    size: i % 7 === 0 ? 2.4 : 1.3
  }));
  let pointer = { x: .5, y: .5 };
  function resize() { canvas.width = innerWidth * devicePixelRatio; canvas.height = innerHeight * devicePixelRatio; }
  addEventListener("resize", resize); resize();
  addEventListener("pointermove", (event) => { pointer = { x: event.clientX / innerWidth, y: event.clientY / innerHeight }; });
  function frame() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const bg = ctx.createRadialGradient(pointer.x * w, pointer.y * h, 0, pointer.x * w, pointer.y * h, Math.max(w, h) * .7);
    bg.addColorStop(0, "rgba(34,211,238,.09)");
    bg.addColorStop(0.4, "rgba(139,92,246,.04)");
    bg.addColorStop(1, "rgba(7,8,16,0)");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
    nodes.forEach((n) => {
      n.x += n.vx + (pointer.x - .5) * .00003; n.y += n.vy + (pointer.y - .5) * .00003;
      if (n.x < 0 || n.x > 1) n.vx *= -1;
      if (n.y < 0 || n.y > 1) n.vy *= -1;
    });
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i], ax = a.x * w, ay = a.y * h;
      ctx.fillStyle = i % 9 === 0 ? "rgba(196,181,253,.85)" : "rgba(103,232,249,.62)";
      ctx.beginPath(); ctx.arc(ax, ay, a.size * devicePixelRatio, 0, Math.PI * 2); ctx.fill();
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j], bx = b.x * w, by = b.y * h, d = Math.hypot(ax - bx, ay - by);
        if (d < 165 * devicePixelRatio) {
          ctx.strokeStyle = `rgba(34,211,238,${(1 - d / (165 * devicePixelRatio)) * .14})`;
          ctx.lineWidth = .8 * devicePixelRatio; ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
        }
      }
    }
    requestAnimationFrame(frame);
  }
  frame();
}

function appendChat(role, message) {
  const node = document.createElement("div");
  node.className = role === "user" ? "user-message" : "bot-message";
  node.textContent = message;
  $("chatMessages").appendChild(node);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
}

async function askSalarAI(message) {
  appendChat("user", message);
  const thinking = document.createElement("div");
  thinking.className = "bot-message typing";
  thinking.textContent = "SalarAI Guide is thinking...";
  $("chatMessages").appendChild(thinking);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  try {
    const reply = await api("/api/chat", { method: "POST", body: JSON.stringify({ message }) });
    thinking.remove();
    appendChat("bot", reply.answer);
    if (reply.suggestions?.length) {
      const chips = document.createElement("div");
      chips.className = "chat-suggestions inline";
      chips.innerHTML = reply.suggestions.map((item) => `<button type="button">${item}</button>`).join("");
      $("chatMessages").appendChild(chips);
    }
  } catch (error) {
    thinking.remove();
    appendChat("bot", error.message);
  }
}

function bindChat() {
  $("chatWidget").classList.add("hidden");
  $("chatToggle").addEventListener("click", () => $("chatPanel").classList.toggle("hidden"));
  $("chatClose").addEventListener("click", () => $("chatPanel").classList.add("hidden"));
  $("chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = $("chatInput").value.trim();
    if (!message) return;
    $("chatInput").value = "";
    await askSalarAI(message);
  });
  document.addEventListener("click", async (event) => {
    const chip = event.target.closest(".chat-suggestions button");
    if (chip) await askSalarAI(chip.textContent.trim());
  });
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    const authTab = event.target.closest("[data-auth]"); if (authTab) setAuthMode(authTab.dataset.auth);
    const authSwitch = event.target.closest("[data-switch-auth]"); if (authSwitch) setAuthMode(authSwitch.dataset.switchAuth);
    const jump = event.target.closest("[data-panel]"); if (jump) navigate(jump.dataset.panel);
  });
  $("authForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const button = $("authSubmit"); button.disabled = true; button.textContent = state.authMode === "login" ? "Signing in..." : "Creating account..."; $("authError").textContent = "";
    try { const data = await api(`/api/${state.authMode}`, { method: "POST", body: JSON.stringify({ username: $("usernameInput").value.trim(), password: $("passwordInput").value }) }); showDashboard(data.username); toast(state.authMode === "login" ? "Welcome back." : "Your account is ready."); }
    catch (error) { $("authError").textContent = error.message; }
    finally { button.disabled = false; button.textContent = state.authMode === "login" ? "Sign in" : "Create account"; }
  });
  $("togglePassword").addEventListener("click", () => { const visible = $("passwordInput").type === "text"; $("passwordInput").type = visible ? "password" : "text"; $("togglePassword").textContent = visible ? "Show" : "Hide"; });
  $("logoutBtn").addEventListener("click", async () => { await api("/api/logout", { method: "POST", body: "{}" }); location.reload(); });
  $("mobileMenu").addEventListener("click", () => document.querySelector(".sidebar").classList.toggle("open"));
  $("sampleBtn").addEventListener("click", () => { $("resumeText").value = "AI Engineer with 3 years of experience building Python and FastAPI services. Built a Generative AI support assistant that reduced resolution time by 32%. Deployed Docker services on AWS and implemented model monitoring. GitHub: github.com/arjun/portfolio Email: arjun@example.com. Mentored two interns and collaborated with product stakeholders."; });
  $("resumeFile").addEventListener("change", async (event) => { const file = event.target.files[0]; if (file) $("resumeText").value = await file.text(); });
  $("analyzeBtn").addEventListener("click", analyzeResume);
  $("roleInput").addEventListener("change", () => { if (state.resumeSkills.length) analyzeResume(); renderRoadmap(); });
  $("salaryForm").addEventListener("submit", predictSalary);
  $("whatIfBtn").addEventListener("click", runWhatIf);
  bindChat();
}

async function init() {
  populateControls(); bindEvents(); initNetwork();
  try { const me = await api("/api/me"); showDashboard(me.username, me.profile || {}); }
  catch { $("authView").classList.remove("hidden"); }
}

init();
