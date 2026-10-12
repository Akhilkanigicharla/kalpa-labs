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
