// Run: node core/functions/agents.test.js — Meta lead follow-up, ads bot and reminder agents against fakes.
const assert = require("assert");
const crypto = require("crypto");
const { appointmentUtc } = require("../automations.js");
const { store, graph } = require("./_fake.js")({
  clients: [
    { id: "re1", name: "Skyline Homes", niche: "realestate", phone_number_id: "PN1", owner_whatsapp: "919000000001", meta_page_id: "PAGE1", meta_ad_account_id: "111", active: true, config: { business: "Skyline Homes Realty", voice_followup: true, ads_autopilot: true } },
    { id: "gy1", name: "IronPulse", niche: "gym", phone_number_id: "PN2", owner_whatsapp: "919000000002", active: true, config: { business: "IronPulse Fitness", address: "Madhapur" } },
  ],
  client_secrets: [{ client_id: "re1", meta_page_token: "pt", meta_ads_token: "at" }],
});
const sign = (b) => "sha256=" + crypto.createHmac("sha256", "appsecret").update(b).digest("hex");

(async () => {
  console.log("BotBhai agent tests");
  // 1. Meta lead → WhatsApp welcome within the same request
  graph.responses["LEAD42"] = { ad_id: "AD9", form_id: "F1", created_time: "2026-10-12T06:00:00+0000", field_data: [
    { name: "full_name", values: ["Anil Reddy"] }, { name: "phone_number", values: ["+91 98765 43210"] }, { name: "budget", values: ["₹1Cr – ₹2Cr"] }, { name: "bhk", values: ["3 BHK"] }] };
  const body = JSON.stringify({ object: "page", entry: [{ changes: [{ field: "leadgen", value: { leadgen_id: "LEAD42", page_id: "PAGE1", form_id: "F1", ad_id: "AD9" } }] }] });
  const t0 = Date.now();
  await require("./metaleads.js").handler({ httpMethod: "POST", headers: { "x-hub-signature-256": sign(body) }, body });
  const lead = store.leads.find((l) => l.contact === "919876543210");
  assert.ok(lead && lead.source === "meta_ads" && lead.details.budget === "₹1Cr – ₹2Cr" && lead.details.consent === "meta_lead_form");
  const welcome = graph.sent.find((m) => m.type === "template" && m.to === "919876543210");
  assert.strictEqual(welcome.template.name, "bb_re_welcome"); assert.strictEqual(welcome.template.components[0].parameters[0].text, "Anil Reddy");
  assert.ok(graph.sent.some((m) => m.to === "919000000001" && /Meta lead: Anil Reddy/.test(m.text.body)));
  assert.strictEqual(store.jobs[0].type, "voice_call");
  console.log(`  ✓ Meta lead saved, WhatsApp welcome sent, owner alerted, voice call queued (${Date.now() - t0} ms)`);

  // 2. Ads bot pauses a bad ad and reports
  graph.responses["act_111/insights"] = { data: [
    { ad_id: "A1", ad_name: "3BHK Tellapur reel", spend: "3000", actions: [{ action_type: "lead", value: "10" }] },
    { ad_id: "A2", ad_name: "Plots carousel", spend: "2500", actions: [] }] };
  await require("./adsbot.js").handler();
  assert.ok(graph.calls.some((c) => c.path === "A2" && c.method === "POST" && c.body.status === "PAUSED"));
  assert.ok(!graph.calls.some((c) => c.path === "A1" && c.method === "POST"));
  assert.strictEqual(store.ad_stats.length, 2);
  const rep = graph.sent.filter((m) => m.to === "919000000001").pop().text.body;
  assert.match(rep, /Spend ₹5,500 · Leads 10 · ₹550\/lead/); assert.match(rep, /Plots carousel: ⏸ paused/);
  console.log("  ✓ ads bot paused the zero-lead ad and sent the owner report");

  // 3. Reminders: booking tomorrow + gym member expiring in 7 days
  const appt = Date.now() + 24 * 3.6e6; const d = new Date(appt + 330 * 60000);
  const iso = d.toISOString().slice(0, 10); const h = d.getUTCHours(), m = d.getUTCMinutes();
  const slot = `${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`;
  assert.ok(Math.abs(appointmentUtc(iso, slot) - appt) < 60000);
  store.leads.push({ id: "L9", client_id: "gy1", contact: "919811111111", name: "Sai", status: "booked", details: { goal: "Weight loss", date: "tomorrow", date_iso: iso, slot } });
  const exp = new Date(Date.now() + 330 * 60000 + 7 * 864e5).toISOString().slice(0, 10);
  store.members.push({ id: "M1", client_id: "gy1", phone: "919822222222", name: "Kiran", plan: "Quarterly plan", expires_on: exp, opted_out: false, reminders: {} });
  const r = await require("./reminders.js").handler();
  assert.strictEqual(r.body, "sent 2");
  assert.ok(graph.sent.some((x) => x.to === "919811111111" && x.template.name === "bb_gym_reminder_day"));
  assert.ok(graph.sent.some((x) => x.to === "919822222222" && x.template.name === "bb_gym_renew_7"));
  assert.ok(store.leads.find((l) => l.id === "L9").details.reminders.day_before);
  const again = await require("./reminders.js").handler(); assert.strictEqual(again.body, "sent 0");
  console.log("  ✓ reminder agent: trial reminder + renewal sent once, not repeated");
  console.log("\nagent tests passed");
})().catch((e) => { console.error(e); process.exit(1); });
