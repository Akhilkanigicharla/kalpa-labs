// Check 111 (Pagination + Limits, 20 Nov 2026). Run: NO_DELAY=1 node core/functions/paging.test.js
// Supabase cuts one reply at 1,000 rows. Lists that the scheduled jobs walk must be read page by page,
// and the fake database must cut replies the same way so a missing page would show up here.
process.env.NO_DELAY = "1";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const many = Array.from({ length: 1203 }, (_, i) => ({ id: String(i + 1).padStart(5, "0"), name: "C" + i, active: true, phone_number_id: null }));
require("./_fake.js")({ clients: many });
const L = require("./_lib.js");

(async () => {
  const all = await L.dbAll("clients?active=eq.true&select=id");
  assert.strictEqual(all.length, 1203, "dbAll returns every row past 1,000");
  assert.strictEqual(new Set(all.map((r) => r.id)).size, 1203, "no row read twice across pages");
  const capped = await L.dbAll("clients?select=id", { page: 100, max: 300 });
  assert.strictEqual(capped.length, 300, "max stops runaway reads");
  const one = await L.db("clients?id=eq.00007&select=id&limit=1");
  assert.deepStrictEqual(one.map((r) => r.id), ["00007"]);
  console.log("  ✓ dbAll reads 1,203 rows in pages, never twice; max caps a runaway list; limit=1 lookups");

  // Every list read in a server function either pages (dbAll) or carries a limit (static check, same rule as eng_check 111)
  const dir = __dirname, bad = [];
  for (const f of fs.readdirSync(dir).filter((f) => f.endsWith(".js") && !f.includes("test") && !f.startsWith("_fake"))) {
    const src = fs.readFileSync(path.join(dir, f), "utf8");
    for (const m of src.matchAll(/\b(db|dbAll)\(\s*[`"]([A-Za-z_]+\?[^`"]*select=[^`"]*)[`"]/g))
      if (m[1] === "db" && !/limit=/.test(m[2])) bad.push(`${f}: ${m[2].slice(0, 60)}`);
  }
  assert.deepStrictEqual(bad, [], "list queries without a limit:\n" + bad.join("\n"));
  console.log("  ✓ every select in core/functions pages or has a limit");

  // Timeout on every database call
  assert.match(fs.readFileSync(path.join(dir, "_lib.js"), "utf8"), /signal: AbortSignal\.timeout\(/);
  console.log("  ✓ database calls time out (10 s) instead of hanging the function");
})().catch((e) => { console.error(e); process.exit(1); });
