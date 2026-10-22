# BotBhai Telugu and Hindi replies: review sheet (A73)

Written by Claude on 22 Oct 2026. **A Telugu speaker (and a Hindi speaker) must read every line before any salon goes live.** Mark a line by writing the better wording in the Notes column and tell Claude, or edit `core/engine.js` (bot replies) and `setups/<setup>/bot.config.js` (`i18n`).

Commands in *stars* (menu, cancel, book, OFFERS, STOP, START, YES, human, bot) stay in English on purpose: customers type them back.

## Bot replies (all setups)

| # | English | తెలుగు | हिंदी | Notes |
|---|---|---|---|---|
| 1 | How can I help? Reply with a number: | మీకు ఎలా సహాయం చేయగలను? నంబర్‌తో రిప్లై ఇవ్వండి: | मैं कैसे मदद करूँ? नंबर से जवाब दें: | |
| 2 | Reply *1* to book your {bookWord}. | బుక్ చేయడానికి *1* అని పంపండి. | बुक करने के लिए *1* भेजें. | |
| 3 | Sorry, we're {note} 🙏 How about tomorrow? (or pick any other day) | క్షమించండి, ఈరోజు మేము మూసి ఉన్నాం 🙏 రేపు ఎలా ఉంటుంది? (లేదా వేరే ఏ రోజైనా ఎంచుకోండి) | माफ़ कीजिए, आज हम बंद हैं 🙏 कल कैसा रहेगा? (या कोई और दिन चुनें) | |
| 4 | Today's slots are over 🌙 How about tomorrow? (or pick any other day) | ఈరోజు స్లాట్లు అయిపోయాయి 🌙 రేపు ఎలా ఉంటుంది? (లేదా వేరే ఏ రోజైనా ఎంచుకోండి) | आज के स्लॉट ख़त्म हो गए 🌙 कल कैसा रहेगा? (या कोई और दिन चुनें) | |
| 5 | Sorry, {day} is fully booked 😕 Which other day works for you? | క్షమించండి, {day} పూర్తిగా బుక్ అయిపోయింది 😕 మీకు వేరే ఏ రోజు వీలవుతుంది? | माफ़ कीजिए, {day} पूरा बुक है 😕 आपके लिए और कौन सा दिन ठीक रहेगा? | |
| 6 | Tomorrow | రేపు | कल | |
| 7 | Day after tomorrow | ఎల్లుండి | परसों | |
| 8 | Let's go! 3 quick questions. | మొదలుపెడదాం! 3 చిన్న ప్రశ్నలు. | चलिए शुरू करते हैं! 3 छोटे सवाल. | |
| 9 | Sure! {heard} 👍 | సరే! {heard} 👍 | ज़रूर! {heard} 👍 | |
| 10 | Great, let's book your {bookWord}. Type *cancel* any time to stop. | సరే, మీ {bookWord} బుక్ చేద్దాం. ఆపాలంటే ఎప్పుడైనా *cancel* అని టైప్ చేయండి. | ठीक है, आपका {bookWord} बुक करते हैं. रोकने के लिए कभी भी *cancel* लिखें. | |
| 11 | {m} isn't free that day, so pick a time below. | ఆ రోజు {m} ఖాళీ లేదు, కింద ఉన్న సమయాల్లో ఒకటి ఎంచుకోండి. | उस दिन {m} खाली नहीं है, नीचे से कोई समय चुनें. | |
| 12 | {m} isn't free that day. | ఆ రోజు {m} ఖాళీ లేదు. | उस दिन {m} खाली नहीं है. | |
| 13 | Please reply A, B, C or D. | దయచేసి A, B, C లేదా D అని పంపండి. | कृपया A, B, C या D भेजें. | |
| 14 | ✅ Correct!  | ✅ సరైన జవాబు!  | ✅ सही जवाब!  | |
| 15 | ❌ Not quite — answer: *{ans}*.  | ❌ కాదు — సరైన జవాబు: *{ans}*.  | ❌ नहीं — सही जवाब: *{ans}*.  | |
| 16 | Sorry, I couldn't read that date (or it's already gone). Try *today*, *tomorrow*, a weekday, or *15/10*. | క్షమించండి, ఆ తేదీ అర్థం కాలేదు (లేదా అది అయిపోయింది). *ఈరోజు*, *రేపు*, ఒక వారం రోజు, లేదా *15/10* లా టైప్ చేయండి. | माफ़ कीजिए, यह तारीख़ समझ नहीं आई (या निकल चुकी है). *आज*, *कल*, कोई दिन, या *15/10* लिखें. | |
| 17 | Sorry, {why} ({date}) 🙏 Which other day works? | క్షమించండి, {date} న మేము మూసి ఉన్నాం 🙏 వేరే ఏ రోజు వీలవుతుంది? | माफ़ कीजिए, {date} को हम बंद हैं 🙏 और कौन सा दिन ठीक रहेगा? | |
| 18 | We take bookings up to {n} days ahead. Could you pick a closer date? | మేము {n} రోజుల ముందు వరకే బుకింగ్ తీసుకుంటాం. దగ్గరి తేదీ ఎంచుకుంటారా? | हम {n} दिन आगे तक ही बुकिंग लेते हैं. कोई नज़दीक की तारीख़ चुनेंगे? | |
| 19 | Just to check: {a} or {b}? | ఒక్కసారి చెప్పండి: {a} కావాలా, {b} కావాలా? | बस पक्का कर लूँ: {a} या {b}? | |
| 20 | Did you mean {list}? | మీకు కావాల్సింది {list}? | क्या आपका मतलब {list} है? | |
| 21 |  or  |  లేదా  |  या  | |
| 22 | Please choose one of the options (reply with the number). | దయచేసి ఆప్షన్లలో ఒకటి ఎంచుకోండి (నంబర్‌తో రిప్లై ఇవ్వండి). | कृपया कोई एक विकल्प चुनें (नंबर से जवाब दें). | |
| 23 | Could you type that again? | మళ్లీ ఒకసారి టైప్ చేస్తారా? | क्या आप फिर से लिख सकते हैं? | |
| 24 | Got it: {got} 👍 | అర్థమైంది: {got} 👍 | समझ गया: {got} 👍 | |
| 25 | Please type the name (letters only). | దయచేసి పేరు టైప్ చేయండి (అక్షరాలు మాత్రమే). | कृपया नाम लिखें (सिर्फ़ अक्षर). | |
| 26 | 🔁 Done, I've moved it.<br><br> | 🔁 అయిపోయింది, మీ బుకింగ్ మార్చాను.<br><br> | 🔁 हो गया, मैंने बुकिंग बदल दी है.<br><br> | |
| 27 | Oops, someone grabbed {gone} a second ago 😅 Here's what's still free: | అయ్యో, {gone} ఇప్పుడే వేరేవాళ్లు తీసుకున్నారు 😅 ఇంకా ఖాళీగా ఉన్నవి ఇవి: | अरे, {gone} अभी-अभी किसी और ने ले लिया 😅 अभी ये खाली हैं: | |
| 28 | You're unsubscribed and won't get any more messages from us. Reply *START* any time to come back. | మీరు అన్‌సబ్‌స్క్రైబ్ అయ్యారు, ఇకపై మా నుంచి మెసేజ్‌లు రావు. మళ్లీ రావాలంటే ఎప్పుడైనా *START* అని పంపండి. | आपका सब्सक्रिप्शन बंद हो गया, अब हमसे कोई मैसेज नहीं आएगा. वापस आने के लिए कभी भी *START* भेजें. | |
| 29 | Cancelled. No worries at all 🙂 Whenever you're ready, reply *book* and I'll find you a new slot. | క్యాన్సిల్ అయింది. పర్వాలేదు 🙂 మళ్లీ కావాలంటే *book* అని పంపండి, కొత్త స్లాట్ చూస్తాను. | कैंसिल हो गया. कोई बात नहीं 🙂 जब चाहें *book* भेजें, मैं नया स्लॉट ढूँढ दूँगा. | |
| 30 | Okay, your booking stays as it is: {date} at {slot}. See you then! 👋 | సరే, మీ బుకింగ్ అలాగే ఉంది: {date}, {slot}. కలుద్దాం! 👋 | ठीक है, आपकी बुकिंग वैसी ही है: {date}, {slot}. मिलते हैं! 👋 | |
| 31 | ✅ Confirmed: {svc}{date} at {slot}. See you! (Reply *menu* for anything else.) | ✅ కన్ఫర్మ్ అయింది: {svc}{date}, {slot}. కలుద్దాం! (ఇంకేమైనా కావాలంటే *menu* అని పంపండి.) | ✅ पक्का हो गया: {svc}{date}, {slot}. मिलते हैं! (कुछ और चाहिए तो *menu* भेजें.) | |
| 32 | No problem! Your current booking is {date} at {slot}. | సరే! మీ ప్రస్తుత బుకింగ్: {date}, {slot}. | कोई बात नहीं! आपकी अभी की बुकिंग: {date}, {slot}. | |
| 33 | Do you want to cancel your {what} on {date} at {slot}? Reply *YES* to cancel, or anything else to keep it. | {date}, {slot} కి ఉన్న మీ {what} క్యాన్సిల్ చేయాలా? క్యాన్సిల్ చేయాలంటే *YES* అని, ఉంచాలంటే ఇంకేదైనా పంపండి. | क्या आप {date}, {slot} वाला अपना {what} कैंसिल करना चाहते हैं? कैंसिल के लिए *YES* भेजें, रखने के लिए कुछ और. | |
| 34 | Yes, cancel | అవును, క్యాన్సిల్ | हाँ, कैंसिल | |
| 35 | Keep it | ఉంచండి | रहने दें | |
| 36 | Done 🎉 You'll get member-only offers, max 2 a month. Reply *STOP* any time to stop. | అయిపోయింది 🎉 మెంబర్లకు మాత్రమే ఆఫర్లు, నెలకు గరిష్ఠంగా 2 వస్తాయి. ఆపాలంటే ఎప్పుడైనా *STOP* అని పంపండి. | हो गया 🎉 आपको सिर्फ़ मेंबर वाले ऑफ़र मिलेंगे, महीने में ज़्यादा से ज़्यादा 2. रोकने के लिए कभी भी *STOP* भेजें. | |
| 37 | No problem, stopped. Nothing was changed. | సరే, ఆపేశాను. ఏమీ మారలేదు. | ठीक है, रोक दिया. कुछ नहीं बदला. | |
| 38 | You don't have an upcoming booking with us, so there's nothing to cancel 🙂 | మీకు రాబోయే బుకింగ్ ఏదీ లేదు, కాబట్టి క్యాన్సిల్ చేయడానికి ఏమీ లేదు 🙂 | आपकी कोई आने वाली बुकिंग नहीं है, इसलिए कैंसिल करने को कुछ नहीं है 🙂 | |
| 39 | Welcome back, {name}! 😊 | మళ్లీ స్వాగతం, {name}! 😊 | फिर से स्वागत है, {name}! 😊 | |
| 40 |  Same *{svc}* as last time? Reply *1* and I'll find you a slot. |  గతసారిలాగే *{svc}* కావాలా? *1* అని పంపండి, స్లాట్ చూస్తాను. |  पिछली बार की तरह *{svc}*? *1* भेजें, मैं स्लॉट ढूँढ दूँगा. | |
| 41 | Welcome back to *{business}* 😊 | *{business}* కి మళ్లీ స్వాగతం 😊 | *{business}* में फिर से स्वागत है 😊 | |
| 42 | Reply *menu* for more options. | ఇంకా ఆప్షన్ల కోసం *menu* అని పంపండి. | और विकल्पों के लिए *menu* भेजें. | |
| 43 | I understand 🙏 Our prices are fixed so every customer gets the same fair price. | అర్థమైంది 🙏 అందరికీ ఒకే న్యాయమైన ధర ఉండాలని మా ధరలు ఫిక్స్‌డ్‌గా ఉంటాయి. | मैं समझता हूँ 🙏 हमारे दाम फ़िक्स हैं ताकि हर ग्राहक को एक जैसा सही दाम मिले. | |
| 44 | <br><br>Good news though: {offer} | <br><br>ఒక మంచి వార్త: {offer} | <br><br>एक अच्छी ख़बर: {offer} | |
| 45 | <br><br>Shall I book you a slot? Reply *1*. | <br><br>స్లాట్ బుక్ చేయమంటారా? *1* అని పంపండి. | <br><br>क्या मैं आपका स्लॉट बुक कर दूँ? *1* भेजें. | |
| 46 | Sure 🙂 I've told the team — someone from *{business}* will message you here shortly (working hours: {hours}). You can also call {phone}. Type *bot* to come back to me. | సరే 🙂 టీమ్‌కి చెప్పాను, *{business}* నుంచి ఎవరైనా త్వరలో ఇక్కడే మెసేజ్ చేస్తారు (పని వేళలు: {hours}). {phone} కి కాల్ కూడా చేయవచ్చు. నా దగ్గరికి తిరిగి రావాలంటే *bot* అని టైప్ చేయండి. | ज़रूर 🙂 मैंने टीम को बता दिया है, *{business}* से कोई जल्द ही यहीं मैसेज करेगा (काम का समय: {hours}). आप {phone} पर कॉल भी कर सकते हैं. मेरे पास वापस आने के लिए *bot* लिखें. | |
| 47 | Sorry, I didn't quite get that. I can help with these: | క్షమించండి, సరిగ్గా అర్థం కాలేదు. నేను వీటిలో సహాయం చేయగలను: | माफ़ कीजिए, मैं ठीक से समझ नहीं पाया. मैं इनमें मदद कर सकता हूँ: | |
| 48 | <br><br>Want member-only offers (max 2 a month)? Reply *OFFERS*. | <br><br>మెంబర్లకు మాత్రమే ఆఫర్లు కావాలా (నెలకు గరిష్ఠంగా 2)? *OFFERS* అని పంపండి. | <br><br>सिर्फ़ मेंबर वाले ऑफ़र चाहिए (महीने में ज़्यादा से ज़्यादा 2)? *OFFERS* भेजें. | |
| 49 | 💍 Congratulations! Our *{item}* packages are *{price}*, and every package includes a trial. | 💍 అభినందనలు! మా *{item}* ప్యాకేజీలు *{price}*, ప్రతి ప్యాకేజీలో ఒక ట్రయల్ ఉంటుంది. | 💍 बधाई हो! हमारे *{item}* पैकेज *{price}* के हैं, और हर पैकेज में एक ट्रायल शामिल है. | |
| 50 | Which events, and on which dates? (e.g. *wedding 22 Jan, haldi 20 Jan*) | ఏ ఫంక్షన్లు, ఏ తేదీల్లో? (ఉదా: *పెళ్లి 22 Jan, హల్దీ 20 Jan*) | कौन से फ़ंक्शन, और किन तारीख़ों पर? (जैसे *शादी 22 Jan, हल्दी 20 Jan*) | |
| 51 | What budget do you have in mind for the whole package? (e.g. *50k*, or *not decided*) | మొత్తం ప్యాకేజీకి మీ బడ్జెట్ ఎంత? (ఉదా: *50k*, లేదా *ఇంకా అనుకోలేదు*) | पूरे पैकेज के लिए आपका बजट कितना है? (जैसे *50k*, या *अभी तय नहीं*) | |
| 52 | Lovely! And your name, please? | బాగుంది! మీ పేరు చెప్తారా? | बढ़िया! आपका नाम बताएँगे? | |
| 53 | Got it 👍<br>📅 {events} | అర్థమైంది 👍<br>📅 {events} | समझ गया 👍<br>📅 {events} | |
| 54 | No problem, our artist will confirm dates with you 👍 | పర్వాలేదు, మా ఆర్టిస్ట్ తేదీలు మీతో కన్ఫర్మ్ చేస్తారు 👍 | कोई बात नहीं, हमारी आर्टिस्ट आपसे तारीख़ें पक्की कर लेंगी 👍 | |
| 55 | Sorry, I couldn't catch a date 🙏 {ask} Or just say *not fixed yet*. | క్షమించండి, తేదీ అర్థం కాలేదు 🙏 {ask} లేదా *ఇంకా ఫిక్స్ కాలేదు* అని చెప్పండి. | माफ़ कीजिए, तारीख़ समझ नहीं आई 🙏 {ask} या बस *अभी तय नहीं* लिखें. | |
| 56 | (date to confirm) | (తేదీ ఇంకా ఖరారు కాలేదు) | (तारीख़ पक्की होनी है) | |
| 57 | So sorry 🙏 our {role} is fully committed on {date}. I've asked the owner to call you; they may be able to suggest another artist or arrangement. | క్షమించండి 🙏 {date} న మా {role} ఖాళీగా లేరు. ఓనర్‌ని మీకు కాల్ చేయమని చెప్పాను; వేరే ఆర్టిస్ట్ లేదా ఏర్పాటు సూచించగలరు. | माफ़ कीजिए 🙏 {date} को हमारी {role} खाली नहीं हैं. मैंने ओनर को आपको कॉल करने को कहा है; वे कोई और आर्टिस्ट या इंतज़ाम सुझा सकते हैं. | |
| 58 | Thank you, {name} 💛 Our {role} has your details and will WhatsApp you shortly ({hours}).<br><br>Would you like to book your *bridal trial* now? It's included in the package. | ధన్యవాదాలు, {name} 💛 మా {role} దగ్గర మీ వివరాలు ఉన్నాయి, త్వరలో WhatsApp చేస్తారు ({hours}).<br><br>ఇప్పుడే మీ *బ్రైడల్ ట్రయల్* బుక్ చేయాలా? అది ప్యాకేజీలోనే ఉంది. | धन्यवाद, {name} 💛 हमारी {role} के पास आपकी जानकारी है, वे जल्द ही WhatsApp करेंगी ({hours}).<br><br>क्या अभी अपना *ब्राइडल ट्रायल* बुक करें? यह पैकेज में शामिल है. | |
| 59 | Book a bridal trial | బ్రైడల్ ట్రయల్ బుక్ చేయండి | ब्राइडल ट्रायल बुक करें | |
| 60 | Talk to the artist | ఆర్టిస్ట్‌తో మాట్లాడాలి | आर्टिस्ट से बात करनी है | |
| 61 | Lovely! Let's book your *{trial}* 💄 Type *cancel* any time to stop. | బాగుంది! మీ *{trial}* బుక్ చేద్దాం 💄 ఆపాలంటే ఎప్పుడైనా *cancel* అని టైప్ చేయండి. | बढ़िया! आपका *{trial}* बुक करते हैं 💄 रोकने के लिए कभी भी *cancel* लिखें. | |
| 62 | team | టీమ్ | टीम | |
| 63 | artist | ఆర్టిస్ట్ | आर्टिस्ट | |
| 64 | Excellent — you're exam-ready on these topics. The full course has 5 mock tests to keep you sharp. | అద్భుతం — ఈ టాపిక్‌లలో మీరు పరీక్షకు సిద్ధంగా ఉన్నారు. పూర్తి కోర్సులో 5 మాక్ టెస్టులు ఉన్నాయి. | शानदार — इन टॉपिक्स पर आप परीक्षा के लिए तैयार हैं. पूरे कोर्स में 5 मॉक टेस्ट हैं. | |
| 65 | Good — one gap to fix. The 30-day plan targets exactly these weak areas. | బాగుంది — ఒక లోటు సరిచేయాలి. 30 రోజుల ప్లాన్ సరిగ్గా ఈ బలహీన అంశాలపైనే పనిచేస్తుంది. | अच्छा — एक कमी दूर करनी है. 30 दिन का प्लान इन्हीं कमज़ोर हिस्सों पर काम करता है. | |
| 66 | Let's build the basics. Start with the free daily question and chapter-wise practice. | బేసిక్స్ నుంచి మొదలుపెడదాం. ఉచిత రోజువారీ ప్రశ్న, చాప్టర్ వారీ ప్రాక్టీస్‌తో మొదలుపెట్టండి. | चलिए बेसिक्स से शुरू करते हैं. मुफ़्त रोज़ाना सवाल और चैप्टर के हिसाब से प्रैक्टिस से शुरू करें. | |

## Salon setup

| # | English | తెలుగు | हिंदी | Notes |
|---|---|---|---|---|
| 1 | Hi ✨ Welcome to *{business}*! Book a slot, check prices or see today's offers. | నమస్కారం ✨ *{business}* కి స్వాగతం! స్లాట్ బుక్ చేయండి, ధరలు చూడండి లేదా ఈరోజు ఆఫర్లు చూడండి. | नमस्ते ✨ *{business}* में आपका स्वागत है! स्लॉट बुक करें, रेट देखें या आज के ऑफ़र देखें. | |
| 2 | Book a service | సర్వీస్ బుక్ చేయండి | सर्विस बुक करें | |
| 3 | Price list | ధరల జాబితా | रेट लिस्ट | |
| 4 | Today's offers | ఈరోజు ఆఫర్లు | आज के ऑफ़र | |
| 5 | Timings & location | సమయాలు & లొకేషన్ | समय और पता | |
| 6 | Talk to the salon | సెలూన్‌తో మాట్లాడండి | सैलून से बात करें | |
| 7 | Which service would you like? | మీకు ఏ సర్వీస్ కావాలి? | आपको कौन सी सर्विस चाहिए? | |
| 8 | Which day? (today, tomorrow, Saturday, or 18/10) | ఏ రోజు? (ఈరోజు, రేపు, శనివారం, లేదా 18/10) | कौन सा दिन? (आज, कल, शनिवार, या 18/10) | |
| 9 | Choose a time: | సమయం ఎంచుకోండి: | समय चुनें: | |
| 10 | Your name for the booking? | బుకింగ్ కోసం మీ పేరు? | बुकिंग के लिए आपका नाम? | |
| 11 | 💖 *Booking confirmed*<br>👤 {name}<br>✂️ {service}<br>📅 {date} at {slot}<br>📍 {address}<br><br>We'll remind you 2 hours before. Reply *menu* to book another. | 💖 *బుకింగ్ కన్ఫర్మ్ అయింది*<br>👤 {name}<br>✂️ {service}<br>📅 {date}, {slot}<br>📍 {address}<br><br>2 గంటల ముందు గుర్తు చేస్తాం. ఇంకో బుకింగ్ కోసం *menu* అని పంపండి. | 💖 *बुकिंग पक्की*<br>👤 {name}<br>✂️ {service}<br>📅 {date}, {slot}<br>📍 {address}<br><br>हम 2 घंटे पहले याद दिलाएँगे. एक और बुकिंग के लिए *menu* भेजें. | |
| 12 | Price list | ధరల జాబితా | रेट लिस्ट | |
| 13 | appointment | అపాయింట్‌మెంట్ | अपॉइंटमेंट | |
| 14 | 🎉 This week: *Hair spa + haircut ₹1,299* (save ₹150) and *20% off facials* Mon–Thu. Mention this chat at the counter. | 🎉 ఈ వారం: *హెయిర్ స్పా + హెయిర్‌కట్ ₹1,299* (₹150 ఆదా), సోమ–గురు *ఫేషియల్స్‌పై 20% తగ్గింపు*. కౌంటర్‌లో ఈ చాట్ గురించి చెప్పండి. | 🎉 इस हफ़्ते: *हेयर स्पा + हेयरकट ₹1,299* (₹150 की बचत) और सोम–गुरु *फ़ेशियल पर 20% छूट*. काउंटर पर इस चैट का ज़िक्र करें. | |
| 15 | 💍 Bridal packages start at ₹15,000 and include a trial. Reply *human* and our bridal artist will call you. | 💍 బ్రైడల్ ప్యాకేజీలు ₹15,000 నుంచి మొదలు, ట్రయల్ కూడా ఉంటుంది. *human* అని పంపండి, మా బ్రైడల్ ఆర్టిస్ట్ కాల్ చేస్తారు. | 💍 ब्राइडल पैकेज ₹15,000 से शुरू होते हैं और इनमें ट्रायल शामिल है. *human* भेजें, हमारी ब्राइडल आर्टिस्ट आपको कॉल करेंगी. | |
| 16 | 🏠 Home service is available within 5 km for bookings above ₹1,500. | 🏠 ₹1,500 పైన బుకింగ్‌లకు 5 కి.మీ. లోపల హోమ్ సర్వీస్ ఉంది. | 🏠 ₹1,500 से ज़्यादा की बुकिंग पर 5 किमी के अंदर होम सर्विस मिलती है. | |
| 17 | UPI, cards and cash are all accepted. | UPI, కార్డులు, క్యాష్ అన్నీ తీసుకుంటాం. | UPI, कार्ड और कैश सब चलते हैं. | |
| 18 | We use L'Oréal Professionnel and O3+ products. | మేము L'Oréal Professionnel, O3+ ప్రొడక్ట్స్ వాడతాం. | हम L'Oréal Professionnel और O3+ प्रोडक्ट इस्तेमाल करते हैं. | |
| 19 | from ₹15,000 | ₹15,000 నుంచి | ₹15,000 से | |
| 20 | Haircut (men) | హెయిర్‌కట్ (మగవారికి) | हेयरकट (पुरुष) | |
| 21 | Haircut & styling (women) | హెయిర్‌కట్ & స్టైలింగ్ (ఆడవారికి) | हेयरकट और स्टाइलिंग (महिला) | |
| 22 | Beard trim | గడ్డం ట్రిమ్ | दाढ़ी ट्रिम | |
| 23 | Hair spa | హెయిర్ స్పా | हेयर स्पा | |
| 24 | Facial (fruit / gold) | ఫేషియల్ (ఫ్రూట్ / గోల్డ్) | फ़ेशियल (फ्रूट / गोल्ड) | |
| 25 | Bridal makeup | బ్రైడల్ మేకప్ | ब्राइडल मेकअप | |
| 26 | Bridal makeup trial | బ్రైడల్ మేకప్ ట్రయల్ | ब्राइडल मेकअप ट्रायल | |

## Real estate setup

| # | English | తెలుగు | हिंदी | Notes |
|---|---|---|---|---|
| 1 | Hello 👋 Welcome to *{business}*. Tell me what you're looking for and I'll shortlist homes and book a free site visit. | నమస్కారం 👋 *{business}* కి స్వాగతం. మీకు ఎలాంటి ఇల్లు కావాలో చెప్పండి, ఇళ్లు షార్ట్‌లిస్ట్ చేసి ఉచిత సైట్ విజిట్ బుక్ చేస్తాను. | नमस्ते 👋 *{business}* में स्वागत है. बताइए आपको कैसा घर चाहिए, मैं घर शॉर्टलिस्ट करके फ़्री साइट विज़िट बुक कर दूँगा. | |
| 2 | Find a home + site visit | ఇల్లు వెతకండి + సైట్ విజిట్ | घर ढूँढें + साइट विज़िट | |
| 3 | Current projects | ప్రస్తుత ప్రాజెక్టులు | मौजूदा प्रोजेक्ट | |
| 4 | Home loan help | హోమ్ లోన్ సహాయం | होम लोन मदद | |
| 5 | Office location | ఆఫీస్ లొకేషన్ | ऑफ़िस का पता | |
| 6 | Talk to an advisor | అడ్వైజర్‌తో మాట్లాడండి | एडवाइज़र से बात करें | |
| 7 | Are you looking to buy or rent? | మీరు కొనాలనుకుంటున్నారా, అద్దెకు కావాలా? | आप ख़रीदना चाहते हैं या किराए पर लेना? | |
| 8 | What size? | ఎంత సైజు? | कितना बड़ा? | |
| 9 | Your budget? | మీ బడ్జెట్? | आपका बजट? | |
| 10 | Preferred area? (e.g. Gachibowli, Kollur, Tellapur, Kompally) | ఏ ఏరియా కావాలి? (ఉదా: Gachibowli, Kollur, Tellapur, Kompally) | कौन सा इलाका पसंद है? (जैसे Gachibowli, Kollur, Tellapur, Kompally) | |
| 11 | When can you come for a free site visit? (today, tomorrow, Sunday, or 19/10) | ఉచిత సైట్ విజిట్‌కు ఎప్పుడు రాగలరు? (ఈరోజు, రేపు, ఆదివారం, లేదా 19/10) | फ़्री साइट विज़िट के लिए कब आ सकते हैं? (आज, कल, रविवार, या 19/10) | |
| 12 | Preferred time: | మీకు వీలైన సమయం: | पसंदीदा समय: | |
| 13 | Your name? | మీ పేరు? | आपका नाम? | |
| 14 | 🏡 *Site visit booked*<br>👤 {name}<br>🔎 {purpose} · {bhk} · {budget}<br>📍 Area: {area}<br>📅 {date} at {slot}<br><br>An advisor will WhatsApp you 3 matching options before the visit. Free pick-up from {address} is available. | 🏡 *సైట్ విజిట్ బుక్ అయింది*<br>👤 {name}<br>🔎 {purpose} · {bhk} · {budget}<br>📍 ఏరియా: {area}<br>📅 {date}, {slot}<br><br>విజిట్‌కు ముందు అడ్వైజర్ మీకు సరిపోయే 3 ఆప్షన్లు WhatsApp చేస్తారు. {address} నుంచి ఉచిత పికప్ ఉంది. | 🏡 *साइट विज़िट बुक हो गई*<br>👤 {name}<br>🔎 {purpose} · {bhk} · {budget}<br>📍 इलाका: {area}<br>📅 {date}, {slot}<br><br>विज़िट से पहले एडवाइज़र आपको 3 मिलते-जुलते विकल्प WhatsApp करेंगे. {address} से फ़्री पिक-अप मिलता है. | |
| 15 | Current projects | ప్రస్తుత ప్రాజెక్టులు | मौजूदा प्रोजेक्ट | |
| 16 | site visit | సైట్ విజిట్ | साइट विज़िट | |
| 17 | 🏦 We work with SBI, HDFC and ICICI for home loans up to 80–90% of the property value. Rough EMI: ₹50L for 20 years at 8.5% ≈ ₹43,400/month. Reply *human* for a free eligibility check. | 🏦 ఆస్తి విలువలో 80–90% వరకు హోమ్ లోన్ల కోసం SBI, HDFC, ICICI తో పనిచేస్తాం. సుమారు EMI: ₹50L, 20 ఏళ్లు, 8.5% ≈ నెలకు ₹43,400. ఉచిత ఎలిజిబిలిటీ చెక్ కోసం *human* అని పంపండి. | 🏦 प्रॉपर्टी की कीमत के 80–90% तक होम लोन के लिए हम SBI, HDFC और ICICI के साथ काम करते हैं. अंदाज़न EMI: ₹50L, 20 साल, 8.5% ≈ ₹43,400/महीना. फ़्री एलिजिबिलिटी चेक के लिए *human* भेजें. | |
| 18 | ✅ All our projects are TS-RERA registered. We share the RERA number and approved layout before your visit. | ✅ మా ప్రాజెక్టులన్నీ TS-RERA రిజిస్టర్డ్. విజిట్‌కు ముందే RERA నంబర్, అప్రూవ్డ్ లేఅవుట్ పంపుతాం. | ✅ हमारे सभी प्रोजेक्ट TS-RERA रजिस्टर्ड हैं. विज़िट से पहले हम RERA नंबर और मंज़ूर लेआउट भेजते हैं. | |
| 19 | Skyline Meadows is ready to move. Skyline Crest possession is planned for Dec 2027 (as per RERA). | Skyline Meadows వెంటనే గృహప్రవేశానికి సిద్ధంగా ఉంది. Skyline Crest పొసెషన్ Dec 2027కి ప్లాన్ చేశారు (RERA ప్రకారం). | Skyline Meadows रहने के लिए तैयार है. Skyline Crest का पज़ेशन Dec 2027 में तय है (RERA के अनुसार). | |
| 20 | There's no brokerage on our own projects. Rentals carry a one-time fee of 15 days' rent. | మా సొంత ప్రాజెక్టులపై బ్రోకరేజ్ లేదు. అద్దెలకు ఒకసారి 15 రోజుల అద్దె ఫీజు ఉంటుంది. | हमारे अपने प्रोजेक्ट पर कोई ब्रोकरेज नहीं. किराए पर एक बार 15 दिन के किराए जितनी फ़ीस लगती है. | |
| 21 | 🌏 We handle NRI purchases end to end, including video site visits and power-of-attorney guidance. | 🌏 NRI కొనుగోళ్లను మొదటి నుంచి చివరి వరకు చూసుకుంటాం, వీడియో సైట్ విజిట్లు, పవర్-ఆఫ్-అటార్నీ గైడెన్స్‌తో సహా. | 🌏 NRI ख़रीद हम शुरू से आख़िर तक संभालते हैं, वीडियो साइट विज़िट और पावर-ऑफ़-अटॉर्नी गाइडेंस समेत. | |
| 22 | ₹18L onwards | ₹18L నుంచి | ₹18L से | |
| 23 | ₹22k – ₹60k / month | నెలకు ₹22k – ₹60k | ₹22k – ₹60k / महीना | |
| 24 | Buy | కొనడం | ख़रीदना | |
| 25 | Rent | అద్దెకు | किराए पर | |
| 26 | Invest in a plot | ప్లాట్‌లో పెట్టుబడి | प्लॉट में निवेश | |
| 27 | 4 BHK / villa | 4 BHK / విల్లా | 4 BHK / विला | |
| 28 | Plot | ప్లాట్ | प्लॉट | |
| 29 | Under ₹50L | ₹50L లోపు | ₹50L से कम | |
| 30 | Above ₹2Cr | ₹2Cr పైన | ₹2Cr से ऊपर | |
| 31 | Rent under ₹40k | అద్దె ₹40k లోపు | किराया ₹40k से कम | |
| 32 | Green Acres plots, Shadnagar | Green Acres ప్లాట్లు, Shadnagar | Green Acres प्लॉट, Shadnagar | |
| 33 | Rentals in Gachibowli / Kondapur | Gachibowli / Kondapur లో అద్దె ఇళ్లు | Gachibowli / Kondapur में किराए के घर | |

## Gym setup

| # | English | తెలుగు | हिंदी | Notes |
|---|---|---|---|---|
| 1 | Hey 💪 Welcome to *{business}*! Grab a *free trial session*, check membership plans or talk to a trainer. | హాయ్ 💪 *{business}* కి స్వాగతం! *ఉచిత ట్రయల్ సెషన్* తీసుకోండి, మెంబర్‌షిప్ ప్లాన్లు చూడండి లేదా ట్రైనర్‌తో మాట్లాడండి. | हाय 💪 *{business}* में स्वागत है! *फ़्री ट्रायल सेशन* लें, मेंबरशिप प्लान देखें या ट्रेनर से बात करें. | |
| 2 | Book a free trial | ఉచిత ట్రయల్ బుక్ చేయండి | फ़्री ट्रायल बुक करें | |
| 3 | Membership plans | మెంబర్‌షిప్ ప్లాన్లు | मेंबरशिप प्लान | |
| 4 | Personal training | పర్సనల్ ట్రైనింగ్ | पर्सनल ट्रेनिंग | |
| 5 | Timings & location | సమయాలు & లొకేషన్ | समय और पता | |
| 6 | Talk to the front desk | ఫ్రంట్ డెస్క్‌తో మాట్లాడండి | फ़्रंट डेस्क से बात करें | |
| 7 | What's your main goal? | మీ ముఖ్య లక్ష్యం ఏమిటి? | आपका मुख्य लक्ष्य क्या है? | |
| 8 | When do you want your free trial? (today, tomorrow, Monday, or 20/10) | మీ ఉచిత ట్రయల్ ఎప్పుడు కావాలి? (ఈరోజు, రేపు, సోమవారం, లేదా 20/10) | फ़्री ट्रायल कब चाहिए? (आज, कल, सोमवार, या 20/10) | |
| 9 | Pick a time: | సమయం ఎంచుకోండి: | समय चुनें: | |
| 10 | Your name? | మీ పేరు? | आपका नाम? | |
| 11 | 🔥 *Free trial booked*<br>👤 {name}<br>🎯 Goal: {goal}<br>📅 {date} at {slot}<br>📍 {address}<br><br>Bring sports shoes and a water bottle. A trainer will do a free body-composition check for you. | 🔥 *ఉచిత ట్రయల్ బుక్ అయింది*<br>👤 {name}<br>🎯 లక్ష్యం: {goal}<br>📅 {date}, {slot}<br>📍 {address}<br><br>స్పోర్ట్స్ షూస్, వాటర్ బాటిల్ తీసుకురండి. ట్రైనర్ మీకు ఉచితంగా బాడీ-కంపోజిషన్ చెక్ చేస్తారు. | 🔥 *फ़्री ट्रायल बुक हो गया*<br>👤 {name}<br>🎯 लक्ष्य: {goal}<br>📅 {date}, {slot}<br>📍 {address}<br><br>स्पोर्ट्स शूज़ और पानी की बोतल साथ लाएँ. ट्रेनर आपका फ़्री बॉडी-कंपोज़िशन चेक करेंगे. | |
| 12 | Membership plans | మెంబర్‌షిప్ ప్లాన్లు | मेंबरशिप प्लान | |
| 13 | free trial | ఉచిత ట్రయల్ | फ़्री ट्रायल | |
| 14 | 🧑‍🏫 Certified personal trainers: ₹4,000/month for 12 sessions, including a diet plan. Reply *1* to start with a free trial. | 🧑‍🏫 సర్టిఫైడ్ పర్సనల్ ట్రైనర్లు: నెలకు ₹4,000, 12 సెషన్లు, డైట్ ప్లాన్‌తో సహా. ఉచిత ట్రయల్‌తో మొదలుపెట్టాలంటే *1* అని పంపండి. | 🧑‍🏫 सर्टिफ़ाइड पर्सनल ट्रेनर: ₹4,000/महीना, 12 सेशन, डाइट प्लान के साथ. फ़्री ट्रायल से शुरू करने के लिए *1* भेजें. | |
| 15 | Every member gets a basic diet chart. Detailed nutrition coaching comes with personal training. | ప్రతి మెంబర్‌కు బేసిక్ డైట్ చార్ట్ ఇస్తాం. వివరమైన న్యూట్రిషన్ కోచింగ్ పర్సనల్ ట్రైనింగ్‌తో వస్తుంది. | हर मेंबर को बेसिक डाइट चार्ट मिलता है. डिटेल्ड न्यूट्रिशन कोचिंग पर्सनल ट्रेनिंग के साथ आती है. | |
| 16 | 👩 Women-only batch 10 AM – 12 PM with female trainers, plus a separate changing room. | 👩 ఆడవారికి మాత్రమే బ్యాచ్ ఉదయం 10 – మధ్యాహ్నం 12, మహిళా ట్రైనర్లతో; వేరే చేంజింగ్ రూమ్ కూడా ఉంది. | 👩 सिर्फ़ महिलाओं का बैच सुबह 10 – दोपहर 12, महिला ट्रेनरों के साथ; अलग चेंजिंग रूम भी है. | |
| 17 | Half-yearly and annual plans can be frozen for up to 30 days (medical or travel). | 6 నెలల, సంవత్సరం ప్లాన్లను 30 రోజుల వరకు ఫ్రీజ్ చేయవచ్చు (మెడికల్ లేదా ప్రయాణం). | छमाही और सालाना प्लान 30 दिन तक फ़्रीज़ हो सकते हैं (मेडिकल या यात्रा). | |
| 18 | Renew before expiry and get 10% off. Reply *human* and the desk will send a payment link. | గడువు ముగిసేలోపు రిన్యూ చేస్తే 10% తగ్గింపు. *human* అని పంపండి, డెస్క్ పేమెంట్ లింక్ పంపుతుంది. | एक्सपायरी से पहले रिन्यू करें और 10% छूट पाएँ. *human* भेजें, डेस्क पेमेंट लिंक भेजेगा. | |
| 19 | UPI, cards, cash and no-cost EMI on annual plans. | UPI, కార్డులు, క్యాష్, సంవత్సరం ప్లాన్లపై నో-కాస్ట్ EMI. | UPI, कार्ड, कैश और सालाना प्लान पर नो-कॉस्ट EMI. | |
| 20 | ₹4,000 / month | నెలకు ₹4,000 | ₹4,000 / महीना | |
| 21 | Weight loss | బరువు తగ్గడం | वज़न घटाना | |
| 22 | Muscle gain | కండలు పెంచడం | मसल्स बढ़ाना | |
| 23 | General fitness | సాధారణ ఫిట్‌నెస్ | जनरल फ़िटनेस | |
| 24 | Strength / powerlifting | స్ట్రెంత్ / పవర్‌లిఫ్టింగ్ | स्ट्रेंथ / पावरलिफ़्टिंग | |
| 25 | Yoga / Zumba | యోగా / జుంబా | योग / ज़ुम्बा | |
| 26 | Monthly | నెలవారీ | मासिक | |
| 27 | Quarterly | 3 నెలలు | तिमाही | |
| 28 | Half-yearly | 6 నెలలు | छमाही | |
| 29 | Annual (best value) | సంవత్సరం (బెస్ట్ వాల్యూ) | सालाना (सबसे फ़ायदेमंद) | |
| 30 | Personal training add-on | పర్సనల్ ట్రైనింగ్ యాడ్-ఆన్ | पर्सनल ट्रेनिंग ऐड-ऑन | |

## Exam kits setup

| # | English | తెలుగు | हिंदी | Notes |
|---|---|---|---|---|
| 1 | Hi 📚 Welcome to *{business}*. Take a free 3-question quiz for your exam and get a daily practice question every morning. | హాయ్ 📚 *{business}* కి స్వాగతం. మీ పరీక్ష కోసం ఉచిత 3-ప్రశ్నల క్విజ్ రాయండి, ప్రతి ఉదయం ఒక ప్రాక్టీస్ ప్రశ్న పొందండి. | हाय 📚 *{business}* में स्वागत है. अपनी परीक्षा के लिए फ़्री 3-सवाल क्विज़ दें और हर सुबह एक प्रैक्टिस सवाल पाएँ. | |
| 2 | Take today's free quiz | ఈరోజు ఉచిత క్విజ్ | आज का फ़्री क्विज़ | |
| 3 | Courses, kits & fees | కోర్సులు, కిట్లు & ఫీజులు | कोर्स, किट और फ़ीस | |
| 4 | Daily question plan | రోజువారీ ప్రశ్న ప్లాన్ | रोज़ाना सवाल प्लान | |
| 5 | How it works | ఇది ఎలా పనిచేస్తుంది | यह कैसे काम करता है | |
| 6 | Free demo class / counsellor | ఉచిత డెమో క్లాస్ / కౌన్సెలర్ | फ़्री डेमो क्लास / काउंसलर | |
| 7 | Which exam are you preparing for? | మీరు ఏ పరీక్షకు ప్రిపేర్ అవుతున్నారు? | आप किस परीक्षा की तैयारी कर रहे हैं? | |
| 8 | Nice work! What's your name? I'll send your score card and tomorrow's question. | బాగా చేశారు! మీ పేరు ఏమిటి? మీ స్కోర్ కార్డ్, రేపటి ప్రశ్న పంపుతాను. | बहुत बढ़िया! आपका नाम क्या है? मैं आपका स्कोर कार्ड और कल का सवाल भेजूँगा. | |
| 9 | 🏆 *Score card — {name}*<br>📝 {service}: *{score}/3*<br><br>{advice}<br><br>Reply *2* for courses and fees, or *human* to book a free demo class with a counsellor. | 🏆 *స్కోర్ కార్డ్ — {name}*<br>📝 {service}: *{score}/3*<br><br>{advice}<br><br>కోర్సులు, ఫీజుల కోసం *2* అని, కౌన్సెలర్‌తో ఉచిత డెమో క్లాస్ కోసం *human* అని పంపండి. | 🏆 *स्कोर कार्ड — {name}*<br>📝 {service}: *{score}/3*<br><br>{advice}<br><br>कोर्स और फ़ीस के लिए *2* भेजें, या काउंसलर के साथ फ़्री डेमो क्लास के लिए *human* भेजें. | |
| 10 | Courses, kits & fees | కోర్సులు, కిట్లు & ఫీజులు | कोर्स, किट और फ़ीस | |
| 11 | quiz | క్విజ్ | क्विज़ | |
| 12 | 📅 You'll get one exam-level question every morning at 7:00 AM, with the answer and a 2-line explanation in the evening. Free forever. Reply STOP any time to unsubscribe. | 📅 ప్రతి ఉదయం 7:00 కి ఒక పరీక్ష స్థాయి ప్రశ్న వస్తుంది, సాయంత్రం జవాబు, 2 లైన్ల వివరణతో. ఎప్పటికీ ఉచితం. ఆపాలంటే ఎప్పుడైనా STOP అని పంపండి. | 📅 हर सुबह 7:00 बजे एक परीक्षा-स्तर का सवाल आता है, और शाम को जवाब के साथ 2 लाइन की व्याख्या. हमेशा मुफ़्त. रोकने के लिए कभी भी STOP भेजें. | |
| 13 | Each kit has the syllabus map, 300+ solved questions, 5 mock tests and a 30-day plan, all as PDF on WhatsApp. | ప్రతి కిట్‌లో సిలబస్ మ్యాప్, 300+ సాల్వ్ చేసిన ప్రశ్నలు, 5 మాక్ టెస్టులు, 30 రోజుల ప్లాన్ ఉంటాయి, అన్నీ WhatsApp లో PDF గా. | हर किट में सिलेबस मैप, 300+ हल किए सवाल, 5 मॉक टेस्ट और 30 दिन का प्लान है, सब WhatsApp पर PDF में. | |
| 14 | Not happy within 7 days? Full refund, no questions. | 7 రోజుల్లో నచ్చకపోతే పూర్తి రీఫండ్, ఏ ప్రశ్నలూ అడగం. | 7 दिन में पसंद न आए तो पूरा रिफ़ंड, कोई सवाल नहीं. | |
| 15 | ₹18,000 (kit alone ₹199) | ₹18,000 (కిట్ మాత్రమే ₹199) | ₹18,000 (सिर्फ़ किट ₹199) | |
| 16 | ₹12,000 (kit alone ₹149) | ₹12,000 (కిట్ మాత్రమే ₹149) | ₹12,000 (सिर्फ़ किट ₹149) | |
| 17 | ₹6,500 (kit alone ₹149) | ₹6,500 (కిట్ మాత్రమే ₹149) | ₹6,500 (सिर्फ़ किट ₹149) | |
| 18 | ₹15,000 (kit alone ₹199) | ₹15,000 (కిట్ మాత్రమే ₹199) | ₹15,000 (सिर्फ़ किट ₹199) | |
| 19 | TSPSC Group 2 — 4-month batch | TSPSC Group 2 — 4 నెలల బ్యాచ్ | TSPSC Group 2 — 4 महीने का बैच | |
| 20 | SSC CGL — weekend batch | SSC CGL — వీకెండ్ బ్యాచ్ | SSC CGL — वीकेंड बैच | |
| 21 | RRB NTPC — online batch | RRB NTPC — ఆన్‌లైన్ బ్యాచ్ | RRB NTPC — ऑनलाइन बैच | |
| 22 | Bank PO — prelims + mains | Bank PO — ప్రిలిమ్స్ + మెయిన్స్ | Bank PO — प्रीलिम्स + मेन्स | |
