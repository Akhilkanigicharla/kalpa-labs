#!/usr/bin/env node
// Task engine for 00-hq/ROADMAP.md, inspired by Taskmaster AI's list / next / show / validate-dependencies
// workflow (eyaltoledano/claude-task-master). Our own code: Taskmaster is MIT + Commons Clause, so nothing is copied
// and it isn't bundled. ROADMAP.md stays the single source of truth; this only reads it.
//
//   node 00-hq/agents/tasks.js next [--queue agent|ceo]   what to build next (resumes [~] first, deps must be done)
//   node 00-hq/agents/tasks.js list [--status todo|started|done|blocked] [--world b1] [--queue agent|ceo]
//   node 00-hq/agents/tasks.js show A05,A41
//   node 00-hq/agents/tasks.js validate                    duplicate ids, unknown/circular deps, ticks without proof
//   node 00-hq/agents/tasks.js stats                       progress per world
//
// Dependencies: write "needs A05" or "needs A05, A09" (or "shared with A05", "after A05") in an item's text.
const fs = require("fs");
const path = require("path");

const ROADMAP = path.join(__dirname, "..", "ROADMAP.md");
const STATUS = { " ": "todo", "~": "started", x: "done", "!": "blocked" };
const ITEM = /^- \[( |~|x|!)\] (💰 )?\*\*([AC]\d+[a-z]?)\*\* ([^·]+?) · (.*)$/;
const DEP = /\b(?:needs|after|shared with|depends on)\s+((?:[AC]\d+[a-z]?(?:\s*(?:,|and|&)\s*)?)+)/gi;

function parse(text) {
  const items = [];
  let queue = null, section = "";
  text.split("\n").forEach((line, i) => {
    if (/^## Agent queue/.test(line)) queue = "agent";
    else if (/^## CEO queue/.test(line)) queue = "ceo";
    else if (/^###? /.test(line)) section = line.replace(/^#+\s*/, "");
    const m = line.match(ITEM);
    if (!m || !queue) return;
    const [, mark, paid, id, world, rest] = m;
    const deps = new Set();
    for (const d of rest.matchAll(DEP)) for (const x of d[1].match(/[AC]\d+[a-z]?/g)) if (x !== id) deps.add(x);
    const done = rest.match(/\(done (\d{4}-\d{2}-\d{2}), ([0-9a-f]{7,40})/);
    const check = (rest.match(/Check:\s*([^]*?)(?:\s*\(done|$)/) || [])[1];
    items.push({ id, queue, section, world: world.trim(), status: STATUS[mark], paid: !!paid, line: i + 1,
      title: rest.split(/\s*Check:/)[0].trim(), check: check ? check.trim() : null, deps: [...deps],
      done_at: done ? done[1] : null, commit: done ? done[2] : null });
  });
  return items;
}

const load = (file = ROADMAP) => parse(fs.readFileSync(file, "utf8"));
const byId = (items) => Object.fromEntries(items.map((t) => [t.id, t]));

function ready(t, map) {
  return t.deps.every((d) => !map[d] || map[d].status === "done");
}

/** Next item: a started [~] item first (resume), else the first todo whose dependencies are done. Blocked [!] skipped. */
function next(items, queue = "agent") {
  const map = byId(items), q = items.filter((t) => t.queue === queue);
  return q.find((t) => t.status === "started" && ready(t, map)) || q.find((t) => t.status === "todo" && ready(t, map)) || null;
}

function validate(items) {
  const problems = [], map = {}, seen = new Set();
  for (const t of items) {
    if (seen.has(t.id)) problems.push(`${t.id}: duplicate id (line ${t.line})`);
    seen.add(t.id); map[t.id] = map[t.id] || t;
  }
  for (const t of items) {
    for (const d of t.deps) if (!map[d]) problems.push(`${t.id}: depends on unknown ${d}`);
    if (t.status === "done" && t.queue === "agent" && !t.commit) problems.push(`${t.id}: ticked without "(done YYYY-MM-DD, <commit>)"`);
    if (t.status === "done") for (const d of t.deps) if (map[d] && map[d].status !== "done") problems.push(`${t.id}: done but its dependency ${d} is not`);
    if (t.queue === "agent" && !t.check) problems.push(`${t.id}: no "Check:" (CLAUDE.md rule 5: tests before ticks)`);
  }
  const state = {};  // cycle detection (DFS)
  const visit = (id, trail) => {
    if (state[id] === 2 || !map[id]) return;
    if (state[id] === 1) { problems.push(`circular dependency: ${[...trail.slice(trail.indexOf(id)), id].join(" -> ")}`); return; }
    state[id] = 1;
    for (const d of map[id].deps) visit(d, [...trail, id]);
    state[id] = 2;
  };
  for (const t of items) visit(t.id, []);
  return [...new Set(problems)];
}

function stats(items) {
  const out = {};
  for (const t of items.filter((x) => x.queue === "agent")) {
    const w = (out[t.world.split(/[ /+]/)[0]] ||= { total: 0, done: 0, started: 0, blocked: 0 });
    w.total++; if (t.status === "done") w.done++; if (t.status === "started") w.started++; if (t.status === "blocked") w.blocked++;
  }
  return out;
}

function fmt(t) {
  const icon = { todo: "[ ]", started: "[~]", done: "[x]", blocked: "[!]" }[t.status];
  return `${icon} ${t.id.padEnd(5)} ${t.world.padEnd(8)} ${t.title.slice(0, 90)}${t.deps.length ? `  (needs ${t.deps.join(", ")})` : ""}`;
}

function main(argv) {
  const [cmd = "next", ...rest] = argv;
  const opt = (k) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? rest[i + 1] : null; };
  const items = load();
  if (cmd === "next") {
    const t = next(items, opt("queue") || "agent");
    console.log(t ? `${fmt(t)}\n   Check: ${t.check || "-"}\n   ROADMAP.md line ${t.line}` : "Nothing ready: every item is done, blocked or waiting on a dependency.");
  } else if (cmd === "list") {
    items.filter((t) => (!opt("status") || t.status === opt("status")) && (!opt("world") || t.world.startsWith(opt("world")))
      && (!opt("queue") || t.queue === opt("queue"))).forEach((t) => console.log(fmt(t)));
  } else if (cmd === "show") {
    const map = byId(items);
    for (const id of (rest[0] || "").split(",")) console.log(map[id] ? JSON.stringify(map[id], null, 1) : `${id}: not found`);
  } else if (cmd === "validate") {
    const p = validate(items);
    console.log(p.length ? p.map((x) => "✗ " + x).join("\n") : `✓ ${items.length} roadmap items valid`);
    return p.length ? 1 : 0;
  } else if (cmd === "stats") {
    for (const [w, s] of Object.entries(stats(items))) console.log(`${w.padEnd(10)} ${"█".repeat(s.done)}${"░".repeat(s.total - s.done)} ${s.done}/${s.total}${s.started ? ` · ${s.started} started` : ""}${s.blocked ? ` · ${s.blocked} blocked` : ""}`);
  } else {
    console.log("usage: tasks.js next|list|show|validate|stats"); return 2;
  }
  return 0;
}

module.exports = { parse, load, next, validate, stats };
if (require.main === module) process.exitCode = main(process.argv.slice(2));
