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
  ]
};
