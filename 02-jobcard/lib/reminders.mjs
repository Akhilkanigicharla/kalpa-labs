// Service reminders. The technician sends each one himself from his own WhatsApp (wa.me link with a
// prefilled message), one customer at a time: no bulk sends, no messages from us to his customers.

const APPLIANCE_TE = { split_ac: "స్ప్లిట్ ఏసీ", window_ac: "విండో ఏసీ", cassette_ac: "క్యాసెట్ ఏసీ", ac: "ఏసీ", fridge: "ఫ్రిజ్", washing_machine: "వాషింగ్ మెషిన్" };
const APPLIANCE_HI = { split_ac: "स्प्लिट एसी", window_ac: "विंडो एसी", cassette_ac: "कैसेट एसी", ac: "एसी", fridge: "फ़्रिज", washing_machine: "वॉशिंग मशीन" };
const APPLIANCE_EN = { split_ac: "split AC", window_ac: "window AC", cassette_ac: "cassette AC", ac: "AC", fridge: "fridge", washing_machine: "washing machine" };
const DAY = 86400000;
const addDays = (iso, n) => new Date(Date.parse(iso + "T00:00:00Z") + n * DAY).toISOString().slice(0, 10);
const nice = (iso) => new Date(iso + "T00:00:00Z").toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "UTC" });

/**
 * Customers whose next service is due: from `overdueDays` ago up to `aheadDays` ahead of `today` (YYYY-MM-DD, IST).
 * Each customer's LATEST visit decides; only a next service that was actually said counts (never invented);
 * only opted-in customers with a phone; earliest due first, at most `max`.
 */
export function dueCustomers(jobs, customers, today, { aheadDays = 7, overdueDays = 30, max = 5 } = {}) {
  const byId = new Map(customers.map((c) => [c.id, c]));
  const from = addDays(today, -overdueDays); const to = addDays(today, aheadDays);
  const latest = new Map();
  for (const j of jobs) { // the latest visit decides: if it said no next service, he was just there
    if (!j.customer_id) continue;
    const prev = latest.get(j.customer_id);
    if (!prev || String(j.visited_at) > String(prev.visited_at)) latest.set(j.customer_id, j);
  }
  return [...latest.values()]
    .filter((j) => j.next_service && j.next_service >= from && j.next_service <= to)
    .map((j) => ({ job: j, customer: byId.get(j.customer_id) }))
    .filter((r) => r.customer && r.customer.phone && r.customer.opted_in_whatsapp)
    .sort((a, b) => a.job.next_service.localeCompare(b.job.next_service) || a.customer.name.localeCompare(b.customer.name))
    .slice(0, max);
}

export function reminderText({ customer, job }, supplier, lang = "te") {
  const name = customer.name || ""; const due = nice(job.next_service);
  if (lang === "hi") return `नमस्ते ${name} जी, आपके ${APPLIANCE_HI[job.appliance] || "एसी"} की सर्विस का समय आ गया है (${due})। इस हफ़्ते आकर कर दूँ? – ${supplier}`;
  if (lang === "en") return `Hello ${name}, your ${APPLIANCE_EN[job.appliance] || "AC"} is due for service (${due}). Shall I come this week? – ${supplier}`;
  return `నమస్తే ${name} గారు, మీ ${APPLIANCE_TE[job.appliance] || "ఏసీ"} సర్వీస్ సమయం వచ్చింది (${due}). ఈ వారం వచ్చి చేయమంటారా? – ${supplier}`;
}

/** wa.me click-to-chat link: opens the technician's own WhatsApp with the message typed in; he presses send. */
export function waLink(phone10, text) {
  if (!/^[6-9]\d{9}$/.test(String(phone10))) throw new Error("not an Indian mobile number");
  return `https://wa.me/91${phone10}?text=${encodeURIComponent(text)}`;
}
