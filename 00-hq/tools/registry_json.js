// Every agent in 00-hq/agents/registry.js as one JSON list for the CEO Room's "All agents" view (dataset `registry`).
// Usage: node 00-hq/tools/registry_json.js > registry.json   then upload it to the CEO Room as the registry file.
// State words match 00-hq/agents/live_status.py roster rows, so the two views agree.
"use strict";
const { AGENTS } = require("../agents/registry.js");
const STATE = { code: "ready", n8n: "ready", claude: "on call", human: "needs you", planned: "planned" };
const trig = (t) => (!t ? "" : typeof t === "string" ? t : Object.entries(t).map(([k, v]) => k + ": " + v).join(", "));
const rows = AGENTS.map((a) => ({
  id: a.id, name: a.name, world: a.unit, team: a.team, runs_as: a.runs_as, state: STATE[a.runs_as] || a.runs_as,
  mission: a.mission || "", trigger: trig(a.trigger), kpi: a.kpi || "",
  validator: (a.validator || {}).name || "", checks: ((a.validator || {}).checks || []).join("; "),
  tools: (a.tools || []).join(", "), tokens: a.tokens || 0, code: a.code || "", human_needed: !!a.human_needed,
}));
process.stdout.write(JSON.stringify(rows));
