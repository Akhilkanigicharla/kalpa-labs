/*
 * BotBhai automation logic (pure functions — no network, fully unit-tested).
 * Used by the Netlify functions: metaleads.js (Meta lead ads), adsbot.js (daily ad guard),
 * reminders.js (booking reminders, review asks, renewals, win-backs).
 */
"use strict";
const IST_OFFSET_MIN = 330;

// ---------- Meta Lead Ads: turn Graph API field_data into a clean lead
function parseMetaLead(lead) {
  const f = {};
  for (const x of lead.field_data || []) f[x.name] = (x.values || [])[0] || "";
  const pick = (...keys) => { for (const k of keys) if (f[k]) return f[k]; return ""; };
  const name = pick("full_name", "name", "first_name") + (f.last_name ? " " + f.last_name : "");
  const phone = normalizePhone(pick("phone_number", "phone", "whatsapp_number", "mobile_number"));
  const known = new Set(["full_name", "name", "first_name", "last_name", "phone_number", "phone", "whatsapp_number", "mobile_number", "email"]);
  const answers = Object.fromEntries(Object.entries(f).filter(([k]) => !known.has(k)));
  return { name: name.trim() || null, phone, email: f.email || null, answers, ad_id: lead.ad_id || null, form_id: lead.form_id || null, created_time: lead.created_time || null };
}

// Indian numbers → WhatsApp wa_id format (91XXXXXXXXXX). Returns "" if not a valid mobile.
function normalizePhone(raw) {
  let d = String(raw || "").replace(/\D/g, "");
  if (d.startsWith("0")) d = d.replace(/^0+/, "");
  if (d.length === 10 && /^[6-9]/.test(d)) d = "91" + d;
  if (d.length === 12 && d.startsWith("91") && /^[6-9]/.test(d[2])) return d;
  if (d.length >= 11 && d.length <= 15 && !d.startsWith("91")) return d; // international lead
  return "";
}

// ---------- Ads guard: decide what to do with each ad from yesterday's insights
const LEAD_ACTIONS = ["lead", "leadgen_grouped", "onsite_conversion.lead_grouped", "onsite_conversion.messaging_conversation_started_7d"];
function leadsFrom(actions) {
  let n = 0;
  for (const a of actions || []) if (LEAD_ACTIONS.includes(a.action_type)) n = Math.max(n, Number(a.value) || 0);
  return n;
}
/**
 * rules: { target_cpl, kill_multiplier, min_spend_to_judge, scale_below_multiplier }
 * returns [{ ad_id, ad_name, spend, leads, cpl, verdict: "pause"|"scale"|"keep"|"learning", reason }]
 */
function judgeAds(rows, rules) {
  const r = Object.assign({ kill_multiplier: 1.6, min_spend_to_judge: 300, scale_below_multiplier: 0.7 }, rules);
  return rows.map((row) => {
    const spend = Number(row.spend) || 0; const leads = leadsFrom(row.actions);
    const cpl = leads ? Math.round(spend / leads) : null;
    let verdict = "keep", reason = "Within target.";
    if (spend < r.min_spend_to_judge && !(leads === 0 && spend >= r.target_cpl * 1.5)) { verdict = "learning"; reason = `Only ₹${spend} spent — too early to judge.`; }
    else if (leads === 0 && spend >= r.target_cpl * 1.5) { verdict = "pause"; reason = `₹${spend} spent, 0 leads (target ₹${r.target_cpl}/lead).`; }
    else if (cpl !== null && cpl > r.target_cpl * r.kill_multiplier) { verdict = "pause"; reason = `₹${cpl}/lead is over ${r.kill_multiplier}× target ₹${r.target_cpl}.`; }
    else if (cpl !== null && cpl < r.target_cpl * r.scale_below_multiplier) { verdict = "scale"; reason = `₹${cpl}/lead beats target ₹${r.target_cpl} — raise budget 20%.`; }
    return { ad_id: row.ad_id, ad_name: row.ad_name, spend, leads, cpl, verdict, reason };
  });
}
function adsReport(business, verdicts, autopilot) {
  const spend = verdicts.reduce((s, v) => s + v.spend, 0), leads = verdicts.reduce((s, v) => s + v.leads, 0);
  const lines = verdicts.filter((v) => v.verdict !== "keep" && v.verdict !== "learning").map((v) => `• ${v.ad_name}: ${v.verdict === "pause" ? (autopilot ? "⏸ paused" : "⚠️ pause suggested") : "🚀 scale"} — ${v.reason}`);
  return `📊 ${business} ads — yesterday\nSpend ₹${spend.toLocaleString("en-IN")} · Leads ${leads} · ${leads ? `₹${Math.round(spend / leads)}/lead` : "no leads"}\n` + (lines.length ? lines.join("\n") : "All ads within target. No action needed.");
}

// ---------- Reminders: what to send now for a booked lead
function slotToMinutes(slot) {
  const m = String(slot || "").match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i); if (!m) return null;
  let h = +m[1] % 12; if (/pm/i.test(m[3])) h += 12; return h * 60 + +m[2];
}
// Appointment time in UTC ms from date_iso (IST calendar date) + slot ("4:00 PM" IST)
function appointmentUtc(dateIso, slot) {
  const mins = slotToMinutes(slot); if (!dateIso || mins === null) return null;
  const [y, mo, d] = dateIso.split("-").map(Number);
  return Date.UTC(y, mo - 1, d, 0, 0) + (mins - IST_OFFSET_MIN) * 60000;
}
/**
 * Given a lead row (details has date_iso, slot, reminders{}), returns the reminder keys due now.
 * Windows: "day_before" 20–28h before, "two_hours" 1–3h before, "after_visit" 20–30h after (review / feedback / next step).
 */
function dueReminders(lead, nowMs) {
  const d = lead.details || {}; const sent = d.reminders || {};
  if (lead.status !== "booked" || !d.date_iso) return [];
  const t = appointmentUtc(d.date_iso, d.slot); if (!t) return [];
  const h = (t - nowMs) / 3.6e6; const due = [];
  if (h <= 28 && h > 20 && !sent.day_before) due.push("day_before");
  if (h <= 3 && h > 1 && !sent.two_hours) due.push("two_hours");
  if (h <= -20 && h > -30 && !sent.after_visit) due.push("after_visit");
  return due;
}
// Gym/coaching renewals: members table rows {expires_on (YYYY-MM-DD), reminders{}}
function dueRenewals(member, nowMs) {
  const sent = member.reminders || {}; if (!member.expires_on) return [];
  const [y, m, d] = member.expires_on.split("-").map(Number);
  const days = Math.round((Date.UTC(y, m - 1, d) - (nowMs + IST_OFFSET_MIN * 60000 - ((nowMs + IST_OFFSET_MIN * 60000) % 864e5))) / 864e5);
  const due = [];
  for (const k of [7, 3, 1]) if (days === k && !sent["renew_" + k]) due.push("renew_" + k);
  if (days === -15 && !sent.winback) due.push("winback");
  return due;
}

module.exports = { parseMetaLead, normalizePhone, judgeAds, leadsFrom, adsReport, slotToMinutes, appointmentUtc, dueReminders, dueRenewals };
