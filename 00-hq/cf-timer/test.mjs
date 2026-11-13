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
// A237: free agents start on time every 30 min (GitHub's own cron drops most slots)
assert.deepEqual(await run("20,50 * * * *", new Date("2026-11-13T07:50:00Z"), { GH_TOKEN: "x" }, fake), ["agents.yml 204"]);
const toml = (await import("node:fs")).readFileSync(new URL("./wrangler.toml", import.meta.url), "utf8");
assert.ok(toml.includes('"20,50 * * * *"'), "wrangler.toml cron for agents");
console.log("PASS cf-timer: 9 checks");
