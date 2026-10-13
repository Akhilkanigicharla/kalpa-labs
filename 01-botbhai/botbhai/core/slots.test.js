// Run: node core/slots.test.js   (A02: slot engine unit tests; no network)
const assert = require("assert");
const S = require("./slots.js");
let n = 0; const ok = (name, fn) => { fn(); n++; console.log("  ✓", name); };
const labels = (xs) => xs.map((x) => x.label);
// 2026-10-14 is a Wednesday; 2026-10-18 a Sunday; 2026-10-20 a Tuesday.
const base = {
  schedule: {
    hours: { default: [["10:00", "20:00"]], sun: [["11:00", "14:00"]] },
    weekly_off: [2],
    breaks: [["14:00", "15:00"]],
    interval: 30,
    default_minutes: 30,
    durations: { "Keratin treatment": 90 },
  },
  holidays: [{ date: "2026-11-08", name: "Diwali" }],
  capacity: 1,
  lead_minutes: 30,
};
const ist = (iso, hhmm) => new Date(`${iso}T${hhmm}:00+05:30`).getTime();

console.log("BotBhai slot engine tests");

ok("time parsing and labels round-trip", () => {
  assert.strictEqual(S.toMin("10:00"), 600);
  assert.strictEqual(S.toMin("7 pm"), 1140);
  assert.strictEqual(S.toMin("12:30 AM"), 30);
  assert.strictEqual(S.toMin("12 pm"), 720);
  assert.strictEqual(S.toMin("25:00"), null);
  assert.strictEqual(S.toMin("13 pm"), null);
  assert.strictEqual(S.label(960), "4:00 PM");
  assert.strictEqual(S.label(S.toMin("9:30 AM")), "9:30 AM");
});

ok("range maths: merge, subtract, intersect", () => {
  const r = (a, b) => ({ start: a, end: b });
  assert.deepStrictEqual(S.merge([r(600, 700), r(650, 800), r(900, 950)]), [r(600, 800), r(900, 950)]);
  assert.deepStrictEqual(S.subtract([r(600, 1200)], [r(840, 900)]), [r(600, 840), r(900, 1200)]);
  assert.deepStrictEqual(S.intersect([r(600, 1200)], [r(720, 1260)]), [r(720, 1200)]);
});

ok("weekday hours with a lunch break, 30-min grid", () => {
  const xs = labels(S.free({ cfg: base, date_iso: "2026-10-14" }));
  assert.strictEqual(xs[0], "10:00 AM");
  assert.strictEqual(xs[xs.length - 1], "7:30 PM");          // 7:30 + 30 min ends exactly at 8 PM
  assert.ok(!xs.includes("2:00 PM") && !xs.includes("2:30 PM")); // break
  assert.ok(xs.includes("1:30 PM") && xs.includes("3:00 PM"));
  assert.strictEqual(xs.length, 18);
});

ok("per-day hours (short Sunday) and weekly off", () => {
  assert.deepStrictEqual(labels(S.free({ cfg: base, date_iso: "2026-10-18" })), ["11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM"]);
  assert.deepStrictEqual(S.free({ cfg: base, date_iso: "2026-10-20" }), []);
  assert.strictEqual(S.closedReason(base, "2026-10-20"), "we're closed on Tuesdays");
});

ok("holiday closes the day with its name", () => {
  assert.deepStrictEqual(S.free({ cfg: base, date_iso: "2026-11-08" }), []);
  assert.strictEqual(S.closedReason(base, "2026-11-08"), "we're closed for Diwali");
});

ok("special date REPLACES weekly hours (cal.com override rule), even on a weekly-off day", () => {
  const cfg = JSON.parse(JSON.stringify(base));
  cfg.schedule.special = [{ date: "2026-10-20", hours: [["10:00", "12:00"]], name: "Dhanteras" },
                          { date: "2026-10-21", closed: true, name: "staff outing" }];
  assert.deepStrictEqual(labels(S.free({ cfg, date_iso: "2026-10-20" })), ["10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM"]);
  assert.deepStrictEqual(S.free({ cfg, date_iso: "2026-10-21" }), []);
  assert.match(S.closedReason(cfg, "2026-10-21"), /closed on Wed, 21 Oct \(staff outing\)/);
});

ok("closing early today trims the day; closed today closes it", () => {
  const cfg = JSON.parse(JSON.stringify(base));
  cfg.schedule.closing_today = { date: "2026-10-14", at: "16:00" };
  const xs = labels(S.free({ cfg, date_iso: "2026-10-14" }));
  assert.strictEqual(xs[xs.length - 1], "3:30 PM");
  assert.strictEqual(S.day(cfg, "2026-10-14").note, "closing early today at 4:00 PM");
  cfg.schedule.closing_today = { date: "2026-10-14", closed: true };
  assert.deepStrictEqual(S.free({ cfg, date_iso: "2026-10-14" }), []);
});

ok("owner phrases become closing entries", () => {
  const now = ist("2026-10-14", "11:00");
  assert.deepStrictEqual(S.parseClosing("closing early today at 6", now), { date: "2026-10-14", at: "6:00 PM" });
  assert.deepStrictEqual(S.parseClosing("shop closed today", now), { date: "2026-10-14", closed: true });
  assert.strictEqual(S.parseClosing("what time do you close?", now), null);
});

ok("minimum notice + IST rounding: 11:07 AM now -> first slot 12:00 PM", () => {
  const xs = labels(S.free({ cfg: base, date_iso: "2026-10-14", now: ist("2026-10-14", "11:07") }));
  assert.strictEqual(xs[0], "12:00 PM");                       // 11:37 rounded up to the 30-min grid
  const tomorrow = labels(S.free({ cfg: base, date_iso: "2026-10-15", now: ist("2026-10-14", "19:50") }));
  assert.strictEqual(tomorrow[0], "10:00 AM");                 // notice only applies to today
  assert.strictEqual(S.istIso(Date.UTC(2026, 9, 13, 19, 0)), "2026-10-14"); // 00:30 IST is already tomorrow
});

ok("service duration: a 90-min keratin must finish before the break and closing", () => {
  const xs = labels(S.free({ cfg: base, date_iso: "2026-10-14", service: "Keratin treatment" }));
  assert.ok(xs.includes("12:30 PM") && !xs.includes("1:00 PM")); // 1:00 + 90 = 2:30 hits the break
  assert.strictEqual(xs[xs.length - 1], "6:30 PM");
  const catalog = { ...base, catalog: [{ name: "Bridal makeup", minutes: 120 }] };
  assert.strictEqual(S.durationOf(S.schedule(catalog), "Bridal makeup"), 120);
});

ok("interval overlap: a 90-min booking at 4 PM blocks 4:30 and 5 PM too", () => {
  const busy = [{ date_iso: "2026-10-14", slot: "4:00 PM", service: "Keratin treatment" }];
  const xs = labels(S.free({ cfg: base, date_iso: "2026-10-14", busy }));
  for (const t of ["3:30 PM", "4:00 PM", "4:30 PM", "5:00 PM"]) {
    if (t === "3:30 PM") assert.ok(xs.includes(t)); else assert.ok(!xs.includes(t), t);
  }
  assert.ok(xs.includes("5:30 PM"));
  // a long service can't start just before an existing booking either
  const k = labels(S.free({ cfg: base, date_iso: "2026-10-14", busy, service: "Keratin treatment" }));
  assert.ok(!k.includes("3:00 PM") && k.includes("5:30 PM"));
});

ok("capacity: 2 chairs; peak overlap, not booking count, decides", () => {
  const cfg = { ...base, capacity: 2 };
  const busy = [{ date_iso: "2026-10-14", slot: "11:00 AM" }, { date_iso: "2026-10-14", slot: "11:30 AM" }];
  const free = S.free({ cfg, date_iso: "2026-10-14", busy, service: "Keratin treatment" });
  const at11 = free.find((x) => x.label === "11:00 AM");
  assert.strictEqual(at11.free, 1);                            // only one booking at any moment
  const busy2 = busy.concat([{ date_iso: "2026-10-14", slot: "11:00 AM" }]);
  assert.ok(!labels(S.free({ cfg, date_iso: "2026-10-14", busy: busy2 })).includes("11:00 AM"));
});

ok("staff: 'any stylist' = union; off days, own hours and named bookings", () => {
  const cfg = JSON.parse(JSON.stringify(base));
  delete cfg.capacity;
  cfg.schedule.staff = [{ name: "Ravi", off_days: [3] },               // Wednesday off
                        { name: "Sana", hours: [["12:00", "20:00"]] },
                        { name: "Imran", off_dates: ["2026-10-15"] }];
  const wed = S.free({ cfg, date_iso: "2026-10-14" });
  assert.deepStrictEqual(wed.find((x) => x.label === "10:00 AM").staff, ["Imran"]);
  assert.deepStrictEqual(wed.find((x) => x.label === "12:00 PM").staff, ["Sana", "Imran"]);
  const busy = [{ date_iso: "2026-10-14", slot: "12:00 PM", staff: "Sana" }, { date_iso: "2026-10-14", slot: "12:00 PM", staff: "Imran" }];
  assert.ok(!labels(S.free({ cfg, date_iso: "2026-10-14", busy })).includes("12:00 PM"));
  const unassigned = [{ date_iso: "2026-10-14", slot: "1:00 PM" }];
  assert.strictEqual(S.free({ cfg, date_iso: "2026-10-14", busy: unassigned }).find((x) => x.label === "1:00 PM").free, 1);
});

ok("blocked slots and fixed labels from older setups", () => {
  const busy = [{ date_iso: "2026-10-14", slot: "11:00 AM", blocked: true }];
  const xs = labels(S.free({ cfg: base, date_iso: "2026-10-14", busy, labels: ["10:00 AM", "11:00 AM", "Morning batch"] }));
  assert.deepStrictEqual(xs, ["10:00 AM", "Morning batch"]);
});

ok("legacy setup without a schedule still works (v3.0 behaviour)", () => {
  const legacy = { closed_weekdays: [0], capacity: 2 };
  const xs = labels(S.free({ cfg: legacy, date_iso: "2026-10-14", labels: ["11:00 AM", "4:00 PM"],
                             busy: [{ date_iso: "2026-10-14", slot: "4:00 PM" }, { date_iso: "2026-10-14", slot: "4:00 PM" }] }));
  assert.deepStrictEqual(xs, ["11:00 AM"]);
  assert.strictEqual(S.closedReason(legacy, "2026-10-18"), "we're closed on Sundays");
});

ok("no duplicate starts when ranges touch", () => {
  const cfg = JSON.parse(JSON.stringify(base));
  cfg.schedule.special = [{ date: "2026-10-15", hours: [["10:00", "11:00"], ["10:30", "12:00"]] }];
  const xs = labels(S.free({ cfg, date_iso: "2026-10-15" }));
  assert.strictEqual(new Set(xs).size, xs.length);
  assert.deepStrictEqual(xs, ["10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM"]);
});

console.log(`slot engine tests passed (${n})`);
