// Submits a setup's WhatsApp message templates to Meta for approval (usually approved in minutes to 24 h).
// Usage: WA_ACCESS_TOKEN=... node tools/create-templates.js <salon|realestate|gym|examkits> <WABA_ID>
const [setup, waba] = process.argv.slice(2);
if (!setup || !waba || !process.env.WA_ACCESS_TOKEN) { console.error("usage: WA_ACCESS_TOKEN=... node tools/create-templates.js <setup> <waba_id>"); process.exit(1); }
const templates = require(`../setups/${setup}/templates.json`);
const fs = require("fs"), path = require("path");
// Meta needs a sample image "handle" for templates with an image header (Resumable Upload API, needs META_APP_ID)
async function uploadHandle(file) {
  const buf = fs.readFileSync(file); const H = { Authorization: `OAuth ${process.env.WA_ACCESS_TOKEN}` };
  const sess = await (await fetch(`https://graph.facebook.com/v21.0/${process.env.META_APP_ID}/uploads?file_length=${buf.length}&file_type=image/png`, { method: "POST", headers: H })).json();
  const up = await (await fetch(`https://graph.facebook.com/v21.0/${sess.id}`, { method: "POST", headers: Object.assign({ file_offset: "0" }, H), body: buf })).json();
  return up.h;
}
(async () => {
  for (const [key, t] of Object.entries(templates)) {
    const example = t.params.map((p) => ({ name: "Priya", business: "Glow Studio", service: "Hair spa", date: "Tue, 13 Oct", slot: "4:00 PM", address: "Jubilee Hills", area: "Kollur", bhk: "3 BHK", plan: "Annual plan", review_link: "https://g.page/r/example", exam: "SSC CGL", question: "If 20% of x is 50, x = ? A) 100 B) 200 C) 250 D) 500", summary: "12 leads, ₹180 per lead" }[p] || "example"));
    const components = [{ type: "BODY", text: t.body, ...(example.length ? { example: { body_text: [example] } } : {}) }];
    if (t.card && process.env.META_APP_ID) {
      const file = path.join(__dirname, "..", "web", "dist", "cards", "demo", t.card);
      if (fs.existsSync(file)) components.unshift({ type: "HEADER", format: "IMAGE", example: { header_handle: [await uploadHandle(file)] } });
    }
    if (t.buttons) components.push({ type: "BUTTONS", buttons: t.buttons.map((b) => ({ type: "QUICK_REPLY", text: b })) });
    const res = await fetch(`https://graph.facebook.com/v21.0/${waba}/message_templates`, { method: "POST", headers: { Authorization: `Bearer ${process.env.WA_ACCESS_TOKEN}`, "Content-Type": "application/json" }, body: JSON.stringify({ name: t.name, category: t.category, language: t.language, components }) });
    const out = await res.json(); console.log(key.padEnd(14), t.name.padEnd(26), res.ok ? `submitted (${out.status || "PENDING"})` : `error: ${out.error && out.error.message}`);
  }
})();
