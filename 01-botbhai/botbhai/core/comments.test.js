// Comment → DM (A100) pure logic. Run: node core/comments.test.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const C = require("./comments.js");
const fx = (f) => JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/comments", f), "utf8"));
const NOW = Date.parse("2026-11-01T10:00:00Z");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };

console.log("Comment → DM logic (A100)");
ok("parses an Instagram comments webhook (fixture)", () => {
  const [e] = C.parseCommentEvents(fx("ig_comment.json"));
  assert.deepStrictEqual({ p: e.platform, a: e.account_id, c: e.comment_id, t: e.text, f: e.from_id, u: e.from_name, m: e.media_id },
    { p: "instagram", a: "17841400000000001", c: "17900000000000011", t: "PRICE please", f: "1789000000000077", u: "asha.hyd", m: "17950000000000099" });
});
ok("parses a Facebook Page feed comment and ignores likes / edits / posts", () => {
  const ev = C.parseCommentEvents(fx("fb_feed.json"));
  assert.strictEqual(ev.length, 1);
  assert.deepStrictEqual([ev[0].platform, ev[0].account_id, ev[0].comment_id, ev[0].from_name, ev[0].media_id], ["facebook", "100200300", "100200300_555_777", "Ravi K", "100200300_555"]);
  assert.strictEqual(ev[0].created_ms, 1761991200000);
});
ok("rubbish bodies give no events", () => {
  for (const b of [null, {}, { entry: "x" }, { object: "instagram", entry: [{ changes: [{ field: "comments", value: {} }] }] }]) assert.deepStrictEqual(C.parseCommentEvents(b), []);
});
const rules = [{ keyword: "price", reply: "Hi {name}! 2BHK Kondapur ₹78 L.", link: "https://botbhai.example/l/kondapur" }, { keyword: "visit", reply: "Book a visit here:", media_id: "M2" }];
ok("keyword match: whole word, any case, Telugu/Hindi text around it", () => {
  assert.strictEqual(C.matchRule("PRICE please", rules).keyword, "price");
  assert.strictEqual(C.matchRule("ధర? price ఎంత", rules).keyword, "price");
  assert.strictEqual(C.matchRule("priceless view", rules), null);
  assert.strictEqual(C.matchRule("nice flat", rules), null);
});
ok("a rule tied to one post only fires on that post", () => {
  assert.strictEqual(C.matchRule("visit", rules, "M1"), null);
  assert.strictEqual(C.matchRule("visit", rules, "M2").keyword, "visit");
});
ok("decide: replies once, inside 7 days, never to our own account", () => {
  const e = { platform: "instagram", account_id: "A", comment_id: "c1", text: "price", from_id: "U", from_name: "asha", created_ms: NOW - 3600e3 };
  assert.strictEqual(C.decide(e, rules, NOW).action, "reply");
  assert.strictEqual(C.decide(Object.assign({}, e, { from_id: "A" }), rules, NOW).reason, "own_comment");
  assert.strictEqual(C.decide(Object.assign({}, e, { created_ms: NOW - 8 * 864e5 }), rules, NOW).reason, "too_old");
  assert.strictEqual(C.decide(Object.assign({}, e, { text: "wow" }), rules, NOW).reason, "no_keyword");
  assert.strictEqual(C.decide(e, [], NOW).reason, "no_keyword");
});
ok("reply text: name filled, link added, length capped, no template braces left", () => {
  const t = C.replyText(rules[0], { from_name: "asha.hyd" }, "Skyline Homes");
  assert.ok(t.startsWith("Hi asha.hyd! 2BHK Kondapur"));
  assert.ok(t.includes("https://botbhai.example/l/kondapur"));
  assert.ok(!/[{}]/.test(C.replyText({ keyword: "x", reply: "Hi {name} {oops}" }, {}, "B")));
  assert.ok(C.replyText({ keyword: "x", reply: "a".repeat(5000) }, {}, "B").length <= 1000);
});
ok("send body uses the comment id as recipient (Meta private replies)", () => {
  assert.deepStrictEqual(C.sendBody("c9", "hi"), { recipient: { comment_id: "c9" }, message: { text: "hi" } });
});
console.log(`${n} comment→DM tests passed`);
