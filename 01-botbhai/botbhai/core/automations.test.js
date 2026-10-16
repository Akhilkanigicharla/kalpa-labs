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
  assert.deepStrictEqual(A.dueReminders(lead, appt + 24 * 3.6e6), [], "no review ask until the owner marks the visit done (M10)");
  assert.deepStrictEqual(A.dueReminders(lead, appt + 24 * 3.6e6, "completed"), ["after_visit"]);
  assert.deepStrictEqual(A.dueReminders(lead, appt + 24 * 3.6e6, "no_show"), [], "never thank a no-show");
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
ok("autopilot pauses at most half the ads, worst first", () => {
  const v = A.capPauses(A.judgeAds([
    { ad_id: "1", ad_name: "A", spend: "1000", actions: [] },
    { ad_id: "2", ad_name: "B", spend: "1500", actions: [{ action_type: "lead", value: "1" }] },
    { ad_id: "3", ad_name: "C", spend: "900", actions: [{ action_type: "lead", value: "1" }] },
    { ad_id: "4", ad_name: "D", spend: "800", actions: [{ action_type: "lead", value: "4" }] }], { target_cpl: 300 }));
  assert.deepStrictEqual(v.map((x) => x.verdict), ["pause", "pause", "pause_suggested", "scale"]);
  assert.match(A.adsReport("X", v, true), /C: ⚠️ pause suggested/);
});
ok("weekly summary counts only the last 7 days", () => {
  const now = Date.UTC(2026, 9, 12);
  const t = A.weeklySummary("Glow Studio", [
    { score: "hot", status: "booked", source: "whatsapp", created_at: "2026-10-10T10:00:00Z" },
    { score: "warm", status: "callback", source: "meta_ads", created_at: "2026-10-11T10:00:00Z" },
    { score: "hot", status: "booked", source: "whatsapp", created_at: "2026-09-01T10:00:00Z" }], now);
  assert.match(t, /New leads: 2 \(hot 1, warm 1, cold 0\)/); assert.match(t, /Booked: 1 · Asked for a call: 1/); assert.match(t, /whatsapp 1, meta_ads 1/);
});
ok("referral: stable code + friend invite 3 days after the visit", () => {
  const c = A.referralCode("919876543210"); assert.match(c, /^REF-[A-Z0-9]{4}$/); assert.strictEqual(c, A.referralCode("919876543210"));
  assert.notStrictEqual(c, A.referralCode("919876543211"));
  const lead = { status: "booked", details: { date_iso: "2026-10-13", slot: "4:00 PM", reminders: { after_visit: true } } };
  assert.deepStrictEqual(A.dueReminders(lead, A.appointmentUtc("2026-10-13", "4:00 PM") + 75 * 3.6e6, "completed"), ["refer"]);
  assert.deepStrictEqual(A.dueReminders(lead, A.appointmentUtc("2026-10-13", "4:00 PM") + 75 * 3.6e6, "confirmed"), []);
});
ok("M10: 9 PM close-the-day list numbers today's visits by time", () => {
  const list = A.dayCloseList([
    { id: "b2", name: "Ravi", service: "Hair spa", slot: "4:00 PM" }, { id: "b1", name: "Priya", service: "Facial (fruit / gold)", slot: "11:00 AM" },
    { id: "b3", name: null, service: null, slot: "7:00 PM" }], "2026-10-12");
  assert.deepStrictEqual(list.ids, ["b1", "b2", "b3"]);
  assert.match(list.text, /Mon, 12 Oct/); assert.match(list.text, /1\. 11:00 AM · Priya · Facial/); assert.match(list.text, /3\. 7:00 PM · Customer/);
  assert.match(list.text, /all done except/); assert.strictEqual(A.dayCloseList([], "2026-10-12"), null);
});
ok("M10: owner replies parsed (all done / except / no show / done N / Telugu + Hindi)", () => {
  const P = A.parseDayClose;
  assert.deepStrictEqual(P("all done", 4), { completed: [1, 2, 3, 4], no_show: [] });
  assert.deepStrictEqual(P("All done except 3", 4), { completed: [1, 2, 4], no_show: [3] });
  assert.deepStrictEqual(P("done except 2,4", 4), { completed: [1, 3], no_show: [2, 4] });
  assert.deepStrictEqual(P("no show 2 3", 4), { completed: [], no_show: [2, 3] });
  assert.deepStrictEqual(P("2 didn't come", 3), { completed: [], no_show: [2] });
  assert.deepStrictEqual(P("done 1 3, no show 2", 3), { completed: [1, 3], no_show: [2] });
  assert.deepStrictEqual(P("anni ayyayi 2 raledu", 3), { completed: [1, 3], no_show: [2] });
  assert.deepStrictEqual(P("sab ho gaye", 2), { completed: [1, 2], no_show: [] });
  assert.deepStrictEqual(P("all done except 9", 3), { completed: [1, 2, 3], no_show: [] }, "out-of-range numbers ignored");
  assert.strictEqual(P("hi", 3), null); assert.strictEqual(P("what time tomorrow?", 3), null); assert.strictEqual(P("all done", 0), null);
});
console.log(`\n${n} tests passed`);
