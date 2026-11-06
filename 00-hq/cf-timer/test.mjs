// node 00-hq/cf-timer/test.mjs : checks the window and dispatch logic with a fake fetch (no network).
import assert from "node:assert/strict";
import { run, inN8nWindow } from "./worker.js";
const calls = []; const fake = async (url, opt) => { calls.push([url, opt.method]); return { status: url.includes("dispatches") ? 204 : 200 }; };
assert.equal(inN8nWindow(new Date("2026-11-06T00:00:00Z")), true);   // 05:30 IST
assert.equal(inN8nWindow(new Date("2026-11-06T18:55:00Z")), true);   // 00:25 IST
assert.equal(inN8nWindow(new Date("2026-11-06T19:00:00Z")), false);  // 00:30 IST: let it sleep
assert.deepEqual(await run("*/5 * * * *", new Date("2026-11-06T10:00:00Z"), {}, fake), ["n8n 200"]);
assert.deepEqual(await run("*/5 * * * *", new Date("2026-11-06T21:00:00Z"), {}, fake), []);
assert.deepEqual(await run("30 15 * * *", new Date("2026-11-06T15:30:00Z"), {}, fake), ["skip daily-brief.yml (no GH_TOKEN)"]);
assert.deepEqual(await run("30 15 * * *", new Date("2026-11-06T15:30:00Z"), { GH_TOKEN: "x" }, fake), ["daily-brief.yml 204"]);
assert.ok(calls.some(([u, m]) => u.endsWith("/workflows/daily-brief.yml/dispatches") && m === "POST"));
console.log("PASS cf-timer: 7 checks");
