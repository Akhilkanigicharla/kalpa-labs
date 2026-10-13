// Transcript -> job card (rule-based, offline, ₹0). Handles English, Tenglish and Telugu script
// the way AC technicians actually speak ("split AC gas leak undi, gas refill 2500, capacitor 450").
// An LLM can fill gaps later; this pass must never invent a value it did not hear.

const TE_DIGITS = { "౦": 0, "౧": 1, "౨": 2, "౩": 3, "౪": 4, "౫": 5, "౬": 6, "౭": 7, "౮": 8, "౯": 9 };
const NUM_WORDS = { // Telugu/Hindi/English number words technicians use for prices
  "okati": 1, "rendu": 2, "moodu": 3, "mudu": 3, "nalugu": 4, "aidu": 5, "aaru": 6, "edu": 7, "enimidi": 8, "tommidi": 9,
  "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
  "ఒక": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
};
const THOUSAND = /^(velu|vela|veyyi|వేలు|వేల|వెయ్యి|hazaar|hazar|thousand|k)$/i;
const HUNDRED = /^(vandalu|vanda|వందలు|వంద|sau|hundred)$/i;

const APPLIANCES = [
  { key: "split_ac", re: /\bsplit\s*(ac|a\.c\.)?\b|స్ప్లిట్/i },
  { key: "window_ac", re: /\bwindow\s*(ac|a\.c\.)?\b|విండో/i },
  { key: "cassette_ac", re: /\bcassette\b/i },
  { key: "ac", re: /\b(ac|a\.c\.|air\s*conditioner)\b|ఏసీ|ఏ\.సీ/i },
  { key: "fridge", re: /\b(fridge|refrigerator)\b|ఫ్రిజ్/i },
  { key: "washing_machine", re: /\bwashing\s*machine\b|వాషింగ్/i },
];
const BRANDS = ["Voltas", "LG", "Samsung", "Daikin", "Blue Star", "Lloyd", "Carrier", "Hitachi", "Panasonic", "Godrej", "Whirlpool", "Haier", "Mitsubishi", "O General", "IFB", "Croma"];
const ISSUES = [
  { key: "gas_leak", re: /gas\s*(leak|leakage|leaking)|గ్యాస్\s*లీక్/i },
  { key: "not_cooling", re: /not\s*cooling|no\s*cooling|cooling\s*(ledu|raledu|ledhu|nahi|kam|takkuva)|చల్లగా\s*లేదు|కూలింగ్\s*లేదు/i },
  { key: "water_leak", re: /water\s*(leak|leakage|dripping|vastundi|kaarutundi)|నీళ్లు\s*కారుతున్నాయి/i },
  { key: "noise", re: /\bnoise\b|sound\s*(vastundi|chestundi|undi)|శబ్దం/i },
  { key: "not_starting", re: /not\s*(starting|on|working)|on\s*avvatledu|start\s*avvatledu|పని\s*చేయడం\s*లేదు/i },
  { key: "service", re: /(?<!next\s)(?<!jet\s)\b(general\s*)?service\b(?!\s*charge)|\bservicing\b|సర్వీస్(?!\s*చార్జ్)/i }, // not "service charge" or "next service"
  { key: "installation", re: /\binstall(ation)?\b|ఇన్‌?స్టాల్/i },
];
const PARTS = [ // name, regex, default SAC context
  { name: "Gas refill", re: /gas\s*(refill|filling|charging|top\s*up)|గ్యాస్\s*(రీఫిల్|ఫిల్లింగ్)/i },
  { name: "Capacitor", re: /capacitor|కెపాసిటర్/i },
  { name: "PCB repair", re: /\bpcb\b|board\s*repair/i },
  { name: "Compressor", re: /compressor|కంప్రెసర్/i },
  { name: "Fan motor", re: /fan\s*motor|blower\s*motor/i },
  { name: "Copper pipe", re: /copper\s*pipe|pipe\s*(work|change)/i },
  { name: "Service charge", re: /service\s*charge|visit\s*charge|labour|labor|సర్వీస్\s*చార్జ్/i },
  { name: "Jet service", re: /jet\s*(service|wash|cleaning)|water\s*wash/i },
  { name: "Stabilizer", re: /stabili[sz]er/i },
];

const normDigits = (s) => s.replace(/[౦-౯]/g, (d) => TE_DIGITS[d]);

/** Read an amount that starts at word index i: "2500", "2,500", "₹450", "rendu velu", "2.5k", "rendu velu aidu vandalu". */
function readAmount(words, i) {
  let total = 0, used = 0, any = false;
  for (let j = i; j < Math.min(words.length, i + 6); j++) {
    const w = words[j].replace(/^₹|rs\.?|^rupees?$/i, "");
    const num = w.match(/^(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)(k)?$/i);
    if (num) {
      let v = Number(num[1].replace(/,/g, "")); if (num[2]) v *= 1000;
      const next = words[j + 1] || "";
      if (THOUSAND.test(next)) { v *= 1000; j++; } else if (HUNDRED.test(next)) { v *= 100; j++; }
      total += v; used = j - i + 1; any = true; continue;
    }
    const n = NUM_WORDS[w.toLowerCase()];
    if (n !== undefined) {
      const next = words[j + 1] || "";
      if (THOUSAND.test(next)) { total += n * 1000; j++; used = j - i + 1; any = true; continue; }
      if (HUNDRED.test(next)) { total += n * 100; j++; used = j - i + 1; any = true; continue; }
    }
    if (/^(rupees?|rs\.?|₹|ki|ku|ka|antha|avutundi|cost|charge|ayyindi)$/i.test(w) && any) { used = j - i + 1; continue; }
    if (/^(rupees?|rs\.?|₹)$/i.test(w) && !any) continue;
    break;
  }
  return any ? { value: total, used } : null;
}

export function parseTranscript(raw, { now = new Date() } = {}) {
  const text = normDigits(String(raw || "")).replace(/\s+/g, " ").trim();
  const card = { customer: {}, appliance: null, brand: null, issues: [], parts: [], total: null, next_service: null, notes: text };

  const phone = text.replace(/(\d)[\s-](?=\d)/g, "$1").match(/(?:\+?91)?([6-9]\d{9})\b/);
  if (phone) card.customer.phone = phone[1];
  const name = text.match(/(?:customer|name|peru|పేరు|naam)\s*(?:is|:|-)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)/) ||
               text.match(/\b([A-Z][a-z]+)\s+(?:garu|gaaru|గారు|ji)\b/);
  if (name) card.customer.name = name[1];
  const area = text.match(/\b(Ameerpet|SR Nagar|Kukatpally|Madhapur|Gachibowli|Kondapur|Miyapur|Begumpet|Jubilee Hills|Banjara Hills|Secunderabad|Dilsukhnagar|LB Nagar|Uppal|Mehdipatnam|Tolichowki|Manikonda|Kompally|Bachupally)\b/i); // "Ameerpet lo", "in Ameerpet"
  if (area) card.customer.area = area[1];

  const app = APPLIANCES.find((a) => a.re.test(text)); if (app) card.appliance = app.key;
  const tons = text.match(/(\d(?:\.\d)?)\s*(?:ton|tonne|టన్)/i); if (tons) card.capacity_tons = Number(tons[1]);
  const brand = BRANDS.find((b) => new RegExp(`\\b${b.replace(" ", "\\s*")}\\b`, "i").test(text)); if (brand) card.brand = brand;
  card.issues = ISSUES.filter((x) => x.re.test(text)).map((x) => x.key);

  // parts with the amount spoken right after them ("gas refill 2500", "capacitor ki 450")
  const words = text.split(" ").map((w) => w.replace(/[.,;:!?]+$/, ""));
  for (const p of PARTS) {
    const m = text.match(p.re); if (!m) continue;
    const before = text.slice(0, m.index + m[0].length).split(" ").length; // index of the word after the match
    let amt = null;
    for (let k = before; k < Math.min(words.length, before + 3) && !amt; k++) amt = readAmount(words, k);
    card.parts.push({ desc: p.name, qty: 1, rate: amt ? amt.value : null });
  }
  const total = text.match(/(?:total|mottam|మొత్తం|kul)\s*(?:amount)?\s*(?:is|:)?\s*/i);
  if (total) { const k = text.slice(0, total.index + total[0].length).trim().split(" ").length; const a = readAmount(words, k); if (a) card.total = a.value; }
  const sum = card.parts.reduce((s, p) => s + (p.rate || 0), 0);
  card.total_check = card.total == null ? "no spoken total" : card.total === sum ? "matches parts" : `spoken ${card.total} vs parts ${sum}`;

  const months = text.match(/(?:next\s*service|malli|again)\D{0,20}(\d{1,2})\s*(?:months?|nelalu|నెలలు)/i);
  if (months) { const d = new Date(now); d.setUTCMonth(d.getUTCMonth() + Number(months[1])); card.next_service = d.toISOString().slice(0, 10); }
  card.missing = ["phone", "appliance", "parts"].filter((f) => (f === "phone" ? !card.customer.phone : f === "parts" ? !card.parts.length : !card[f]));
  return card;
}
