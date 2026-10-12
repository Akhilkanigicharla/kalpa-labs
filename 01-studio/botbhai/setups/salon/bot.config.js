// BotBhai salon setup — WhatsApp / web / voice conversation config.
// Edit per client in Supabase clients.config (overrides any field here).
module.exports = {
  "id": "salon",
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
      "price": "₹250"
    },
    {
      "name": "Haircut & styling (women)",
      "price": "₹600"
    },
    {
      "name": "Beard trim",
      "price": "₹150"
    },
    {
      "name": "Hair spa",
      "price": "₹1,200"
    },
    {
      "name": "Facial (fruit / gold)",
      "price": "₹999"
    },
    {
      "name": "Bridal makeup",
      "price": "from ₹15,000"
    }
  ],
  "bookWord": "booking",
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
        "home visit"
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
