// BotBhai sales kit (A07 / P1-W2-05): A5 leave-behind card (Telugu + English), one-page proposal, client agreement
// with DPDP processor terms, the salon's customer privacy notice, and the objection sheet. Every price comes from
// 01-botbhai/docs/sales/prices.json, which tools/test_sales_kit.py checks against PLAN.md §2.
//
//   node tools/sales_kit.js all <outdir> [--demo <url>]          every page as HTML (tools/test_sales_kit.py prints them to PDF)
//   node tools/sales_kit.js proposal <salon.json> <out.html>     a proposal with one salon's own numbers
//   node tools/sales_kit.js privacy <salon.json> <out.html>      that salon's customer privacy notice
//
// Research + sources: 01-botbhai/research/sales-kit-scan.md. The agreement's structure and some wording are adapted
// from Common Paper's Cloud Service Agreement v2.1 and DPA v1.1 (CC BY 4.0, https://commonpaper.com/standards).
const fs = require("fs");
const path = require("path");
const { renderSVG } = require("../core/vendor/uqr/index.cjs");

const SALES = path.join(__dirname, "..", "..", "docs", "sales");
const P = JSON.parse(fs.readFileSync(path.join(SALES, "prices.json"), "utf8"));
const TIER = Object.fromEntries(P.tiers.map((t) => [t.id, t]));
const DEMO_URL = "https://claude.ai/artifact/JYxrRm9PHrw2SCBRFRPjUi"; // the live BotBhai demo; switch to the wa.me demo number once Kalpa's WABA is live
const KALPA = { name: "Kalpa Labs", udyam: "UDYAM-TS-02-0382711", city: "Hyderabad, Telangana" };
const VERSION = "v1.0 · 16 Oct 2026";

const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const qr = (text) => renderSVG(text, { ecc: "M", border: 4, pixelSize: 1, whiteColor: "#FFFFFF", blackColor: "#000000" }).replace(/^<svg /, '<svg role="img" aria-label="QR code to the BotBhai demo" ');

// Kalpa tokens (Kalpavruksha, light: these are printed documents), copied from 00-hq/design/tokens.css; keep in sync.
const BASE = `:root{--bg:#F2EEE3;--panel:#FCFAF4;--fg:#1E2A1F;--muted:#5A6152;--rule:#DCD5C3;--soft:#E9E3D3;--accent:#2F6A3A;--accent-fg:#FFFFFF;--madder:#8A4A28;--gold:#C38E12;--ok:#2C7A43;--bad:#B13A2D;--hero:#1D3A25;--hero-fg:#F4EEDC;--hero-mute:#BFCDAE;--l1:#8A4A28;
--f-display:"Rozha One","Noto Serif",Georgia,serif;--f-body:"Anek Latin","Anek Telugu",ui-sans-serif,system-ui,sans-serif;--f-te:"Anek Telugu","Noto Sans Telugu",sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
--temple:radial-gradient(circle at 7px 5px,var(--gold) 2.4px,transparent 2.8px) 0 0/14px 10px,radial-gradient(ellipse 3.2px 2px at 3.5px 5px,var(--leaf,#5E9E4C) 90%,transparent) 0 0/7px 10px}
*{box-sizing:border-box}html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:#fff;color:var(--fg);font:10.5pt/1.45 var(--f-body)}
.te,.te .eyebrow,.eyebrow .te{font-family:var(--f-te)}.te .eyebrow,.eyebrow .te{letter-spacing:0;text-transform:none;font-weight:600;font-size:9pt}h1,h2,.display{font-family:var(--f-display);font-weight:400;margin:0}
.eyebrow{font:600 7.5pt var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin:0 0 2mm}
.muted{color:var(--muted)}.mono{font-family:var(--f-mono)}.small{font-size:8.5pt}
.band{position:relative;background:var(--hero);color:var(--hero-fg);padding:7mm 8mm 6mm}
.band::before,.band::after{content:"";position:absolute;left:0;right:0;height:10px;background:var(--temple)}.band::before{top:0}.band::after{bottom:0;transform:scaleY(-1)}
.band .muted{color:var(--hero-mute)}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:1.6mm 1.5mm;border-bottom:1px solid var(--rule);vertical-align:top}
th{font:600 7.5pt var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.page{page-break-after:always;break-after:page;position:relative;overflow:hidden}.page:last-child{page-break-after:auto;break-after:auto}
.foot{font-size:7.5pt;color:var(--muted)}`;
const doc = (title, size, css, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rozha+One&family=Anek+Latin:wght@400;600;700&family=Anek+Telugu:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>@page{size:${size};margin:0}${BASE}${css}</style></head><body>${body}</body></html>`;

// ---------------------------------------------------------------- 1. A5 leave-behind card (front Telugu, back English)
function card({ demo = DEMO_URL } = {}) {
  const f = TIER.founding;
  const css = `.page{width:148mm;height:210mm;display:flex;flex-direction:column}
.band h1{font-size:21pt;line-height:1.15}.band h1.te{font-family:var(--f-te);font-weight:700;font-size:19pt;line-height:1.35}
.body{padding:6mm 8mm 0;display:flex;flex-direction:column;gap:4mm;flex:1}
ul{margin:0;padding-left:5mm}li{margin:0 0 1.4mm}
.qrrow{display:flex;gap:5mm;align-items:center}.qr{width:34mm;height:34mm;flex:none}.qr svg{width:100%;height:100%;display:block}
.loss{border:1px solid var(--rule);border-radius:3mm;padding:3mm 4mm}.loss p{margin:0 0 2.2mm;display:flex;gap:2mm;align-items:baseline}
.loss p span{flex:1}.loss p i{flex:0 0 22mm;border-bottom:1px solid var(--fg);height:5mm}
.offer{background:color-mix(in srgb,var(--gold) 14%,#fff);border-radius:3mm;padding:3mm 4mm;border-left:4px solid var(--gold)}
.offer b{font-family:var(--f-display);font-weight:400;font-size:13pt}
.foot{margin-top:auto;padding:3mm 8mm 5mm;display:flex;justify-content:space-between;gap:4mm;border-top:1px solid var(--rule)}
.write{display:inline-block;min-width:38mm;border-bottom:1px solid var(--fg);height:4.5mm}`;
  const front = `<section class="page te" lang="te">
<header class="band"><p class="eyebrow">BotBhai · Kalpa Labs</p><h1 class="te">రాత్రి 11 గంటలకూ మీ WhatsApp తెలుగులో జవాబిస్తుంది</h1></header>
<div class="body">
<ul><li>స్లాట్ బుక్ చేస్తుంది, కస్టమర్‌కి రెండుసార్లు గుర్తు చేస్తుంది (ఒక రోజు ముందు, 2 గంటల ముందు).</li>
<li>సంతోషంగా వెళ్లిన కస్టమర్లను మాత్రమే Google రివ్యూ అడుగుతుంది.</li>
<li>కోపంగా ఉన్న కస్టమర్ వస్తే వెంటనే మీకు చెబుతుంది; మీరే జవాబిస్తారు.</li>
<li>60 రోజుల్లో లాభం కనిపించకపోతే, నెలవారీ డబ్బు కట్టడం ఆపేయండి. లాక్-ఇన్ లేదు.</li></ul>
<div class="qrrow"><div class="qr">${qr(demo)}</div><p>ఈ QR స్కాన్ చేసి మీ ఫోన్‌లోనే డెమో చూడండి: <b>"repu haircut kavali"</b> అని టైప్ చేయండి.</p></div>
<div class="loss"><p class="eyebrow" style="display:block">మీ సెలూన్ లెక్కలు</p>
<p><span>రాత్రి 9 తర్వాత వచ్చే WhatsApp లు (వారానికి)</span><i></i></p>
<p><span>గత శనివారం రాని కస్టమర్లు</span><i></i></p>
<p><span>ఫేషియల్ చేస్తుంటే ఫోన్ ఎవరు ఎత్తుతారు?</span><i></i></p></div>
<div class="offer">మొదటి 3 సెలూన్లకు: సెటప్ <b>${inr(f.setup)}</b> · నెలకు <b>${inr(f.monthly)}</b> (3 నెలలు), తర్వాత ${inr(f.monthly_after)}.</div>
</div>
<div class="foot"><span>ఫోన్ / WhatsApp: <span class="write"></span></span><span class="mono">${KALPA.udyam}</span></div></section>`;
  const back = `<section class="page" lang="en">
<header class="band"><p class="eyebrow">BotBhai · Kalpa Labs</p><h1>Your WhatsApp answers at 11 PM, in Telugu.</h1></header>
<div class="body">
<ul><li>Books the slot, then reminds the customer twice: the day before and 2 hours before.</li>
<li>Asks only happy, completed visits for a Google review.</li>
<li>Tells you at once about an unhappy customer, and you reply yourself from your phone.</li>
<li>Done for you: we set it up with your prices in 10 days. Nothing for your staff to learn.</li>
<li>If it doesn't pay for itself in 60 days, stop paying. No lock-in.</li></ul>
<table><thead><tr><th>Plan</th><th class="n">Setup</th><th class="n">Monthly</th></tr></thead><tbody>
${["lite", "standard", "pro"].map((id) => `<tr><td><b>${TIER[id].name}</b></td><td class="n">${inr(TIER[id].setup)}</td><td class="n">${inr(TIER[id].monthly)}</td></tr>`).join("")}
<tr><td><b>Founding</b> <span class="muted small">(first 3 salons)</span></td><td class="n">${inr(f.setup)}</td><td class="n">${inr(f.monthly)} → ${inr(f.monthly_after)}</td></tr></tbody></table>
<p class="small muted" style="margin:0">WhatsApp's own message fees (about ${inr(P.whatsapp_fees.lite_no_marketing)}–${inr(P.whatsapp_fees.typical)} a month) are paid by you directly to Meta, with no markup. Setup: ${esc(P.terms.setup_split)}. Annual prepay: ${esc(P.terms.annual_prepay)}.</p>
<div class="qrrow"><div class="qr">${qr(demo)}</div><p>Scan to try the demo on your own phone. Type <b>"repu haircut kavali"</b> and book a slot.</p></div>
</div>
<div class="foot"><span>Call / WhatsApp: <span class="write"></span></span><span class="mono">${KALPA.name} · ${KALPA.udyam}</span></div></section>`;
  return doc("BotBhai card (A5)", "A5", css, front + back);
}

// ---------------------------------------------------------------- 2. one-page proposal with the salon's own numbers
// The maths is shown on the page so the owner can check it. Assumptions are conservative and stated, never promised.
const ASSUME = { book_rate: 0.25, weeks: 4.3, saturdays: 4, reminder_cut: 1 / 3 };
function proposalNumbers(s) {
  const t = TIER[s.tier || "founding"]; if (!t) throw new Error(`unknown tier ${s.tier}`);
  const ticket = Number(s.avg_ticket); const late = Number(s.after9_per_week); const noshow = Number(s.noshows_last_saturday);
  if (!(ticket > 0) || !(late >= 0) || !(noshow >= 0)) throw new Error("proposal needs avg_ticket > 0, after9_per_week ≥ 0, noshows_last_saturday ≥ 0");
  const lostBookings = Math.round(late * ASSUME.weeks * ASSUME.book_rate);
  const noShows = Math.round(noshow * ASSUME.saturdays);
  const saved = Math.round(noShows * ASSUME.reminder_cut);
  const value = (lostBookings + saved) * ticket;
  const monthly = t.monthly; const fees = s.marketing === false ? P.whatsapp_fees.lite_no_marketing : P.whatsapp_fees.typical;
  const breakEven = Math.ceil((monthly + fees) / ticket);
  return { t, ticket, late, noshow, lostBookings, noShows, saved, value, monthly, fees, breakEven };
}
function proposal(s) {
  const n = proposalNumbers(s); const t = n.t;
  const css = `.page{width:210mm;height:296mm;display:flex;flex-direction:column}
.band h1{font-size:21pt}.wrap{padding:5mm 12mm;display:flex;flex-direction:column;gap:3.5mm}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.box{border:1px solid var(--rule);border-radius:3mm;padding:3.2mm 4mm}.box h2{font-size:14pt;margin-bottom:2mm}
.big{font:400 22pt/1.1 var(--f-display)}.ok{color:var(--ok)}
ul{margin:0;padding-left:5mm}li{margin-bottom:1.2mm}
.sign{display:grid;grid-template-columns:1fr 1fr;gap:10mm;margin-top:7mm}.sign div{border-top:1px solid var(--fg);padding-top:1.5mm;font-size:8.5pt;color:var(--muted)}
.foot{margin-top:auto;padding:4mm 12mm 6mm;border-top:1px solid var(--rule)}`;
  const body = `<section class="page"><header class="band"><p class="eyebrow">Proposal for ${esc(s.name)}${s.area ? " · " + esc(s.area) : ""}</p>
<h1>Answer every WhatsApp, cut no-shows, and get more Google reviews</h1>
<p class="muted" style="margin:2mm 0 0">Prepared by ${KALPA.name} for ${esc(s.owner || "the owner")} · ${esc(s.date || "")}</p></header>
<div class="wrap">
<div class="grid"><div class="box"><h2>What you told us</h2><table><tbody>
<tr><td>WhatsApps after 9 PM, per week</td><td class="n">${n.late}</td></tr>
<tr><td>No-shows last Saturday</td><td class="n">${n.noshow}</td></tr>
<tr><td>Average bill per visit</td><td class="n">${inr(n.ticket)}</td></tr>
<tr><td>Who answers during a facial</td><td class="n">${esc(s.phone_answerer || "-")}</td></tr></tbody></table></div>
<div class="box"><h2>What that may cost you each month</h2><table><tbody>
<tr><td>Late enquiries that could book (1 in 4)</td><td class="n">${n.lostBookings} visits</td></tr>
<tr><td>Saturday no-shows (4 Saturdays)</td><td class="n">${n.noShows} visits</td></tr>
<tr><td>No-shows two reminders can save (about 1 in 3)</td><td class="n">${n.saved} visits</td></tr>
<tr><td><b>Possible extra income</b></td><td class="n"><b>${inr(n.value)}</b></td></tr></tbody></table>
<p class="small muted" style="margin:2mm 0 0">An estimate from your numbers, not a promise. The 1-in-3 comes from a Cochrane review of text reminders (attendance 67.8% → 78.6%).</p></div></div>
<div class="grid"><div class="box"><h2>Your plan: ${esc(t.name)}</h2>
<p class="big">${inr(t.setup)} <span class="small muted">setup</span> + ${inr(n.monthly)}<span class="small muted">/month</span></p>
${t.monthly_after ? `<p class="small" style="margin:1mm 0 0">${inr(t.monthly)} for months 1–3, then ${inr(t.monthly_after)}. ${esc(t.note || "")}.</p>` : ""}
<p class="small" style="margin:2mm 0 0">${esc(t.gives)}.</p></div>
<div class="box"><h2>Pays for itself after</h2><p class="big ok">${n.breakEven} visit${n.breakEven === 1 ? "" : "s"} a month</p>
<p class="small" style="margin:1mm 0 0">${inr(n.monthly)} plan + about ${inr(n.fees)} WhatsApp fees, divided by your ${inr(n.ticket)} average bill. WhatsApp fees go from you directly to Meta, with no markup from us.</p></div></div>
<div class="box"><h2>How it works</h2><ul>
<li><b>Day 1:</b> you sign and pay half the setup fee, ${inr(Math.ceil(t.setup / 2))}, by UPI. We need your price list and 20 minutes to connect your WhatsApp Business number.</li>
<li><b>By day ${P.terms.live_in_days}:</b> BotBhai is live, with your prices, timings and Telugu replies. You pay the other ${inr(t.setup - Math.ceil(t.setup / 2))} at go-live, or we return your advance if we miss day ${P.terms.live_in_days}.</li>
<li><b>Every month:</b> an invoice on WhatsApp, a UPI QR, and a one-page report: bookings, reminders sent, no-shows, reviews and WhatsApp fees.</li>
<li><b>Any month:</b> stop by sending one WhatsApp. No lock-in. Your customer list is exported to you, then deleted from our systems.</li></ul></div>
<div class="sign"><div>For ${esc(s.name)} (name, signature, date)</div><div>For ${KALPA.name}</div></div>
</div><div class="foot">${KALPA.name} · ${KALPA.city} · Udyam ${KALPA.udyam} · Not registered under GST, so no GST is charged. · ${VERSION}</div></section>`;
  return doc(`BotBhai proposal: ${s.name}`, "A4", css, body);
}

// ---------------------------------------------------------------- 3. client agreement with DPDP processor terms
const SUBPROCESSORS = [
  ["Meta Platforms (WhatsApp Business Cloud API)", "Sends and receives your WhatsApp messages", "Your own WhatsApp account; Meta's terms"],
  ["Supabase", "Database: bookings, leads, messages", "Hosted database"],
  ["Netlify", "Runs the bot and serves your pages", "Hosting"],
  ["Groq", "Turns voice notes into text (if you use voice notes)", "Transcription only"],
  ["Sarvam AI", "Telugu/Hindi voice (Pro voice receptionist only)", "Voice only"],
];
function agreement() {
  const css = `.page{width:210mm;padding:0 0 8mm}.band h1{font-size:22pt}
.wrap{padding:5mm 13mm 0;columns:2;column-gap:8mm;font-size:9.3pt;line-height:1.42}
h2{font:600 9.5pt var(--f-body);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin:3.5mm 0 1.2mm;break-after:avoid}
p{margin:0 0 1.6mm}ol{margin:0 0 1.6mm;padding-left:4.5mm}li{margin-bottom:1mm}
.fill{display:inline-block;min-width:34mm;border-bottom:1px solid var(--fg)}
table{font-size:8.3pt;break-inside:avoid}.sign{column-span:all;display:grid;grid-template-columns:1fr 1fr;gap:12mm;margin-top:10mm}
.sign div{border-top:1px solid var(--fg);padding-top:1.5mm;font-size:8.5pt;color:var(--muted)}
.attrib{column-span:all;margin-top:5mm;font-size:7.5pt;color:var(--muted)}`;
  const tiers = P.tiers.map((t) => `${t.name} ${inr(t.setup)} + ${inr(t.monthly)}/month${t.monthly_after ? ` (then ${inr(t.monthly_after)})` : ""}`).join("; ");
  const body = `<section class="page"><header class="band"><p class="eyebrow">BotBhai service agreement · ${VERSION}</p><h1>Agreement between ${KALPA.name} and your salon</h1>
<p class="muted" style="margin:2mm 0 0">Plain-English terms. Please read them; ask us about anything that isn't clear.</p></header>
<div class="wrap">
<h2>1. Who is agreeing</h2>
<p><b>${KALPA.name}</b>, a sole proprietorship in ${KALPA.city}, Udyam ${KALPA.udyam} ("we"), and <b>the salon</b> named below ("you"): <span class="fill"></span>, owner <span class="fill"></span>, address <span class="fill" style="min-width:60mm"></span>.</p>
<h2>2. The service</h2>
<p>BotBhai answers your customers on your WhatsApp Business number (and, if your plan includes them, your website chat and phone line): prices, questions, bookings, reschedules, reminders and review requests, in English, Telugu and Hindi. Your plan: <span class="fill"></span>. Plans and prices: ${esc(tiers)}.</p>
<h2>3. Fees and payment</h2>
<ol><li>Setup fee: ${esc(P.terms.setup_split)}. Monthly fee: paid each month in advance, by UPI, against our invoice. Annual prepay: ${esc(P.terms.annual_prepay)}.</li>
<li>We are not registered under GST, so our invoices carry no GST. If that changes, we will tell you 30 days before any GST is added.</li>
<li>WhatsApp's own message fees and any ad spend are paid by you directly to Meta from your own account. We never add a markup to them.</li>
<li>Founding salons: the founding price stays fixed for 12 months. You can still stop any month.</li></ol>
<h2>4. Go-live promise</h2>
<p>We go live within ${P.terms.live_in_days} days of receiving your price list and access to your WhatsApp Business account. If we miss that, we return your setup advance in full.</p>
<h2>5. Stopping</h2>
<p>There is no lock-in. Send us one WhatsApp to stop; the monthly fee stops from the next month. The setup fee isn't refundable after go-live. We may stop the service with 30 days' notice, or at once if fees are unpaid for 30 days or the service is used for spam.</p>
<h2>6. Your part</h2>
<ol><li>You own your WhatsApp Business account and keep a payment method on it with Meta.</li>
<li>You message only customers who have contacted you or agreed to hear from you. Offers go only to customers who replied OFFERS. You follow WhatsApp's Business Messaging Policy.</li>
<li>You keep your prices, timings and holidays correct, and tell us when they change.</li></ol>
<h2>7. Your customers' data (DPDP Act 2023)</h2>
<p>Your salon decides why and how your customers' personal data is used, so you are the <b>Data Fiduciary</b>. We process it only on your behalf, so we are your <b>Data Processor</b> under section 8 of the Digital Personal Data Protection Act, 2023. This section is the "valid contract" that section asks for. We will:</p>
<ol><li><b>Use it only to run your service</b>, as this agreement and your written instructions say. We tell you at once if we can't follow an instruction. We never sell it, never use it for our own marketing, and never share it except as below.</li>
<li><b>Keep it safe:</b> encrypted connections, access only for the people who run your service (each bound to keep it confidential), access logs kept for 1 year, and the database locked so no web page can read it.</li>
<li><b>Use only these sub-processors</b>, and tell you 10 business days before adding one, so you can object or stop:
<table><thead><tr><th>Sub-processor</th><th>What for</th></tr></thead><tbody>${SUBPROCESSORS.map((r) => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join("")}</tbody></table></li>
<li><b>Tell you about any breach</b> without delay, and within 24 hours of finding it, with what happened, what data, and what we're doing. That gives you time to inform your customers and the Data Protection Board (the Rules ask for a detailed report within 72 hours).</li>
<li><b>Help you answer customers</b> who ask to see, correct or erase their data, or who withdraw consent. STOP on WhatsApp is honoured automatically.</li>
<li><b>Keep it only as long as needed:</b> chat messages for 180 days, bookings and leads while you are our client, unless you ask for less.</li>
<li><b>When you stop:</b> on request we send you an export (Excel) within 7 days, then delete your customers' data within 30 days. We keep only what the law makes us keep, such as our invoices to you.</li></ol>
<h2>8. Confidentiality</h2>
<p>Each of us keeps the other's business information private, during this agreement and after it. Founding salons agree that we may share anonymised results (no names or numbers) as case studies.</p>
<h2>9. What we can and can't promise</h2>
<p>We set up and run BotBhai with care and fix problems quickly. We can't promise a number of bookings or income, and we aren't responsible for outages or rule changes at WhatsApp, Meta or other providers. Neither of us is liable for indirect losses. Our total liability is limited to the fees you paid us in the 3 months before the claim, except for breaking section 7 through our own fault.</p>
<h2>10. Law and disputes</h2>
<p>Indian law applies. We will first try to settle any dispute by talking for 15 days. After that, courts in Hyderabad decide.</p>
<div class="sign"><div>For the salon: name, signature, date</div><div>For ${KALPA.name}: name, signature, date</div></div>
<p class="attrib">Structure and some wording adapted from the Common Paper Cloud Service Agreement v2.1 and Data Processing Agreement v1.1 (commonpaper.com/standards), licensed CC BY 4.0. Changes: shortened, rewritten in plain English for India and the DPDP Act 2023.</p>
</div></section>`;
  return doc("BotBhai service agreement", "A4", css, body);
}

// ---------------------------------------------------------------- 4. the salon's customer privacy notice (Telugu + English)
function privacy(s = {}) {
  const name = s.name || "[Salon name]"; const phone = s.owner_phone || "[owner's phone]";
  const css = `.page{width:210mm;min-height:297mm}.band h1{font-size:20pt}.cols{display:grid;grid-template-columns:1fr 1fr;gap:7mm;padding:6mm 12mm}
h2{font:600 9.5pt var(--f-body);color:var(--accent);margin:3mm 0 1mm}.te h2{font-family:var(--f-te)}p,li{font-size:9.3pt;margin:0 0 1.4mm}ul{margin:0;padding-left:4.5mm}
@media screen{body{background:var(--bg)}.page{max-width:210mm;margin:0 auto;background:#fff;min-height:auto;width:auto}.cols{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));padding:16px}}`;
  const en = `<div lang="en"><h2>Who we are</h2><p><b>${esc(name)}</b> uses BotBhai, run for us by ${KALPA.name} (Hyderabad), to answer WhatsApp, book visits and send reminders.</p>
<h2>What we collect</h2><ul><li>Your name and WhatsApp number</li><li>Your messages and voice notes (voice notes are turned into text)</li><li>Your bookings and the services you choose</li></ul>
<h2>Why</h2><ul><li>To reply, book, reschedule or cancel your visit</li><li>To remind you a day before and 2 hours before</li><li>To ask for a review after a completed visit</li><li>Offers <b>only</b> if you reply OFFERS</li></ul>
<h2>Who helps us</h2><p>${KALPA.name} (our data processor), WhatsApp/Meta, and our hosting providers. Nobody else, and your data is never sold.</p>
<h2>How long</h2><p>Messages for 180 days; bookings while you visit us, and then we delete them.</p>
<h2>Your rights</h2><ul><li>Reply <b>STOP</b> at any time to stop all messages; <b>START</b> to come back</li><li>Ask us to show, correct or delete your data</li><li>Name someone to act for you</li></ul>
<h2>Questions or complaints</h2><p>WhatsApp or call ${esc(phone)}. We reply within 7 days. If you're not satisfied, you can complain to the Data Protection Board of India.</p></div>`;
  const te = `<div lang="te" class="te"><h2>మేము ఎవరు</h2><p><b>${esc(name)}</b> WhatsApp కి జవాబివ్వడానికి, బుకింగ్‌లకు, గుర్తు చేయడానికి BotBhai ని వాడుతుంది. దీన్ని మా తరఫున ${KALPA.name} (హైదరాబాద్) నడుపుతుంది.</p>
<h2>మేము తీసుకునే వివరాలు</h2><ul><li>మీ పేరు, WhatsApp నంబర్</li><li>మీ మెసేజ్‌లు, వాయిస్ నోట్స్ (వాయిస్ నోట్స్‌ని టెక్స్ట్‌గా మారుస్తాం)</li><li>మీ బుకింగ్‌లు, మీరు ఎంచుకున్న సేవలు</li></ul>
<h2>ఎందుకు</h2><ul><li>జవాబివ్వడానికి, బుక్/మార్పు/రద్దు చేయడానికి</li><li>ఒక రోజు ముందు, 2 గంటల ముందు గుర్తు చేయడానికి</li><li>విజిట్ పూర్తయ్యాక రివ్యూ అడగడానికి</li><li>ఆఫర్లు, మీరు OFFERS అని పంపితేనే</li></ul>
<h2>మాకు సహాయం చేసేవారు</h2><p>${KALPA.name} (మా డేటా ప్రాసెసర్), WhatsApp/Meta, మా హోస్టింగ్ సంస్థలు. ఇంకెవరికీ ఇవ్వం; మీ డేటాను ఎప్పుడూ అమ్మం.</p>
<h2>ఎంత కాలం</h2><p>మెసేజ్‌లు 180 రోజులు; బుకింగ్‌లు మీరు మా కస్టమర్‌గా ఉన్నంత వరకు, ఆ తర్వాత తొలగిస్తాం.</p>
<h2>మీ హక్కులు</h2><ul><li>ఎప్పుడైనా <b>STOP</b> అని పంపితే మెసేజ్‌లు ఆగిపోతాయి; మళ్లీ కావాలంటే <b>START</b></li><li>మీ వివరాలు చూపించమని, సరిచేయమని, తొలగించమని అడగవచ్చు</li><li>మీ తరఫున ఇంకొకరిని నియమించవచ్చు</li></ul>
<h2>ప్రశ్నలు, ఫిర్యాదులు</h2><p>${esc(phone)} కి WhatsApp లేదా కాల్ చేయండి. 7 రోజుల్లో జవాబిస్తాం. సంతృప్తి లేకపోతే Data Protection Board of India కి ఫిర్యాదు చేయవచ్చు.</p></div>`;
  return doc(`Privacy notice: ${name}`, "A4", css, `<section class="page"><header class="band"><p class="eyebrow">Privacy notice · <span class="te" lang="te">గోప్యతా నోటీసు</span></p><h1>How ${esc(name)} uses your details</h1>
<p class="muted" style="margin:2mm 0 0">Under the Digital Personal Data Protection Act, 2023 · ${VERSION}</p></header><div class="cols">${en}${te}</div></section>`);
}

// ---------------------------------------------------------------- 5. objection sheet (Akhil's pocket answers)
const OBJECTIONS = [
  ["Will it replace my receptionist?", "No. It takes the 11 PM messages and the calls during a facial, so your staff can look after the customer in the chair. Hard questions and unhappy customers come straight to you.", "రిసెప్షనిస్ట్‌ని తీసేయదు. రాత్రి మెసేజ్‌లు, ఫేషియల్ టైమ్ కాల్స్ అది చూసుకుంటుంది; కష్టమైనవి మీకే వస్తాయి.", ""],
  ["Will WhatsApp ban my number?", "We use Meta's official WhatsApp Business platform, not the unofficial apps that get banned. We message only customers who wrote to you or agreed to hear from you, and STOP always works.", "మేము Meta అధికారిక WhatsApp Business ప్లాట్‌ఫాం వాడతాం. మీకు మెసేజ్ చేసినవారికి, ఒప్పుకున్నవారికి మాత్రమే పంపుతాం.", "Meta: Get opt-in for WhatsApp"],
  [`DINGG is only ${inr(999)} a month.`, "DINGG is software your staff must run. BotBhai is done for you: it chats in Telugu at 11 PM, books against a real calendar and sends the reminders, without anyone touching a screen.", "DINGG ని మీ స్టాఫ్ నడపాలి. BotBhai మీ తరఫున రాత్రీ తెలుగులో చాట్ చేసి బుక్ చేస్తుంది.", "PLAN.md §2 alternatives"],
  ["It's too expensive.", `Your own numbers decide. It pays for itself after a few extra visits a month (the proposal shows the exact number). Start on Lite at ${inr(TIER.lite.monthly)} a month, and stop any month if it doesn't pay.`, "నెలకు కొన్ని విజిట్లు వస్తే చాలు, ఖర్చు తిరిగి వస్తుంది. నచ్చకపోతే ఏ నెలైనా ఆపేయవచ్చు.", ""],
  ["My customers won't chat with a bot.", "They already WhatsApp you. BotBhai answers in their own mix of Telugu and English, in seconds, and hands over to you the moment they ask for a person.", "మీ కస్టమర్లు ఇప్పటికే WhatsApp చేస్తున్నారు. వాళ్ల భాషలోనే జవాబిస్తుంది; మనిషి కావాలంటే మీకు ఇస్తుంది.", ""],
  ["What if you disappear?", `Kalpa Labs is Udyam-registered (${KALPA.udyam}). Your WhatsApp account stays yours, there's no lock-in, and you can export your customer list to Excel any day.`, "WhatsApp అకౌంట్ మీదే. లాక్-ఇన్ లేదు. మీ కస్టమర్ లిస్ట్ ఎప్పుడైనా Excel లో తీసుకోవచ్చు.", ""],
  ["Do reminders really stop no-shows?", "Not all of them, but a Cochrane review of text reminders found attendance rose from 67.8% to 78.6%. BotBhai sends two reminders, and customers can reschedule in one tap instead of just not coming.", "అన్నీ ఆగవు, కానీ రిమైండర్లతో రాని వాళ్లు తగ్గుతారు. ఒక్క ట్యాప్‌తో టైమ్ మార్చుకోవచ్చు.", "Cochrane CD007458 (2013)"],
  ["My nephew / a freelancer does our marketing.", "Keep them for posts. BotBhai does a different job: it answers and books every enquiry, day and night, and shows you each month what it booked.", "పోస్ట్‌లకి వాళ్లని ఉంచుకోండి. BotBhai ప్రతి మెసేజ్‌కీ జవాబిచ్చి బుక్ చేస్తుంది.", ""],
  ["Who pays WhatsApp's fees?", `You do, directly to Meta from your own account, with no markup from us: about ${inr(P.whatsapp_fees.lite_no_marketing)}–${inr(P.whatsapp_fees.typical)} a month for a busy salon.`, "WhatsApp ఫీజు మీరే నేరుగా Meta కి కడతారు; మేము ఏమీ కలపం.", "PLAN.md §3a"],
];
function objections() {
  const css = `.page{width:210mm;min-height:297mm}.band h1{font-size:22pt}.wrap{padding:5mm 12mm;display:grid;gap:3mm}
.o{border:1px solid var(--rule);border-left:4px solid var(--l1);border-radius:2.5mm;padding:2.6mm 4mm;break-inside:avoid}
.o h2{font:700 10.5pt var(--f-body);margin:0 0 1mm}.o p{margin:0 0 1mm;font-size:9.3pt}.o .te{color:var(--accent)}
.rules{font-size:8.5pt;color:var(--muted);padding:0 12mm 6mm}`;
  const body = `<section class="page"><header class="band"><p class="eyebrow">BotBhai · objection sheet</p><h1>When the owner says…</h1>
<p class="muted" style="margin:2mm 0 0">Answer in one breath, then show the demo. Never promise a number of bookings.</p></header>
<div class="wrap">${OBJECTIONS.map(([q, a, te, src]) => `<div class="o"><h2>“${esc(q)}”</h2><p>${esc(a)}</p><p class="te" lang="te">${esc(te)}</p>${src ? `<p class="small muted">Source: ${esc(src)}</p>` : ""}</div>`).join("")}</div>
<p class="rules">Rules: no cold calls; at most 3 follow-ups (days 2, 5, 10), and stop on "no"; never promise results; prices only from this kit (PLAN.md §2). ${VERSION}</p></section>`;
  return doc("BotBhai objection sheet", "A4", css, body);
}

module.exports = { card, proposal, proposalNumbers, agreement, privacy, objections, P, TIER, ASSUME, DEMO_URL, OBJECTIONS, SUBPROCESSORS };

if (require.main === module) {
  const [cmd, a, b] = process.argv.slice(2);
  const opt = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : undefined; };
  const load = (f) => JSON.parse(fs.readFileSync(f, "utf8"));
  if (cmd === "all") {
    fs.mkdirSync(a, { recursive: true });
    const ex = load(path.join(SALES, "example-salon.json"));
    const files = { "card-a5.html": card({ demo: opt("--demo") || DEMO_URL }), "proposal-example.html": proposal(ex), "agreement.html": agreement(),
      "privacy-notice-example.html": privacy(ex), "objections.html": objections() };
    for (const [f, h] of Object.entries(files)) fs.writeFileSync(path.join(a, f), h);
    console.log(JSON.stringify({ files: Object.keys(files), numbers: proposalNumbers(ex) }));
  } else if (cmd === "proposal") fs.writeFileSync(b, proposal(load(a)));
  else if (cmd === "privacy") fs.writeFileSync(b, privacy(load(a)));
  else { console.error("usage: node tools/sales_kit.js all <outdir> [--demo <url>] | proposal <salon.json> <out.html> | privacy <salon.json> <out.html>"); process.exit(1); }
}
