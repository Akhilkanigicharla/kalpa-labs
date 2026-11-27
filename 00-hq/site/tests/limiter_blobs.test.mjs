// A303: the shared limiter against the real @netlify/blobs package and its local BlobsServer (no network, no account).
// Each call gets a fresh local Map, like a new Netlify function copy; the 13th message in a minute must still be refused.
// Needs `npm ci` in 00-hq/site once.  node 00-hq/site/tests/limiter_blobs.test.mjs
import assert from "node:assert";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { BlobsServer } from "@netlify/blobs/server";
import { getStore } from "@netlify/blobs";
import { limitedShared, LIMIT } from "../netlify/functions/chat.mjs";
const dir = mkdtempSync(join(tmpdir(), "blobs-")), port = 20000 + Math.floor(Math.random() * 20000);
const server = new BlobsServer({ directory: dir, token: "t", port }); await server.start();
try {
  const url = `http://localhost:${port}`;
  const store = getStore({ name: "chat-limit", consistency: "strong", edgeURL: url, uncachedEdgeURL: url, siteID: "s", token: "t" });
  await store.setJSON("2020-01-01/" + "c".repeat(32), { t: 1, n: 1 });
  const now = Date.now(), out = [];
  for (let k = 0; k <= LIMIT; k++) out.push(await limitedShared("10.0.0.1", { store, mem: new Map(), now: now + k, sweep: k === 0, timeoutMs: 2000 }));
  assert.strictEqual(out.map(Number).join(""), "0".repeat(LIMIT) + "1");
  const { blobs } = await store.list();
  assert.strictEqual(blobs.length, 1); assert.ok(!blobs[0].key.startsWith("2020-"), "old day swept");
  console.log("limiter on real Blobs package: PASS");
} finally { await server.stop(); rmSync(dir, { recursive: true, force: true }); }
