// Billing function (A05) against the in-memory Supabase + Meta fake. Run: NO_DELAY=1 node core/functions/billing.test.js
const assert = require("assert");
const ADMIN = "k".repeat(40);
Object.assign(process.env, { SITE_URL: "https://botbhai.example", BILLING_ADMIN_KEY: ADMIN, BILLING_UPI_ID: "kalpalabs@ybl", BILLING_PHONE: "+91 90000 00000" });
const { store, graph } = require("./_fake.js")({ clients: [
  { id: "c1", name: "Glow Studio", niche: "salon", phone_number_id: "PNID", owner_whatsapp: "919000000000", active: true, config: { business: "Glow Studio", address: "Ameerpet, Hyderabad" } },
  { id: "c2", name: "Shine Salon", niche: "salon", phone_number_id: "PNID2", owner_whatsapp: "919111111111", active: true, config: {} },
] });
const { handler } = require("./billing.js");
const call = (method, body, { key = ADMIN, query, ip = "1.2.3.4" } = {}) => handler({ httpMethod: method, headers: Object.assign({ "x-nf-client-connection-ip": ip }, key ? { authorization: "Bearer " + key } : {}), queryStringParameters: query || {}, body: body ? JSON.stringify(body) : undefined })
  .then((r) => Object.assign(r, { data: /json/.test((r.headers || {})["Content-Type"] || "") ? JSON.parse(r.body) : null }));
const toOwner = (n) => graph.sent.filter((m) => m.to === n);
let k = 0; const ok = (name) => { k++; console.log("  ✓ " + name); };

(async () => {
  // ---- admin auth
  assert.strictEqual((await call("GET", null, { key: null })).statusCode, 401);
  assert.strictEqual((await call("GET", null, { key: "x".repeat(40) })).statusCode, 401);
  const saved = process.env.BILLING_ADMIN_KEY; process.env.BILLING_ADMIN_KEY = "short";
  assert.strictEqual((await call("GET", null, { key: "short" })).statusCode, 503, "a weak admin key must disable admin");
  process.env.BILLING_ADMIN_KEY = saved; ok("admin needs the BILLING_ADMIN_KEY (≥ 32 characters); wrong or weak key refused");

  // ---- create
  let r = await call("POST", { action: "create", client_id: "c1", items: [{ desc: "BotBhai Founding setup", amount: 2999 }], period: "Oct 2026", due_days: 7 });
  assert.strictEqual(r.statusCode, 200, r.body);
  const inv = r.data.invoice;
  assert.match(inv.number, /^KL\/\d\d-\d\d\/001$/); assert.strictEqual(inv.total_paise, 299900); assert.strictEqual(inv.status, "due");
  assert.strictEqual(inv.bill_to.name, "Glow Studio"); assert.strictEqual(inv.bill_to.address, "Ameerpet, Hyderabad");
  assert.ok(inv.due_on > inv.issued_on); assert.match(inv.link, /^https:\/\/botbhai\.example\/\.netlify\/functions\/billing\?v=[0-9a-f]{32}$/);
  ok("create: numbered KL/YY-YY/001, bill-to snapshot from the client, due in 7 days, view link");
  r = await call("POST", { action: "create", client_id: "c2", items: [{ desc: "Monthly plan", amount: 1499 }, { desc: "Extra voice minutes", amount: 3, qty: 50 }], period: "Nov 2026" });
  assert.strictEqual(r.data.invoice.total_paise, 149900 + 15000); assert.match(r.data.invoice.number, /\/002$/);
  ok("create: several lines, quantity × rate, next number 002");
  for (const bad of [{ client_id: "nope", items: [{ desc: "x", amount: 1 }] }, { client_id: "c1", items: [] }, { client_id: "c1", items: [{ desc: "x", amount: -1 }] }, { client_id: "c1", items: [{ desc: "x", amount: 1 }], due_days: 400 }]) {
    const b = await call("POST", Object.assign({ action: "create" }, bad));
    assert.ok([400, 404].includes(b.statusCode), JSON.stringify(bad) + " → " + b.statusCode);
  }
  assert.strictEqual(store.invoices.length, 2); ok("create: bad client, no lines, negative amount, silly due date refused (no number used up)");

  // ---- the salon's page (no login)
  const key = inv.link.split("v=")[1];
  let page = await call("GET", null, { key: null, query: { v: key } });
  assert.strictEqual(page.statusCode, 200); assert.match(page.headers["Content-Type"], /text\/html/);
  assert.match(page.body, /<h1>Invoice<\/h1>/); assert.match(page.body, /UDYAM-TS-02-0382711/); assert.match(page.body, /upi:\/\/pay\?pa=kalpalabs%40ybl/);
  assert.match(page.headers["Content-Security-Policy"], /default-src 'none'/); assert.strictEqual(page.headers["Cache-Control"], "no-store");
  assert.match(page.headers["X-Robots-Tag"], /noindex/); assert.ok(!("Access-Control-Allow-Origin" in page.headers));
  ok("public page: invoice HTML with UPI link, strict CSP, no-store, noindex, no CORS");
  assert.strictEqual((await call("GET", null, { key: null, query: { v: "0".repeat(32) } })).statusCode, 404);
  assert.strictEqual((await call("GET", null, { key: null, query: { v: "../etc" } })).statusCode, 404);
  ok("public page: unknown or malformed key → 404");

  // ---- send on WhatsApp
  r = await call("POST", { action: "send", number: inv.number });
  assert.strictEqual(r.statusCode, 200, r.body);
  const msg = toOwner("919000000000").pop(); assert.strictEqual(msg.type, "text");
  assert.match(msg.text.body, new RegExp(`Invoice ${inv.number.replace(/\//g, "\\/")}`)); assert.match(msg.text.body, /₹2,999\.00/); assert.match(msg.text.body, /v=[0-9a-f]{32}/);
  assert.ok(store.invoices[0].sent_at); ok("send: WhatsApp text to the owner with amount, due date and link; sent_at saved");
  graph.failNextTextTo = "919000000000"; // outside the 24-hour window → approved utility template
  r = await call("POST", { action: "send", number: inv.number }); assert.strictEqual(r.statusCode, 200);
  const tpl = toOwner("919000000000").pop(); assert.strictEqual(tpl.type, "template"); assert.match(JSON.stringify(tpl.template.components), /botbhai\.example/);
  ok("send: falls back to the owner_alert template outside the 24-hour window");
  process.env.SITE_URL = "https://botbhai-glow-studio-ameerpet-hyderabad.netlify.app"; graph.failNextTextTo = "919000000000";
  await call("POST", { action: "send", number: inv.number });
  const sent = JSON.stringify(toOwner("919000000000").pop().template.components);
  assert.ok(sent.includes(`https://botbhai-glow-studio-ameerpet-hyderabad.netlify.app/.netlify/functions/billing?v=${key}`), "link cut in template: " + sent);
  process.env.SITE_URL = "https://botbhai.example"; ok("template fallback never cuts the payment link (long site URL)");

  // ---- reminders, paid, void
  store.invoices[0].due_on = "2026-01-01";
  r = await call("POST", { action: "remind", number: inv.number }); assert.strictEqual(r.statusCode, 200);
  assert.match(toOwner("919000000000").pop().text.body, /reminder.*overdue/is); ok("remind: polite overdue reminder");
  let list = (await call("GET")).data;
  assert.strictEqual(list.invoices.length, 2); assert.ok(list.invoices.find((i) => i.number === inv.number).overdue_days > 200);
  assert.deepStrictEqual(list.clients.map((c) => c.name).sort(), ["Glow Studio", "Shine Salon"]); assert.strictEqual(list.seller.upi_ready, true);
  ok("list: invoices with overdue days, clients for the form, seller readiness");
  assert.strictEqual((await call("POST", { action: "paid", number: inv.number, ref: "62981234 5678" })).statusCode, 400);
  r = await call("POST", { action: "paid", number: inv.number, ref: "629812345678" }); assert.strictEqual(r.statusCode, 200);
  assert.strictEqual(store.invoices[0].status, "paid"); assert.ok(store.invoices[0].paid_on); assert.strictEqual(store.invoices[0].paid_ref, "629812345678");
  page = await call("GET", null, { key: null, query: { v: key } });
  assert.match(page.body, /class="stamp paid"/); assert.doesNotMatch(page.body, /upi:\/\/pay/); ok("paid: UPI ref checked and saved; page shows PAID and no pay button");
  assert.strictEqual((await call("POST", { action: "remind", number: inv.number })).statusCode, 409); ok("remind refused for a paid invoice");
  r = await call("POST", { action: "void", number: store.invoices[1].number }); assert.strictEqual(r.statusCode, 200); assert.strictEqual(store.invoices[1].status, "void");
  assert.strictEqual((await call("POST", { action: "paid", number: store.invoices[1].number })).statusCode, 409);
  assert.strictEqual(store.invoices.length, 2); ok("void keeps the number (never deleted); a void invoice can't be marked paid");
  assert.strictEqual((await call("POST", { action: "nuke", number: inv.number })).statusCode, 400);
  assert.strictEqual((await call("POST", { action: "paid", number: "KL/26-27/777" })).statusCode, 404);
  assert.strictEqual((await call("DELETE")).statusCode, 405); ok("unknown action, unknown number, other methods refused");

  // ---- public page is rate-limited per IP (keys can't be guessed by brute force)
  let last; for (let i = 0; i < 70; i++) last = await call("GET", null, { key: null, ip: "9.9.9.9", query: { v: "1".repeat(32) } });
  assert.strictEqual(last.statusCode, 429); ok("public page rate-limited per IP");
  console.log(`\nbilling function tests passed (${k})`);
})().catch((e) => { console.error(e); process.exit(1); });
