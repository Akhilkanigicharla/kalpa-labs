// BotBhai gym setup — WhatsApp / web / voice conversation config.
// Edit per client in Supabase clients.config (overrides any field here).
module.exports = {
  "id": "gym",
  "capacity": 10,
  "holidays": [{ "date": "2026-11-08", "name": "Diwali" }],
  "label": "Gym",
  "emoji": "🏋️",
  "business": "IronPulse Fitness",
  "address": "3rd Floor, Madhapur Metro Pillar 1520, Hyderabad",
  "hours": "Mon–Sat 5:00 AM – 11:00 PM · Sun 6:00 AM – 12:00 PM",
  "phone": "+91 90000 00004",
  "greeting": "Hey 💪 Welcome to *{business}*! Grab a *free trial session*, check membership plans or talk to a trainer.",
  "menu": [
    {
      "key": "book",
      "label": "Book a free trial"
    },
    {
      "key": "prices",
      "label": "Membership plans"
    },
    {
      "key": "faq:trainer",
      "label": "Personal training"
    },
    {
      "key": "hours",
      "label": "Timings & location"
    },
    {
      "key": "human",
      "label": "Talk to the front desk"
    }
  ],
  "catalogTitle": "Membership plans",
  "catalog": [
    {
      "name": "Monthly",
      "price": "₹1,499"
    },
    {
      "name": "Quarterly",
      "price": "₹3,999"
    },
    {
      "name": "Half-yearly",
      "price": "₹6,999"
    },
    {
      "name": "Annual (best value)",
      "price": "₹11,999"
    },
    {
      "name": "Personal training add-on",
      "price": "₹4,000 / month"
    }
  ],
  "bookWord": "free trial",
  "steps": [
    {
      "field": "goal",
      "ask": "What's your main goal?",
      "choices": [
        "Weight loss",
        "Muscle gain",
        "General fitness",
        "Strength / powerlifting",
        "Yoga / Zumba"
      ]
    },
    {
      "field": "date",
      "ask": "When do you want your free trial? (today, tomorrow, Monday, or 20/10)",
      "type": "date"
    },
    {
      "field": "slot",
      "ask": "Pick a time:",
      "choices": [
        "6:00 AM",
        "8:00 AM",
        "6:00 PM",
        "8:00 PM"
      ]
    },
    {
      "field": "name",
      "ask": "Your name?",
      "type": "name"
    }
  ],
  "confirm": "🔥 *Free trial booked*\n👤 {name}\n🎯 Goal: {goal}\n📅 {date} at {slot}\n📍 {address}\n\nBring sports shoes and a water bottle. A trainer will do a free body-composition check for you.",
  "faqs": [
    {
      "id": "trainer",
      "k": [
        "trainer",
        "personal training",
        "pt",
        "coach"
      ],
      "a": "🧑‍🏫 Certified personal trainers: ₹4,000/month for 12 sessions, including a diet plan. Reply *1* to start with a free trial."
    },
    {
      "k": [
        "diet",
        "nutrition",
        "protein",
        "meal"
      ],
      "a": "Every member gets a basic diet chart. Detailed nutrition coaching comes with personal training."
    },
    {
      "k": [
        "ladies",
        "women",
        "female",
        "girls"
      ],
      "a": "👩 Women-only batch 10 AM – 12 PM with female trainers, plus a separate changing room."
    },
    {
      "k": [
        "freeze",
        "pause",
        "hold"
      ],
      "a": "Half-yearly and annual plans can be frozen for up to 30 days (medical or travel)."
    },
    {
      "k": [
        "renew",
        "renewal",
        "expire",
        "expiry"
      ],
      "a": "Renew before expiry and get 10% off. Reply *human* and the desk will send a payment link."
    },
    {
      "k": [
        "pay",
        "upi",
        "gpay",
        "card",
        "emi",
        "cash"
      ],
      "a": "UPI, cards, cash and no-cost EMI on annual plans."
    }
  ],
  // A73: Telugu and Hindi replies (Claude, 22 Oct 2026; a Telugu speaker reviews before go-live)
  "i18n": {
    "te": {
      "greeting": "హాయ్ 💪 *{business}* కి స్వాగతం! *ఉచిత ట్రయల్ సెషన్* తీసుకోండి, మెంబర్‌షిప్ ప్లాన్లు చూడండి లేదా ట్రైనర్‌తో మాట్లాడండి.",
      "menu": [
        "ఉచిత ట్రయల్ బుక్ చేయండి",
        "మెంబర్‌షిప్ ప్లాన్లు",
        "పర్సనల్ ట్రైనింగ్",
        "సమయాలు & లొకేషన్",
        "ఫ్రంట్ డెస్క్‌తో మాట్లాడండి"
      ],
      "asks": {
        "goal": "మీ ముఖ్య లక్ష్యం ఏమిటి?",
        "date": "మీ ఉచిత ట్రయల్ ఎప్పుడు కావాలి? (ఈరోజు, రేపు, సోమవారం, లేదా 20/10)",
        "slot": "సమయం ఎంచుకోండి:",
        "name": "మీ పేరు?"
      },
      "confirm": "🔥 *ఉచిత ట్రయల్ బుక్ అయింది*\n👤 {name}\n🎯 లక్ష్యం: {goal}\n📅 {date}, {slot}\n📍 {address}\n\nస్పోర్ట్స్ షూస్, వాటర్ బాటిల్ తీసుకురండి. ట్రైనర్ మీకు ఉచితంగా బాడీ-కంపోజిషన్ చెక్ చేస్తారు.",
      "catalogTitle": "మెంబర్‌షిప్ ప్లాన్లు",
      "bookWord": "ఉచిత ట్రయల్",
      "faqs": [
        "🧑‍🏫 సర్టిఫైడ్ పర్సనల్ ట్రైనర్లు: నెలకు ₹4,000, 12 సెషన్లు, డైట్ ప్లాన్‌తో సహా. ఉచిత ట్రయల్‌తో మొదలుపెట్టాలంటే *1* అని పంపండి.",
        "ప్రతి మెంబర్‌కు బేసిక్ డైట్ చార్ట్ ఇస్తాం. వివరమైన న్యూట్రిషన్ కోచింగ్ పర్సనల్ ట్రైనింగ్‌తో వస్తుంది.",
        "👩 ఆడవారికి మాత్రమే బ్యాచ్ ఉదయం 10 – మధ్యాహ్నం 12, మహిళా ట్రైనర్లతో; వేరే చేంజింగ్ రూమ్ కూడా ఉంది.",
        "6 నెలల, సంవత్సరం ప్లాన్లను 30 రోజుల వరకు ఫ్రీజ్ చేయవచ్చు (మెడికల్ లేదా ప్రయాణం).",
        "గడువు ముగిసేలోపు రిన్యూ చేస్తే 10% తగ్గింపు. *human* అని పంపండి, డెస్క్ పేమెంట్ లింక్ పంపుతుంది.",
        "UPI, కార్డులు, క్యాష్, సంవత్సరం ప్లాన్లపై నో-కాస్ట్ EMI."
      ],
      "labels": {
        "₹4,000 / month": "నెలకు ₹4,000",
        "Weight loss": "బరువు తగ్గడం",
        "Muscle gain": "కండలు పెంచడం",
        "General fitness": "సాధారణ ఫిట్‌నెస్",
        "Strength / powerlifting": "స్ట్రెంత్ / పవర్‌లిఫ్టింగ్",
        "Yoga / Zumba": "యోగా / జుంబా",
        "Monthly": "నెలవారీ",
        "Quarterly": "3 నెలలు",
        "Half-yearly": "6 నెలలు",
        "Annual (best value)": "సంవత్సరం (బెస్ట్ వాల్యూ)",
        "Personal training add-on": "పర్సనల్ ట్రైనింగ్ యాడ్-ఆన్"
      }
    },
    "hi": {
      "greeting": "हाय 💪 *{business}* में स्वागत है! *फ़्री ट्रायल सेशन* लें, मेंबरशिप प्लान देखें या ट्रेनर से बात करें.",
      "menu": [
        "फ़्री ट्रायल बुक करें",
        "मेंबरशिप प्लान",
        "पर्सनल ट्रेनिंग",
        "समय और पता",
        "फ़्रंट डेस्क से बात करें"
      ],
      "asks": {
        "goal": "आपका मुख्य लक्ष्य क्या है?",
        "date": "फ़्री ट्रायल कब चाहिए? (आज, कल, सोमवार, या 20/10)",
        "slot": "समय चुनें:",
        "name": "आपका नाम?"
      },
      "confirm": "🔥 *फ़्री ट्रायल बुक हो गया*\n👤 {name}\n🎯 लक्ष्य: {goal}\n📅 {date}, {slot}\n📍 {address}\n\nस्पोर्ट्स शूज़ और पानी की बोतल साथ लाएँ. ट्रेनर आपका फ़्री बॉडी-कंपोज़िशन चेक करेंगे.",
      "catalogTitle": "मेंबरशिप प्लान",
      "bookWord": "फ़्री ट्रायल",
      "faqs": [
        "🧑‍🏫 सर्टिफ़ाइड पर्सनल ट्रेनर: ₹4,000/महीना, 12 सेशन, डाइट प्लान के साथ. फ़्री ट्रायल से शुरू करने के लिए *1* भेजें.",
        "हर मेंबर को बेसिक डाइट चार्ट मिलता है. डिटेल्ड न्यूट्रिशन कोचिंग पर्सनल ट्रेनिंग के साथ आती है.",
        "👩 सिर्फ़ महिलाओं का बैच सुबह 10 – दोपहर 12, महिला ट्रेनरों के साथ; अलग चेंजिंग रूम भी है.",
        "छमाही और सालाना प्लान 30 दिन तक फ़्रीज़ हो सकते हैं (मेडिकल या यात्रा).",
        "एक्सपायरी से पहले रिन्यू करें और 10% छूट पाएँ. *human* भेजें, डेस्क पेमेंट लिंक भेजेगा.",
        "UPI, कार्ड, कैश और सालाना प्लान पर नो-कॉस्ट EMI."
      ],
      "labels": {
        "₹4,000 / month": "₹4,000 / महीना",
        "Weight loss": "वज़न घटाना",
        "Muscle gain": "मसल्स बढ़ाना",
        "General fitness": "जनरल फ़िटनेस",
        "Strength / powerlifting": "स्ट्रेंथ / पावरलिफ़्टिंग",
        "Yoga / Zumba": "योग / ज़ुम्बा",
        "Monthly": "मासिक",
        "Quarterly": "तिमाही",
        "Half-yearly": "छमाही",
        "Annual (best value)": "सालाना (सबसे फ़ायदेमंद)",
        "Personal training add-on": "पर्सनल ट्रेनिंग ऐड-ऑन"
      }
    }
  }
};
