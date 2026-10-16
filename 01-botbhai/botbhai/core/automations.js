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
// Validator rule: autopilot never pauses more than half the ads in one day; the worst go first, the rest wait for the owner.
function capPauses(verdicts) {
  const limit = Math.floor(verdicts.length / 2);
  const ranked = verdicts.filter((v) => v.verdict === "pause").sort((a, b) => (b.cpl === null ? Infinity : b.cpl) - (a.cpl === null ? Infinity : a.cpl) || b.spend - a.spend);
  const allowed = new Set(ranked.slice(0, limit).map((v) => v.ad_id));
  return verdicts.map((v) => (v.verdict === "pause" && !allowed.has(v.ad_id) ? Object.assign({}, v, { verdict: "pause_suggested", reason: v.reason + " (needs your OK: daily pause limit reached)" }) : v));
}
// Monday summary for the owner from the last 7 days of leads.
function weeklySummary(business, leads, nowMs) {
  const week = leads.filter((l) => nowMs - Date.parse(l.created_at || l.updated_at) <= 7 * 864e5);
  const by = (k, v) => week.filter((l) => l[k] === v).length;
  const src = {}; for (const l of week) src[l.source] = (src[l.source] || 0) + 1;
  return `📅 ${business} — last 7 days\nNew leads: ${week.length} (hot ${by("score", "hot")}, warm ${by("score", "warm")}, cold ${by("score", "cold")})\nBooked: ${by("status", "booked") + by("status", "quiz_done")} · Asked for a call: ${by("status", "callback")}\nSources: ${Object.entries(src).map(([k, n]) => `${k} ${n}`).join(", ") || "none"}`;
}
function adsReport(business, verdicts, autopilot) {
  const spend = verdicts.reduce((s, v) => s + v.spend, 0), leads = verdicts.reduce((s, v) => s + v.leads, 0);
  const lines = verdicts.filter((v) => v.verdict !== "keep" && v.verdict !== "learning").map((v) => `• ${v.ad_name}: ${v.verdict === "pause" ? (autopilot ? "⏸ paused" : "⚠️ pause suggested") : v.verdict === "pause_suggested" ? "⚠️ pause suggested" : "🚀 scale"} — ${v.reason}`);
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
 * outcome = the bookings row status. M10: the review ask and the referral invite go ONLY to visits the owner marked
 * "completed" in the 9 PM close-the-day list; no-shows and unmarked days get nothing (safe default).
 */
function dueReminders(lead, nowMs, outcome) {
  const d = lead.details || {}; const sent = d.reminders || {};
  if (lead.status !== "booked" || !d.date_iso) return [];
  const t = appointmentUtc(d.date_iso, d.slot); if (!t) return [];
  const h = (t - nowMs) / 3.6e6; const due = [];
  if (h <= 28 && h > 20 && !sent.day_before) due.push("day_before");
  if (h <= 3 && h > 1 && !sent.two_hours) due.push("two_hours");
  const came = outcome === "completed";
  if (came && h <= -20 && h > -30 && !sent.after_visit) due.push("after_visit");
  if (came && h <= -72 && h > -84 && !sent.refer) due.push("refer"); // 3 days later: invite a friend
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

// ---------- M10: the owner's 9 PM "close the day" list and their reply
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function dayLabel(iso) { const d = new Date(iso + "T00:00:00Z"); return `${DAYS[d.getUTCDay()]}, ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; }
/** bookings: today's confirmed rows {id, name, service, slot}. Returns { text, ids } (ids in list order) or null if none. */
function dayCloseList(bookings, dateIso) {
  if (!bookings || !bookings.length) return null;
  const rows = bookings.slice().sort((a, b) => (slotToMinutes(a.slot) ?? 9999) - (slotToMinutes(b.slot) ?? 9999));
  const lines = rows.map((b, i) => `${i + 1}. ${b.slot} · ${b.name || "Customer"}${b.service ? " · " + b.service : ""}`);
  return { ids: rows.map((b) => b.id), text: `🌙 Close the day: ${dayLabel(dateIso)}\n${lines.join("\n")}\n\nWho came? Reply *all done*, or *all done except 2* (2 didn't come), or *no show 2 3*.\nOnly people marked done get the review request.` };
}
const NUMS = (s) => (String(s).match(/\d{1,3}/g) || []).map(Number);
/** Owner's reply → { completed: [n], no_show: [n] } (1-based list numbers), or null if it isn't a close-the-day reply. */
function parseDayClose(text, count) {
  const t = String(text || "").toLowerCase().replace(/[’']/g, "").trim();
  if (!count) return null;
  const all = Array.from({ length: count }, (_, i) => i + 1);
  const inRange = (xs) => [...new Set(xs)].filter((x) => x >= 1 && x <= count);
  const ALL = /\b(all|anni|andaru|sab|everyone|everybody)\b[^\d]*\b(done|came|ok|okay|vacharu|vachcharu|vachharu|ayyayi|ayyindi|aaye|ho gaye|hogaye|aa gaye)\b|^(all done|done all|anni ayyayi|sab ho gaye|sab aa gaye)\b/;
  const NOSHOW = /(no[\s-]?show|didnt come|did not come|not come|absent|raledu|raaledu|nahi aaye|nahi aaya|nahi aayi)/;
  const EXCEPT = /\b(except|but|tappa|chhodke|chodke|minus)\b/;
  if (ALL.test(t) || /^\s*(done|came|ok|okay)\b[^\d]*\b(except|but|tappa|chhodke|chodke|minus)\b/.test(t)) {
    const rest = t.split(EXCEPT).length > 1 ? t.split(EXCEPT).slice(1).join(" ") : NOSHOW.test(t) ? t : "";
    const ns = inRange(NUMS(rest));
    return { completed: all.filter((x) => !ns.includes(x)), no_show: ns };
  }
  if (!NOSHOW.test(t) && !/\bdone\b|\bcame\b|\bvacharu\b/.test(t)) return null;
  const out = { completed: [], no_show: [] };
  for (const part of t.split(/[,;\n]|\band\b/)) {
    if (NOSHOW.test(part)) out.no_show.push(...NUMS(part));
    else if (/\bdone\b|\bcame\b|\bvacharu\b/.test(part)) out.completed.push(...NUMS(part));
  }
  out.no_show = inRange(out.no_show); out.completed = inRange(out.completed).filter((x) => !out.no_show.includes(x));
  return out.completed.length || out.no_show.length ? out : null;
}

// Referral codes: short, stable per customer ("REF-7KQ2"), so word-of-mouth becomes trackable leads.
function referralCode(contact) {
  let h = 2166136261; for (const c of String(contact)) h = Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0;
  return "REF-" + h.toString(36).toUpperCase().slice(-4).padStart(4, "X");
}

module.exports = { referralCode, parseMetaLead, normalizePhone, judgeAds, capPauses, weeklySummary, leadsFrom, adsReport, slotToMinutes, appointmentUtc, dueReminders, dueRenewals, dayCloseList, parseDayClose };
