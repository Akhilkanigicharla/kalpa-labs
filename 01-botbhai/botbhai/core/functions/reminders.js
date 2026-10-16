/*
 * Follow-up agent — runs hourly. After-visit review asks and referrals go only to visits marked done in the
 * owner's 9 PM close-the-day list (dayclose.js); no-shows and unmarked days get nothing.
 * Booking reminders (24 h and 2 h before) cut no-shows; the after-visit
 * message asks for a Google review (salon), feedback + next step (real estate), or check-in (gym/coaching).
 * Renewal reminders 7/3/1 days before expiry and a win-back 15 days after, from the members table.
 */
const { db, sendTemplate, templatesFor, cardUrl, enc, istTodayIso } = require("./_lib.js");
const { dueReminders, dueRenewals, referralCode } = require("../automations.js");

exports.handler = async () => {
  const now = Date.now(); let sent = 0;
  const clients = await db("clients?active=eq.true&phone_number_id=not.is.null&select=*");
  for (const c of clients) {
    const tpl = templatesFor(c.niche); const cfg = c.config || {};
    // only bookings from 4 days ago onwards: the after-visit and referral windows end within 84 hours
    const since = istTodayIso(now - 4 * 864e5);
    const leads = await db(`leads?client_id=eq.${c.id}&status=eq.booked&details->>date_iso=gte.${since}&select=id,contact,name,details,marketing_opt_in&order=updated_at.desc&limit=2000`);
    // M10: only visits the owner marked "completed" in the 9 PM list get the review ask / referral invite
    const completed = new Set((await db(`bookings?client_id=eq.${c.id}&status=eq.completed&date_iso=gte.${since}&select=contact,date_iso`)).map((b) => b.contact + b.date_iso));
    for (const l of leads) for (const key of dueReminders({ status: "booked", details: l.details }, now, completed.has(l.contact + l.details.date_iso) ? "completed" : "unmarked")) {
      if (!tpl[key] || l.contact.startsWith("web:")) continue;
      if (tpl[key].category === "MARKETING" && !l.marketing_opt_in) continue; // promotional messages need opt-in
      try {
        await sendTemplate(c.phone_number_id, l.contact, tpl[key], Object.assign({ business: cfg.business || c.name, review_link: cfg.review_link || "", address: cfg.address || "", card_url: cardUrl(c, tpl[key].card), ref_code: referralCode(l.contact) }, l.details, { name: l.name || "there" }));
        const details = Object.assign({}, l.details, { reminders: Object.assign({}, l.details.reminders, { [key]: new Date().toISOString() }) });
        await db(`leads?id=eq.${l.id}`, { method: "PATCH", prefer: "return=minimal", body: { details } }); sent++;
      } catch (e) { console.error("reminder", key, e.message); }
    }
    const members = await db(`members?client_id=eq.${c.id}&opted_out=eq.false&select=id,phone,name,plan,expires_on,reminders,marketing_opt_in&limit=5000`);
    for (const m of members) for (const key of dueRenewals(m, now)) {
      if (!tpl[key]) continue;
      if (tpl[key].category === "MARKETING" && !m.marketing_opt_in) continue;
      try {
        await sendTemplate(c.phone_number_id, m.phone, tpl[key], { name: m.name || "there", plan: m.plan || "membership", date: m.expires_on, business: cfg.business || c.name, card_url: cardUrl(c, tpl[key].card) });
        await db(`members?id=eq.${m.id}`, { method: "PATCH", prefer: "return=minimal", body: { reminders: Object.assign({}, m.reminders, { [key]: new Date().toISOString() }) } }); sent++;
      } catch (e) { console.error("renewal", key, e.message); }
    }
  }
  return { statusCode: 200, body: `sent ${sent}` };
};
