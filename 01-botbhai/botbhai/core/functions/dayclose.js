/*
 * Close-the-day agent (M10) — runs at 9 PM IST. Sends each owner today's numbered list of confirmed visits.
 * The owner replies on WhatsApp ("all done", "all done except 3", "no show 2"); whatsapp.js applies it to
 * bookings.status (completed / no_show). Review asks and referral invites go only to completed visits, so a
 * day nobody marks gets no review asks at all (safe default).
 * Manual run for a past day: /.netlify/functions/dayclose?date=2026-10-12
 */
const L = require("./_lib.js");
const { dayCloseList } = require("../automations.js");

exports.handler = async (event) => {
  const q = (event && event.queryStringParameters) || {};
  const day = /^\d{4}-\d{2}-\d{2}$/.test(q.date || "") ? q.date : L.istTodayIso();
  let lists = 0;
  const clients = await L.db("clients?active=eq.true&phone_number_id=not.is.null&owner_whatsapp=not.is.null&select=*");
  for (const c of clients) {
    try {
      const rows = await L.db(`bookings?client_id=eq.${c.id}&date_iso=eq.${day}&status=eq.confirmed&select=id,name,service,slot&limit=500`);
      const list = dayCloseList(rows, day); if (!list) continue;
      try { await L.sendText(c.phone_number_id, c.owner_whatsapp, list.text); }
      catch (e) { // outside the 24 h window: the approved utility template, then the list arrives once they reply
        const tpl = L.templatesFor(c.niche).owner_report;
        if (tpl) await L.sendTemplate(c.phone_number_id, c.owner_whatsapp, tpl, { summary: `${rows.length} visits today. Reply to mark who came` });
      }
      const [sess] = await L.db(`sessions?client_id=eq.${c.id}&contact=eq.${L.enc(c.owner_whatsapp)}&select=state`);
      const state = Object.assign({}, sess ? sess.state : {}, { dayclose: { date_iso: day, ids: list.ids, text: list.text } });
      await L.db("sessions?on_conflict=client_id,contact", { method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: { client_id: c.id, contact: c.owner_whatsapp, state, updated_at: new Date().toISOString() } });
      lists++;
    } catch (e) { console.error("dayclose", c.id, e.message); }
  }
  return { statusCode: 200, body: `lists sent ${lists}` };
};
