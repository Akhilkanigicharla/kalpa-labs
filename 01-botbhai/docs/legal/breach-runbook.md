# Breach runbook (DPDP Rule 7) · A350

Not legal advice. The lawyer/CA read in C23 still decides. Written 26 Nov 2026; duties start 13 May 2027.

**Law (checked 26 Nov 2026):** Rule 7(1): tell each affected person without delay, in plain words, through their account or the contact they gave us: (a) what happened, how much, when; (b) the likely effect on them; (c) what we did and are doing; (d) what they can do to protect themselves; (e) a contact who can answer. Rule 7(2): tell the Data Protection Board (a) without delay: what, how much, when, where, likely impact; (b) within 72 hours (or longer if the Board agrees in writing): updated details, facts and reasons, mitigation, findings on who caused it, steps to stop it happening again, and a report on the notices sent to people. Sources: dpdpa.com Rule 7 page (fetched 26 Nov 2026); dpdpa.support and governancedocs.com Rule 7 guides (search, 26 Nov 2026); `dpdp-2027.md` row D9.

## Who is who

| Data | Kalpa's role | Who tells people + Board | Kalpa's clock |
|---|---|---|---|
| Kalpa site form + site chat | Data Fiduciary | Kalpa (Akhil) | person: without delay; Board: at once, full report ≤ 72 h |
| BotBhai (a salon's customers) | Data Processor | the salon (Fiduciary) | tell the salon **within 24 hours** of finding it (agreement clause); help the salon with its notices |

**Incident lead:** Akhil Kanigicharla (aakhiil51458@gmail.com). Claude sessions and free agents only collect facts and draft; Akhil sends every notice. No one ever pastes passwords, keys or customer data into chat, issues or logs.

**A breach is** any personal data seen, copied, changed, lost or deleted by someone who should not have: leaked key, open database table, wrong person sent a message, stolen phone with the admin logged in, provider tells us they were breached.

## First hour (start the clock: write the time you found it)

| Minute | Do | Who |
|---|---|---|
| 0–10 | Write down: time found, how found, what looks wrong. Open `00-hq/log/incidents/<date>-breach.md` from the drill format below. | Akhil |
| 10–20 | **Contain:** rotate the leaked key (Supabase / Netlify / Groq / Meta dashboards, Akhil only), switch the site chat/form function off in Netlify if it leaks, turn RLS on / revoke the public role, sign out stolen devices. | Akhil |
| 20–35 | **Scope:** which system, which tables, how many people, which fields (name, phone, chat text…), from when to when. Supabase and Netlify logs; `git log` for a pushed secret (GitHub secret scanning). | Akhil + Claude session |
| 35–45 | **Decide whose data:** site form/chat → Kalpa is Fiduciary → Board + person notices below. BotBhai → tell each affected salon now (salon template), do not message their customers ourselves unless the salon asks in writing. | Akhil |
| 45–60 | Send the Board "without delay" notice (part A). Draft person notices (part B). Keep evidence: export the logs, don't delete anything. | Akhil |

Then: person notices sent the same day; full Board report (part C) before 72 h from the time found; salon follow-up every 24 h until closed.

## Template A · Board, without delay (Rule 7(2)(a))

> Subject: Personal data breach intimation, Kalpa Labs (UDYAM-TS-02-0382711)
>
> What happened: [nature: e.g. database table readable without login]
> How much: [number of people, which fields]
> When: [start date/time] to [end date/time] IST; found [date/time] IST
> Where: [system, e.g. Supabase project hosted in [region]]
> Likely impact: [e.g. names and phone numbers may be used for spam calls]
> Contact: Akhil Kanigicharla, aakhiil51458@gmail.com
> A detailed report follows within 72 hours.

Send through the Board's own channel once it publishes one (check dpb.gov.in on the day; unverified today).

## Template B · each affected person (Rule 7(1)), 5 languages

Send through the contact they gave us (WhatsApp only to people who opted in; otherwise the phone/email on the form). Plain words, no blame, no legal jargon.

**English**
> Kalpa Labs: a security problem affected your data.
> What happened: on [date] [what], your [name / phone / chat messages] could be seen by [who].
> What it may mean for you: [e.g. you may get spam calls or messages pretending to be us].
> What we did: [closed the gap at time; changed keys; told the Data Protection Board].
> What you can do: ignore messages asking for OTPs or money in our name; we never ask for them. [extra step].
> Questions: Akhil, aakhiil51458@gmail.com.

**తెలుగు**
> Kalpa Labs: ఒక భద్రతా సమస్య వల్ల మీ సమాచారం ప్రభావితమైంది.
> ఏమి జరిగింది: [తేదీ] న [ఏమి], మీ [పేరు / ఫోన్ / చాట్ సందేశాలు] [ఎవరికి] కనిపించి ఉండవచ్చు.
> మీపై ప్రభావం: [ఉదా: మా పేరుతో స్పామ్ కాల్స్ రావచ్చు].
> మేము చేసింది: [సమస్యను మూసివేశాం; కీలు మార్చాం; డేటా ప్రొటెక్షన్ బోర్డుకు తెలిపాం].
> మీరు చేయగలిగేది: మా పేరుతో OTP లేదా డబ్బు అడిగే సందేశాలను పట్టించుకోవద్దు; మేము ఎప్పుడూ అడగము.
> ప్రశ్నలు: Akhil, aakhiil51458@gmail.com.

**हिन्दी**
> Kalpa Labs: एक सुरक्षा समस्या से आपका डेटा प्रभावित हुआ है।
> क्या हुआ: [तारीख] को [क्या], आपका [नाम / फ़ोन / चैट संदेश] [किसे] दिख सकता था।
> आप पर असर: [जैसे: हमारे नाम से स्पैम कॉल आ सकते हैं]।
> हमने क्या किया: [कमी बंद की; चाबियाँ बदलीं; डेटा प्रोटेक्शन बोर्ड को बताया]।
> आप क्या करें: हमारे नाम से OTP या पैसे माँगने वाले संदेशों को नज़रअंदाज़ करें; हम कभी नहीं माँगते।
> सवाल: Akhil, aakhiil51458@gmail.com.

**Tenglish**
> Kalpa Labs: oka security problem valla mee data affect ayyindi.
> Em jarigindi: [date] na [what], mee [name / phone / chat messages] [evariki] kanipinchi undavachu.
> Meeku effect: [eg: maa peru tho spam calls raavachu].
> Memu chesindi: [gap close chesam; keys marchaam; Data Protection Board ki cheppam].
> Meeru cheyyalsindi: maa peru tho OTP leda dabbulu adige messages ni pattinchukovaddu; memu eppudu adagamu.
> Questions: Akhil, aakhiil51458@gmail.com.

**Hinglish**
> Kalpa Labs: ek security problem se aapka data affect hua hai.
> Kya hua: [date] ko [what], aapka [name / phone / chat messages] [kisko] dikh sakta tha.
> Aap par asar: [jaise: humare naam se spam calls aa sakti hain].
> Humne kya kiya: [gap band kiya; keys badli; Data Protection Board ko bataya].
> Aap kya karein: humare naam se OTP ya paise maangne wale messages ignore karein; hum kabhi nahi maangte.
> Sawal: Akhil, aakhiil51458@gmail.com.

Translations drafted by Claude; a native speaker checks Telugu and Hindi before first real use (C23 lawyer read covers the English).

## Template C · Board, full report within 72 h (Rule 7(2)(b))

1. **Updated description:** nature, extent (people, fields), timing, location, impact (update template A).
2. **Facts and reasons:** timeline from first bad event to containment; root cause in one paragraph.
3. **Mitigation done or planned:** with dates.
4. **Who caused it:** findings so far (outside attacker / our mistake / provider), with evidence kept.
5. **Stop it happening again:** the fix, the test that now guards it, the roadmap item id.
6. **Notices to people:** how many sent, when, by which channel, copy of the text, how many bounced.

If 72 h is not enough, ask the Board in writing for more time before the 72 h end, and say why.

## Template D · BotBhai salon, within 24 h (our agreement)

> Subject: Data breach notice from Kalpa Labs (your Data Processor)
>
> We found a security problem on [date/time] IST that affects your customers' data in BotBhai.
> What: [nature] · How many: [number of your customers, which fields] · When: [from–to]
> What we did: [containment]. What we are still doing: [next steps].
> What you need to do as the Data Fiduciary: tell your affected customers without delay and the Data Protection Board (full report within 72 h). Ready-to-send texts in English, Telugu, Hindi, Tenglish and Hinglish are attached (template B), and we will send them from BotBhai on your written OK.
> We will update you every 24 hours until it is closed. Contact: Akhil, aakhiil51458@gmail.com.

## After it is closed

- Write the incident note in `00-hq/log/incidents/` (same format as the drill).
- Add a test that fails if the same gap returns; add a roadmap item for anything bigger.
- Keep the incident note and evidence for at least 1 year (Rule 6(1)(e) logs).

## Drill (once a year, and before 13 May 2027)

Tabletop: pick a scenario, walk the first hour on paper, time each step, fill the templates with fake data, list gaps. Log in `00-hq/log/incidents/drill-YYYY-MM-DD.md`. First drill: `00-hq/log/incidents/drill-2026-11-26.md`.
