// Run: node core/automations.test.js
const assert = require("assert");
const A = require("./automations.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
console.log("BotBhai automation tests");

ok("phone normalisation", () => {
  assert.strictEqual(A.normalizePhone("+91 98480 12345"), "919848012345");
  assert.strictEqual(A.normalizePhone("09848012345"), "919848012345");
  assert.strictEqual(A.normalizePhone("9848012345"), "919848012345");
  assert.strictEqual(A.normalizePhone("12345"), "");
  assert.strictEqual(A.normalizePhone("+971501234567"), "971501234567");
});
ok("Meta lead parsing keeps custom answers", () => {
  const l = A.parseMetaLead({ ad_id: "ad1", form_id: "f1", field_data: [
    { name: "full_name", values: ["Anil Reddy"] }, { name: "phone_number", values: ["+919876543210"] },
    { name: "email", values: ["a@x.in"] }, { name: "what_is_your_budget?", values: ["₹1Cr – ₹2Cr"] }] });
  assert.strictEqual(l.name, "Anil Reddy"); assert.strictEqual(l.phone, "919876543210");
  assert.deepStrictEqual(l.answers, { "what_is_your_budget?": "₹1Cr – ₹2Cr" });
});
ok("ad guard verdicts", () => {
  const v = A.judgeAds([
    { ad_id: "1", ad_name: "Good", spend: "1200", actions: [{ action_type: "lead", value: "6" }] },     // ₹200 vs target 400 → scale
    { ad_id: "2", ad_name: "Bad", spend: "1500", actions: [{ action_type: "lead", value: "2" }] },      // ₹750 > 640 → pause
    { ad_id: "3", ad_name: "Dead", spend: "700", actions: [] },                                         // 0 leads, ≥600 → pause
    { ad_id: "4", ad_name: "New", spend: "120", actions: [] },                                          // learning
    { ad_id: "5", ad_name: "OK", spend: "800", actions: [{ action_type: "onsite_conversion.messaging_conversation_started_7d", value: "2" }] }, // ₹400 keep
  ], { target_cpl: 400 });
  assert.deepStrictEqual(v.map((x) => x.verdict), ["scale", "pause", "pause", "learning", "keep"]);
  const rep = A.adsReport("Skyline Homes", v, false);
  assert.match(rep, /Spend ₹4,320 · Leads 10 · ₹432\/lead/); assert.match(rep, /pause suggested/);
});
ok("appointment time in IST", () => {
  // 13 Oct 2026 4:00 PM IST = 10:30 UTC
  assert.strictEqual(new Date(A.appointmentUtc("2026-10-13", "4:00 PM")).toISOString(), "2026-10-13T10:30:00.000Z");
  assert.strictEqual(A.slotToMinutes("12:00 PM"), 720); assert.strictEqual(A.slotToMinutes("12:30 AM"), 30);
});
ok("booking reminders fire once in each window", () => {
  const lead = { status: "booked", details: { date_iso: "2026-10-13", slot: "4:00 PM", reminders: {} } };
  const appt = A.appointmentUtc("2026-10-13", "4:00 PM");
  assert.deepStrictEqual(A.dueReminders(lead, appt - 24 * 3.6e6), ["day_before"]);
  assert.deepStrictEqual(A.dueReminders(lead, appt - 2 * 3.6e6), ["two_hours"]);
  assert.deepStrictEqual(A.dueReminders(lead, appt + 24 * 3.6e6), ["after_visit"]);
  lead.details.reminders.two_hours = true; assert.deepStrictEqual(A.dueReminders(lead, appt - 2 * 3.6e6), []);
  assert.deepStrictEqual(A.dueReminders({ status: "callback", details: lead.details }, appt - 24 * 3.6e6), []);
});
ok("renewal reminders 7/3/1 days and win-back", () => {
  const now = Date.UTC(2026, 9, 12, 4, 0); // 12 Oct 9:30 AM IST
  assert.deepStrictEqual(A.dueRenewals({ expires_on: "2026-10-19" }, now), ["renew_7"]);
  assert.deepStrictEqual(A.dueRenewals({ expires_on: "2026-10-13" }, now), ["renew_1"]);
  assert.deepStrictEqual(A.dueRenewals({ expires_on: "2026-09-27" }, now), ["winback"]);
  assert.deepStrictEqual(A.dueRenewals({ expires_on: "2026-10-19", reminders: { renew_7: true } }, now), []);
});
console.log(`\n${n} tests passed`);
