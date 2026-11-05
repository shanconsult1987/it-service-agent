HTML = r"""<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport" content="width=device-width,initial-scale=1">

<title>Contoso IT Agent | Day 3 Operations</title>

<style>

body {
    font-family: Segoe UI, Arial, sans-serif;
    margin: 0;
    background: #f4f6f8;
    color: #17202a;
}

header {
    background: #172b4d;
    color: white;
    padding: 22px 28px;
}

main {
    padding: 22px;
    max-width: 1250px;
    margin: auto;
}

.grid {
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(210px, 1fr)
    );
    gap: 14px;
}

.card {
    background: white;
    border: 1px solid #dfe4ea;
    border-radius: 10px;
    padding: 16px;
}

h1 {
    font-size: 22px;
    margin: 0;
}

h2 {
    font-size: 17px;
    margin: 0 0 12px;
}

.value {
    font-size: 27px;
    font-weight: 650;
    margin-top: 8px;
}

.muted {
    color: #5e6c84;
    font-size: 13px;
}

section {
    margin: 18px 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    background: white;
}

td, th {
    padding: 9px;
    border-bottom: 1px solid #e5e9ef;
    text-align: left;
    font-size: 13px;
}

button {
    padding: 8px 12px;
    border: 0;
    border-radius: 6px;
    background: #1769aa;
    color: white;
    cursor: pointer;
}

</style>

</head>

<body>

<header>

<h1>
Contoso IT Service Agent — Day 3 Control Room
</h1>

<div class="muted" style="color:#dbe5f2">

GOVERN · EVALUATE · OPERATE · SCALE

</div>

</header>

<main>

<p>

<button onclick="load()">
Refresh dashboard
</button>

<span class="muted">
Auto-refresh every 10 seconds · Metrics are process-local
</span>

</p>

<div id="kpis" class="grid"></div>

<section class="card">

<h2>Governance and Responsible AI</h2>

<div id="controls"></div>

</section>

<section class="card">

<h2>Evaluation results</h2>

<div id="evaluation"></div>

</section>

<section class="card">

<h2>LLM and HTTP operations</h2>

<div id="runtime"></div>

</section>

<section class="card">

<h2>Cost and ROI</h2>

<div id="finance"></div>

</section>

<section class="card">

<h2>Recent audit events</h2>

<div id="audit"></div>

</section>

</main>

<script>

const el = id => document.getElementById(id);

const money = (value, currency) => {

    if (
        value === null
        || value === undefined
    ) {
        return "Not configured";
    }

    return new Intl.NumberFormat(
        undefined,
        {
            style: "currency",
            currency: currency || "USD"
        }
    ).format(value);

};

function card(label, value, note) {

    return `
        <div class="card">

            <div class="muted">${label}</div>

            <div class="value">${value}</div>

            <div class="muted">${note || ""}</div>

        </div>
    `;

}

function table(rows, heads) {

    return `

        <table>

            <thead>

                <tr>

                    ${heads.map(
                        item => `<th>${item}</th>`
                    ).join("")}

                </tr>

            </thead>

            <tbody>

                ${rows.map(
                    row => `
                        <tr>
                            ${row.map(
                                value => `<td>${String(value ?? "")}</td>`
                            ).join("")}
                        </tr>
                    `
                ).join("")}

            </tbody>

        </table>

    `;

}

async function load() {

    try {

        const response = await fetch(
            "/api/dashboard"
        );

        if (!response.ok) {
            throw new Error(
                "Dashboard API returned " + response.status
            );
        }

        const d = await response.json();

        const l = d.runtime.llm;

        const h = d.runtime.http;

        el("kpis").innerHTML =

            card(
                "HTTP requests",
                h.requests,
                "Current server process"
            )

            +

            card(
                "LLM calls",
                l.calls,
                "Errors: " + l.errors
            )

            +

            card(
                "Total tokens",
                l.total_tokens,
                "Prompt " + l.prompt_tokens
                + " / completion "
                + l.completion_tokens
            )

            +

            card(
                "Regression pass rate",
                d.evaluation.pass_rate_percent + "%",
                d.evaluation.passed
                + " / "
                + d.evaluation.case_count
                + " cases"
            );

        el("controls").innerHTML =

            "<h3>Governance</h3>"

            +

            table(
                d.governance.controls.map(
                    item => [
                        item.id,
                        item.name,
                        item.status,
                        item.owner
                    ]
                ),
                [
                    "ID",
                    "Control",
                    "Status",
                    "Owner"
                ]
            )

            +

            "<h3>Responsible AI</h3>"

            +

            table(
                d.responsible_ai.controls.map(
                    item => [
                        item.id,
                        item.name,
                        item.status,
                        item.owner,
                        item.reviewer || "Not recorded",
                        item.evidence_reference || "Not recorded"
                    ]
                ),
                [
                    "ID",
                    "Control",
                    "Status",
                    "Owner",
                    "Reviewer",
                    "Evidence"
                ]
            );

        el("evaluation").innerHTML = table(
            d.evaluation.results.map(
                item => [
                    item.id,
                    item.passed ? "PASS" : "FAIL",
                    JSON.stringify(item.checks)
                ]
            ),
            [
                "Case",
                "Result",
                "Checks"
            ]
        );

        el("runtime").innerHTML = table(
            [
                [
                    "LLM latency average/max",
                    l.latency.avg_ms
                    + " / "
                    + l.latency.max_ms
                    + " ms"
                ],
                [
                    "HTTP latency average/max",
                    h.latency.avg_ms
                    + " / "
                    + h.latency.max_ms
                    + " ms"
                ],
                [
                    "LLM models",
                    JSON.stringify(l.models)
                ],
                [
                    "HTTP endpoints",
                    JSON.stringify(h.endpoints)
                ],
                [
                    "Usage unavailable calls",
                    l.usage_unavailable
                ]
            ],
            [
                "Metric",
                "Value"
            ]
        );

        el("finance").innerHTML = table(
            [
                ["LLM model", d.cost.model],
                [
                    "LLM estimated cost",
                    money(
                        d.cost.estimated_cost,
                        d.cost.currency
                    )
                ],
                [
                    "Annual incidents (assumption)",
                    d.roi.annual_incidents
                ],
                [
                    "Hours saved (assumption)",
                    d.roi.hours_saved
                ],
                [
                    "Annual benefit",
                    money(
                        d.roi.annual_benefit,
                        "USD"
                    )
                ],
                [
                    "Annual cost",
                    money(
                        d.roi.annual_cost,
                        "USD"
                    )
                ],
                [
                    "Net benefit",
                    money(
                        d.roi.net_benefit,
                        "USD"
                    )
                ],
                [
                    "ROI",
                    d.roi.roi_percent === null
                    ? "N/A"
                    : d.roi.roi_percent + "%"
                ],
                [
                    "Interpretation",
                    d.roi.assumption_note
                ]
            ],
            [
                "Measure",
                "Value"
            ]
        );

        el("audit").innerHTML = table(
            d.audit.slice().reverse().map(
                item => [
                    item.timestamp,
                    item.event_type,
                    item.incident_id,
                    item.outcome
                ]
            ),
            [
                "Timestamp",
                "Event",
                "Incident",
                "Outcome"
            ]
        );

    } catch (error) {

        el("kpis").textContent =
            "Dashboard error: " + error;

    }

}

load();

setInterval(load, 10000);

</script>

</body>

</html>
"""