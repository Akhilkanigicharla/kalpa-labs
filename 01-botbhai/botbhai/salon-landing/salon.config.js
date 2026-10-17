/*
 * ============================================================================
 *  SALON CONFIG: the ONLY file you edit to set up a new salon.
 * ============================================================================
 *  How to edit (no coding needed):
 *    - Change the text between the quotes "like this". Keep the quotes and the commas.
 *    - Text with { en: "...", te: "..." } has English and Telugu versions. If you
 *      don't have the Telugu yet, put the English in both, or plain "text" (used for both).
 *    - Prices are plain numbers (no ₹ and no commas): 1499, not "₹1,499".
 *    - Times are 24-hour "HH:MM": "10:00" is 10 AM, "21:00" is 9 PM.
 *    - After saving, open index.html and check the page. Before going live, run
 *      `node scripts/bake.js` (Netlify and the GitHub Pages workflow do this for you).
 *
 *  Everything below is PLACEHOLDER data. While `demo` is true, the page shows a
 *  "template preview" notice and never opens WhatsApp by itself.
 * ============================================================================
 */
window.SALON_CONFIG = {
  // Set to false only when every placeholder below is replaced with the salon's real details.
  demo: true,

  // ---------------------------------------------------------------------------
  // 1. SALON DETAILS (edit these for every new salon)
  // ---------------------------------------------------------------------------
  business: {
    name: "Your Salon Name",
    // schema.org type for Google: "HairSalon", "BeautySalon", "DaySpa" or "NailSalon".
    type: "HairSalon",
    tagline: {
      en: "Haircuts, colour, skin and bridal care. Book in 30 seconds on WhatsApp.",
      te: "హెయిర్‌కట్, కలర్, స్కిన్, బ్రైడల్ కేర్. వాట్సాప్‌లో 30 సెకన్లలో బుక్ చేయండి."
    },
    // Short description for Google and link previews (about 150 characters).
    description: {
      en: "Your Salon Name in Your Area, Hyderabad: haircuts, hair spa, colour, facials and bridal makeup. See prices and book on WhatsApp.",
      te: "హైదరాబాద్, Your Area లోని Your Salon Name: హెయిర్‌కట్, హెయిర్ స్పా, కలర్, ఫేషియల్, బ్రైడల్ మేకప్. ధరలు చూసి వాట్సాప్‌లో బుక్ చేయండి."
    },
    logo: "assets/logo.svg",
    // Link-preview image for WhatsApp/Facebook: a 1200 × 630 JPG or PNG (not SVG).
    ogImage: "assets/og-image.png",
    priceRange: "₹₹"
  },

  contact: {
    // WhatsApp number in international format: +91 then the 10-digit number.
    // PLACEHOLDER: replace with the salon's WhatsApp Business number.
    whatsapp: "+91 90000 00000",
    // Phone for calls (can be the same number). Leave "" to hide the call button.
    phone: "+91 90000 00000",
    email: ""
  },

  address: {
    street: "Shop No. 1, Sample Building, Sample Road",
    area: "Your Area",
    city: "Hyderabad",
    state: "Telangana",
    pincode: "500000",
    country: "IN",
    // Google Maps link: open the salon on Google Maps → Share → Copy link, paste it here.
    mapsUrl: "https://www.google.com/maps/search/?api=1&query=Your+Salon+Name+Hyderabad",
    // Optional exact location for Google (from the same Maps page). Leave null if unsure.
    geo: null // example: { lat: 17.4326, lng: 78.4071 }
  },

  // Opening hours. Each row: the days, opening time and closing time (24-hour).
  // A day that appears in no row is shown as "Closed".
  hours: [
    { days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], open: "10:00", close: "21:00" },
    { days: ["Sunday"], open: "10:00", close: "20:00" }
  ],
  // Extra closed dates (festivals, holidays), as "YYYY-MM-DD".
  holidays: [
    { date: "2026-11-08", name: { en: "Diwali", te: "దీపావళి" } }
  ],
  timezone: "Asia/Kolkata",

  // Services and prices, in groups. `id` must be unique and use only a-z, 0-9 and "-".
  // `from: true` shows "from ₹..." for services whose price depends on hair length etc.
  services: [
    {
      group: { en: "Hair", te: "హెయిర్" },
      items: [
        { id: "haircut-men", name: { en: "Haircut (men)", te: "హెయిర్‌కట్ (పురుషులు)" }, price: 250, duration: 30 },
        { id: "haircut-women", name: { en: "Haircut (women)", te: "హెయిర్‌కట్ (మహిళలు)" }, price: 500, duration: 45, from: true },
        { id: "hair-spa", name: { en: "Hair spa", te: "హెయిర్ స్పా" }, price: 900, duration: 60 },
        { id: "global-colour", name: { en: "Global hair colour", te: "గ్లోబల్ హెయిర్ కలర్" }, price: 1800, duration: 120, from: true }
      ]
    },
    {
      group: { en: "Skin", te: "స్కిన్" },
      items: [
        { id: "cleanup", name: { en: "Clean-up", te: "క్లీన్-అప్" }, price: 600, duration: 45 },
        { id: "facial", name: { en: "Facial", te: "ఫేషియల్" }, price: 1200, duration: 60, from: true },
        { id: "threading", name: { en: "Eyebrow threading", te: "ఐబ్రో థ్రెడింగ్" }, price: 60, duration: 10 }
      ]
    },
    {
      group: { en: "Bridal", te: "బ్రైడల్" },
      items: [
        { id: "bridal-makeup", name: { en: "Bridal makeup", te: "బ్రైడల్ మేకప్" }, price: 15000, from: true },
        { id: "party-makeup", name: { en: "Party makeup", te: "పార్టీ మేకప్" }, price: 3000, duration: 90, from: true }
      ]
    }
  ],

  // Offers banner. Set `show: false` to hide it. It also hides itself after `until`.
  offer: {
    show: true,
    text: {
      en: "Sample offer: 20% off hair spa on weekdays. Replace or turn off in salon.config.js.",
      te: "నమూనా ఆఫర్: వారం రోజుల్లో హెయిర్ స్పాపై 20% తగ్గింపు. salon.config.js లో మార్చండి లేదా ఆపండి."
    },
    until: "2026-12-31"
  },

  // Booking form settings.
  booking: {
    // Customers can pick a date from today up to this many days ahead.
    maxDaysAhead: 30,
    // A slot for today is offered only if it ends at least this many minutes from now.
    minNoticeMinutes: 60,
    // Time slots offered in the form. A slot shows only on days the salon is open at that time.
    slots: [
      { id: "morning", label: { en: "Morning", te: "ఉదయం" }, from: "10:00", to: "12:00" },
      { id: "afternoon", label: { en: "Afternoon", te: "మధ్యాహ్నం" }, from: "12:00", to: "16:00" },
      { id: "evening", label: { en: "Evening", te: "సాయంత్రం" }, from: "16:00", to: "21:00" }
    ],
    // Language of the WhatsApp booking message the salon receives: "en" (always English,
    // easiest for staff and the BotBhai bot to read) or "visitor" (the language the visitor chose).
    messageLanguage: "en"
  },

  // Frequently asked questions (shown as tap-to-open rows).
  faq: [
    {
      q: { en: "Do I need an appointment?", te: "అపాయింట్‌మెంట్ తప్పనిసరా?" },
      a: { en: "Walk-ins are welcome, but booking on WhatsApp means no waiting.", te: "నేరుగా రావచ్చు, కానీ వాట్సాప్‌లో బుక్ చేస్తే ఎదురుచూడాల్సిన అవసరం ఉండదు." }
    },
    {
      q: { en: "How do I pay?", te: "ఎలా చెల్లించాలి?" },
      a: { en: "UPI, cards and cash are accepted at the salon.", te: "సెలూన్‌లో UPI, కార్డులు, నగదు తీసుకుంటాం." }
    },
    {
      q: { en: "Can I change or cancel my booking?", te: "బుకింగ్ మార్చవచ్చా లేదా రద్దు చేయవచ్చా?" },
      a: { en: "Yes. Message us on the same WhatsApp chat at least 2 hours before your slot.", te: "అవును. మీ సమయానికి కనీసం 2 గంటల ముందు అదే వాట్సాప్ చాట్‌లో మెసేజ్ చేయండి." }
    },
    {
      q: { en: "Do you do bridal makeup at home?", te: "ఇంటికి వచ్చి బ్రైడల్ మేకప్ చేస్తారా?" },
      a: { en: "Yes, on request. Send the date and venue on WhatsApp and we will share a quote.", te: "అవును, అడిగితే చేస్తాం. తేదీ, వేదిక వాట్సాప్‌లో పంపండి, మేము ధర చెబుతాం." }
    }
  ],

  // OPTIONAL reviews. This section stays HIDDEN while the list is empty.
  // Add ONLY real reviews, word for word, with the customer's permission. Never write,
  // edit or pay for reviews: fake reviews break India's consumer-protection rules
  // (BIS IS 19000:2022 on online consumer reviews) and Google's policies.
  // Example: { quote: "Very neat haircut, on time.", author: "Ravi K.", source: "Google", stars: 5 }
  reviews: [],
  // Optional link to the salon's Google reviews (shown in the reviews section if set).
  reviewsUrl: "",

  // Optional social links. Leave "" to hide.
  social: { instagram: "", facebook: "" },

  // Brand colours. Leave "" to use the Kalpa design defaults (indigo + turmeric).
  // `primary` is used for the hero and buttons, so pick a dark colour: white text must stay readable on it.
  brand: { primary: "", accent: "" },

  site: {
    // The live address of this page, e.g. "https://your-salon.netlify.app" (no "/" at the end).
    // Used for Google, link previews and the sitemap.
    url: "https://example.netlify.app",
    // Optional link to the salon's privacy notice (Kalpa's sample: 01-botbhai/docs/sales/privacy-notice.pdf).
    privacyUrl: "",
    credit: { text: "Website by BotBhai · Kalpa Labs", url: "" }
  },

  // ---------------------------------------------------------------------------
  // 2. PAGE TEXT in English and Telugu (usually no need to edit)
  // ---------------------------------------------------------------------------
  defaultLanguage: "en",
  languages: { en: "English", te: "తెలుగు" },
  text: {
    en: {
      demoNotice: "Template preview: replace the placeholder details in salon.config.js and set demo: false before going live.",
      skip: "Skip to booking form",
      bookOnWhatsApp: "Book on WhatsApp",
      bookWithForm: "Pick a time",
      call: "Call",
      openNow: "Open now",
      closedNow: "Closed now",
      closesAt: "closes {time}",
      opensAt: "opens {day} {time}",
      today: "today",
      tomorrow: "tomorrow",
      servicesTitle: "Services & prices",
      servicesNote: "Prices include taxes. Final price may vary with hair length and products.",
      from: "from",
      minutes: "{n} min",
      book: "Book",
      bookService: "Book {service}",
      offerLabel: "Offer",
      offerUntil: "till {date}",
      formTitle: "Book a slot",
      formIntro: "Fill this in and tap send. WhatsApp opens with your booking message ready. Nothing is saved on this website.",
      nameLabel: "Your name",
      phoneLabel: "Mobile number",
      phoneHint: "10-digit Indian mobile number",
      serviceLabel: "Service",
      servicePlaceholder: "Choose a service",
      dateLabel: "Preferred date",
      slotLabel: "Time slot",
      slotPlaceholder: "Choose a time",
      noSlots: "No slots left on this day. Please pick another date.",
      noteLabel: "Note (optional)",
      notePlaceholder: "Anything we should know? e.g. stylist preference",
      submit: "Send booking on WhatsApp",
      privacy: "Your details are not stored on this website. They go straight from your WhatsApp to the salon.",
      privacyLink: "Privacy notice",
      errSummary: "Please fix {n} field(s) below.",
      errName: "Please enter your name.",
      errPhone: "Enter a valid 10-digit mobile number starting with 6, 7, 8 or 9.",
      errService: "Please choose a service.",
      errDate: "Please choose a date.",
      errDateRange: "Please choose a date between today and {date}.",
      errDateClosed: "The salon is closed on that day. Please pick another date.",
      errSlot: "Please choose a time slot.",
      sentTitle: "Opening WhatsApp…",
      sentBody: "Your booking message is ready. Tap send in WhatsApp; the salon will confirm your slot.",
      sentDemo: "Template preview: this is the message a customer would send. WhatsApp is not opened automatically while demo is true.",
      openWhatsApp: "Open WhatsApp",
      hoursTitle: "Hours & location",
      closed: "Closed",
      directions: "Get directions",
      holidaysTitle: "Holidays",
      faqTitle: "Questions",
      reviewsTitle: "What customers say",
      reviewsMore: "Read all reviews",
      floatLabel: "Chat with {name} on WhatsApp",
      waGreeting: "Hi {name}, I would like to book an appointment.",
      msgIntro: "Hi {name}, I would like to book an appointment.",
      msgName: "Name",
      msgPhone: "Phone",
      msgService: "Service",
      msgDate: "Date",
      msgTime: "Time",
      msgNote: "Note",
      msgFooter: "(Sent from the website booking form)",
      footerFind: "Find us",
      rights: "All rights reserved."
    },
    te: {
      demoNotice: "టెంప్లేట్ ప్రివ్యూ: లైవ్‌కి ముందు salon.config.js లో నమూనా వివరాలు మార్చి demo: false పెట్టండి.",
      skip: "బుకింగ్ ఫారానికి వెళ్ళండి",
      bookOnWhatsApp: "వాట్సాప్‌లో బుక్ చేయండి",
      bookWithForm: "సమయం ఎంచుకోండి",
      call: "కాల్",
      openNow: "ఇప్పుడు తెరిచి ఉంది",
      closedNow: "ఇప్పుడు మూసి ఉంది",
      closesAt: "{time}కి మూస్తాం",
      opensAt: "{day} {time}కి తెరుస్తాం",
      today: "ఈరోజు",
      tomorrow: "రేపు",
      servicesTitle: "సేవలు & ధరలు",
      servicesNote: "ధరల్లో పన్నులు కలిపే ఉన్నాయి. జుట్టు పొడవు, ప్రోడక్ట్‌లను బట్టి ధర మారవచ్చు.",
      from: "నుండి",
      minutes: "{n} నిమి",
      book: "బుక్",
      bookService: "{service} బుక్ చేయండి",
      offerLabel: "ఆఫర్",
      offerUntil: "{date} వరకు",
      formTitle: "స్లాట్ బుక్ చేయండి",
      formIntro: "ఇది నింపి పంపండి నొక్కండి. మీ బుకింగ్ మెసేజ్‌తో వాట్సాప్ తెరుచుకుంటుంది. ఈ వెబ్‌సైట్‌లో ఏదీ సేవ్ కాదు.",
      nameLabel: "మీ పేరు",
      phoneLabel: "మొబైల్ నంబర్",
      phoneHint: "10 అంకెల భారతీయ మొబైల్ నంబర్",
      serviceLabel: "సేవ",
      servicePlaceholder: "సేవను ఎంచుకోండి",
      dateLabel: "తేదీ",
      slotLabel: "సమయం",
      slotPlaceholder: "సమయం ఎంచుకోండి",
      noSlots: "ఈ రోజుకి స్లాట్లు లేవు. వేరే తేదీ ఎంచుకోండి.",
      noteLabel: "గమనిక (ఐచ్ఛికం)",
      notePlaceholder: "మాకు తెలియాల్సింది ఏదైనా? ఉదా: స్టైలిస్ట్ ఎంపిక",
      submit: "వాట్సాప్‌లో బుకింగ్ పంపండి",
      privacy: "మీ వివరాలు ఈ వెబ్‌సైట్‌లో సేవ్ కావు. అవి మీ వాట్సాప్ నుండి నేరుగా సెలూన్‌కి వెళ్తాయి.",
      privacyLink: "గోప్యతా నోటీసు",
      errSummary: "కింద {n} వివరాలు సరిచేయండి.",
      errName: "దయచేసి మీ పేరు రాయండి.",
      errPhone: "6, 7, 8 లేదా 9తో మొదలయ్యే సరైన 10 అంకెల మొబైల్ నంబర్ ఇవ్వండి.",
      errService: "దయచేసి ఒక సేవను ఎంచుకోండి.",
      errDate: "దయచేసి తేదీ ఎంచుకోండి.",
      errDateRange: "ఈరోజు నుండి {date} లోపు తేదీ ఎంచుకోండి.",
      errDateClosed: "ఆ రోజు సెలూన్ మూసి ఉంటుంది. వేరే తేదీ ఎంచుకోండి.",
      errSlot: "దయచేసి సమయం ఎంచుకోండి.",
      sentTitle: "వాట్సాప్ తెరుస్తున్నాం…",
      sentBody: "మీ బుకింగ్ మెసేజ్ సిద్ధంగా ఉంది. వాట్సాప్‌లో పంపండి నొక్కండి; సెలూన్ మీ స్లాట్‌ను నిర్ధారిస్తుంది.",
      sentDemo: "టెంప్లేట్ ప్రివ్యూ: కస్టమర్ పంపే మెసేజ్ ఇదే. demo: true ఉన్నంతవరకు వాట్సాప్ దానంతట అదే తెరుచుకోదు.",
      openWhatsApp: "వాట్సాప్ తెరవండి",
      hoursTitle: "సమయాలు & చిరునామా",
      closed: "మూసి ఉంటుంది",
      directions: "దారి చూడండి",
      holidaysTitle: "సెలవులు",
      faqTitle: "ప్రశ్నలు",
      reviewsTitle: "కస్టమర్లు ఏమంటున్నారు",
      reviewsMore: "అన్ని రివ్యూలు చదవండి",
      floatLabel: "{name}తో వాట్సాప్‌లో చాట్ చేయండి",
      waGreeting: "నమస్తే {name}, నేను అపాయింట్‌మెంట్ బుక్ చేయాలనుకుంటున్నాను.",
      msgIntro: "నమస్తే {name}, నేను అపాయింట్‌మెంట్ బుక్ చేయాలనుకుంటున్నాను.",
      msgName: "పేరు",
      msgPhone: "ఫోన్",
      msgService: "సేవ",
      msgDate: "తేదీ",
      msgTime: "సమయం",
      msgNote: "గమనిక",
      msgFooter: "(వెబ్‌సైట్ బుకింగ్ ఫారం నుండి పంపబడింది)",
      footerFind: "మా చిరునామా",
      rights: "అన్ని హక్కులు ప్రత్యేకించబడ్డాయి."
    }
  }
};
