// BotBhai examkits setup — WhatsApp / web / voice conversation config.
// Edit per client in Supabase clients.config (overrides any field here).
module.exports = {
  // quiz questions live in quiz.js
  "id": "examkits",
  "capacity": 30,
  "holidays": [{ "date": "2026-11-08", "name": "Diwali" }],
  "label": "Exam kits",
  "emoji": "📚",
  "business": "Vidya Competitive Academy",
  "address": "2nd Floor, Ashok Nagar X Roads, Hyderabad (classes online + offline)",
  "hours": "Office Mon–Sat 8:00 AM – 8:00 PM · daily quiz 7:00 AM",
  "phone": "+91 90000 00005",
  "greeting": "Hi 📚 Welcome to *{business}*. Take a free 3-question quiz for your exam and get a daily practice question every morning.",
  "menu": [
    {
      "key": "book",
      "label": "Take today's free quiz"
    },
    {
      "key": "prices",
      "label": "Courses, kits & fees"
    },
    {
      "key": "faq:daily",
      "label": "Daily question plan"
    },
    {
      "key": "hours",
      "label": "How it works"
    },
    {
      "key": "human",
      "label": "Free demo class / counsellor"
    }
  ],
  "catalogTitle": "Courses, kits & fees",
  "catalog": [
    {
      "name": "TSPSC Group 2 — 4-month batch",
      "price": "₹18,000 (kit alone ₹199)"
    },
    {
      "name": "SSC CGL — weekend batch",
      "price": "₹12,000 (kit alone ₹149)"
    },
    {
      "name": "RRB NTPC — online batch",
      "price": "₹6,500 (kit alone ₹149)"
    },
    {
      "name": "Bank PO — prelims + mains",
      "price": "₹15,000 (kit alone ₹199)"
    }
  ],
  "bookWord": "quiz",
  "quiz": true,
  "steps": [
    {
      "field": "service",
      "ask": "Which exam are you preparing for?",
      "choices": [
        "TSPSC Group 2",
        "SSC CGL",
        "RRB NTPC",
        "Bank PO"
      ]
    },
    {
      "field": "q1",
      "type": "quiz",
      "n": 0
    },
    {
      "field": "q2",
      "type": "quiz",
      "n": 1
    },
    {
      "field": "q3",
      "type": "quiz",
      "n": 2
    },
    {
      "field": "name",
      "ask": "Nice work! What's your name? I'll send your score card and tomorrow's question.",
      "type": "name"
    }
  ],
  "confirm": "🏆 *Score card — {name}*\n📝 {service}: *{score}/3*\n\n{advice}\n\nReply *2* for courses and fees, or *human* to book a free demo class with a counsellor.",
  "faqs": [
    {
      "id": "daily",
      "k": [
        "daily",
        "every day",
        "morning",
        "subscribe"
      ],
      "a": "📅 You'll get one exam-level question every morning at 7:00 AM, with the answer and a 2-line explanation in the evening. Free forever. Reply STOP any time to unsubscribe."
    },
    {
      "k": [
        "pdf",
        "notes",
        "material",
        "syllabus"
      ],
      "a": "Each kit has the syllabus map, 300+ solved questions, 5 mock tests and a 30-day plan, all as PDF on WhatsApp."
    },
    {
      "k": [
        "refund"
      ],
      "a": "Not happy within 7 days? Full refund, no questions."
    }
  ],
  quizBank: require("./quiz.js")
};
