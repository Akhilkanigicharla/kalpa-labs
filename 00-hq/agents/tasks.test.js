// Run: node 00-hq/agents/tasks.test.js
const assert = require("assert");
const T = require("./tasks.js");

const md = `# Roadmap
## Agent queue
### Sprint 1
- [x] **A01** b1 · build engine. Check: tests green. (done 2026-10-13, abc1234)
- [ ] **A02** b1 · billing, needs A03. Check: PDF renders.
- [ ] **A03** b1 · invoice table. Check: schema test.
- [~] **A04** b2 · half done. Check: e2e.
- [!] **A05** b3 · blocked on Telegram. Check: posts.
## CEO queue
- [ ] **C01** HQ · approve plan (15 min)
- [ ] 💰 **C02** b1 · buy SIM
`;
const items = T.parse(md);
assert.strictEqual(items.length, 7);
assert.deepStrictEqual(items.map((t) => t.status), ["done", "todo", "todo", "started", "blocked", "todo", "todo"]);
assert.deepStrictEqual(items[1].deps, ["A03"]);
assert.strictEqual(items[0].commit, "abc1234");
assert.ok(items[6].paid && items[5].queue === "ceo");
console.log("  ✓ parses status, world, deps, proof, CEO 💰 items");

assert.strictEqual(T.next(items).id, "A04", "started items are resumed first");
const noStarted = items.map((t) => (t.id === "A04" ? { ...t, status: "done", commit: "x" } : t));
assert.strictEqual(T.next(noStarted).id, "A03", "A02 waits for its dependency A03");
assert.strictEqual(T.next(items, "ceo").id, "C01");
const allDone = items.map((t) => ({ ...t, status: t.queue === "agent" && t.status !== "blocked" ? "done" : t.status, commit: "x" }));
assert.strictEqual(T.next(allDone), null, "blocked items are never picked");
console.log("  ✓ next: resume [~] first, respect dependencies, skip [!] blocked");

assert.deepStrictEqual(T.validate(items), []);
const bad = T.parse(md.replace("needs A03", "needs A09").replace("(done 2026-10-13, abc1234)", "")
  .replace("invoice table.", "invoice table, needs A02.") + "- [ ] **A03** b1 · dup. Check: x.\n");
const p = T.validate(T.parse(md.replace("invoice table.", "invoice table, needs A02.").replace("(done 2026-10-13, abc1234)", "") + "- [ ] **A03** b1 · dup. Check: x.\n"));
assert.ok(p.some((x) => x.includes("duplicate id")) && p.some((x) => x.includes("circular")) && p.some((x) => x.includes("ticked without")), p);
assert.ok(T.validate(bad).some((x) => x.includes("unknown A09")));
console.log("  ✓ validate: duplicates, unknown deps, circular deps, ticks without proof");

assert.deepStrictEqual(T.stats(items).b1, { total: 3, done: 1, started: 0, blocked: 0 });
assert.deepStrictEqual(T.validate(T.load()), [], "the real ROADMAP.md must stay valid");
console.log("  ✓ stats per world; real ROADMAP.md is valid");
console.log("task engine tests passed");
