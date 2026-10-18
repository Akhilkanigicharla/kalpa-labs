// Telugu first, then Hindi and English. Every key exists in all three (test/web.test.mjs checks).
export const STR = {
  te: { tabDue: "సర్వీస్", due: "సర్వీస్ రావాల్సినవి", customers: "కస్టమర్లు", bills: "బిల్లులు", record: "రికార్డ్", amc: "AMC ముగుస్తున్నవి",
    remind: "WhatsApp లో గుర్తుచేయండి", call: "కాల్", overdue: "ఆలస్యం", dueOn: "తేదీ", none: "ఈ నెల ఎవరూ లేరు.", notOpted: "{n} మంది WhatsApp కి ఒప్పుకోలేదు — కస్టమర్ల ట్యాబ్‌లో టిక్ చేయండి.",
    search: "పేరు, ఏరియా లేదా ఫోన్", spent: "మొత్తం", last: "చివరి విజిట్", optIn: "WhatsApp గుర్తుచేయడానికి ఒప్పుకున్నారు", unpaid: "రావాల్సిన డబ్బు", paid: "చెల్లించారు", notPaid: "బాకీ",
    signIn: "ఫోన్ నంబర్‌తో లాగిన్", phone: "మొబైల్ నంబర్", sendCode: "కోడ్ పంపండి", code: "SMS లో వచ్చిన 6 అంకెల కోడ్", verify: "లాగిన్", badPhone: "10 అంకెల మొబైల్ నంబర్ ఇవ్వండి",
    hold: "నొక్కి మాట్లాడండి", stop: "ఆపడానికి నొక్కండి", heard: "నేను విన్నది", offline: "ఇంటర్నెట్ లేదు. జాబితాలు చూడవచ్చు; రికార్డింగ్ కోసం సిగ్నల్ కావాలి.", minutes: "ఈ నెల వాయిస్: {used}/{limit} నిమిషాలు",
    demo: "డెమో — తయారుచేసిన పేర్లు, నంబర్లు", signOut: "లాగౌట్", error: "ఏదో తప్పు జరిగింది. మళ్ళీ ప్రయత్నించండి.", noMic: "ఈ ఫోన్‌లో మైక్ దొరకలేదు." },
  hi: { tabDue: "सर्विस", due: "सर्विस बाकी", customers: "ग्राहक", bills: "बिल", record: "रिकॉर्ड", amc: "AMC खत्म हो रहे",
    remind: "WhatsApp पर याद दिलाएँ", call: "कॉल", overdue: "देर", dueOn: "तारीख", none: "इस महीने कोई नहीं।", notOpted: "{n} ग्राहकों ने WhatsApp की हाँ नहीं कही — ग्राहक टैब में टिक करें।",
    search: "नाम, इलाका या फ़ोन", spent: "कुल", last: "आख़िरी विज़िट", optIn: "WhatsApp रिमाइंडर के लिए हाँ कही", unpaid: "बाकी पैसे", paid: "मिल गया", notPaid: "बाकी",
    signIn: "फ़ोन नंबर से लॉगिन", phone: "मोबाइल नंबर", sendCode: "कोड भेजें", code: "SMS में आया 6 अंकों का कोड", verify: "लॉगिन", badPhone: "10 अंकों का मोबाइल नंबर डालें",
    hold: "दबाकर बोलिए", stop: "रोकने के लिए दबाएँ", heard: "मैंने क्या सुना", offline: "इंटरनेट नहीं है। सूचियाँ देख सकते हैं; रिकॉर्डिंग के लिए सिग्नल चाहिए।", minutes: "इस महीने वॉइस: {used}/{limit} मिनट",
    demo: "डेमो — बनाए हुए नाम और नंबर", signOut: "लॉग आउट", error: "कुछ गड़बड़ हुई। फिर कोशिश करें।", noMic: "इस फ़ोन में माइक नहीं मिला।" },
  en: { tabDue: "Due", due: "Service due", customers: "Customers", bills: "Bills", record: "Record", amc: "AMC ending soon",
    remind: "Remind on WhatsApp", call: "Call", overdue: "overdue", dueOn: "due", none: "Nobody this month.", notOpted: "{n} due customers haven't agreed to WhatsApp — tick them in Customers.",
    search: "Name, area or phone", spent: "Total", last: "Last visit", optIn: "Agreed to WhatsApp reminders", unpaid: "Money to collect", paid: "paid", notPaid: "unpaid",
    signIn: "Sign in with your phone", phone: "Mobile number", sendCode: "Send code", code: "6-digit code from the SMS", verify: "Sign in", badPhone: "Enter a 10-digit mobile number",
    hold: "Tap and speak", stop: "Tap to stop", heard: "What I heard", offline: "No internet. Lists still work; recording needs signal.", minutes: "Voice this month: {used}/{limit} min",
    demo: "Demo — made-up names and numbers", signOut: "Sign out", error: "Something went wrong. Please try again.", noMic: "No microphone found on this phone." },
};
export const t = (lang, key, vars = {}) => (STR[lang] || STR.te)[key].replace(/\{(\w+)\}/g, (_, k) => vars[k]);
export const pickLang = (nav = "te") => (/^hi/.test(nav) ? "hi" : /^en/.test(nav) ? "en" : "te");
