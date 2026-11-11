/* UI labels in English, Telugu and Hindi. {x} marks a value filled in by the app. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.JyotishI18n = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const T = {
    title: ['Kalpa Jyotish', 'కల్ప జ్యోతిష్', 'कल्प ज्योतिष'],
    tagline: ['Birth star, name syllable and good days, worked out on your phone.', 'జన్మ నక్షత్రం, నామ అక్షరం, మంచి రోజులు, మీ ఫోన్‌లోనే లెక్కిస్తుంది.', 'जन्म नक्षत्र, नाम अक्षर और शुभ दिन, आपके फ़ोन पर ही गणना।'],
    disclaimer: ['For guidance and tradition. No health, legal or money predictions.', 'మార్గదర్శనం, సంప్రదాయం కోసం మాత్రమే. ఆరోగ్యం, చట్టం, డబ్బు గురించి ఎలాంటి జోస్యం లేదు.', 'केवल मार्गदर्शन और परंपरा के लिए। स्वास्थ्य, कानूनी या धन संबंधी कोई भविष्यवाणी नहीं।'],
    tabStar: ['Birth star', 'జన్మ నక్షత్రం', 'जन्म नक्षत्र'],
    tabNames: ['Names', 'పేర్లు', 'नाम'],
    tabDays: ['Good days', 'మంచి రోజులు', 'शुभ दिन'],
    tabAbout: ['About', 'వివరాలు', 'जानकारी'],
    theme: ['Light or dark', 'లైట్ / డార్క్', 'लाइट / डार्क'],
    birthDate: ['Date of birth', 'పుట్టిన తేదీ', 'जन्म की तारीख'],
    birthTime: ['Time of birth', 'పుట్టిన సమయం', 'जन्म का समय'],
    place: ['Place', 'ప్రదేశం', 'स्थान'],
    otherPlace: ['Other place (enter details)', 'ఇతర ప్రదేశం (వివరాలు ఇవ్వండి)', 'अन्य स्थान (विवरण भरें)'],
    lat: ['Latitude', 'అక్షాంశం', 'अक्षांश'],
    lon: ['Longitude', 'రేఖాంశం', 'देशांतर'],
    tz: ['Time zone', 'టైమ్ జోన్', 'समय क्षेत्र'],
    remember: ['Remember on this phone', 'ఈ ఫోన్‌లో గుర్తుంచుకో', 'इस फ़ोन पर याद रखें'],
    find: ['Find birth star', 'జన్మ నక్షత్రం చూడండి', 'जन्म नक्षत्र देखें'],
    rasi: ['Moon sign (rasi)', 'రాశి', 'राशि'],
    nakshatra: ['Birth star (nakshatra)', 'నక్షత్రం', 'नक्षत्र'],
    pada: ['pada {p}', '{p}వ పాదం', 'चरण {p}'],
    akshara: ['Name syllable', 'నామ అక్షరం', 'नाम अक्षर'],
    tithi: ['Tithi', 'తిథి', 'तिथि'],
    vara: ['Weekday', 'వారం', 'वार'],
    moonLon: ['Moon (sidereal, Lahiri)', 'చంద్రుడు (నిరయన, లాహిరి)', 'चंद्र (निरयण, लाहिड़ी)'],
    until: ['until {t}', '{t} వరకు', '{t} तक'],
    sunrise: ['Sunrise {t}', 'సూర్యోదయం {t}', 'सूर्योदय {t}'],
    estimated: ['(sunrise estimated)', '(సూర్యోదయం అంచనా)', '(सूर्योदय अनुमानित)'],
    edgeWarn: ['Birth time is within {m} minutes of a pada change. Please check the exact time with a panchang or your family priest.', 'పుట్టిన సమయం పాదం మారే సమయానికి {m} నిమిషాల దగ్గరలో ఉంది. ఖచ్చితమైన సమయాన్ని పంచాంగం లేదా మీ పురోహితులతో సరిచూసుకోండి.', 'जन्म का समय चरण बदलने से {m} मिनट के भीतर है। सही समय पंचांग या अपने पुरोहित से जाँच लें।'],
    beforeSunrise: ['Born before sunrise, so the Vedic weekday is the previous day.', 'సూర్యోదయానికి ముందు పుట్టారు, కాబట్టి వారం ముందు రోజుదే.', 'सूर्योदय से पहले जन्म, इसलिए वार पिछले दिन का है।'],
    seeNames: ['See names for this syllable', 'ఈ అక్షరంతో పేర్లు చూడండి', 'इस अक्षर से नाम देखें'],
    syllable: ['Syllable', 'అక్షరం', 'अक्षर'],
    anySyllable: ['Any syllable', 'ఏ అక్షరమైనా', 'कोई भी अक्षर'],
    gender: ['For', 'ఎవరికి', 'किसके लिए'],
    any: ['Any', 'ఎవరైనా', 'कोई भी'],
    boy: ['Boy', 'అబ్బాయి', 'लड़का'],
    girl: ['Girl', 'అమ్మాయి', 'लड़की'],
    letter: ['First letter (English)', 'మొదటి అక్షరం (ఇంగ్లీష్)', 'पहला अक्षर (अंग्रेज़ी)'],
    number: ['Name number', 'పేరు సంఖ్య', 'नाम अंक'],
    countNames: ['Names found: {n}', '{n} పేర్లు', '{n} नाम'],
    noNames: ['No names in our list start with this syllable. Many families also use the other syllables of the same nakshatra:', 'ఈ అక్షరంతో మా జాబితాలో పేర్లు లేవు. చాలా కుటుంబాలు అదే నక్షత్రంలోని ఇతర అక్షరాలు కూడా వాడతారు:', 'हमारी सूची में इस अक्षर से कोई नाम नहीं है। कई परिवार उसी नक्षत्र के दूसरे अक्षर भी लेते हैं:'],
    noMatch: ['No names match these choices.', 'ఈ ఎంపికలకు సరిపడే పేర్లు లేవు.', 'इन विकल्पों से कोई नाम नहीं मिला।'],
    checkName: ['Number of any name (Chaldean)', 'ఏ పేరుకైనా సంఖ్య (కల్డియన్)', 'किसी भी नाम का अंक (कैल्डियन)'],
    nameInput: ['Name in English letters', 'ఇంగ్లీష్ అక్షరాల్లో పేరు', 'अंग्रेज़ी अक्षरों में नाम'],
    total: ['Total {t}, number {s}', 'మొత్తం {t}, సంఖ్య {s}', 'कुल {t}, अंक {s}'],
    from: ['From', 'ఎప్పటి నుండి', 'कब से'],
    days: ['Days', 'రోజులు', 'दिन'],
    show: ['Show days', 'రోజులు చూపించు', 'दिन दिखाएँ'],
    priest: ['Traditional guidance, check with your family priest.', 'సంప్రదాయ మార్గదర్శనం మాత్రమే, మీ కుటుంబ పురోహితులను సంప్రదించండి.', 'पारंपरिक मार्गदर्शन, अपने कुल पुरोहित से पुष्टि करें।'],
    atSunrise: ['Tithi and nakshatra shown are the ones at local sunrise.', 'చూపిన తిథి, నక్షత్రం స్థానిక సూర్యోదయం సమయానివి.', 'दिखाई गई तिथि और नक्षत्र स्थानीय सूर्योदय के समय के हैं।'],
    onlyClear: ['Hide commonly avoided days', 'సాధారణంగా వదిలేసే రోజులు దాచు', 'प्रायः टाले जाने वाले दिन छिपाएँ'],
    avoidAmavasya: ['Amavasya: commonly avoided', 'అమావాస్య: సాధారణంగా వదిలేస్తారు', 'अमावस्या: प्रायः टाली जाती है'],
    avoidRikta: ['Rikta tithi: commonly avoided', 'రిక్త తిథి: సాధారణంగా వదిలేస్తారు', 'रिक्ता तिथि: प्रायः टाली जाती है'],
    noDays: ['Every day in this range is a commonly avoided one.', 'ఈ రోజులన్నీ సాధారణంగా వదిలేసేవే.', 'इस अवधि के सभी दिन प्रायः टाले जाने वाले हैं।'],
    privacyH: ['Your details stay on this phone', 'మీ వివరాలు ఈ ఫోన్‌లోనే ఉంటాయి', 'आपकी जानकारी इसी फ़ोन पर रहती है'],
    privacyP: ['Every calculation runs inside this page. Nothing is sent to any server, and the page makes no network calls. Birth details are saved on this phone only if you tick "Remember on this phone".', 'అన్ని లెక్కలు ఈ పేజీలోనే జరుగుతాయి. ఏ సర్వర్‌కూ ఏమీ పంపదు, ఈ పేజీ ఇంటర్నెట్ వాడదు. "ఈ ఫోన్‌లో గుర్తుంచుకో" టిక్ చేస్తేనే పుట్టిన వివరాలు ఈ ఫోన్‌లో సేవ్ అవుతాయి.', 'सारी गणना इसी पेज में होती है। किसी सर्वर पर कुछ नहीं भेजा जाता और पेज कोई नेटवर्क कॉल नहीं करता। जन्म विवरण इस फ़ोन पर तभी सहेजे जाते हैं जब आप "इस फ़ोन पर याद रखें" चुनें।'],
    clear: ['Delete saved details', 'సేవ్ చేసిన వివరాలు తొలగించు', 'सहेजी जानकारी हटाएँ'],
    cleared: ['Deleted from this phone.', 'ఈ ఫోన్ నుండి తొలగించాం.', 'इस फ़ोन से हटा दी गई।'],
    howH: ['How it is worked out', 'ఎలా లెక్కిస్తుంది', 'गणना कैसे होती है'],
    howP: ['Moon and Sun positions come from the open-source astronomy-engine library (accurate to about 1 arcminute). Rasi and nakshatra use the Lahiri ayanamsa. In Good days, tithi and nakshatra are taken at local sunrise. Times can differ by a few minutes from a printed panchang; near a change, follow your panchang.', 'చంద్ర, సూర్య స్థానాలు ఓపెన్ సోర్స్ astronomy-engine లైబ్రరీ నుండి (సుమారు 1 ఆర్క్ నిమిషం ఖచ్చితత్వం). రాశి, నక్షత్రం లాహిరి అయనాంశతో. మంచి రోజుల్లో తిథి, నక్షత్రం స్థానిక సూర్యోదయం సమయానివి. ముద్రించిన పంచాంగంతో కొన్ని నిమిషాల తేడా రావచ్చు; మారే సమయం దగ్గర పంచాంగాన్నే నమ్మండి.', 'चंद्र और सूर्य की स्थिति ओपन सोर्स astronomy-engine लाइब्रेरी से आती है (लगभग 1 आर्क मिनट सटीक)। राशि और नक्षत्र लाहिड़ी अयनांश से। शुभ दिन में तिथि और नक्षत्र स्थानीय सूर्योदय के समय के हैं। छपे पंचांग से कुछ मिनट का अंतर हो सकता है; बदलाव के पास पंचांग को ही मानें।'],
    creditsH: ['Credits', 'కృతజ్ఞతలు', 'आभार'],
    credits: ['astronomy-engine by Don Cross (MIT licence). Fonts: Rozha One and Anek (SIL Open Font Licence). Name list and syllable table written by Kalpa Labs; syllable lists vary by region, so follow your family custom.', 'astronomy-engine, Don Cross (MIT లైసెన్స్). ఫాంట్లు: Rozha One, Anek (SIL Open Font Licence). పేర్ల జాబితా, అక్షరాల పట్టిక Kalpa Labs తయారు చేసింది; ప్రాంతాన్ని బట్టి అక్షరాలు మారవచ్చు, మీ కుటుంబ ఆచారం పాటించండి.', 'astronomy-engine, Don Cross (MIT लाइसेंस)। फ़ॉन्ट: Rozha One और Anek (SIL Open Font Licence)। नामों की सूची और अक्षर तालिका Kalpa Labs ने लिखी है; क्षेत्र के अनुसार अक्षर बदलते हैं, अपने कुल की परंपरा मानें।'],
    errPrefix: ['Please check: {e}', 'దయచేసి సరిచూడండి: {e}', 'कृपया जाँचें: {e}'],
    otherSyl: ['Other syllables of {n}', '{n} లోని ఇతర అక్షరాలు', '{n} के अन्य अक्षर'],
  };
  const LANGS = ['en', 'te', 'hi'];
  function t(lang, key, vars) {
    const row = T[key];
    if (!row) return key;
    let s = row[Math.max(0, LANGS.indexOf(lang))];
    for (const [k, v] of Object.entries(vars || {})) s = s.split('{' + k + '}').join(String(v));
    return s;
  }
  return { T, LANGS, t };
});
