// Comment → DM webhook (A100), offline fixtures. Run: NO_DELAY=1 node core/functions/comments.test.js
process.env.NO_DELAY = "1";
const assert = require("assert");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const rules = [{ keyword: "price", reply: "Hi {name}! 2BHK Kondapur, ₹78 L. Details:", link: "https://botbhai.example/l/kondapur" }];
const { store, graph } = require("./_fake.js")({
  clients: [{ id: "re1", name: "Skyline", niche: "realestate", owner_whatsapp: "919000000001", phone_number_id: "PN1", meta_page_id: "100200300", ig_user_id: "17841400000000001", active: true,
    config: { business: "Skyline Homes", comment_dm: rules } }],
  vault: [{ name: "client:re1:meta_page", secret: "pagetok" }],
});
const fn = require("./comments.js");
const fx = (f) => JSON.parse(fs.readFileSync(path.join(__dirname, "../fixtures/comments", f), "utf8"));
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");
const post = async (payload, sig) => { const body = JSON.stringify(payload); const r = await fn.handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sig || sign(body) }, body }); return Object.assign(r, { data: JSON.parse(r.body) }); };
const fresh = (p) => { const b = JSON.parse(JSON.stringify(p)); for (const e of b.entry) { e.time = Math.floor(Date.now() / 1000); for (const c of e.changes) if (c.value.created_time) c.value.created_time = e.time; } return b; };
const dms = () => graph.calls.filter((c) => /\/messages$/.test(c.path) && c.body && c.body.recipient && c.body.recipient.comment_id);
let n = 0; const ok = async (name, f) => { await f(); n++; console.log("  ✓", name); };

(async () => {
  console.log("Comment → DM webhook (A100)");
  await ok("verify handshake and bad signature / method", async () => {
    assert.strictEqual((await fn.handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "verify", "hub.challenge": "42" } })).body, "42");
    assert.strictEqual((await fn.handler({ httpMethod: "GET", queryStringParameters: { "hub.mode": "subscribe", "hub.verify_token": "no" } })).statusCode, 403);
    assert.strictEqual((await post(fx("ig_comment.json"), "sha256=bad")).statusCode, 401);
    assert.strictEqual((await fn.handler({ httpMethod: "PUT", headers: {} })).statusCode, 405);
  });
  await ok("dry run by default: IG keyword comment → lead + inbox chat saved, NOTHING sent", async () => {
    const r = await post(fresh(fx("ig_comment.json")));
    assert.deepStrictEqual(r.data.results, ["dry_run"]);
    assert.strictEqual(dms().length, 0);
    assert.strictEqual(graph.sent.length, 0); // no owner alert either
    const lead = store.leads.find((l) => l.contact === "ig:1789000000000077");
    assert.strictEqual(lead.source, "instagram_comment");
    assert.strictEqual(lead.details.comment.keyword, "price");
    assert.strictEqual(lead.details.comment.dm, "dry_run");
    assert.ok(store.sessions.find((s) => s.contact === "ig:1789000000000077"), "shows in the inbox");
    assert.ok(store.messages.some((m) => m.contact === "ig:1789000000000077" && m.direction === "out" && m.body.startsWith("[dry run, not sent] Hi asha.hyd!")));
  });
  await ok("Meta retries the same comment: handled once", async () => {
    assert.deepStrictEqual((await post(fresh(fx("ig_comment.json")))).data.results, ["duplicate"]);
    assert.strictEqual(store.leads.filter((l) => l.contact === "ig:1789000000000077").length, 1);
  });
  await ok("env switch alone is not enough: client must opt in too", async () => {
    process.env.COMMENT_DM_LIVE = "1";
    const b = fresh(fx("ig_comment.json")); b.entry[0].changes[0].value.id = "17900000000000012";
    assert.deepStrictEqual((await post(b)).data.results, ["dry_run"]);
    assert.strictEqual(dms().length, 0);
  });
  await ok("live: FB comment → one private reply to the comment id via the Page, with the Vault token; owner alerted", async () => {
    store.clients[0].config.comment_dm_live = true;
    const r = await post(fresh(fx("fb_feed.json")));
    assert.deepStrictEqual(r.data.results, ["sent"]);
    const [dm] = dms();
    assert.strictEqual(dm.path, "100200300/messages");
    assert.strictEqual(dm.auth, "Bearer pagetok");
    assert.deepStrictEqual(dm.body.recipient, { comment_id: "100200300_555_777" });
    assert.ok(dm.body.message.text.includes("https://botbhai.example/l/kondapur"));
    assert.strictEqual(store.leads.find((l) => l.contact === "fb:6543210").details.comment.dm, "sent");
    assert.ok(graph.sent.some((m) => m.to === "919000000001"), "owner alert on WhatsApp");
  });
  await ok("never DMs: no keyword, older than 7 days, own account, unknown account, bad ids", async () => {
    const before = dms().length;
    const mk = (v, id) => { const b = fresh(fx("ig_comment.json")); Object.assign(b.entry[0].changes[0].value, v); if (id) b.entry[0].id = id; return b; };
    assert.deepStrictEqual((await post(mk({ id: "1", text: "lovely flat" }))).data.results, ["no_keyword"]);
    const old = mk({ id: "2" }); old.entry[0].time -= 8 * 86400;
    assert.deepStrictEqual((await post(old)).data.results, ["too_old"]);
    assert.deepStrictEqual((await post(mk({ id: "3", from: { id: "17841400000000001", username: "skyline" } }))).data.results, ["own_comment"]);
    assert.deepStrictEqual((await post(mk({ id: "4" }, "999"))).data.results, ["no_client"]);
    assert.deepStrictEqual((await post(mk({ id: "5&active=eq.false" }))).data.results, ["bad_ids"]);
    assert.strictEqual(dms().length, before);
  });
  await ok("no Page token in Vault: nothing sent, lead still saved", async () => {
    store.vault.length = 0;
    const b = fresh(fx("ig_comment.json")); Object.assign(b.entry[0].changes[0].value, { id: "6", from: { id: "1789000000000088", username: "kiran" } });
    assert.deepStrictEqual((await post(b)).data.results, ["dry_run"]);
    assert.ok(store.leads.find((l) => l.contact === "ig:1789000000000088"));
  });
  await ok("rubbish JSON → 400, no crash", async () => {
    const body = "{not json"; assert.strictEqual((await fn.handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body })).statusCode, 400);
  });
  delete process.env.COMMENT_DM_LIVE;
  console.log(`${n} comment→DM webhook tests passed`);
})().catch((e) => { console.error(e); process.exit(1); });
