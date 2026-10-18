/*
 * Daily AMC / service reminders (b2.q11). Netlify Scheduled Function, 09:00 IST.
 * For each Pro technician with customers due this week, sends ONE approved WhatsApp template to the technician
 * (not to his customers): "5 customers are due: Sita, Ravi, …" with a button to the "my customers" page, where
 * each customer has a wa.me link with a prefilled Telugu message he sends himself from his own WhatsApp.
 *
 * Env (Akhil sets them in Netlify): SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WA_ACCESS_TOKEN,
 *   WA_PHONE_NUMBER_ID (the JobCard number), WA_REMINDER_TEMPLATE (default jobcard_due_list).
 * Meta template (Akhil creates it, category Utility, te/hi/en): body "{{1}} customers are due for service this week: {{2}}.
 *   Tap below to remind each one from your own WhatsApp." URL button: https://<site>/?tab={{1}}
 */
import { db } from "./jobcard.js";
import { dueCustomers } from "../../lib/reminders.mjs";

const GRAPH = "https://graph.facebook.com/v21.0";
const DAY = 86400000;
const istToday = (now) => new Date(now + 330 * 60000).toISOString().slice(0, 10);
const shift = (iso, n) => new Date(Date.parse(iso + "T00:00:00Z") + n * DAY).toISOString().slice(0, 10);
const LANG = { te: "te", hi: "hi", en: "en" };
const REMINDER_PLANS = new Set(["pro", "team"]); // PLAN.md §2: AMC reminders are a Pro feature

async function sendTemplate(to, lang, count, names) {
  const r = await fetch(`${GRAPH}/${process.env.WA_PHONE_NUMBER_ID}/messages`, { method: "POST",
    headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to, type: "template", template: {
      name: process.env.WA_REMINDER_TEMPLATE || "jobcard_due_list", language: { code: LANG[lang] || "te" },
      components: [
        { type: "body", parameters: [{ type: "text", text: String(count) }, { type: "text", text: names }] },
        { type: "button", sub_type: "url", index: "0", parameters: [{ type: "text", text: "due" }] },
      ] } }) });
  if (!r.ok) throw new Error(`template ${r.status}`);
}

export async function runReminders({ now = Date.now() } = {}) {
  const today = istToday(now); const out = { technicians: 0, sent: 0, skipped: 0, failed: 0 };
  const techs = await db("technicians?select=id,name,phone,language,plan");
  for (const t of techs) {
    if (!REMINDER_PLANS.has(t.plan)) { out.skipped++; continue; }
    out.technicians++;
    try {
      const [jobs, customers] = await Promise.all([
        db(`job_cards?technician_id=eq.${t.id}&visited_at=gte.${shift(today, -400)}&select=customer_id,next_service,appliance,visited_at`),
        db(`customers?technician_id=eq.${t.id}&opted_in_whatsapp=eq.true&select=id,name,phone,opted_in_whatsapp`),
      ]);
      const due = dueCustomers(jobs, customers, today);
      if (!due.length) continue;
      // once a day per technician, even if the function runs twice
      const claimed = await db("reminder_sends?on_conflict=technician_id,day", { method: "POST", body: { technician_id: t.id, day: today, count: due.length }, prefer: "resolution=ignore-duplicates,return=representation" });
      if (!claimed.length) continue;
      const names = due.map((d) => d.customer.name).join(", ").slice(0, 200);
      await sendTemplate(`91${t.phone}`, t.language, due.length, names);
      out.sent++;
    } catch (e) { out.failed++; console.error("reminders", t.id, e.message); }
  }
  return out;
}

export default async () => new Response(JSON.stringify(await runReminders()), { headers: { "Content-Type": "application/json" } });
export const config = { schedule: "30 3 * * *" }; // 03:30 UTC = 09:00 IST
