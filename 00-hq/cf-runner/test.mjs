// node 00-hq/cf-runner/test.mjs : cf-runner logic with an in-process mock of GitHub + models (no network).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runOnce, pickTask, isStale, applyResult, callModels, RULES, MODELS } from "./lib.js";
import { makeMock } from "./mock.mjs";
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const NOW = Date.parse("2026-11-19T10:00:00Z");
const old = "2026-11-19T06:00:00Z", fresh = "2026-11-19T09:30:00Z";
const row = (id, extra = {}) => ({ id, world: "hq", priority: "P1", owner: "Forge", title: `T ${id} ✨ నమస్తే`, details: "d", status: "todo", created: old, ...extra });
const env = { GH_TOKEN: "x", GROQ_API_KEY: "g", RETRY_MS: "0", TEST_MODE: "1", GH_API: "http://127.0.0.1:1", MODEL_API: "http://127.0.0.1:1" };
const quiet = () => {};

// stale / fresh / bad ids
ok(isStale(row("K001"), NOW), "old todo is stale");
ok(!isStale(row("K002", { created: fresh }), NOW), "fresh row left to GitHub Actions");
ok(!isStale(row("K003", { status: "review" }), NOW), "only todo");
ok(!isStale(row("../../etc/x"), NOW) && !isStale(row("K1/../a"), NOW), "hostile id never picked");
ok(!isStale(row("K004", { created: "not a date" }), NOW), "bad date skipped");
// priority then oldest, across worlds
const p = pickTask({ b1: [row("K010", { priority: "P2" })], hq: [row("K011", { created: "2026-11-19T05:00:00Z" }), row("K012", { created: "2026-11-19T04:00:00Z" })] }, NOW, 90);
ok(p.t.id === "K012" && p.world === "hq", "P1 before P2, oldest first");

// full run: PASS → knowledge file + review, one atomic commit
let m = makeMock({ tasks: { hq: [row("K020", { read: ["README.md", "../secret", "https://evil.example/x"] })] }, files: { "README.md": "# Kalpa" } });
let r = await runOnce(env, NOW, m.handle, quiet);
ok(r.startsWith("K020 review"), `PASS run: ${r}`);
const hq = JSON.parse(m.files["00-hq/tasks/hq.json"]);
ok(hq[0].status === "review" && hq[0].output === "00-hq/knowledge/K020.md", "row moved to review");
ok(m.files["00-hq/knowledge/K020.md"].includes("1. Draft text ✓") && m.files["00-hq/knowledge/K020.md"].includes("cf-runner"), "knowledge file written, UTF-8 kept");
ok(m.commits.length === 1 && m.modelCalls === 2, "one commit, draft + vigil calls");

// FIX → todo with notes; third FIX → rejected
m = makeMock({ tasks: { hq: [row("K021", { tries: 2 })] }, verdict: "FIX: add numbers" });
r = await runOnce(env, NOW, m.handle, quiet);
ok(r.startsWith("K021 rejected") && JSON.parse(m.files["00-hq/tasks/hq.json"])[0].vigil_notes === "FIX: add numbers", `FIX at 3 tries → rejected: ${r}`);
ok(!("00-hq/knowledge/K021.md" in m.files), "no knowledge file on FIX");

// race: main moved → nothing written
m = makeMock({ tasks: { hq: [row("K022")] }, moveMain: true });
r = await runOnce(env, NOW, m.handle, quiet);
ok(r.startsWith("main moved") && m.commits.length === 0 && JSON.parse(m.files["00-hq/tasks/hq.json"])[0].status === "todo", "422 race leaves main untouched");

// no token / kill switch / nothing stale / no model key
ok((await runOnce({}, NOW, m.handle, quiet)) === "skip (no GH_TOKEN)", "no token → skip");
ok((await runOnce({ ...env, ENABLED: "0" }, NOW, m.handle, quiet)) === "off", "kill switch");
m = makeMock({ tasks: { hq: [row("K023", { created: fresh })] } });
ok((await runOnce(env, NOW, m.handle, quiet)) === "nothing stale", "fresh rows untouched");
m = makeMock({ tasks: { hq: [row("K024")] } });
r = await runOnce({ ...env, GROQ_API_KEY: "" }, NOW, m.handle, quiet);
ok(r.includes("skipped") && m.commits.length === 0, "no model → no commit spam");

// test overrides ignored outside TEST_MODE: real hosts only
const seen = [];
await runOnce({ GH_TOKEN: "x", GH_API: "http://127.0.0.1:1" }, NOW, async (u) => { seen.push(u); return { status: 500, ok: false }; }, quiet);
ok(seen[0].startsWith("https://api.github.com/"), "GH_API override needs TEST_MODE");
seen.length = 0;
await runOnce({ GH_TOKEN: "x", TEST_MODE: "1", GH_API: "https://evil.example" }, NOW, async (u) => { seen.push(u); return { status: 500, ok: false }; }, quiet);
ok(seen[0].startsWith("https://api.github.com/"), "non-localhost override refused");

// model fallbacks: 429 retried once, cut-off and unclosed think skipped
let calls = 0;
const seq = [{ status: 429 }, { status: 200, body: { choices: [{ finish_reason: "length", message: { content: "half" } }] } },
  { status: 200, body: { choices: [{ finish_reason: "stop", message: { content: "<think>x" } }] } },
  { status: 200, body: { choices: [{ finish_reason: "stop", message: { content: "<think>a</think> done" } }] } }];
const ff = async () => { const s = seq[calls++]; return { status: s.status, ok: s.status < 300, json: async () => s.body }; };
const res = await callModels(MODELS, [], { GROQ_API_KEY: "g", OPENROUTER_API_KEY: "o", RETRY_MS: "0" }, ff, quiet);
ok(res.text === "done" && calls === 4, `fallback chain: ${JSON.stringify(res)} after ${calls}`);
ok((await callModels(MODELS, [], { GROQ_API_KEY: "g" }, async () => { throw new Error("timeout"); }, quiet)).text === null, "network errors → null, no throw");

// applyResult mirrors runner.py: vigil missing → no try used
const t = row("K030"); ok(applyResult(t, { draft: "d", model: "m", verdict: null }, "2026-11-19T10:00:00Z").status === "skipped" && !t.tries, "no vigil → no try used");

// RULES stay identical to runner.py
const py = readFileSync(new URL("../agents/runner.py", import.meta.url), "utf8").match(/RULES = """([\s\S]*?)"""/)[1];
ok(py === RULES, "RULES copy matches runner.py");
const toml = readFileSync(new URL("./wrangler.toml", import.meta.url), "utf8");
ok(toml.includes('"5,35 * * * *"') && !toml.includes("TEST_MODE"), "cron set, no TEST_MODE in prod config");
console.log(`PASS cf-runner: ${n} checks`);
// queue file keeps runner.py's format (indent 1, UTF-8 as is) so commits show one-row diffs
m = makeMock({ tasks: { hq: [row("K040")] } });
await runOnce(env, NOW, m.handle, quiet);
const q = m.files["00-hq/tasks/hq.json"];
assert.ok(q.startsWith('[\n {\n  "id": "K040"') && q.includes("నమస్తే") && q.endsWith("]\n"), "queue format matches runner.py");
console.log("PASS cf-runner: queue format check");
