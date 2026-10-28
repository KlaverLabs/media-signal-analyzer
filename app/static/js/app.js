(() => {
const B = window.BOOT;
const $ = id => document.getElementById(id);
const ICON = {"Observed": "🔴", "Not observed": "🟢", "Cannot assess": "⚪"};
const SCORE_COL = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ea580c", 5: "#dc2626"};
// DOM is built with textContent only: model output and source text are never injected as HTML.
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }

let report = null, selected = null, barChart = null, donutChart = null, printing = false;
const shown = new Set(Object.keys(ICON));

/* ---------- tabs ---------- */
function showTab(name) {
  for (const t of ["analyzer", "trace"]) {
    $(`${t}-panel`).classList.toggle("hidden", t !== name);
    $(`tab-${t}`).setAttribute("aria-selected", String(t === name));
  }
  history.replaceState(null, "", "#" + name);
  if (name === "analyzer" && report) { barChart && barChart.resize(); donutChart && donutChart.resize(); }
}
document.querySelectorAll("[data-tab]").forEach(b => b.onclick = () => showTab(b.dataset.tab));

/* ---------- gauge ---------- */
const CX = 170, CY = 160, R = 115;
const pt = (v, r) => { const a = Math.PI * (1 - v / 100); return [CX + r * Math.cos(a), CY - r * Math.sin(a)]; };
const arc = (v0, v1, r) => { const [x0, y0] = pt(v0, r), [x1, y1] = pt(v1, r); return `M${x0.toFixed(1)} ${y0.toFixed(1)} A${r} ${r} 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`; };
function svg(tag, attrs, text) { const e = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text) e.textContent = text; return e; }
(function drawGauge() {
  const g = $("gauge-static");
  [["Low", 0, "var(--c-low)"], ["Moderate", 25, "var(--c-mod)"], ["Elevated", 50, "var(--c-elev)"], ["High", 75, "var(--c-high)"]].forEach(([label, v, col]) => {
    g.append(svg("path", {d: arc(v, v + 25, R), class: "gauge-band", stroke: col}));
    const [x, y] = pt(v + 12.5, R); g.append(svg("text", {x: x.toFixed(1), y: (y + 3).toFixed(1), class: "gauge-band-label"}, label));
  });
  [0, 25, 50, 75, 100].forEach(v => {
    const [x0, y0] = pt(v, R + 13), [x1, y1] = pt(v, R + 21), [tx, ty] = pt(v, R + 33);
    g.append(svg("line", {x1: x0, y1: y0, x2: x1, y2: y1, stroke: "var(--muted)", "stroke-width": 2}));
    g.append(svg("text", {x: tx.toFixed(1), y: (ty + 3).toFixed(1), class: "gauge-text"}, String(v)));
  });
})();
function setGauge(value) {
  const n = $("needle"), t = $("gauge-value");
  if (value == null) { n.classList.add("off"); t.textContent = "—"; return; }
  n.classList.remove("off");
  requestAnimationFrame(() => { n.style.transform = `rotate(${-90 + value * 1.8}deg)`; });
  t.textContent = value.toFixed(1);
}

/* ---------- charts ---------- */
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function drawCharts() {
  barChart && barChart.destroy(); donutChart && donutChart.destroy();
  const ink = css("--ink"), grid = css("--line"), anim = printing ? false : undefined;
  const r = report.results;
  barChart = new Chart($("bar"), {
    type: "bar",
    data: {labels: r.map(x => `${x.id}. ${x.name.split(" /")[0].slice(0, 26)}`),
      datasets: [{data: r.map(x => x.score), borderWidth: r.map(x => x.id === selected ? 3 : 0), borderColor: ink,
        backgroundColor: r.map(x => x.score == null ? "#94a3b8" : SCORE_COL[x.score])}]},
    options: {indexAxis: "y", maintainAspectRatio: false, animation: anim, plugins: {legend: {display: false},
        tooltip: {callbacks: {label: c => { const x = r[c.dataIndex]; return x.score == null ? "Cannot assess (not scored)" : `Score ${x.score}/5 — ${x.status}`; }}}},
      scales: {x: {min: 0, max: 5, ticks: {stepSize: 1, color: ink}, grid: {color: grid}}, y: {ticks: {color: ink, font: {size: 10}}, grid: {display: false}}},
      onClick: (_, els) => { if (els.length) select(r[els[0].index].id, true); },
      onHover: (e, els) => { e.native.target.style.cursor = els.length ? "pointer" : "default"; }}
  });
  donutChart = new Chart($("donut"), {
    type: "doughnut",
    data: {labels: ["Observed", "Not observed", "Cannot assess"],
      datasets: [{data: [report.observed_count, report.not_observed_count, report.cannot_assess_count],
        backgroundColor: ["#dc2626", "#22c55e", "#94a3b8"], borderColor: css("--card")}]},
    options: {maintainAspectRatio: false, animation: anim, plugins: {legend: {position: "bottom", labels: {color: ink}}}}
  });
}

/* ---------- source view + selection ---------- */
function renderSource() {
  const s = $("source"), t = report.text, r = report.results.find(x => x.id === selected);
  s.replaceChildren();
  if (r && r.quote_verified) {
    s.append(document.createTextNode(t.slice(0, r.quote_start)));
    const m = el("mark", "", t.slice(r.quote_start, r.quote_end)); s.append(m);
    s.append(document.createTextNode(t.slice(r.quote_end)));
    $("src-note").textContent = `Highlighting evidence for #${r.id} ${r.name}`;
    m.scrollIntoView({block: "center", behavior: "smooth"});
  } else {
    s.textContent = t;
    $("src-note").textContent = r ? `#${r.id} ${r.name}: no supporting quote (${r.status}).` : "Select a finding to highlight its supporting quote.";
  }
}
function select(id, scrollCard) {
  selected = id;
  document.querySelectorAll(".ind-card").forEach(c => c.classList.toggle("active", Number(c.dataset.id) === id));
  if (scrollCard) { const c = document.querySelector(`.ind-card[data-id="${id}"]`); c && c.scrollIntoView({block: "nearest", behavior: "smooth"}); }
  drawCharts(); renderSource();
}

/* ---------- render report ---------- */
function renderCards() {
  const box = $("cards"); box.replaceChildren();
  report.results.filter(r => shown.has(r.status)).forEach(r => {
    const c = el("article", `card ind-card st-${r.status.replace(" ", "-")}`); c.dataset.id = r.id; c.tabIndex = 0;
    if (r.id === selected) c.classList.add("active");
    const head = el("div", "flex justify-between gap-2");
    head.append(el("b", "text-sm", `${ICON[r.status]} ${r.id}. ${r.name}`), el("span", "badge", r.score == null ? r.status : `${r.status} · ${r.score}/5`));
    c.append(head);
    if (r.quote) c.append(el("blockquote", "quote", r.quote));
    const p1 = el("p", "text-sm mt-1"), p2 = el("p", "text-xs muted mt-1");
    p1.append(el("b", "", "Rationale: "), document.createTextNode(r.rationale));
    p2.append(el("b", "", "Missing context: "), document.createTextNode(r.missing_context));
    c.append(p1, p2);
    c.onclick = () => select(r.id, false);
    c.onkeydown = e => { if (e.key === "Enter") select(r.id, false); };
    box.append(c);
  });
}
function renderFilters() {
  const f = $("filters"); f.replaceChildren();
  Object.keys(ICON).forEach(s => {
    const l = el("label", "flex items-center gap-1"), cb = el("input"); cb.type = "checkbox"; cb.checked = shown.has(s);
    cb.onchange = () => { cb.checked ? shown.add(s) : shown.delete(s); renderCards(); };
    l.append(cb, document.createTextNode(`${ICON[s]} ${s}`)); f.append(l);
  });
}
function renderReport(r) {
  report = r; selected = null;
  $("results").classList.remove("hidden");
  const eng = $("engine"); eng.textContent = r.engine_label; eng.className = "badge " + (r.engine === "llm" ? "badge-llm" : "badge-fallback");
  $("model").textContent = r.model ? `model: ${r.model}` : "";
  $("assessed").textContent = `${r.assessed_count}/20 indicators assessed · avg score ${r.average_score ?? "n/a"}`;
  const w = $("warnings"); w.replaceChildren(); r.warnings.forEach(x => w.append(el("div", "banner banner-warn mb-2", x)));
  const ins = $("insufficient"); ins.classList.toggle("hidden", !r.insufficient_context);
  ins.textContent = r.banner ? `${r.banner} (only ${r.assessed_count} of 20 indicators could be assessed; at least 3 are required).` : "";
  $("band").textContent = r.band ? `Band: ${r.band}` : "Index not calculated";
  setGauge(r.intensity_index);
  renderFilters(); renderCards(); drawCharts(); renderSource();
  $("results").scrollIntoView({behavior: "smooth", block: "start"});
}

/* ---------- analyze ---------- */
function showMsg(kind, text) {
  const m = $("msg"); m.textContent = text; m.className = "banner mt-4 " + (kind === "warn" ? "banner-warn" : "banner-err");
}
async function runAnalysis() {
  const go = $("go"); go.disabled = true; go.textContent = "Analyzing…"; $("msg").classList.add("hidden");
  try {
    const res = await fetch("/api/analyze", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: $("url").value, text: $("text").value, force_fallback: $("force").checked})});
    const data = await res.json();
    if (!res.ok) { showMsg(res.status === 422 ? "warn" : "err", typeof data.detail === "string" ? data.detail : "Invalid request."); return; }
    renderReport(data);
  } catch (e) { showMsg("err", "Network error: " + e.message); }
  finally { go.disabled = false; go.textContent = "Analyze"; }
}
$("form-card").onsubmit = e => { e.preventDefault(); runAnalysis(); };
$("sample").onclick = () => { $("text").value = B.sample; $("url").value = ""; };

/* ---------- exports ---------- */
function toMarkdown(r) {
  const L = [`# Signal Analysis Report`, ``, `- ${r.engine_label}${r.model ? ` (${r.model})` : ""}`,
    `- Signal Intensity Index: ${r.intensity_index ?? "not calculated"}${r.band ? ` (${r.band})` : ""}`,
    `- Assessed: ${r.assessed_count}/20 · Observed ${r.observed_count} · Not observed ${r.not_observed_count} · Cannot assess ${r.cannot_assess_count}`];
  if (r.banner) L.push(`- **${r.banner}**`);
  L.push(``, `> ${r.gauge_disclaimer}`, `> ${r.disclaimer}`, ``);
  r.results.forEach(x => {
    L.push(`## ${x.id}. ${x.name} — ${x.status}${x.score != null ? ` (${x.score}/5)` : ""}`);
    if (x.quote) L.push(`> "${x.quote}"`);
    L.push(`- Rationale: ${x.rationale}`, `- Missing context: ${x.missing_context}`, ``);
  });
  return L.join("\n");
}
$("dl-json").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: "application/json"}));
  a.download = "signal_report.json"; a.click(); URL.revokeObjectURL(a.href);
};
$("copy-md").onclick = async e => {
  const b = e.target; try { await navigator.clipboard.writeText(toMarkdown(report)); b.textContent = "Copied ✓"; }
  catch { b.textContent = "Copy failed"; } setTimeout(() => b.textContent = "Copy Markdown", 1500);
};
$("print").onclick = () => window.print();
// Print always uses the light palette; charts are redrawn without animation so they are fully rendered.
window.addEventListener("beforeprint", () => { printing = true; document.documentElement.classList.add("printing"); if (report) drawCharts(); });
window.addEventListener("afterprint", () => { printing = false; document.documentElement.classList.remove("printing"); if (report) drawCharts(); });

/* ---------- TraceCheck ---------- */
(function trace() {
  $("post-text").textContent = B.claim;
  const total = B.stages.reduce((n, s) => n + s.questions.length, 0);
  $("total").textContent = total;
  const acc = $("accordion"); let checked = 0;
  B.stages.forEach((s, idx) => {
    const wrap = el("div"), btn = el("button", "acc-btn"), node = el("span", "node", String(idx + 1));
    const label = el("span"); label.append(el("b", "", s.title), el("br"), el("span", "text-xs", s.summary));
    btn.append(node, label); btn.setAttribute("aria-expanded", "false");
    const panel = el("div", "acc-panel"); let done = 0;
    s.questions.forEach(q => {
      const l = el("label", "flex gap-2 items-start mb-1"), cb = el("input"); cb.type = "checkbox";
      cb.onchange = () => {
        const d = cb.checked ? 1 : -1; checked += d; done += d;
        node.classList.toggle("done", done === s.questions.length);
        $("progress").textContent = checked; $("bar-fill").style.width = `${checked / total * 100}%`;
      };
      l.append(cb, el("span", "", q)); panel.append(l);
    });
    btn.onclick = () => {
      const open = !panel.classList.contains("open");
      acc.querySelectorAll(".acc-panel").forEach(p => p.classList.remove("open"));
      acc.querySelectorAll(".acc-btn").forEach(b => b.setAttribute("aria-expanded", "false"));
      panel.classList.toggle("open", open); btn.setAttribute("aria-expanded", String(open));
    };
    wrap.append(btn, panel); acc.append(wrap);
  });
  $("progress").textContent = 0;

  const counter = $("reposts"); let n = 4821;
  const bump = k => { n += k; counter.textContent = n.toLocaleString("en-US"); counter.classList.remove("bump"); void counter.offsetWidth; counter.classList.add("bump"); };
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) setInterval(() => bump(1 + Math.floor(Math.random() * 6)), 2600);
  else counter.style.animation = "none";

  const ic = $("interceptor");
  $("repost-btn").onclick = () => ic.classList.add("open");
  $("hold").onclick = () => { ic.classList.remove("open"); $("toast").textContent = "✔ You held the post to verify first."; };
  $("share-anyway").onclick = () => {
    ic.classList.remove("open"); bump(1);
    $("toast").textContent = checked < total ? `Reposted with ${total - checked} of ${total} checks still unconsidered.` : "Reposted after working through every check.";
  };
  $("open-suite").onclick = () => { ic.classList.remove("open"); $("text").value = B.claim; $("url").value = ""; showTab("analyzer"); runAnalysis(); };
})();

showTab(location.hash === "#trace" ? "trace" : "analyzer");
})();
