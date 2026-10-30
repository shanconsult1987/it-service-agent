
"""Responsive executive dashboard with live refresh."""
import json
from app.dashboard import executive_dashboard


def render_dashboard():
    payload = json.dumps(
        executive_dashboard()
    ).replace("</", "<\\/")

    html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contoso | IT Service Agent Operations</title>
<style>
:root {
  color-scheme:dark;
  --bg:#08111f; --panel:#111d30; --panel2:#16263d;
  --ink:#eef5ff; --muted:#9eb0ca; --line:#293a54;
  --blue:#70b7ff; --green:#5fe0ad; --amber:#ffca73; --red:#ff858b;
}
* { box-sizing:border-box; }
body {
  margin:0; color:var(--ink);
  background:
    radial-gradient(ellipse at 10% 0%,#1b416b 0,transparent 35%),
    radial-gradient(ellipse at 100% 20%,#1b3151 0,transparent 30%),
    var(--bg);
  font:14px/1.5 "Segoe UI",Arial,sans-serif;
}
main { max-width:1400px; margin:auto; padding:28px 22px 45px; }
header { display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }
.brand { display:flex; align-items:center; gap:12px; }
.logo {
  width:45px;height:45px;display:grid;place-items:center;border-radius:14px;
  background:linear-gradient(135deg,#318bff,#64e1bd);color:#071421;font-weight:900;font-size:20px;
}
.eyebrow { color:var(--blue);font-size:11px;letter-spacing:.16em;font-weight:750; }
h1 { font-size:clamp(26px,4vw,38px); margin:4px 0; letter-spacing:-.04em; }
h2 { margin:0 0 12px; font-size:16px; }
h3 { margin:16px 0 8px; font-size:13px; }
p { margin:4px 0; color:var(--muted); }
.small,.label { font-size:12px;color:var(--muted); }
.actions { display:flex; gap:9px; align-items:center; flex-wrap:wrap; }
.pill { border:1px solid #2b5278;background:#122c47;color:#c6e4ff;padding:7px 10px;border-radius:99px;font-size:11px; }
button { background:#1a2d47;color:var(--ink);border:1px solid #324967;padding:9px 13px;border-radius:10px;cursor:pointer; }
button:hover { border-color:var(--blue); }
.grid { display:grid;gap:14px;margin-top:18px; }
.kpis { grid-template-columns:repeat(4,minmax(0,1fr)); }
.two { grid-template-columns:1.05fr .95fr; }
.three { grid-template-columns:repeat(3,minmax(0,1fr)); }
.card {
  min-width:0;padding:18px;border:1px solid var(--line);border-radius:17px;
  background:linear-gradient(145deg,#142239eF,#0f1929f2);
  box-shadow:0 14px 35px #0003;
}
.kpi { position:relative;overflow:hidden; }
.kpi:after { content:"";position:absolute;width:100px;height:100px;border-radius:50%;right:-35px;top:-45px;background:#70b7ff0e; }
.kpi .value { font-size:clamp(24px,3vw,34px);font-weight:800;letter-spacing:-.04em;margin:8px 0 2px;overflow-wrap:anywhere; }
.value { font-size:23px;font-weight:760;letter-spacing:-.03em; }
.green { color:var(--green); } .amber { color:var(--amber); } .red { color:var(--red); } .blue { color:var(--blue); }
.line { height:1px;background:var(--line);margin:12px 0; }
.rowline { display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line); }
.rowline:last-child { border-bottom:0; }
.tag { border:1px solid #334963;background:#20334a;color:#d3e5fa;border-radius:7px;padding:3px 7px;font-size:11px;white-space:nowrap; }
.bar { height:8px;border-radius:20px;background:#26374d;overflow:hidden;margin:10px 0 14px; }
.bar span { display:block;height:100%;width:0;background:linear-gradient(90deg,#4b9dff,#61e2b1);transition:width .5s ease; }
table { border-collapse:collapse;width:100%;font-size:12px; }
th,td { padding:9px 6px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere; }
th { color:var(--muted);font-weight:600; }
.event { padding:10px 0;border-bottom:1px solid var(--line); }
.event:last-child { border-bottom:0; }
.event-title { display:flex;justify-content:space-between;gap:12px; }
pre { white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.55 Consolas,monospace;color:#cbdcf3; }
footer { display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:20px;color:var(--muted);font-size:12px; }
a { color:var(--blue); }
@media(max-width:950px) { .kpis{grid-template-columns:repeat(2,minmax(0,1fr));}.two,.three{grid-template-columns:1fr;} }
@media(max-width:480px) { main{padding:18px 11px;}.card{padding:13px;} }
</style>
</head>
<body>
<main>
<header>
  <div class="brand">
    <div class="logo">C</div>
    <div>
      <div class="eyebrow">CONTOSO · OPERATIONS INTELLIGENCE</div>
      <h1>IT Service Agent</h1>
      <p>Governance, evaluation and live operational health</p>
    </div>
  </div>
  <div class="actions">
    <span class="pill" id="healthPill">CHECKING SERVICE</span>
    <button onclick="refreshDashboard()">↻ Refresh now</button>
  </div>
</header>

<div class="grid kpis">
  <section class="card kpi"><div class="label">HTTP requests</div><div class="value" id="requests">—</div><div class="small" id="requestScope">Current process</div></section>
  <section class="card kpi"><div class="label">HTTP error rate</div><div class="value" id="errorRate">—</div><div class="small" id="errorCount">Awaiting measurements</div></section>
  <section class="card kpi"><div class="label">Acceptance checks</div><div class="value" id="evaluationScore">—</div><div class="small" id="evaluationLabel">Authored acceptance cases</div></section>
  <section class="card kpi"><div class="label">p95 response latency</div><div class="value" id="latency">—</div><div class="small">Rolling retained sample</div></section>
</div>

<div class="grid two">
  <section class="card">
    <h2>Operational service pulse</h2>
    <p class="small">Process-local counters reset when the server restarts.</p>
    <div class="rowline"><span>Server started (UTC)</span><strong id="started">—</strong></div>
    <div class="rowline"><span>Average latency</span><strong id="averageLatency">—</strong></div>
    <div class="rowline"><span>Latency observations retained</span><strong id="latencySamples">—</strong></div>
    <div class="rowline"><span>Current warning signals</span><strong id="warningCount">—</strong></div>
    <div id="warningList"></div>
    <h3>Requests by endpoint</h3>
    <div id="endpointTable"></div>
    <h3>Responses by status</h3>
    <div id="statusTable"></div>
  </section>

  <section class="card">
    <h2>Guardrails and audit trail</h2>
    <p class="small">Recent local audit events, not a permanent all-time count.</p>
    <div class="three grid" style="margin-top:12px">
      <div><div class="label">Recent rejections</div><div class="value amber" id="rejections">—</div></div>
      <div><div class="label">Recent escalations</div><div class="value blue" id="escalations">—</div></div>
      <div><div class="label">Recent audit records</div><div class="value" id="auditEvents">—</div></div>
    </div>
    <div class="line"></div>
    <div class="rowline"><span>Description limit</span><strong id="descriptionLimit">—</strong></div>
    <div class="rowline"><span>Incident ID limit</span><strong id="incidentLimit">—</strong></div>
    <h3>Recent events</h3>
    <div id="auditList"></div>
  </section>
</div>

<div class="grid two">
  <section class="card">
    <h2>Evaluation scorecard</h2>
    <p class="small">Acceptance fixtures only. This is not training data or production model accuracy.</p>
    <div class="value" id="evaluationSummary">—</div>
    <div class="bar"><span id="evaluationBar"></span></div>
    <div id="evaluationTable"></div>
  </section>

  <section class="card">
    <h2>Responsible AI control register</h2>
    <p class="small">A declared status is not proof. Review the evidence required for each control.</p>
    <div class="value" id="controlSummary">—</div>
    <div class="bar"><span id="controlBar"></span></div>
    <div class="rowline"><span>Needs evidence</span><strong class="amber" id="needsEvidence">—</strong></div>
    <div class="rowline"><span>In review</span><strong id="inReview">—</strong></div>
    <div class="rowline"><span>Pass, declared</span><strong class="green" id="controlsPassed">—</strong></div>
    <div class="rowline"><span>Fail, declared</span><strong class="red" id="controlsFailed">—</strong></div>
    <div id="controlsTable"></div>
  </section>
</div>

<div class="grid two">
  <section class="card">
    <h2>Business value model</h2>
    <p class="small">Calculated from data/roi.json. These are assumptions until validated against measured outcomes.</p>
    <div class="three grid">
      <div><div class="label">Annual incidents</div><div class="value" id="annualIncidents">—</div></div>
      <div><div class="label">Estimated hours saved</div><div class="value" id="hoursSaved">—</div></div>
      <div><div class="label">Indicative ROI</div><div class="value" id="roi">—</div></div>
    </div>
    <div class="line"></div>
    <div class="rowline"><span>Estimated annual benefit</span><strong id="annualBenefit">—</strong></div>
    <div class="rowline"><span>Estimated annual cost</span><strong id="annualCost">—</strong></div>
    <div class="rowline"><span>Estimated net benefit</span><strong id="netBenefit">—</strong></div>
    <p class="small" id="roiBasis"></p>
  </section>

  <section class="card">
    <h2>Latest persisted agent state</h2>
    <p class="small">Current values read from the existing Day 2 state file.</p>
    <pre id="latestState">Loading…</pre>
    <div class="line"></div>
    <h3>Monitoring scope and caveats</h3>
    <p class="small" id="scopeText">—</p>
    <p class="small">Local audit JSONL is not tamper-proof. Production needs central logging, access control, retention and alert routing.</p>
  </section>
</div>

<footer>
  <span id="updated">Waiting for first refresh…</span>
  <span><a href="https://github.com/microsoft/responsible-ai-toolbox" target="_blank" rel="noreferrer">Microsoft Responsible AI Toolbox ↗</a></span>
</footer>
</main>

<script>
const initialData = __PAYLOAD__;
const fmt = value => value === null || value === undefined ? "Not available" : Number(value).toLocaleString();
const money = value => value === null || value === undefined ? "Not available" :
  new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(value);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const objTable = obj => {
  const entries = Object.entries(obj || {});
  if (!entries.length) return '<p class="small">No observations yet.</p>';
  return '<table><tbody>'+entries.map(([k,v])=>
    `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")+'</tbody></table>';
};

function render(data) {
  const runtime=data.runtime, evaluation=data.evaluation;
  const rai=data.responsible_ai, roi=data.roi;
  const guard=data.guardrails, audit=data.audit;

  document.getElementById("requests").textContent=fmt(runtime.requests_total);
  document.getElementById("requestScope").textContent=runtime.scope;
  document.getElementById("errorRate").textContent=
    runtime.error_rate_percent===null?"—":runtime.error_rate_percent+"%";
  document.getElementById("errorCount").textContent=fmt(runtime.errors_total)+" HTTP error responses";
  document.getElementById("evaluationScore").textContent=evaluation.passed+"/"+evaluation.total;
  document.getElementById("evaluationLabel").textContent=evaluation.score_percent+"% of authored cases passed";
  document.getElementById("latency").textContent=
    runtime.p95_latency_ms===null?"—":runtime.p95_latency_ms+" ms";
  document.getElementById("started").textContent=runtime.started_at_utc;
  document.getElementById("averageLatency").textContent=
    runtime.average_latency_ms===null?"—":runtime.average_latency_ms+" ms";
  document.getElementById("latencySamples").textContent=fmt(runtime.latency_sample_count);
  document.getElementById("warningCount").textContent=fmt(runtime.warnings.length);
  document.getElementById("warningList").innerHTML=runtime.warnings.length ?
    runtime.warnings.map(w=>`<div class="event"><span class="amber">${esc(w.code)}</span><br><span class="small">${esc(w.message)}</span></div>`).join("") :
    '<p class="small green">No configured runtime warning threshold is currently breached.</p>';
  document.getElementById("endpointTable").innerHTML=objTable(runtime.requests_by_endpoint);
  document.getElementById("statusTable").innerHTML=objTable(runtime.responses_by_status);

  document.getElementById("rejections").textContent=fmt(guard.recent_rejection_events);
  document.getElementById("escalations").textContent=fmt(guard.recent_escalation_events);
  document.getElementById("auditEvents").textContent=fmt(audit.events_in_summary);
  document.getElementById("descriptionLimit").textContent=fmt(guard.description_max_characters)+" characters";
  document.getElementById("incidentLimit").textContent=fmt(guard.incident_id_max_characters)+" characters";
  document.getElementById("auditList").innerHTML=audit.latest_events.length ?
    audit.latest_events.map(e=>`<div class="event">
      <div class="event-title"><strong>${esc(e.event_type||"Unknown event")}</strong><span class="tag">${esc(e.outcome||"")}</span></div>
      <div class="small">${esc(e.timestamp_utc||"Timestamp unavailable")}</div>
      <div class="small">Correlation: ${esc(e.correlation_id||"—")} · Incident: ${esc(e.incident_id||"—")}</div>
      <div class="small">Reason: ${esc(e.reason_code||"—")}</div>
    </div>`).join("") : '<p class="small">No audit events recorded yet.</p>';

  document.getElementById("evaluationSummary").textContent=
    `${evaluation.passed} of ${evaluation.total} acceptance cases passed`;
  document.getElementById("evaluationBar").style.width=
    `${evaluation.total ? evaluation.passed/evaluation.total*100 : 0}%`;
  document.getElementById("evaluationTable").innerHTML=
    '<table><thead><tr><th>Case</th><th>Expected → observed</th><th>Result</th></tr></thead><tbody>'+
    evaluation.results.map(r=>`<tr>
      <td><strong>${esc(r.id)}</strong><br>${esc(r.description)}</td>
      <td>Category: ${esc(r.expected.category)} → ${esc(r.observed.category)}<br>
      Priority: ${esc(r.expected.priority)} → ${esc(r.observed.priority)}<br>
      Policy: ${esc(r.expected.policy)} → ${esc(r.observed.policy)}</td>
      <td class="${r.passed?"green":"red"}">${r.passed?"PASS":"FAIL"}</td>
    </tr>`).join("")+'</tbody></table>';

  document.getElementById("controlSummary").textContent=
    `${rai.passed} of ${rai.total} controls marked Pass`;
  document.getElementById("controlBar").style.width=
    `${rai.total ? rai.passed/rai.total*100 : 0}%`;
  document.getElementById("needsEvidence").textContent=fmt(rai.needs_evidence);
  document.getElementById("inReview").textContent=fmt(rai.in_review);
  document.getElementById("controlsPassed").textContent=fmt(rai.passed);
  document.getElementById("controlsFailed").textContent=fmt(rai.failed);
  document.getElementById("controlsTable").innerHTML=rai.controls.map(c=>
    `<div class="rowline"><span><strong>${esc(c.id)}</strong> · ${esc(c.name)}<br>
      <span class="small">Owner: ${esc(c.owner)}</span><br>
      <span class="small">${esc(c.evidence_required||"Evidence requirement not defined")}</span>
    </span><span class="tag">${esc(c.status)}</span></div>`
  ).join("");

  document.getElementById("annualIncidents").textContent=fmt(roi.annual_incidents);
  document.getElementById("hoursSaved").textContent=fmt(roi.hours_saved)+" h";
  document.getElementById("roi").textContent=roi.roi_percent===null?"—":roi.roi_percent+"%";
  document.getElementById("annualBenefit").textContent=money(roi.annual_benefit);
  document.getElementById("annualCost").textContent=money(roi.annual_cost);
  document.getElementById("netBenefit").textContent=money(roi.net_benefit);
  document.getElementById("roiBasis").textContent=roi.basis;

  document.getElementById("latestState").textContent=JSON.stringify(data.latest_state,null,2);
  document.getElementById("scopeText").textContent=data.scope;
  document.getElementById("healthPill").textContent="DASHBOARD DATA AVAILABLE";
  document.getElementById("healthPill").className="pill";
  document.getElementById("updated").textContent=
    "Last refreshed "+new Date().toLocaleTimeString()+" · auto-refresh every 10 seconds";
}

async function refreshDashboard() {
  try {
    const health=await fetch("/health",{cache:"no-store"});
    const response=await fetch("/api/dashboard",{cache:"no-store"});
    if(!response.ok) throw new Error("Dashboard HTTP "+response.status);
    render(await response.json());
    if(!health.ok) document.getElementById("healthPill").textContent="HEALTH CHECK FAILED";
  } catch(error) {
    render(initialData);
    document.getElementById("healthPill").textContent="LIVE REFRESH FAILED";
    document.getElementById("updated").textContent=
      "Live refresh failed; showing initial snapshot. "+error.message;
  }
}
render(initialData);
refreshDashboard();
setInterval(refreshDashboard,10000);
</script>
</body>
</html>'''

    return html.replace("__PAYLOAD__", payload)
