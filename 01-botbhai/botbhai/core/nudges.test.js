// Run: node core/nudges.test.js — owner nudges appended to the 9 PM close-the-day message (A80)
const assert = require("assert");
const { ownerNudges } = require("./automations.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
console.log("BotBhai owner nudge tests");
const T = "2026-11-20"; // today (Fri); tomorrow = 2026-11-21
const b = (contact, name, date_iso, status = "confirmed", confirmed_at = null) => ({ contact, name, date_iso, slot: "11:00 AM", status, confirmed_at });

ok("nothing to say → empty string", () => {
  assert.strictEqual(ownerNudges([], T), "");
  assert.strictEqual(ownerNudges(null, T), "");
});

ok("tomorrow: counts visits and names the ones not confirmed", () => {
  const out = ownerNudges([b("1", "Ravi", "2026-11-21", "confirmed", "2026-11-20T08:00:00Z"), b("2", "Sita", "2026-11-21"), b("3", "Anu", "2026-11-21", "rescheduled"), b("4", "X", "2026-11-21", "cancelled")], T);
  assert.match(out, /Tomorrow: 3 visits, 2 not confirmed yet \(Sita, Anu\)/);
});

ok("tomorrow empty is said only when the salon had visits recently", () => {
  assert.match(ownerNudges([b("1", "Ravi", "2026-11-18", "completed")], T), /Tomorrow has no bookings yet/);
});

ok("no-shows in the last 7 days who have not rebooked", () => {
  const out = ownerNudges([b("1", "Ravi", "2026-11-17", "no_show"), b("2", "Sita", "2026-11-18", "no_show"), b("2", "Sita", "2026-11-23"), b("3", "Old", "2026-11-01", "no_show")], T);
  assert.match(out, /1 no-show this week has not rebooked: Ravi/);
  assert.doesNotMatch(out, /Sita|Old/);
});

ok("regulars (2+ visits) not seen in 45+ days and not booked ahead", () => {
  const rows = [b("1", "Lakshmi", "2026-08-01", "completed"), b("1", "Lakshmi", "2026-09-20", "completed"),
    b("2", "Once", "2026-08-01", "completed"),
    b("3", "Recent", "2026-08-01", "completed"), b("3", "Recent", "2026-11-10", "completed"),
    b("4", "Booked", "2026-08-01", "completed"), b("4", "Booked", "2026-09-01", "completed"), b("4", "Booked", "2026-11-25")];
  const out = ownerNudges(rows, T);
  assert.match(out, /1 regular has not come in 45\+ days: Lakshmi/);
  assert.match(out, /a call from you works better than a bot message/);
  assert.doesNotMatch(out, /Once|Recent|Booked\b.*45/);
});

ok("this week vs last week counts completed visits only", () => {
  const rows = [b("1", "A", "2026-11-20", "completed"), b("2", "B", "2026-11-14", "completed"), b("3", "C", "2026-11-13", "completed"), b("4", "D", "2026-11-12", "completed"), b("5", "E", "2026-11-19", "no_show")];
  assert.match(ownerNudges(rows, T), /This week: 2 visits done \(last week 2\)/);
});

ok("long name lists are cut to 3 plus a count; missing names say Customer", () => {
  const rows = ["A", "B", "C", "D", null].map((nm, i) => b(String(i), nm, "2026-11-21"));
  assert.match(ownerNudges(rows, T), /5 not confirmed yet \(A, B, C \+2 more\)/);
  assert.match(ownerNudges([b("9", "", "2026-11-21")], T), /\(Customer\)/);
});

ok("at most 4 lines, under a heading, and never offers to message customers", () => {
  const rows = [b("1", "T", "2026-11-21"), b("2", "N", "2026-11-17", "no_show"), b("3", "R", "2026-08-01", "completed"), b("3", "R", "2026-09-01", "completed"), b("4", "W", "2026-11-19", "completed")];
  const out = ownerNudges(rows, T);
  const lines = out.split("\n").filter((l) => l.trim());
  assert.strictEqual(lines[0], "💡 For you:");
  assert.ok(lines.length <= 5, out);
  assert.doesNotMatch(out, /I will message|bot will send|sending them/i);
});

ok("bad dates and unknown statuses are ignored, not crashed on", () => {
  assert.strictEqual(ownerNudges([{ contact: "1", date_iso: "not-a-date", status: "confirmed" }, { contact: "2", date_iso: T, status: "weird" }], T), "");
});

console.log(`owner nudge tests passed (${n})`);
