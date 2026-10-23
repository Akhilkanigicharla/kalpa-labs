// A74 · Free AI fallback for messages the rules don't understand.
// Only the unanswered text goes to a free model (private n8n workflow, Groq free tier). The model may only
// pick an intent (and a service name from this setup's own list); the engine then answers with its own
// facts, so prices and slots always come from the setup, never from the model. A free-text reply is used
// only for "other" and only if it carries no number, price or time. Anything else → the normal menu.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BotBhaiFallback = factory();
})(typeof self !== "undefined" ? self : this, function () {
  const INTENTS = ["book", "reschedule", "cancel", "prices", "hours", "offers", "human", "faq", "other"];

  function request(cfg, text) {
    const services = (cfg.catalog || []).map((c) => c.name);
    const faqs = (cfg.faqs || []).map((q, i) => `${i}: ${q.k.slice(0, 6).join(", ")}`).join("; ");
    const system = [
      `You read one WhatsApp message sent to ${cfg.business}. It may be English, Telugu, Hindi or a mix, with typos.`,
      `Reply with JSON only: {"intent": one of ${JSON.stringify(INTENTS)}, "service": one name from the list or null, "faq": number or null, "reply": string or null}.`,
      `FAQ topics (number: keywords): ${faqs}.`,
      `Services: ${JSON.stringify(services)}.`,
      `book = wants an appointment; reschedule = move an existing one; cancel = cancel one; prices = asks cost; hours = timings, location or directions; offers = discounts or deals; human = complaint or wants a person; faq = the question matches one FAQ topic (give its number); other = anything else.`,
      `"reply" only for intent other: one short polite line in the customer's language saying the team will check and reply. Never state a fact, price, number, date or time. Never promise anything.`,
    ].join("\n");
    return { system, user: String(text).slice(0, 500) };
  }

  const NUMBERY = /[0-9०-९౦-౯₹]|\b(rs|inr|rupees?|rupay|pm|o'?clock)\b|\ba\.m\.|రూపాయ|रुपय|रुपए|https?:|www\./i;

  // Turn the model's raw text into a safe decision, or null (caller keeps the menu reply).
  function guard(cfg, raw) {
    let o;
    try { o = JSON.parse(String(raw).trim().replace(/^```(json)?\s*|\s*```$/g, "")); } catch (e) { return null; }
    if (!o || typeof o !== "object" || !INTENTS.includes(o.intent)) return null;
    const svc = typeof o.service === "string" && (cfg.catalog || []).find((c) => c.name.toLowerCase() === o.service.trim().toLowerCase());
    const out = { intent: o.intent, service: svc ? svc.name : null, faq: null, reply: null };
    if (o.intent === "faq") {
      if (!Number.isInteger(o.faq) || !(cfg.faqs || [])[o.faq]) return null;
      out.faq = o.faq;
    }
    if (o.intent === "other") {
      const r = typeof o.reply === "string" ? o.reply.trim() : "";
      if (!r || r.length > 300 || NUMBERY.test(r)) return null;
      out.reply = r;
    }
    return out;
  }

  // The message the rules engine already understands for this decision (menu labels come from the setup).
  function engineText(cfg, d) {
    const label = (key) => { const m = (cfg.menu || []).find((x) => x.key === key); return m ? m.label : null; };
    switch (d.intent) {
      case "book": return d.service ? "book " + d.service : "book";
      case "reschedule": return "reschedule";
      case "cancel": return "cancel";
      case "prices": return label("prices") || "price list";
      case "hours": return label("hours") || "timings";
      case "offers": return label("faq:offers") || "offers";
      case "human": return "talk to a person";
      case "faq": return cfg.faqs[d.faq].k[0];
      default: return null;
    }
  }

  // bot = createBot(...), out = the engine result (its state is reused) that logged "unanswered", ask(system, user) → Promise<string>.
  async function rescue(bot, out, meta, ask, ms = 8000) {
    const state = out.state;
    const miss = out.events.find((e) => e.type === "unanswered");
    if (!miss || !ask) return out;
    const req = request(bot.config, miss.text);
    let raw, timer;
    try { raw = await Promise.race([ask(req.system, req.user), new Promise((_, no) => { timer = setTimeout(() => no(new Error("timeout")), ms); })]); }
    catch (e) { return out; }
    finally { clearTimeout(timer); }
    const d = guard(bot.config, raw);
    if (!d) return out;
    const ev = { type: "ai_fallback", intent: d.intent, text: miss.text };
    if (d.intent === "other") return Object.assign({}, out, { replies: [{ text: d.reply }].concat(out.replies), events: out.events.concat(ev) });
    let again = bot.handle(state, engineText(bot.config, d), meta);
    if (d.intent === "reschedule" && again.events.some((e) => e.type === "unanswered")) again = bot.handle(state, "book", meta); // nothing booked yet
    if (again.events.some((e) => e.type === "unanswered")) return out;
    return Object.assign({}, again, { events: out.events.concat(ev, again.events) });
  }

  return { INTENTS, request, guard, engineText, rescue };
});
