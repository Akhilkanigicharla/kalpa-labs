// Run: node 00-hq/agents/run.test.js
const assert = require("assert");
const R = require("./run.js");
const { AGENTS } = require("./registry.js");
assert.deepStrictEqual(R.check(), []); console.log(`  ✓ registry valid: ${AGENTS.length} agents, each with a validator, KPI and honest status`);
const st = { active_setups: ["salon"], clients: { salon: 0 } };
const tue = R.plan("2026-10-13", st), ids = tue.worlds.flatMap((w) => w.run.map((a) => a.id));
assert.ok(ids.includes("b1.salon.pitch") && !ids.includes("b1.gym.pitch")); console.log("  ✓ only launched setups get sales agents (salon yes, gym not yet)");
assert.ok(!ids.includes("b1.salon.reviews")); console.log("  ✓ delivery agents wait for the first client");
const live = R.plan("2026-10-13", { active_setups: ["salon"], clients: { salon: 2 } }).worlds.flatMap((w) => w.run.map((a) => a.id));
assert.ok(live.includes("b1.salon.reviews")); console.log("  ✓ with 2 salon clients, delivery agents switch on");
for (const w of R.plan("2026-11-01", { active_setups: ["salon", "gym", "examkits", "realestate"], clients: { salon: 9, gym: 9, examkits: 9, realestate: 9 } }).worlds) assert.ok(w.used <= w.budget, w.world);
console.log("  ✓ token budgets never exceeded, even with every setup live (extra work is deferred)");
assert.ok(!ids.some((id) => AGENTS.find((a) => a.id === id).runs_as === "planned")); console.log("  ✓ planned agents never scheduled");
console.log("orchestrator tests passed");

// A42: registry follows the roadmap; WORLD_SHARE change waits for Akhil (C01)
const { WORLD_SHARE, PROPOSED_WORLD_SHARE } = require("./registry.js");
const sum = (o) => Object.values(o).reduce((a, b) => a + b, 0);
assert.strictEqual(sum(WORLD_SHARE), 100); assert.strictEqual(sum(PROPOSED_WORLD_SHARE), 100);
assert.deepStrictEqual(Object.keys(PROPOSED_WORLD_SHARE).sort(), Object.keys(WORLD_SHARE).sort());
console.log("  ✓ current and proposed world shares each add up to 100%");
assert.deepStrictEqual(R.activeShare({}), WORLD_SHARE);
assert.deepStrictEqual(R.activeShare({ world_share_approved: false }), WORLD_SHARE);
assert.deepStrictEqual(R.activeShare({ world_share_approved: true }), PROPOSED_WORLD_SHARE);
console.log("  ✓ proposed share is used only after Akhil approves it (state.json world_share_approved)");
const pend = R.plan("2026-10-13", st), appr = R.plan("2026-10-13", Object.assign({ world_share_approved: true }, st));
assert.ok(pend.share_pending && !appr.share_pending);
assert.strictEqual(appr.worlds.find((w) => w.world === "b1").budget, 400000 * PROPOSED_WORLD_SHARE.b1 / 100);
console.log("  ✓ today's plan flags the pending proposal and switches budgets once approved");
const byId = Object.fromEntries(AGENTS.map((a) => [a.id, a]));
for (const u of ["b2", "b4", "b5", "b6", "b7"]) assert.notStrictEqual(byId[`${u}.builder`].runs_as, "planned", u);
assert.strictEqual(byId["b3.builder"].runs_as, "planned");
console.log("  ✓ worlds with built code have live builders; b3 (no code yet) stays planned");
for (const id of ["hq.marketing", "hq.tasks", "hq.sprint", "hq.quality", "b1.salon.social", "b2.invoice", "b4.lifeboat", "b5.calculators", "b6.ingest", "b7.gate"])
  assert.ok(byId[id] && byId[id].runs_as !== "planned", id);
console.log("  ✓ agents exist for every built roadmap item (marketing, task engine, sprints, quality, social, world engines)");
assert.ok(byId["b7.marketer"].runs_as === "planned" && /off/i.test(byId["b7.marketer"].mission)); console.log("  ✓ Trading Lab marketing stays switched off (SEBI)");
console.log("registry update tests passed");
