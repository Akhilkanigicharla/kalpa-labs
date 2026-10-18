/*
 * Meta ads bot — runs every morning (netlify.toml schedule). For each client with an ad account:
 * pulls yesterday's per-ad results from the Marketing API, judges each ad against the setup's target
 * cost-per-lead, pauses losers if the client allowed autopilot (never more than half the ads a day), and WhatsApps
 * the owner a report. On Mondays it also sends every owner a 7-day lead summary.
 */
const { db, graph, sendTemplate, sendText, templatesFor, clientToken } = require("./_lib.js");
const { judgeAds, capPauses, adsReport, weeklySummary } = require("../automations.js");
const ADS = { salon: require("../../setups/salon/ads.config.json"), realestate: require("../../setups/realestate/ads.config.json"), gym: require("../../setups/gym/ads.config.json"), examkits: require("../../setups/examkits/ads.config.json") };

exports.handler = async () => {
  // Mondays (IST): weekly lead summary to every owner, ads or not
  if (new Date(Date.now() + 330 * 60000).getUTCDay() === 1) {
    for (const c of await db("clients?active=eq.true&owner_whatsapp=not.is.null&select=*")) {
      try {
        const leads = await db(`leads?client_id=eq.${c.id}&select=score,status,source,created_at,updated_at&order=updated_at.desc&limit=2000`);
        const text = weeklySummary((c.config || {}).business || c.name, leads, Date.now());
        await sendText(c.phone_number_id, c.owner_whatsapp, text).catch(() => sendTemplate(c.phone_number_id, c.owner_whatsapp, templatesFor(c.niche).owner_report, { summary: text.split("\n")[1] }));
      } catch (e) { console.error("weekly", c.name, e.message); }
    }
  }
  const clients = await db("clients?active=eq.true&meta_ad_account_id=not.is.null&select=*");
  for (const c of clients) {
    try {
      const adsToken = await clientToken(c.id, "meta_ads");
      if (!adsToken) continue;
      const rules = Object.assign({}, ADS[c.niche].rules, (c.config || {}).ads_rules);
      const ins = await graph(`act_${c.meta_ad_account_id}/insights?level=ad&date_preset=yesterday&fields=ad_id,ad_name,spend,impressions,clicks,actions&limit=200`, { token: adsToken });
      const verdicts = capPauses(judgeAds(ins.data || [], rules));
      const autopilot = !!(c.config || {}).ads_autopilot;
      if (autopilot) for (const v of verdicts.filter((x) => x.verdict === "pause")) await graph(v.ad_id, { method: "POST", token: adsToken, body: { status: "PAUSED" } });
      await db("ad_stats", { method: "POST", prefer: "return=minimal", body: verdicts.map((v) => ({ client_id: c.id, day: new Date(Date.now() - 864e5).toISOString().slice(0, 10), ad_id: v.ad_id, ad_name: v.ad_name, spend: v.spend, leads: v.leads, cpl: v.cpl, verdict: v.verdict })) });
      const report = adsReport((c.config || {}).business || c.name, verdicts, autopilot);
      if (c.owner_whatsapp) {
        // inside 24h window a plain text works; otherwise use the approved owner_report utility template
        await sendText(c.phone_number_id, c.owner_whatsapp, report).catch(() => sendTemplate(c.phone_number_id, c.owner_whatsapp, templatesFor(c.niche).owner_report, { summary: report.split("\n")[1] }));
      }
    } catch (e) { console.error("adsbot", c.name, e.message); }
  }
  return { statusCode: 200, body: "ok" };
};
