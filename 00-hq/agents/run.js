#!/usr/bin/env node
// Kalpa Labs agent orchestrator: validate the registry, plan today's agent work within budgets, export for the Kingdom UI.
//   node 00-hq/agents/run.js check | today [YYYY-MM-DD] | summary | export
"use strict";
const fs = require("fs"), path = require("path");
const { AGENTS, DAILY_TOKENS, WORLD_SHARE } = require("./registry.js");
const ROOT = path.resolve(__dirname, "..", "..");
const DOW = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

function due(agent, date) {
  const c = agent.trigger && agent.trigger.cron; if (!c) return false;
  if (c === "hourly" || c === "daily" || c.startsWith("daily:")) return true;
  if (c.startsWith("weekly:")) return DOW[date.getUTCDay()] === c.slice(7);
  if (c === "monthly") return date.getUTCDate() === 1;
  return false;
}
function runsPerDay(agent) { return agent.trigger.cron === "hourly" ? 24 : 1; }

function check() {
  const errors = [], ids = new Set();
  for (const a of AGENTS) {
    if (ids.has(a.id)) errors.push(`duplicate id ${a.id}`); ids.add(a.id);
    for (const f of ["name", "unit", "team", "mission", "trigger", "validator", "kpi", "runs_as"]) if (!a[f]) errors.push(`${a.id}: missing ${f}`);
    if (!a.validator.checks || !a.validator.checks.length) errors.push(`${a.id}: validator has no checks`);
    if (!["code", "claude", "human", "planned"].includes(a.runs_as)) errors.push(`${a.id}: bad runs_as ${a.runs_as}`);
    if (!WORLD_SHARE[a.unit]) errors.push(`${a.id}: unknown unit ${a.unit}`);
    if (a.runs_as === "code" && a.code && !a.code.startsWith("scheduled task") && !a.code.includes("artifact")) {
      const file = a.code.split(/[#\s+]/)[0];
      if (!fs.existsSync(path.join(ROOT, file)) && !fs.existsSync(path.join(ROOT, "01-botbhai/botbhai", file))) errors.push(`${a.id}: code file not found: ${file}`);
    }
  }
  for (const s of ["salon", "realestate", "gym", "examkits"]) if (AGENTS.filter((a) => a.setup === s && a.team !== "platform-pm").length < 30) errors.push(`setup ${s} has an incomplete team`);
  return errors;
}

// Spend tokens only where it can matter: sales agents for launched setups; delivery/success agents only for setups with clients.
function relevant(a, st) {
  if (!a.setup || a.team.startsWith("platform")) return true;
  if (!st.active_setups.includes(a.setup)) return false;
  if (a.team === "sales") return true;
  return (st.clients[a.setup] || 0) > 0;
}
function plan(dateStr, st = JSON.parse(fs.readFileSync(path.join(__dirname, "state.json"), "utf8"))) {
  const date = dateStr ? new Date(dateStr + "T00:00:00Z") : new Date(Date.now() + 330 * 60000);
  const byWorld = {};
  for (const a of AGENTS.filter((x) => due(x, date) && x.runs_as !== "planned" && relevant(x, st))) (byWorld[a.unit] = byWorld[a.unit] || []).push(a);
  const out = [];
  for (const [u, list] of Object.entries(byWorld)) {
    const budget = Math.round(DAILY_TOKENS * WORLD_SHARE[u] / 100); let used = 0; const run = [], deferred = [];
    // code agents cost no Claude tokens; Claude agents are taken in registry order until the world's budget is used
    for (const a of list.sort((x, y) => (x.runs_as === "code" ? -1 : 1) - (y.runs_as === "code" ? -1 : 1))) {
      const cost = (a.runs_as === "code" ? 0 : a.tokens) * runsPerDay(a);
      if (used + cost <= budget) { used += cost; run.push(a); } else deferred.push(a);
    }
    out.push({ world: u, budget, used, run, deferred });
  }
  return { date: date.toISOString().slice(0, 10), worlds: out.sort((a, b) => a.world.localeCompare(b.world)) };
}

function summary() {
  const s = { total: AGENTS.length, validators: AGENTS.length, byStatus: {}, byWorld: {}, byTeam: {} };
  for (const a of AGENTS) {
    s.byStatus[a.runs_as] = (s.byStatus[a.runs_as] || 0) + 1;
    s.byWorld[a.unit] = (s.byWorld[a.unit] || 0) + 1;
    const team = a.setup ? `${a.setup}:${a.team}` : a.team; s.byTeam[team] = (s.byTeam[team] || 0) + 1;
  }
  return s;
}

function exportForUI() { // compact rows for the Kingdom's Agents tab
  return AGENTS.map((a) => [a.id, a.name, a.unit, a.setup || "", a.team, a.runs_as, a.mission, a.kpi, a.validator.name, a.validator.checks.join("; "), a.trigger.cron || a.trigger.event || "manual", a.human_needed ? 1 : 0]);
}

if (require.main === module) {
  const [cmd = "summary", arg] = process.argv.slice(2);
  if (cmd === "check") { const e = check(); if (e.length) { console.error(e.join("\n")); process.exit(1); } console.log(`registry OK: ${AGENTS.length} agents, ${AGENTS.length} validators`); }
  else if (cmd === "today") {
    const p = plan(arg);
    console.log(`Agent plan for ${p.date} (daily budget ${DAILY_TOKENS.toLocaleString("en-IN")} tokens)`);
    for (const w of p.worlds) {
      console.log(`\n[${w.world}] ${w.run.length} agents run, ${w.deferred.length} deferred · ${w.used.toLocaleString("en-IN")}/${w.budget.toLocaleString("en-IN")} tokens`);
      for (const a of w.run) console.log(`  ${a.runs_as === "code" ? "⚙" : a.runs_as === "human" ? "🙋" : "🤖"} ${a.name} — ${a.mission}`);
      for (const a of w.deferred) console.log(`  ⏸ ${a.name} (over budget, moved to tomorrow)`);
    }
  } else if (cmd === "export") process.stdout.write(JSON.stringify(exportForUI()));
  else console.log(JSON.stringify(summary(), null, 2));
}
module.exports = { check, plan, summary, exportForUI, due, relevant };
