/*
 * A351 · Children's data (DPDP Act s.9 + Rule 10): spot a visitor who says THEY are under 18.
 * Used by the BotBhai engine (WhatsApp, Telegram, web chat) and the Kalpa site chat.
 * Only first-person statements count ("I am 15", "nenu 9th class", "मैं 15 साल का हूँ");
 * a parent booking for a child ("my son is 12") or "I'm 10 minutes late" does not.
 * No dependencies; runs in Node and the browser (self.BotBhaiMinor).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.BotBhaiMinor = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const AGE = "(?:[6-9]|1[0-7])"; // 6–17: younger children rarely type; 18+ is an adult
  const CLS = "(?:[1-9]|1[0-2])"; // school class 1–12
  const ORD = "(?:st|nd|rd|th|va|vi|వ|वीं|वी)?";
  const UNIT = "(?:years?|yrs?|yr|y\\/?o|yo|saal|sal|yella|ellu|samvatsaralu|ఏళ్ళు|ఏళ్లు|ఏండ్లు|సంవత్సరాలు|సంవత్సరాల|साल|वर्ष|बरस)";
  const NOT_AGE = "(?!\\s*(?:min|mins|minute|minutes|hour|hours|hrs|km|kms|people|persons|members|days?|weeks?|months?|rs|rupees|%|kg|am|pm|o'?clock|th\\s+floor))";
  const END = "(?=$|[\\s,.!?;:)\\]])";
  const RULES = [
    // English / Tenglish / Hinglish in Latin letters
    new RegExp(`\\b(?:i am|i'm|im|iam|i m)\\s+(?:only\\s+|just\\s+)?${AGE}${END}${NOT_AGE}`),
    new RegExp(`\\b(?:my age is|my age|naa vayasu|na vayasu|naa age|na age|meri age|meri umar|meri umra|mera age)\\s*(?:is|:|-)?\\s*(?:only\\s+)?${AGE}\\b`),
    new RegExp(`\\b(?:i am|i'm|im|iam|i m|nenu|naaku|naku|main|mai|mein)\\s+(?:only\\s+)?${AGE}\\s*${UNIT}`),
    new RegExp(`\\b${AGE}\\s*${UNIT}\\s*(?:old\\s+)?(?:ka|ki)\\s+(?:hoon|hu|hun)\\b`), // "15 saal ka hoon"
    new RegExp(`\\b(?:i am|i'm|im|iam|i m)\\s+(?:a\\s+)?(?:minor|under\\s*-?\\s*18|below\\s+18|not\\s+(?:yet\\s+)?18)\\b`),
    new RegExp(`\\b(?:i am|i'm|im|iam|i m)\\s+(?:in|studying|in\\s+class|studying\\s+in)\\s+(?:class\\s+|std\\s+|standard\\s+|grade\\s+)?${CLS}${ORD}(?:\\s*(?:class|std|standard|grade))?\\b`),
    new RegExp(`\\b(?:nenu|main|mai|mein)\\s+${CLS}${ORD}\\s*(?:class|std|standard|tharagathi|taragati|kaksha)\\b`), // "nenu 9th class", "main 9th class mein"
    new RegExp(`\\b(?:i study|i'm studying|im studying|nenu chaduvutunna)\\s+(?:in\\s+)?(?:class\\s+)?${CLS}${ORD}(?:\\s*(?:class|std|standard|grade))?\\b`),
    new RegExp(`\\b(?:under|below)\\s*-?\\s*18\\s+(?:nenu|hoon|hu|hun|ni|ki)\\b`),
    // Telugu script
    new RegExp(`(?:నాకు|నా వయసు|నా వయస్సు|నేను)\\s*${AGE}\\s*(?:ఏళ్ళు|ఏళ్లు|ఏండ్లు|సంవత్సరాలు|సంవత్సరాల|years?)`),
    new RegExp(`(?:నా వయసు|నా వయస్సు)\\s*${AGE}`),
    new RegExp(`నేను\\s*${CLS}\\s*(?:వ|వ\\s)?\\s*(?:తరగతి|క్లాస్|class)`),
    new RegExp(`నేను\\s*(?:మైనర్|18\\s*ఏళ్ల\\s*లోపు)`),
    // Hindi script
    new RegExp(`(?:मैं|मेरी उम्र|मेरी आयु|मेरी उमर)\\s*${AGE}\\s*(?:साल|वर्ष|बरस)?\\s*(?:का|की|है|हूँ|हूं)`),
    new RegExp(`मैं\\s*${CLS}\\s*(?:वीं|वी|th)?\\s*(?:कक्षा|क्लास|class)`),
    new RegExp(`मैं\\s*(?:नाबालिग|18\\s*से\\s*कम)`),
  ];
  // Someone writing about another person, or saying they are 18+, is not a minor visitor.
  const NOT_SELF = /\b(my|our|naa|na|meri|mera|mere)\s+(son|daughter|kid|kids|child|children|baby|brother|sister|friend|cousin|nephew|niece|student|students|koduku|kuthuru|kuturu|beta|beti|bhai|behen|bachcha|bacha|bacche)\b|నా (కొడుకు|కూతురు|పాప|బాబు)|मेरा (बेटा|भाई)|मेरी (बेटी|बहन)/;

  function clean(s) {
    return String(s || "").normalize("NFC").replace(/[​-‍⁠﻿]/g, "").toLowerCase()
      .replace(/[’`]/g, "'").replace(/[०-९]/g, (d) => String(d.charCodeAt(0) - 0x966)) // Devanagari digits
      .replace(/[౦-౯]/g, (d) => String(d.charCodeAt(0) - 0xc66)) // Telugu digits
      .replace(/\s+/g, " ").trim();
  }

  // true when the writer says they themselves are under 18
  function isMinor(text) {
    const s = clean(text);
    if (!s || s.length > 2000) return false;
    // check each clause on its own, so "my son is 12, I am 40" stays an adult and "I am 15, my mom said ok" counts
    return s.split(/[,.;!?\n]| and | but | aur | mariyu /).some((c) => {
      const part = c.trim();
      return part && !NOT_SELF.test(part) && RULES.some((re) => re.test(part));
    });
  }

  // Fixed replies (no model in the loop), one per Kalpa language. No legal claims, no proof asked.
  const REPLY = {
    en: "Thank you for writing to us 🙏 As you are under 18, we can't take your details or book here. Please ask a parent or guardian to message or call us. We have not saved your details.",
    te: "మాకు మెసేజ్ చేసినందుకు ధన్యవాదాలు 🙏 మీకు 18 ఏళ్లు నిండలేదు కాబట్టి ఇక్కడ మీ వివరాలు తీసుకోలేము, బుకింగ్ చేయలేము. దయచేసి మీ తల్లిదండ్రులు లేదా సంరక్షకులను మాకు మెసేజ్ లేదా కాల్ చేయమని చెప్పండి. మీ వివరాలు మేము సేవ్ చేయలేదు.",
    hi: "हमें लिखने के लिए धन्यवाद 🙏 आप 18 साल से कम हैं, इसलिए हम यहाँ आपकी जानकारी नहीं ले सकते और बुकिंग नहीं कर सकते. कृपया अपने माता-पिता या अभिभावक से हमें मैसेज या कॉल करने को कहें. हमने आपकी जानकारी सेव नहीं की है.",
    tg: "Message chesinanduku thanks 🙏 Meeku 18 years nindaledu kabatti ikkada mee details teesukolemu, booking cheyalemu. Dayachesi mee parents leda guardian ni maaku message leda call cheyamani cheppandi. Mee details memu save cheyaledu.",
    hg: "Humein message karne ke liye thanks 🙏 Aap 18 saal se kam hain, isliye hum yahan aapki details nahi le sakte aur booking nahi kar sakte. Please apne parents ya guardian se humein message ya call karne ko kahiye. Humne aapki details save nahi ki hain.",
  };
  // the site chat names languages differently
  const ALIAS = { "te-latn": "tg", "hi-latn": "hg" };
  function reply(lang) { return REPLY[ALIAS[lang] || lang] || REPLY.en; }

  return { isMinor, reply, REPLY };
});
