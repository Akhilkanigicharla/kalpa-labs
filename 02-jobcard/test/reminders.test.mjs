// A37 (b2.q11): daily "customers due" reminder to the technician, and the wa.me messages he sends himself.
import { test } from "node:test";
import assert from "node:assert/strict";
import { installFake } from "./fake.mjs";
import { dueCustomers, reminderText, waLink } from "../lib/reminders.mjs";

const TODAY = "2026-10-18";
const customers = [
  { id: "c1", name: "Sita", phone: "9000033333", opted_in_whatsapp: true },
  { id: "c2", name: "Ravi", phone: "9000044444", opted_in_whatsapp: true },
  { id: "c3", name: "Lakshmi", phone: "9000055555", opted_in_whatsapp: false }, // never agreed: no reminder
  { id: "c4", name: "Anil", phone: null, opted_in_whatsapp: true },             // no number
  { id: "c5", name: "Meena", phone: "9000066666", opted_in_whatsapp: true },
];
const job = (customer_id, next_service, visited_at = "2026-04-18T10:00:00Z", appliance = "split_ac") => ({ customer_id, next_service, visited_at, appliance });

test("due list: said-out-loud next service only, opted in, latest job per customer, earliest first, max 5", () => {
  const jobs = [job("c1", "2026-10-20"), job("c2", "2026-10-15"), job("c3", "2026-10-19"), job("c4", "2026-10-19"),
    job("c5", "2026-12-01"), job("c1", "2027-04-20", "2026-10-01T10:00:00Z"), job("c2", null, "2026-10-17T10:00:00Z")];
  // Sita's latest visit moved her next service to April; Ravi was visited yesterday (no next service said): neither is due
  assert.deepEqual(dueCustomers(jobs, customers, TODAY).map((r) => r.customer.name), []);
  assert.deepEqual(dueCustomers(jobs.slice(0, 5), customers, TODAY).map((r) => r.customer.name), ["Ravi", "Sita"]);
  const many = Array.from({ length: 8 }, (_, i) => ({ id: "m" + i, name: "M" + i, phone: "90000700" + String(i).padStart(2, "0"), opted_in_whatsapp: true }));
  const due = dueCustomers(many.map((c, i) => job(c.id, `2026-10-${String(12 + i).padStart(2, "0")}`)), many, TODAY);
  assert.equal(due.length, 5); assert.deepEqual(due.map((d) => d.job.next_service), ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]);
  assert.equal(dueCustomers([job("c1", "2026-09-01")], customers, TODAY).length, 0, "more than 30 days overdue drops off");
  assert.equal(dueCustomers([job("c1", "2026-10-26")], customers, TODAY).length, 0, "more than a week ahead waits");
});

test("prefilled Telugu / Hindi / English message and a wa.me link he sends himself", () => {
  const r = { customer: customers[0], job: job("c1", "2026-10-20") };
  const te = reminderText(r, "Ravi Cooling");
  assert.equal(te, "నమస్తే Sita గారు, మీ స్ప్లిట్ ఏసీ సర్వీస్ సమయం వచ్చింది (20 Oct). ఈ వారం వచ్చి చేయమంటారా? – Ravi Cooling");
  assert.match(reminderText(r, "Ravi Cooling", "hi"), /स्प्लिट एसी/); assert.match(reminderText(r, "Ravi Cooling", "en"), /split AC is due/);
  const link = waLink("9000033333", te);
  assert.ok(link.startsWith("https://wa.me/919000033333?text=%E0%B0")); assert.equal(decodeURIComponent(link.split("text=")[1]), te);
  assert.throws(() => waLink("12345", "x"), /Indian mobile/);
});

test("cron: one template to each Pro technician with customers due, once a day; free and empty skipped", async () => {
  const fx = installFake({
    technicians: [
      { id: "t1", name: "Ravi", phone: "9000022222", language: "te", plan: "pro" },
      { id: "t2", name: "Imran", phone: "9000077777", language: "hi", plan: "free" },
      { id: "t3", name: "Kiran", phone: "9000088888", language: "en", plan: "pro" },
    ],
    customers: customers.map((c) => ({ ...c, technician_id: "t1" })).concat([{ id: "x1", technician_id: "t2", name: "Usha", phone: "9100000001", opted_in_whatsapp: true }]),
    job_cards: [{ technician_id: "t1", ...job("c1", "2026-10-20") }, { technician_id: "t1", ...job("c5", null, "2024-01-01T00:00:00Z") }, { technician_id: "t1", ...job("c2", "2026-10-15") }, { technician_id: "t1", ...job("c3", "2026-10-19") },
      { technician_id: "t2", ...job("x1", "2026-10-19") }],
    reminder_sends: [],
  });
  process.env.WA_PHONE_NUMBER_ID = "PNID";
  const { runReminders } = await import("../bot/functions/reminders.js");
  const now = Date.parse("2026-10-18T03:30:00Z");
  assert.deepEqual(await runReminders({ now }), { technicians: 2, sent: 1, skipped: 1, failed: 0 });
  assert.equal(fx.sent.length, 1); const m = fx.sent[0];
  assert.equal(m.to, "919000022222"); assert.equal(m.type, "template"); assert.equal(m.template.language.code, "te");
  assert.deepEqual(m.template.components[0].parameters.map((p) => p.text), ["2", "Ravi, Sita"]);
  assert.ok(!fx.sent.some((x) => ["919000033333", "919000044444", "919100000001"].includes(x.to)), "never messages customers");
  await runReminders({ now: now + 3600000 }); assert.equal(fx.sent.length, 1, "second run the same day sends nothing");
  await runReminders({ now: now + 86400000 }); assert.equal(fx.sent.length, 2, "next day sends again");
});
