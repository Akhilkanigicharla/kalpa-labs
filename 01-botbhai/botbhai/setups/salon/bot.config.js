// BotBhai salon setup — WhatsApp / web / voice conversation config.
// Edit per client in Supabase clients.config (overrides any field here).
module.exports = {
  "id": "salon",
  "capacity": 3,
  "enquiry_role": "bridal artist",
  "enquiry_trial": "Bridal makeup trial",
  "bridal_full_dates": [],
  "closed_weekdays": [],
  "holidays": [{ "date": "2026-11-08", "name": "Diwali" }],
  "label": "Salon",
  "emoji": "💇",
  "business": "Glow Studio Unisex Salon",
  "address": "Road No. 36, Jubilee Hills, Hyderabad",
  "hours": "Every day 10:00 AM – 9:00 PM",
  "phone": "+91 90000 00002",
  "greeting": "Hi ✨ Welcome to *{business}*! Book a slot, check prices or see today's offers.",
  "menu": [
    {
      "key": "book",
      "label": "Book a service"
    },
    {
      "key": "prices",
      "label": "Price list"
    },
    {
      "key": "faq:offers",
      "label": "Today's offers"
    },
    {
      "key": "hours",
      "label": "Timings & location"
    },
    {
      "key": "human",
      "label": "Talk to the salon"
    }
  ],
  "catalogTitle": "Price list",
  "catalog": [
    {
      "name": "Haircut (men)",
      "price": "₹250",
      "aliases": ["cutting", "hair cutting", "gents cut", "gents haircut", "gents cutting", "men cut", "mens cut", "boys cut", "boy cut", "male haircut", "kids cut", "baal katwana", "jutt cutting", "జుట్టు కటింగ్", "కటింగ్"]
    },
    {
      "name": "Haircut & styling (women)",
      "price": "₹600",
      "aliases": ["cutting", "hair cutting", "ladies cut", "ladies haircut", "ladies cutting", "ladies hair cut", "women cut", "womens cut", "girls cut", "girl cut", "female haircut", "layer cut", "step cut", "u cut", "feather cut", "hair styling", "blow dry", "కటింగ్"]
    },
    {
      "name": "Beard trim",
      "price": "₹150",
      "aliases": ["beard", "shave", "shaving", "gaddam", "dadhi", "గడ్డం"]
    },
    {
      "name": "Hair spa",
      "price": "₹1,200",
      "aliases": ["హెయిర్ స్పా", "हेयर स्पा", "spa"]
    },
    {
      "name": "Facial (fruit / gold)",
      "price": "₹999",
      "aliases": ["facial", "gold facial", "fruit facial", "ఫేషియల్", "फेशियल"]
    },
    {
      "name": "Bridal makeup",
      "price": "from ₹15,000",
      "enquiry": true
    }
  ],
  "bookWord": "appointment",
  "steps": [
    {
      "field": "service",
      "ask": "Which service would you like?",
      "choices": "catalog"
    },
    {
      "field": "date",
      "ask": "Which day? (today, tomorrow, Saturday, or 18/10)",
      "type": "date"
    },
    {
      "field": "slot",
      "ask": "Choose a time:",
      "choices": [
        "11:00 AM",
        "1:00 PM",
        "4:00 PM",
        "7:00 PM"
      ]
    },
    {
      "field": "name",
      "ask": "Your name for the booking?",
      "type": "name"
    }
  ],
  "confirm": "💖 *Booking confirmed*\n👤 {name}\n✂️ {service}\n📅 {date} at {slot}\n📍 {address}\n\nWe'll remind you 2 hours before. Reply *menu* to book another.",
  "faqs": [
    {
      "id": "offers",
      "k": [
        "offer",
        "offers",
        "discount",
        "deal",
        "combo",
        "package"
      ],
      "a": "🎉 This week: *Hair spa + haircut ₹1,299* (save ₹150) and *20% off facials* Mon–Thu. Mention this chat at the counter."
    },
    {
      "k": [
        "bridal",
        "wedding",
        "party makeup",
        "engagement"
      ],
      "a": "💍 Bridal packages start at ₹15,000 and include a trial. Reply *human* and our bridal artist will call you."
    },
    {
      "k": [
        "home service",
        "at home",
        "home visit",
        "come home",
        "come to my home",
        "come to my house",
        "intiki vastara",
        "intiki vachi",
        "intiki ra",
        "ghar pe",
        "ghar par",
        "ghar aa"
      ],
      "a": "🏠 Home service is available within 5 km for bookings above ₹1,500."
    },
    {
      "k": [
        "pay",
        "upi",
        "gpay",
        "card",
        "cash"
      ],
      "a": "UPI, cards and cash are all accepted."
    },
    {
      "k": [
        "product",
        "products",
        "brand",
        "loreal",
        "l'oreal"
      ],
      "a": "We use L'Oréal Professionnel and O3+ products."
    }
  ]
};
