/* Kalpa Jyotish reference data. Written for Kalpa Labs; names in English (en), Telugu (te), Hindi (hi).
   Classic script (UMD): works in the browser via <script> and in Node via require(). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.JyotishData = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const RASIS = [
    { en: 'Mesha (Aries)', te: 'మేషం', hi: 'मेष' },
    { en: 'Vrishabha (Taurus)', te: 'వృషభం', hi: 'वृषभ' },
    { en: 'Mithuna (Gemini)', te: 'మిథునం', hi: 'मिथुन' },
    { en: 'Karka (Cancer)', te: 'కర్కాటకం', hi: 'कर्क' },
    { en: 'Simha (Leo)', te: 'సింహం', hi: 'सिंह' },
    { en: 'Kanya (Virgo)', te: 'కన్య', hi: 'कन्या' },
    { en: 'Tula (Libra)', te: 'తుల', hi: 'तुला' },
    { en: 'Vrischika (Scorpio)', te: 'వృశ్చికం', hi: 'वृश्चिक' },
    { en: 'Dhanu (Sagittarius)', te: 'ధనుస్సు', hi: 'धनु' },
    { en: 'Makara (Capricorn)', te: 'మకరం', hi: 'मकर' },
    { en: 'Kumbha (Aquarius)', te: 'కుంభం', hi: 'कुंभ' },
    { en: 'Meena (Pisces)', te: 'మీనం', hi: 'मीन' },
  ];

  // 27 nakshatras. `ak` = the 4 pada syllables (Devanagari, Hoda/Avakahada chakra as in most Hindi
  // panchangs), `ro` = roman labels. Checked 7 Nov 2026 against himalayanacademy.com (ch08 sec04)
  // and dekhopanchang.com; known regional variants are listed in `alt`.
  const NAKSHATRAS = [
    { en: 'Ashwini', te: 'అశ్విని', hi: 'अश्विनी', ak: ['चु', 'चे', 'चो', 'ला'], ro: ['Chu', 'Che', 'Cho', 'La'] },
    { en: 'Bharani', te: 'భరణి', hi: 'भरणी', ak: ['ली', 'लू', 'ले', 'लो'], ro: ['Li', 'Lu', 'Le', 'Lo'] },
    { en: 'Krittika', te: 'కృత్తిక', hi: 'कृत्तिका', ak: ['अ', 'इ', 'उ', 'ए'], ro: ['A', 'I', 'U', 'E'] },
    { en: 'Rohini', te: 'రోహిణి', hi: 'रोहिणी', ak: ['ओ', 'वा', 'वी', 'वू'], ro: ['O', 'Va', 'Vi', 'Vu'], alt: 'pada 4 Vo in some lists' },
    { en: 'Mrigashira', te: 'మృగశిర', hi: 'मृगशिरा', ak: ['वे', 'वो', 'का', 'की'], ro: ['Ve', 'Vo', 'Ka', 'Ki'], alt: 'pada 4 Ke in some lists' },
    { en: 'Ardra', te: 'ఆర్ద్ర', hi: 'आर्द्रा', ak: ['कू', 'घ', 'ङ', 'छ'], ro: ['Ku', 'Gha', 'Nga', 'Chha'], alt: 'pada 4 Na in some lists' },
    { en: 'Punarvasu', te: 'పునర్వసు', hi: 'पुनर्वसु', ak: ['के', 'को', 'हा', 'ही'], ro: ['Ke', 'Ko', 'Ha', 'Hi'] },
    { en: 'Pushya', te: 'పుష్యమి', hi: 'पुष्य', ak: ['हू', 'हे', 'हो', 'डा'], ro: ['Hu', 'He', 'Ho', 'Da (retroflex)'] },
    { en: 'Ashlesha', te: 'ఆశ్లేష', hi: 'आश्लेषा', ak: ['डी', 'डू', 'डे', 'डो'], ro: ['Di (retroflex)', 'Du (retroflex)', 'De (retroflex)', 'Do (retroflex)'] },
    { en: 'Magha', te: 'మఖ', hi: 'मघा', ak: ['मा', 'मी', 'मू', 'मे'], ro: ['Ma', 'Mi', 'Mu', 'Me'] },
    { en: 'Purva Phalguni', te: 'పుబ్బ', hi: 'पूर्वा फाल्गुनी', ak: ['मो', 'टा', 'टी', 'टू'], ro: ['Mo', 'Ta (retroflex)', 'Ti (retroflex)', 'Tu (retroflex)'] },
    { en: 'Uttara Phalguni', te: 'ఉత్తర', hi: 'उत्तरा फाल्गुनी', ak: ['टे', 'टो', 'पा', 'पी'], ro: ['Te (retroflex)', 'To (retroflex)', 'Pa', 'Pi'] },
    { en: 'Hasta', te: 'హస్త', hi: 'हस्त', ak: ['पू', 'ष', 'ण', 'ठ'], ro: ['Pu', 'Sha', 'Na (retroflex)', 'Tha (retroflex)'] },
    { en: 'Chitra', te: 'చిత్త', hi: 'चित्रा', ak: ['पे', 'पो', 'रा', 'री'], ro: ['Pe', 'Po', 'Ra', 'Ri'] },
    { en: 'Swati', te: 'స్వాతి', hi: 'स्वाती', ak: ['रू', 'रे', 'रो', 'ता'], ro: ['Ru', 'Re', 'Ro', 'Ta'], alt: 'pada 3 Ra in some lists' },
    { en: 'Vishakha', te: 'విశాఖ', hi: 'विशाखा', ak: ['ती', 'तू', 'ते', 'तो'], ro: ['Ti', 'Tu', 'Te', 'To'] },
    { en: 'Anuradha', te: 'అనూరాధ', hi: 'अनुराधा', ak: ['ना', 'नी', 'नू', 'ने'], ro: ['Na', 'Ni', 'Nu', 'Ne'] },
    { en: 'Jyeshtha', te: 'జ్యేష్ఠ', hi: 'ज्येष्ठा', ak: ['नो', 'या', 'यी', 'यू'], ro: ['No', 'Ya', 'Yi', 'Yu'] },
    { en: 'Mula', te: 'మూల', hi: 'मूल', ak: ['ये', 'यो', 'भा', 'भी'], ro: ['Ye', 'Yo', 'Bha', 'Bhi'], alt: 'Ba, Bi in some lists' },
    { en: 'Purva Ashadha', te: 'పూర్వాషాఢ', hi: 'पूर्वाषाढ़ा', ak: ['भू', 'धा', 'फा', 'ढा'], ro: ['Bhu', 'Dha', 'Pha', 'Dha (retroflex)'] },
    { en: 'Uttara Ashadha', te: 'ఉత్తరాషాఢ', hi: 'उत्तराषाढ़ा', ak: ['भे', 'भो', 'जा', 'जी'], ro: ['Bhe', 'Bho', 'Ja', 'Ji'], alt: 'Be, Bo in some lists' },
    { en: 'Shravana', te: 'శ్రవణం', hi: 'श्रवण', ak: ['जू', 'जे', 'जो', 'घा'], ro: ['Ju', 'Je', 'Jo', 'Gha'], alt: 'Khi, Khu, Khe, Kho in some lists' },
    { en: 'Dhanishtha', te: 'ధనిష్ఠ', hi: 'धनिष्ठा', ak: ['गा', 'गी', 'गू', 'गे'], ro: ['Ga', 'Gi', 'Gu', 'Ge'] },
    { en: 'Shatabhisha', te: 'శతభిషం', hi: 'शतभिषा', ak: ['गो', 'सा', 'सी', 'सू'], ro: ['Go', 'Sa', 'Si', 'Su'] },
    { en: 'Purva Bhadrapada', te: 'పూర్వాభాద్ర', hi: 'पूर्वा भाद्रपद', ak: ['से', 'सो', 'दा', 'दी'], ro: ['Se', 'So', 'Da', 'Di'] },
    { en: 'Uttara Bhadrapada', te: 'ఉత్తరాభాద్ర', hi: 'उत्तरा भाद्रपद', ak: ['दू', 'थ', 'झ', 'ञ'], ro: ['Du', 'Tha', 'Jha', 'Nya'], alt: 'pada 3 Jna, pada 4 Da in some lists' },
    { en: 'Revati', te: 'రేవతి', hi: 'रेवती', ak: ['दे', 'दो', 'चा', 'ची'], ro: ['De', 'Do', 'Cha', 'Chi'] },
  ];

  const TITHIS = [
    { en: 'Pratipada', te: 'పాడ్యమి', hi: 'प्रतिपदा' },
    { en: 'Dwitiya', te: 'విదియ', hi: 'द्वितीया' },
    { en: 'Tritiya', te: 'తదియ', hi: 'तृतीया' },
    { en: 'Chaturthi', te: 'చవితి', hi: 'चतुर्थी' },
    { en: 'Panchami', te: 'పంచమి', hi: 'पंचमी' },
    { en: 'Shashthi', te: 'షష్ఠి', hi: 'षष्ठी' },
    { en: 'Saptami', te: 'సప్తమి', hi: 'सप्तमी' },
    { en: 'Ashtami', te: 'అష్టమి', hi: 'अष्टमी' },
    { en: 'Navami', te: 'నవమి', hi: 'नवमी' },
    { en: 'Dashami', te: 'దశమి', hi: 'दशमी' },
    { en: 'Ekadashi', te: 'ఏకాదశి', hi: 'एकादशी' },
    { en: 'Dwadashi', te: 'ద్వాదశి', hi: 'द्वादशी' },
    { en: 'Trayodashi', te: 'త్రయోదశి', hi: 'त्रयोदशी' },
    { en: 'Chaturdashi', te: 'చతుర్దశి', hi: 'चतुर्दशी' },
    { en: 'Purnima', te: 'పౌర్ణమి', hi: 'पूर्णिमा' },
    { en: 'Amavasya', te: 'అమావాస్య', hi: 'अमावस्या' },
  ];

  const PAKSHAS = [
    { en: 'Shukla paksha (waxing)', te: 'శుక్ల పక్షం', hi: 'शुक्ल पक्ष' },
    { en: 'Krishna paksha (waning)', te: 'కృష్ణ పక్షం', hi: 'कृष्ण पक्ष' },
  ];

  // Index 0 = Sunday, same as Date#getUTCDay.
  const VARAS = [
    { en: 'Sunday (Ravivara)', te: 'ఆదివారం', hi: 'रविवार' },
    { en: 'Monday (Somavara)', te: 'సోమవారం', hi: 'सोमवार' },
    { en: 'Tuesday (Mangalavara)', te: 'మంగళవారం', hi: 'मंगलवार' },
    { en: 'Wednesday (Budhavara)', te: 'బుధవారం', hi: 'बुधवार' },
    { en: 'Thursday (Guruvara)', te: 'గురువారం', hi: 'गुरुवार' },
    { en: 'Friday (Shukravara)', te: 'శుక్రవారం', hi: 'शुक्रवार' },
    { en: 'Saturday (Shanivara)', te: 'శనివారం', hi: 'शनिवार' },
  ];

  // name, lat (N+), lon (E+), IANA time zone. Coordinates are city centres (rounded); fine for
  // Moon sign work (1 degree of longitude moves sunrise by 4 minutes, the Moon by under 1 arcminute).
  const CITIES = [
    ['Hyderabad', 17.385, 78.4867, 'Asia/Kolkata'],
    ['Vijayawada', 16.5062, 80.648, 'Asia/Kolkata'],
    ['Visakhapatnam', 17.6868, 83.2185, 'Asia/Kolkata'],
    ['Guntur', 16.3067, 80.4365, 'Asia/Kolkata'],
    ['Tirupati', 13.6288, 79.4192, 'Asia/Kolkata'],
    ['Warangal', 17.9689, 79.5941, 'Asia/Kolkata'],
    ['Chennai', 13.0827, 80.2707, 'Asia/Kolkata'],
    ['Bengaluru', 12.9716, 77.5946, 'Asia/Kolkata'],
    ['Kochi', 9.9312, 76.2673, 'Asia/Kolkata'],
    ['Mumbai', 19.076, 72.8777, 'Asia/Kolkata'],
    ['Pune', 18.5204, 73.8567, 'Asia/Kolkata'],
    ['Ahmedabad', 23.0225, 72.5714, 'Asia/Kolkata'],
    ['New Delhi', 28.6139, 77.209, 'Asia/Kolkata'],
    ['Jaipur', 26.9124, 75.7873, 'Asia/Kolkata'],
    ['Lucknow', 26.8467, 80.9462, 'Asia/Kolkata'],
    ['Varanasi', 25.3176, 82.9739, 'Asia/Kolkata'],
    ['Ujjain', 23.1765, 75.7885, 'Asia/Kolkata'],
    ['Kolkata', 22.5726, 88.3639, 'Asia/Kolkata'],
    ['Bhubaneswar', 20.2961, 85.8245, 'Asia/Kolkata'],
    ['Dubai', 25.2048, 55.2708, 'Asia/Dubai'],
    ['Doha', 25.2854, 51.531, 'Asia/Qatar'],
    ['Riyadh', 24.7136, 46.6753, 'Asia/Riyadh'],
    ['Singapore', 1.3521, 103.8198, 'Asia/Singapore'],
    ['Kuala Lumpur', 3.139, 101.6869, 'Asia/Kuala_Lumpur'],
    ['London', 51.5074, -0.1278, 'Europe/London'],
    ['New York', 40.7128, -74.006, 'America/New_York'],
    ['Edison, New Jersey', 40.5187, -74.4121, 'America/New_York'],
    ['Chicago', 41.8781, -87.6298, 'America/Chicago'],
    ['Dallas', 32.7767, -96.797, 'America/Chicago'],
    ['San Jose (Bay Area)', 37.3382, -121.8863, 'America/Los_Angeles'],
    ['Seattle', 47.6062, -122.3321, 'America/Los_Angeles'],
    ['Toronto', 43.6532, -79.3832, 'America/Toronto'],
    ['Sydney', -33.8688, 151.2093, 'Australia/Sydney'],
    ['Melbourne', -37.8136, 144.9631, 'Australia/Melbourne'],
    ['Auckland', -36.8485, 174.7633, 'Pacific/Auckland'],
  ].map(([name, lat, lon, tz]) => ({ name, lat, lon, tz }));

  return { RASIS, NAKSHATRAS, TITHIS, PAKSHAS, VARAS, CITIES };
});
