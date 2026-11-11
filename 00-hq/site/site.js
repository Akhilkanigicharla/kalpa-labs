(function(){
const NS='http://www.w3.org/2000/svg';
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.append(e);return e;};
/* humanoid mini robot */
function bot(g,color,mode){
 const SH='#eef1f5',J='#2a2e35',E='#c9ced6';
 el('ellipse',{cx:0,cy:1,rx:12,ry:3.6,fill:'#000',opacity:.15},g);
 const r=el('g',{class:mode||'working'},g);
 [-3.6,3.6].forEach(x=>{const L=el('g',{},r);el('rect',{x:x-3,y:-33,width:6,height:16,rx:3,fill:SH,stroke:E,'stroke-width':.6},L);el('circle',{cx:x,cy:-17,r:2.4,fill:J},L);el('rect',{x:x-2.7,y:-17,width:5.4,height:15,rx:2.6,fill:SH,stroke:E,'stroke-width':.6},L);el('rect',{x:x-3.6,y:-3,width:7.6,height:3.4,rx:1.6,fill:J},L);});
 const T=el('g',{class:'torso'},r);
 el('rect',{x:-7.5,y:-37,width:15,height:6,rx:2.5,fill:J},T);
 el('path',{d:'M-10.5 -58 Q0 -61 10.5 -58 L8 -36 Q0 -34 -8 -36 Z',fill:SH,stroke:E,'stroke-width':.7},T);
 el('circle',{cx:0,cy:-49,r:2.2,fill:color,class:'glow'},T);
 [[-12.5,'arm-a'],[12.5,'arm-b']].forEach(([x,c])=>{const A=el('g',{class:'limb '+c},T);el('rect',{x:x-2.4,y:-57,width:4.8,height:13,rx:2.4,fill:SH,stroke:E,'stroke-width':.6},A);el('circle',{cx:x,cy:-44,r:1.9,fill:J},A);el('rect',{x:x-2.2,y:-44,width:4.4,height:11,rx:2.2,fill:SH,stroke:E,'stroke-width':.6},A);el('circle',{cx:x,cy:-32.5,r:2.3,fill:J},A);});
 el('rect',{x:-2.2,y:-62,width:4.4,height:5,rx:1.5,fill:J},T);
 el('ellipse',{cx:0,cy:-69,rx:7.2,ry:8.4,fill:SH,stroke:E,'stroke-width':.7},T);
 el('path',{d:'M-6 -71 Q0 -77 6 -71 L5.4 -64 Q0 -61.5 -5.4 -64 Z',fill:'#0d0f13'},T);
 el('rect',{x:-4,y:-69.5,width:8,height:1.6,rx:.8,fill:color,class:'glow'},T);
}
function human(g){
 el('ellipse',{cx:0,cy:2,rx:18,ry:5,fill:'#000',opacity:.12},g);
 el('rect',{x:-13,y:-32,width:26,height:34,rx:10,fill:'#2F6A3A'},g);
 el('path',{d:'M-4 -32 L0 -26 L4 -32z',fill:'#fff'},g);
 el('circle',{cx:0,cy:-43,r:11,fill:'#a9714b'},g);
 el('path',{d:'M-11 -44 Q-11 -58 0 -58 Q11 -58 11 -44 Q8 -51 0 -50.5 Q-8 -51 -11 -44z',fill:'#1e1a17'},g);
 el('circle',{cx:-4,cy:-43,r:1.4,fill:'#1e1a17'},g);el('circle',{cx:4,cy:-43,r:1.4,fill:'#1e1a17'},g);
 el('path',{d:'M-3.5 -38 Q0 -35 3.5 -38',stroke:'#1e1a17','stroke-width':1.4,fill:'none','stroke-linecap':'round'},g);
}
document.querySelectorAll('[data-bot]').forEach(g=>bot(g,g.dataset.bot,'waving'));
document.querySelectorAll('[data-human]').forEach(g=>human(g));

/* ---------- i18n ---------- */
const TE={nav_live:'లైవ్ AI',tip_go:'వివరాలు చూడండి',tree_note:'పండును ట్యాప్ చేస్తే ఆ ఉత్పత్తి తెరుచుకుంటుంది. చెట్టును ట్యాప్ చేస్తే ఆకులు రాలుతాయి. మా AI ఏజెంట్లు రోజూ నిజంగా చేసే పనులను ఈ రోబోలు చూపిస్తాయి.',d_h:'ఇప్పుడే మా AIతో మాట్లాడండి',d_p:'Kalpa Bhai నిజమైన AI, BotBhai మీ సెలూన్‌లో పెట్టేది ఇలాంటిదే. సహాయం చేయలేకపోతే, అఖిల్ కాల్ చేయడానికి మీ నంబర్ అడుగుతుంది.',d_l1:'ధరలు, ఉచిత పైలట్ లేదా వర్క్‌షాప్ గురించి అడగండి',d_l2:'తెలుగు, హిందీ, ఇంగ్లీష్ లేదా కలిపి టైప్ చేయండి',d_l3:'"కాల్ చేయండి" అని చెప్పి మీ నంబర్ ఇవ్వండి',nav_products:'ఉత్పత్తులు',nav_how:'ఎలా పనిచేస్తుంది',nav_workshop:'వర్క్‌షాప్',nav_faq:'ప్రశ్నలు',cta_salon:'ఉచిత 14 రోజుల పైలట్',cta_demo:'AIతో చాట్ చేయండి',
h1:'మీ కస్టమర్లకు <em>తెలుగు, హిందీ, ఇంగ్లీష్‌లో</em> రాత్రి 11 గంటలకైనా జవాబు.',
lead:'BotBhai జిమ్‌లు, సెలూన్లు, రియల్ ఎస్టేట్ ఏజెంట్ల కస్టమర్లకు 5 భాషల్లో జవాబిస్తుంది, స్లాట్ లేదా సైట్ విజిట్ బుక్ చేస్తుంది, గుర్తు చేస్తుంది, అవసరమైనప్పుడు మీకు అప్పగిస్తుంది. 16 నవంబర్ నుంచి 14 రోజుల ఉచిత పైలట్.',
trust1:'అధికారిక WhatsApp APIపై నిర్మించబడింది',trust2:'యాప్ ఇన్‌స్టాల్ అవసరం లేదు',trust3:'ఉద్యమ్ నమోదిత MSME',online:'AI సహాయకుడు · 5 భాషలు',demo_note:'ఇది నిజమైన AI, BotBhai మీ సెలూన్‌లో పెట్టేది ఇలాంటిదే. ఏదైనా అడగండి, లేదా కాల్ బ్యాక్ అడగండి.',
st_pilot:'పైలట్ డేకి రోజులు (16 నవం)',st_launch:'పబ్లిక్ లాంచ్‌కి రోజులు (13 డిసెం)',st_agents:'ఒక వ్యవస్థాపకుడితో పనిచేసే AI ఏజెంట్లు',st_langs:'భాషలు: తెలుగు, హిందీ, ఇంగ్లీష్',
p_h:'నిజమైన భారతీయ పనికి చిన్న, నిజాయితీ గల టూల్స్',p_p:'ప్రతి ఉత్పత్తి ఒక పనిని బాగా చేస్తుంది. ధరలు రూపాయల్లో, ఎలాంటి బంధనం లేదు.',
h_h:'"స్లాట్ ఉందా?" నుంచి కన్ఫర్మ్ బుకింగ్ వరకు',s1h:'కస్టమర్ మెసేజ్',s1p:'WhatsApp లేదా వెబ్‌సైట్‌లో, తెలుగు, హిందీ, ఇంగ్లీష్ లేదా కలిపి. "రేపు" అంటే రేపే అని అర్థం చేసుకుంటుంది.',
s2h:'BotBhai జవాబు',s2p:'మీ సెలూన్ వివరాల నుంచే ధరలు, సమయాలు, ఖాళీ స్లాట్లు. ధరను ఎప్పుడూ ఊహించదు; సందేహం ఉంటే మీ సిబ్బందికి పంపుతుంది.',s3h:'నియంత్రణ మీదే',s3p:'బుకింగ్ కన్ఫర్మ్, 24 గం, 2 గం ముందు రిమైండర్లు, యజమానికి రోజువారీ జాబితా. ఏ చాట్‌నైనా ఒక్క ట్యాప్‌తో మీరు తీసుకోవచ్చు.',
t_h:'ఒక వ్యవస్థాపకుడు. 22 AI సహచరులు.',t_p:'Kalpa Labs ఉచిత, ఓపెన్ AI మోడల్స్‌పై నడుస్తుంది. ఈ పేజీలో ప్రతి మాట మేము నిజంగా తయారు చేసినదానితో సరిచూసినదే; ఇంకా సిద్ధం కానివి "ప్లాన్" అని గుర్తించాం.',
ribbon:'3 స్థానాలు',f_h:'14 రోజుల ఉచిత పైలట్, తర్వాత ఫౌండింగ్ ధరలు',f_per:' / నెల, మొదటి 3 నెలలు',f1:'₹2,999 ఒక్కసారి సెటప్, మేమే చేస్తాం',f2:'WhatsApp బాట్, బుకింగ్స్, రిమైండర్లు, యజమాని అలర్ట్స్, డాష్‌బోర్డ్',f3:'తెలుగు, హిందీ, ఇంగ్లీష్',f4:'ఐచ్ఛిక సోషల్ టీమ్ యాడ్-ఆన్: ₹999 / నెల',f_cta:'పైలట్ అడగండి',f_small:'పైలట్ ముగిసి మీరు అవును అనే వరకు చెల్లింపు లేదు.',
w_h:'"Claude Code with me": 90 నిమిషాల్లో 3 చిన్న AI టూల్స్',w_when:', ఆది 29 నవం, ఉ. 11:00, Google Meetలో, తెలుగులో',w_p:'ప్రారంభకుల కోసం. మనం కలిసి నేర్చుకుంటాం; ఇది నిపుణుల కోర్సు కాదు, ఆదాయ హామీ లేదు. పూర్తి అజెండా, మెటీరియల్ ఇప్పుడు తయారు చేసి పరీక్షిస్తున్నాం. ఉచిత వెయిట్‌లిస్ట్‌లో చేరండి: అజెండా ప్రచురించిన తర్వాతే చెల్లింపు, ఉపయోగపడకపోతే 7 రోజుల్లో పూర్తి రిఫండ్.',w_cta:'ఉచిత వెయిట్‌లిస్ట్‌లో చేరండి',
g_h:'మీకేం కావాలో చెప్పండి. అఖిల్ స్వయంగా జవాబిస్తారు.',g_p:'మీ నంబర్‌ను ఈ విషయంపై జవాబివ్వడానికి మాత్రమే వాడతాం. స్పామ్ లేదు, ఎవరితోనూ పంచుకోం.',
l_interest:'నాకు ఆసక్తి ఉన్నది',o_salon:'నా జిమ్/సెలూన్/రియల్ ఎస్టేట్ కోసం BotBhai (ఉచిత పైలట్)',o_workshop:'వర్క్‌షాప్ వెయిట్‌లిస్ట్ (ఉచితం) · 29 నవం',o_kits:'పరీక్ష / డబ్బు కిట్స్',o_other:'ఇంకేదైనా',l_name:'మీ పేరు',l_phone:'WhatsApp నంబర్',l_consent:'ఈ విషయం గురించి Kalpa Labs నన్ను WhatsAppలో సంప్రదించడానికి అంగీకరిస్తున్నాను. నా డేటాను ఎప్పుడైనా తొలగించమని అడగవచ్చు.',l_send:'పంపండి',
q_h:'సూటిగా జవాబులు',q1:'ఇది బాట్ అని కస్టమర్లకు తెలుస్తుందా?',a1:'అవును. చాట్ మొదట్లోనే ఇది ఆటోమేటెడ్ సహాయకుడు అని చెబుతుంది, అడిగినప్పుడల్లా మీ సిబ్బందికి అప్పగిస్తుంది.',q2:'తప్పు జవాబిస్తే?',a2:'మీరు ఇచ్చిన ధరలు, సమయాలే వాడుతుంది. ఖచ్చితంగా తెలియకపోతే లేదా కస్టమర్ కోపంగా ఉంటే, ఊహించకుండా మీకు అప్పగిస్తుంది.',q3:'కంప్యూటర్ లేదా కొత్త నంబర్ కావాలా?',a3:'కంప్యూటర్ అవసరం లేదు. సెలూన్‌కు ఒక WhatsApp నంబర్ చాలు; పైలట్‌లో సెటప్ చేయడంలో సహాయం చేస్తాం.',q4:'నా కస్టమర్ల డేటా సురక్షితమా?',a4:'భారత DPDP చట్టాన్ని పాటిస్తాం: మీ సూచనల మేరకే పనిచేస్తాం, డేటా మేము మీ సెలూన్ కోసం నడిపే సురక్షిత డేటాబేస్‌లో, మీరు అడిగితే తొలగిస్తాం. అనుమతి ఇచ్చిన కస్టమర్లకే మెసేజ్‌లు.',q5:'మీరు కొత్తవారు. ఎందుకు నమ్మాలి?',a5:'న్యాయమైన ప్రశ్న. ఇంకా కస్టమర్లు లేరు, అందుకే మొదటి సెలూన్లకు ఉచిత పైలట్; ఉపయోగపడకపోతే ఏమీ చెల్లించనక్కర్లేదు. ఎప్పుడైనా ఆపవచ్చు.',
fo_h:'"మా ఇరుగుపొరుగు దుకాణాలకు ఉండాలనుకున్న టూల్స్ నేను తయారు చేస్తాను."',fo_p:'అఖిల్ కనిగిచర్ల, వ్యవస్థాపకుడు. Kalpa Labs పేరు కల్పవృక్షం నుంచి వచ్చింది: ఒక చెట్టు, ఏడు కొమ్మలు, ప్రతి కొమ్మ రోజువారీ పనికి ఒక చిన్న టూల్. హైదరాబాద్‌లో AI టీమ్‌తో నడిచే ఏకవ్యక్తి సంస్థ. లాంచ్‌ను ఫాలో అవ్వండి, తర్వాత ఏం తయారు చేయాలో చెప్పండి.',
ft0:'ఒక చెట్టు, అనేక శాఖలు, అందరికీ పండ్లు',ft1:'హైదరాబాద్, తెలంగాణ · ఉద్యమ్ నమోదిత MSME (ప్రొప్రైటర్‌షిప్)',ft2:'దాచిన ఛార్జీలు లేవు. ఆదాయ హామీలు ఎప్పుడూ ఇవ్వం.',mb1:'AIతో చాట్ చేయండి',mb2:'ఉచిత సెలూన్ పైలట్'};
const EN={}; document.querySelectorAll('[data-i]').forEach(e=>{EN[e.dataset.i]=e.dataset.html?e.innerHTML:e.textContent;});
let lang='en'; try{lang=localStorage.getItem('kl-lang')||'en';}catch(e){}
function setLang(l){lang=l;document.documentElement.lang=l==='te'?'te':'en';document.body.className=l;
 document.querySelectorAll('[data-i]').forEach(e=>{const k=e.dataset.i;const v=(l==='te'?TE[k]:null)??EN[k];if(v==null)return;if(e.dataset.html)e.innerHTML=v;else e.textContent=v;});  // eng-audit: ok v comes only from this file's own EN/TE text (data-html elements), never from users
 document.querySelectorAll('.lang button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===l)));
 {const sb=document.getElementById('snd');if(sb){sb.setAttribute('aria-label',l==='te'?'ప్రకృతి శబ్దాలు':'Nature sounds');sb.title=l==='te'?'గాలి, పక్షుల శబ్దాలు':'Breeze and birds';}}
 try{localStorage.setItem('kl-lang',l);}catch(e){}
 renderProducts(); resetChat(); if(typeof renderTeam==='function')renderTeam(); closeTip();}
document.querySelectorAll('.lang button').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang)));

/* ---------- countdown ---------- */
function cd(){const d=t=>Math.max(0,Math.ceil((new Date(t)-Date.now())/864e5));
 document.getElementById('cd-pilot').textContent=d('2026-11-16T00:00:00+05:30');document.getElementById('cd-launch').textContent=d('2026-12-13T06:12:00+05:30');}
cd(); setInterval(cd,60000);

/* ---------- products ---------- */
const CHK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
const P=[
 {id:'botbhai',c:'--l1',name:'BotBhai',st:['Built · free pilots from 16 Nov','తయారైంది · 16 నవం నుంచి ఉచిత పైలట్లు'],stc:'--warn',
  for:['For salons, gyms and coaching centres','సెలూన్లు, జిమ్‌లు, కోచింగ్ సెంటర్ల కోసం'],
  pts:[['WhatsApp + website chat in 3 languages','3 భాషల్లో WhatsApp + వెబ్‌సైట్ చాట్'],['Bookings, 24 h and 2 h reminders','బుకింగ్స్, 24 గం, 2 గం రిమైండర్లు'],['Owner alerts and a one-tap shared inbox','యజమాని అలర్ట్స్, ఒక ట్యాప్ షేర్డ్ ఇన్‌బాక్స్']],
  price:['Free pilot, then ₹1,499/mo','ఉచిత పైలట్, తర్వాత ₹1,499/నెల'],cta:'#founding',art:'chat'},
 {id:'kits',c:'--l3',name:'Exam & Money Kits',st:['Built · on sale after payments are set up','తయారైంది · పేమెంట్ సెటప్ తర్వాత అమ్మకం'],stc:'--ok',
  for:['For GATE aspirants and salaried savers','GATE అభ్యర్థులు, జీతం పొందేవారి కోసం'],
  pts:[['GATE 2027 120-day tracker in Google Sheets','Google Sheetsలో GATE 2027 120 రోజుల ట్రాకర్'],['Tax regime + SIP goal planner FY 2026-27','పన్ను విధానం + SIP లక్ష్య ప్లానర్ 2026-27'],['GATE Study Coach skill pack for Claude','Claude కోసం GATE స్టడీ కోచ్ స్కిల్ ప్యాక్']],
  price:['₹199–499 · not on sale yet','₹199–499 · ఇంకా అమ్మకానికి లేదు'],cta:'#signup',art:'sheet'},
 {id:'deals',c:'--l5',name:'Telugu Deals',st:['Calculators built · channel coming','కాలిక్యులేటర్లు తయారు · ఛానల్ త్వరలో'],stc:'--warn',
  for:['For smart shoppers who read Telugu','తెలుగు చదివే తెలివైన కొనుగోలుదారుల కోసం'],
  pts:[['Checked deals on Telegram (channel coming soon)','టెలిగ్రామ్‌లో చెక్ చేసిన డీల్స్ (ఛానల్ త్వరలో)'],['Free tax, SIP, EMI calculators in Telugu','తెలుగులో ఉచిత పన్ను, SIP, EMI కాలిక్యులేటర్లు'],['Every affiliate link marked #ad','ప్రతి అఫిలియేట్ లింక్‌కి #ad గుర్తు']],
  price:['Free','ఉచితం'],cta:'#signup',art:'tag'},
 {id:'jobcard',c:'--l2',name:'Mobile App',st:['Idea stage','ఆలోచన దశ'],stc:'--l0',
  for:['Our own mobile app, coming next','మా సొంత మొబైల్ యాప్, త్వరలో'],
  pts:[['Akhil is choosing the idea now','అఖిల్ ఇప్పుడు ఆలోచనను ఎంచుకుంటున్నారు'],['Built on the same Kalpa AI team','అదే Kalpa AI టీమ్‌తో తయారు'],['Join the list to hear first','ముందుగా తెలుసుకోవడానికి లిస్ట్‌లో చేరండి']],
  price:['Not available yet','ఇంకా అందుబాటులో లేదు'],cta:'#signup',art:'card'},
 {id:'lifeboat',c:'--l4',name:'Tab Lifeboat',st:['In development','అభివృద్ధిలో ఉంది'],stc:'--l0',
  for:['For people with 100 browser tabs','100 బ్రౌజర్ ట్యాబ్స్ ఉండేవారి కోసం'],
  pts:[['Save and restore every tab, with groups','గ్రూప్‌లతో సహా ప్రతి ట్యాబ్ సేవ్, రీస్టోర్'],['Auto-saves every 5 minutes','ప్రతి 5 నిమిషాలకు ఆటో-సేవ్'],['Planned: import from OneTab','ప్లాన్: OneTab నుంచి దిగుమతి']],
  price:['Not available yet','ఇంకా అందుబాటులో లేదు'],cta:'#signup',art:'tabs'},
 {id:'ledger',c:'--l6',name:'Ledger Peaks',st:['Engine built · early access list','ఇంజిన్ తయారు · ముందస్తు జాబితా'],stc:'--l0',
  for:['For software teams using AI','AI వాడే సాఫ్ట్‌వేర్ టీమ్‌ల కోసం'],
  pts:[['Which customer is your AI bill eating?','మీ AI బిల్‌ను ఏ కస్టమర్ తింటున్నారు?'],['Rupee costs by feature and model','ఫీచర్, మోడల్ వారీగా రూపాయి ఖర్చు'],['DPDP readiness score','DPDP సంసిద్ధత స్కోర్']],
  price:['Early access','ముందస్తు ప్రవేశం'],cta:'#signup',art:'chart'}];
const ART={
 chat:'<svg viewBox="0 0 200 160"><rect x="20" y="16" width="120" height="34" rx="12" fill="#fff"/><rect x="60" y="62" width="120" height="34" rx="12" fill="#d9fdd3"/><rect x="20" y="108" width="100" height="34" rx="12" fill="#fff"/><g fill="#8a8fa8"><rect x="32" y="28" width="80" height="6" rx="3"/><rect x="72" y="74" width="90" height="6" rx="3"/><rect x="32" y="120" width="60" height="6" rx="3"/></g></svg>',
 sheet:'<svg viewBox="0 0 200 160"><rect x="24" y="18" width="152" height="124" rx="10" fill="#fff"/><g stroke="#cfd3e0"><path d="M24 48h152M24 78h152M24 108h152M74 18v124M124 18v124"/></g><rect x="80" y="54" width="38" height="18" rx="4" fill="#3B7A3A" opacity=".8"/><rect x="130" y="84" width="38" height="18" rx="4" fill="#C38E12" opacity=".8"/></svg>',
 tag:'<svg viewBox="0 0 200 160"><path d="M40 30h70l60 60-50 50-80-80z" fill="#fff"/><circle cx="62" cy="52" r="8" fill="#9C700E"/><text x="92" y="108" font-size="26" font-family="Georgia" fill="#8A4A28">-40%</text></svg>',
 card:'<svg viewBox="0 0 200 160"><rect x="44" y="14" width="112" height="132" rx="12" fill="#fff"/><circle cx="100" cy="50" r="18" fill="#2F6F78" opacity=".85"/><g fill="#8a8fa8"><rect x="62" y="82" width="76" height="6" rx="3"/><rect x="62" y="96" width="56" height="6" rx="3"/><rect x="62" y="110" width="66" height="6" rx="3"/></g></svg>',
 tabs:'<svg viewBox="0 0 200 160"><g fill="#fff"><rect x="20" y="30" width="50" height="22" rx="6"/><rect x="74" y="30" width="50" height="22" rx="6"/><rect x="128" y="30" width="50" height="22" rx="6"/><rect x="20" y="56" width="158" height="80" rx="8"/></g><path d="M60 110q40-40 80 0" stroke="#7A3F5E" stroke-width="6" fill="none"/></svg>',
 chart:'<svg viewBox="0 0 200 160"><rect x="20" y="18" width="160" height="124" rx="10" fill="#fff"/><g fill="#A8324F"><rect x="44" y="90" width="18" height="36" rx="4"/><rect x="74" y="66" width="18" height="60" rx="4"/><rect x="104" y="46" width="18" height="80" rx="4"/><rect x="134" y="76" width="18" height="50" rx="4" opacity=".55"/></g></svg>'};
let cur='botbhai';
function renderProducts(){const L=lang==='te'?1:0; const tabs=document.getElementById('ptabs'), v=document.getElementById('pview');
 tabs.replaceChildren(...P.map(p=>{const b=document.createElement('button');b.type='button';b.role='tab';b.setAttribute('aria-selected',String(p.id===cur));b.style.setProperty('--c','var('+p.c+')');b.append(document.createElement('i'),document.createTextNode(p.name));b.addEventListener('click',()=>{cur=p.id;renderProducts();});return b;}));
 const p=P.find(x=>x.id===cur); v.style.setProperty('--c','var('+p.c+')');
 v.innerHTML='<div class="txt"><span class="pill" style="--pc:var('+p.stc+')"><i></i><span class="st"></span></span><h3></h3><p class="for"></p><ul>'+p.pts.map(()=>'<li>'+CHK+'<span></span></li>').join('')+'</ul><div class="price"></div><a class="btn btn-acc" style="width:max-content"></a></div><div class="art">'+ART[p.art]+'</div>';
 v.querySelector('.st').textContent=p.st[L]; v.querySelector('h3').textContent=p.name; v.querySelector('.for').textContent=p.for[L];
 v.querySelectorAll('li span').forEach((s,i)=>s.textContent=p.pts[i][L]); v.querySelector('.price').textContent=p.price[L];
 const a=v.querySelector('a'); a.href=p.cta; a.textContent=L?'ఆసక్తి ఉంది':'I\'m interested'; a.addEventListener('click',()=>{const sel=document.getElementById('interest'); sel.value=p.id==='botbhai'?'salon':p.id==='kits'?'kits':'other';});}

/* ---------- live AI chat (Netlify function netlify/functions/chat.mjs, A145; was n8n until the trial ended) ---------- */
const CHAT_URL='/api/chat'; const HIST=[];
const STARTERS={
 en:['How does BotBhai help my salon?','Is the pilot really free?','Tell me about the ₹299 workshop','Please call me back'],
 te:['BotBhai నా సెలూన్‌కి ఎలా సహాయం చేస్తుంది?','పైలట్ నిజంగా ఉచితమా?','₹299 వర్క్‌షాప్ గురించి చెప్పండి','నాకు కాల్ చేయండి']};
const HELLO={en:'Namaste! I\'m Kalpa Bhai, Kalpa Labs\' AI assistant (yes, a bot 🙂). Ask me anything in Telugu, Hindi or English, or leave your number and Akhil will call you.',
 te:'నమస్తే! నేను Kalpa Bhai, Kalpa Labs AI సహాయకుడిని (అవును, బాట్‌నే 🙂). తెలుగు, హిందీ, ఇంగ్లీష్, Tenglish లేదా Hinglish లో ఏదైనా అడగండి, లేదా మీ నంబర్ ఇవ్వండి, అఖిల్ కాల్ చేస్తారు.'};
const OFFLINE={en:'I can\'t reach my brain right now 😅. Please use the form below and Akhil will WhatsApp you.',
 te:'ప్రస్తుతం నేను కనెక్ట్ కాలేకపోతున్నాను 😅. కింది ఫారమ్ నింపండి, అఖిల్ WhatsAppలో జవాబిస్తారు.'};
const chat=document.getElementById('chat'), chips=document.getElementById('chips'), askf=document.getElementById('ask'), askin=document.getElementById('askin');
let busy=false, started=false, talked=false;
let sid; try{sid=sessionStorage.getItem('kl-sid');}catch(e){}
if(!sid){sid='web-'+Date.now().toString(36)+Math.random().toString(36).slice(2,8);try{sessionStorage.setItem('kl-sid',sid);}catch(e){}}
const now=()=>new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true,timeZone:'Asia/Kolkata'});
function bubble(t,side){const m=document.createElement('div');m.className='msg '+side;m.textContent=t;const tm=document.createElement('time');tm.textContent=now()+(side==='out'?' ✓✓':'');m.append(tm);chat.append(m);chat.scrollTop=chat.scrollHeight;return m;}
function typing(){const ty=document.createElement('div');ty.className='typing';ty.setAttribute('aria-label','typing');ty.innerHTML='<i></i><i></i><i></i>';chat.append(ty);chat.scrollTop=chat.scrollHeight;return ty;}
function clean(s){return String(s||'').replace(/\*\*(.+?)\*\*/g,'$1').replace(/^#+\s*/gm,'').replace(/\u2011/g,'-').replace(/\u202f/g,' ').trim();}
async function send(text){
 text=String(text||'').trim(); if(!text||busy) return; busy=true; setBusy();
 talked=true; bubble(text,'out'); const ty=typing(); const t0=Date.now();
 let reply='';
 try{
  const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(),30000);
  const r=await fetch(CHAT_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:sid,chatInput:text,history:HIST.slice(-8)}),signal:ctrl.signal});
  clearTimeout(to); if(!r.ok) throw new Error(r.status);
  const d=await r.json(); reply=clean(Array.isArray(d)?d[0]?.output:(d.output??d.text));
  if(!reply) throw new Error('empty');
  HIST.push({role:'user',content:text},{role:'assistant',content:reply});
  document.getElementById('livedot').style.background='#7CFC9A';
 }catch(e){reply=OFFLINE[lang];document.getElementById('livedot').style.background='#E8B64A';}
 const wait=Math.max(0,(reduce?0:600)-(Date.now()-t0)); await new Promise(r=>setTimeout(r,wait));
 ty.remove(); bubble(reply,'in'); busy=false; setBusy(); askin.focus({preventScroll:true});
}
function setBusy(){askf.querySelector('button').disabled=busy; chips.querySelectorAll('button').forEach(b=>b.disabled=busy);}
function renderChips(){chips.replaceChildren(...STARTERS[lang].map(q=>{const b=document.createElement('button');b.type='button';b.textContent=q;b.disabled=busy;b.addEventListener('click',()=>send(q));return b;}));}
askf.addEventListener('submit',e=>{e.preventDefault();const v=askin.value;askin.value='';send(v);});
function resetChat(){renderChips(); askin.placeholder=lang==='te'?'ఏ భాషలోనైనా టైప్ చేయండి…':'Type in any language…';
 if(!started||!talked){started=true;chat.replaceChildren();const h=typing();setTimeout(()=>{h.remove();bubble(HELLO[lang],'in');},reduce?0:700);}}

/* ---------- team ---------- */
const TEAM=[['Kalpa','Chief of staff','#2F6A3A',['Plans the day and hands out the work','రోజు ప్లాన్ చేసి పని పంచుతుంది']],['Chitti','WhatsApp helper','#25D366',['Answers customers on WhatsApp','WhatsAppలో కస్టమర్లకు జవాబిస్తుంది']],['Scout','Finds customers','#8A4A28',['Builds lead lists from allowed public sources only','అనుమతి ఉన్న పబ్లిక్ సోర్సుల నుంచే లీడ్ జాబితాలు']],['Kavi','Writer','#3B7A3A',['Writes posts and messages for Akhil to approve','అఖిల్ ఆమోదం కోసం పోస్టులు, మెసేజ్‌లు రాస్తుంది']],['Adi','Ads & copy','#9C700E',['Drafts ads and headlines','యాడ్స్, హెడ్‌లైన్లు డ్రాఫ్ట్ చేస్తుంది']],['Lens','Brand look','#7A3F5E',['Keeps every page on brand','ప్రతి పేజీ బ్రాండ్‌కు తగ్గట్టు ఉండేలా చూస్తుంది']],['Pixel','Designer','#5E9E4C',['Makes images and layouts','ఇమేజ్‌లు, లేఅవుట్లు తయారు చేస్తుంది']],['Forge','Engineer','#2F6F78',['Writes code and runs the tests','కోడ్ రాసి టెస్ట్‌లు నడుపుతుంది']],['Vigil','Fact-checker','#A8324F',['Checks every fact twice','ప్రతి విషయాన్ని రెండుసార్లు సరిచూస్తుంది']],['Guard','Risk checks','#66655A',['Checks privacy and legal rules','ప్రైవసీ, చట్ట నియమాలు చెక్ చేస్తుంది']],['Deal','Deals hunter','#C38E12',['Verifies deals before they are shared','డీల్స్ పంచుకునే ముందు సరిచూస్తుంది']],['Echo','Librarian','#2F6A3A',['Keeps notes so nothing is forgotten','ఏదీ మర్చిపోకుండా నోట్స్ ఉంచుతుంది']]];
const row=document.getElementById('teamrow');
function renderTeam(){const L=lang==='te'?1:0;
 row.replaceChildren(...TEAM.map(([n,r,c,say],i)=>{const d=document.createElement('button');d.type='button';d.className='card mate';d.setAttribute('aria-expanded','false');
  const s=document.createElementNS(NS,'svg');s.setAttribute('viewBox','-24 -82 48 86');s.setAttribute('aria-hidden','true');const g=el('g',{style:'animation-delay:'+(i*.13)+'s'},s);bot(g,c,i===0?'waving':'working');
  const b=document.createElement('b');b.textContent=n;const sp=document.createElement('span');sp.textContent=r;const sy=document.createElement('span');sy.className='say';sy.hidden=true;sy.textContent=say[L];
  d.append(s,b,sp,sy);
  d.addEventListener('click',()=>{const open=d.getAttribute('aria-expanded')!=='true';d.setAttribute('aria-expanded',String(open));sy.hidden=!open;const m=s.querySelector('g.working,g.waving');if(m&&i!==0)m.setAttribute('class',open?'waving':'working');});
  return d;}));}

/* ---------- form ---------- */
document.querySelectorAll('[data-pick]').forEach(a=>a.addEventListener('click',()=>{document.getElementById('interest').value=a.dataset.pick;}));
const form=document.querySelector('form.signup'), msg=document.getElementById('formmsg');
form.addEventListener('submit',async e=>{e.preventDefault();if(!form.reportValidity())return;
 const fd=new FormData(form); if(fd.get('company')) return; const data=new URLSearchParams(fd).toString();
 const btn=form.querySelector('button[type=submit]'); btn.disabled=true;
 let ok=false;
 try{const r=await fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:data});ok=ok||r.ok;}catch(e){}
 btn.disabled=false;
 try{ if(!ok) throw 0;
  msg.style.color='var(--ok)';msg.textContent=lang==='te'?'ధన్యవాదాలు! అఖిల్ త్వరలో WhatsAppలో జవాబిస్తారు.':'Thank you! Akhil will reply on WhatsApp soon.';form.reset();}
 catch(err){msg.style.color='var(--madder)';msg.textContent=lang==='te'?'పంపడం కాలేదు. కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.':'That did not send. Please try again in a minute.';}});

/* ---------- the living Kalpa tree: branches = products, robots = our AI agents at work ---------- */
document.documentElement.classList.add('js');
const tree=document.getElementById('tree'), tback=document.getElementById('tback'), tfront=document.getElementById('tfront'), tbox=document.getElementById('treebox');
const WIND={v:16,gust:0,shake:0};
let seed=27; const rnd=()=>{seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
const BR=[ // [path, width, world id, name, world colour]
 ['M290 430C240 410 190 400 120 380',15,'botbhai','BotBhai','--l1'],
 ['M310 420C360 400 420 395 485 370',15,'jobcard','Mobile App','--l2'],
 ['M288 360C240 330 190 300 140 250',12,'kits','Exam & Money Kits','--l3'],
 ['M312 350C360 320 410 290 460 240',12,'lifeboat','Tab Lifeboat','--l4'],
 ['M292 300C260 260 230 210 200 150',10,'deals','Telugu Deals','--l5'],
 ['M308 295C340 250 370 200 400 145',10,'ledger','Ledger Peaks','--l6'],
 ['M300 265C300 210 300 150 300 92',11,'trading','Trading Lab','--l0']];
const SHORT={kits:'Kits',deals:'Deals',ledger:'Ledger'};
const LEAF='M0 0C6-7 16-7 24 0C16 7 6 7 0 0Z';
function cluster(par,cx,cy,R,n){
 for(let k=0;k<4;k++)el('circle',{class:'blob',cx:cx+(rnd()-.5)*R*.9,cy:cy+(rnd()-.5)*R*.6,r:R*(.42+.2*rnd()),fill:'var(--tl'+(1+(k%2))+')',style:'animation-delay:'+(1.2+Math.hypot(cx-300,cy-560)/600*1.2).toFixed(2)+'s'},par);
 for(let k=0;k<n;k++){const a=rnd()*6.283,rr=R*Math.sqrt(rnd()),x=cx+Math.cos(a)*rr,y=cy+Math.sin(a)*rr*.8;
  const g=el('g',{transform:`translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${(a*57.3+(rnd()-.5)*70).toFixed(0)}) scale(${(.7+rnd()*.6).toFixed(2)})`},par);
  const d=(1.1+Math.hypot(x-300,y-560)/600*1.2+rnd()*.3).toFixed(2);
  el('path',{d:LEAF,class:'lf',fill:'var(--tl'+(1+Math.floor(rnd()*5))+')',style:'animation-delay:'+d+'s'},g);}}
const sway=[]; // groups that move in the wind: [elements, baseX, baseY, amp, phase]
const crown=el('g',{},tback); cluster(crown,300,190,100,85); cluster(crown,300,275,82,55); sway.push([[crown],300,320,.6,0]);
const fruits=[], paths=[];
BR.forEach(([d,w,id,name,col],i)=>{
 const back=el('g',{},tback), front=el('g',{},tfront);
 const p=el('path',{d,class:'br','stroke-width':w},front); const L=p.getTotalLength(); p.style.setProperty('--len',L.toFixed(0)); p.style.animationDelay=(.75+i*.09)+'s'; paths.push(p);
 const e=p.getPointAtLength(L), m=p.getPointAtLength(L*.55);
 cluster(back,e.x,e.y-6,i===6?58:i<2?60:54,i<2?52:46); cluster(back,m.x,m.y-14,34,20);
 for(let k=0;k<5;k++){const q=p.getPointAtLength(L*(.45+k*.12));const g=el('g',{transform:`translate(${q.x.toFixed(1)} ${q.y.toFixed(1)}) rotate(${(k%2?-60:-120)+rnd()*30}) scale(.8)`},front);el('path',{d:LEAF,class:'lf',fill:'var(--tl'+(3+k%3)+')',style:'animation-delay:'+(1.5+i*.1+k*.06).toFixed(2)+'s'},g);}
 const fx=e.x, fy=e.y+(i===6?-6:20);
 const f=el('g',{class:'fruit',tabindex:'0',role:'button','aria-label':name,style:'animation-delay:'+(2.3+i*.12)+'s'},front);
 if(i!==6)el('path',{d:`M${e.x} ${e.y}L${fx} ${fy-12}`,stroke:'var(--bark)','stroke-width':2.5},f);
 el('circle',{class:'halo',cx:fx,cy:fy,r:24},f);
 const fb=el('g',{class:'fb'},f);
 el('circle',{class:'ring',cx:fx,cy:fy,r:15,fill:'var(--gold)',stroke:'var('+col+')','stroke-width':3.5},fb);
 el('circle',{cx:fx-5,cy:fy-5,r:4,fill:'#fff',opacity:.55},fb);
 el('path',{d:LEAF,fill:'var(--tl3)',transform:`translate(${fx} ${fy-14}) rotate(-35) scale(.55)`},fb);
 const t=el('text',{class:'flabel',x:fx,y:fy+(i===6?-26:38)},f); t.textContent=SHORT[id]||name;
 f.addEventListener('click',ev=>{ev.stopPropagation();openTip(i);});
 f.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();openTip(i);}});
 fruits.push(f); sway.push([[back,front],+d.split(' ')[0].slice(1),+d.split(' ')[1].split('C')[0],1.1+(i%3)*.3,i*1.3]);
});
// grass tufts along the ground
const grassEls=[];for(let k=0;k<30;k++){const x=(60+k*16+rnd()*8).toFixed(0),h=(8+rnd()*12).toFixed(0);const g=el('path',{class:'grass','data-x':x,d:`M${x} 568q-3-${h} -6-${+h+3}M${x} 568q1-${+h+2} 4-${+h+4}`},document.getElementById('grass'));grassEls.push(g);}

/* product tip */
const tip=document.getElementById('tip'); let tipFor=-1;
function closeTip(){if(!tip)return;tip.hidden=true;fruits.forEach(f=>f.classList.remove('on'));tipFor=-1;}
function openTip(i){
 if(tipFor===i){closeTip();return;} closeTip(); tipFor=i; const [, , id, name, col]=BR[i]; const L=lang==='te'?1:0; const p=P.find(x=>x.id===id);
 tip.style.setProperty('--c','var('+col+')'); document.getElementById('tipname').textContent=name;
 const st=document.getElementById('tipst'); st.style.setProperty('--pc','var('+(p?p.stc:'--l0')+')');
 st.querySelector('span').textContent=p?p.st[L]:(L?'పరిశోధన మాత్రమే · పేపర్ ట్రేడింగ్':'Research only · paper trading');
 document.getElementById('tipfor').textContent=p?p.for[L]:(L?'మా సొంత అభ్యాసం కోసం. టిప్స్ ఇవ్వం, నిజమైన డబ్బుతో ట్రేడ్ చేయం.':'For our own learning. We never give tips or trade real money.');
 const go=document.getElementById('tipgo'); go.hidden=!p; go.onclick=()=>{cur=id;renderProducts();closeTip();};
 fruits[i].classList.add('on'); tip.hidden=false;
 const fr=fruits[i].querySelector('.ring').getBoundingClientRect(), br=tbox.getBoundingClientRect();
 const w=tip.offsetWidth, h=tip.offsetHeight; let x=fr.left-br.left+fr.width/2-w/2, y=fr.bottom-br.top+10;
 x=Math.max(0,Math.min(br.width-w,x)); if(y+h>br.height) y=Math.max(0,fr.top-br.top-h-10);
 tip.style.left=x+'px'; tip.style.top=y+'px'; tip.querySelector('.x').focus({preventScroll:true});}
tip.querySelector('.x').addEventListener('click',closeTip);
document.addEventListener('click',e=>{if(!tip.hidden&&!tip.contains(e.target))closeTip();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!tip.hidden){const i=tipFor;closeTip();fruits[i]&&fruits[i].focus();}});

/* robots walking the branches, each showing what it is doing */
const WALK=[ // branch, name, colour, tasks [en, te]
 [2,'Chitti','#25D366',[['Replying to a customer in Telugu','కస్టమర్‌కు తెలుగులో జవాబిస్తోంది'],['Booking a 6 PM slot','సాయంత్రం 6 గంటల స్లాట్ బుక్ చేస్తోంది']]],
 [3,'Forge','#2F6F78',[['Running 120 tests before a release','రిలీజ్ ముందు 120 టెస్ట్‌లు నడుపుతోంది'],['Fixing a bug a user reported','యూజర్ చెప్పిన బగ్ సరిచేస్తోంది']]],
 [4,'Kavi','#3B7A3A',[['Writing a Telugu post for Akhil to approve','అఖిల్ ఆమోదం కోసం తెలుగు పోస్ట్ రాస్తోంది'],['Translating a reply into Hindi','జవాబును హిందీలోకి అనువదిస్తోంది']]],
 [5,'Vigil','#A8324F',[['Checking a price twice','ధరను రెండుసార్లు సరిచూస్తోంది'],['Confirming a rule on the official site','అధికారిక సైట్‌లో నియమాన్ని నిర్ధారిస్తోంది']]]];
const bubbles=document.getElementById('bubbles');
const walkers=WALK.map(([b,name,col,tasks],k)=>{
 const front=tfront.children[b], p=paths[b], L=p.getTotalLength();
 const g=el('g',{class:'walker'},front); const inner=el('g',{},g); bot(inner,col,'working');
 const bub=document.createElement('div'); bub.className='bub'; bub.style.setProperty('--c',col); bubbles.append(bub);
 return {g,p,L,t:.42+k*.08,v:(k%2?-1:1)*.045,name,tasks,n:k,bub,on:false};});
function placeBot(w,time){
 const pt=w.p.getPointAtLength(w.L*w.t), a=w.p.getPointAtLength(Math.min(w.L,w.L*w.t+1)), dir=a.x>=pt.x?1:-1, face=w.v*dir>0?1:-1;
 const bob=reduce?0:Math.abs(Math.sin(time*6+w.n))*1.6;
 w.g.setAttribute('transform',`translate(${pt.x.toFixed(1)} ${(pt.y-5-bob).toFixed(1)}) scale(${.62*face} .62)`);}
function placeBubble(w){
 if(!w.on)return; const m=w.g.getScreenCTM(); if(!m)return; const head=new DOMPoint(0,-84).matrixTransform(m), br=tbox.getBoundingClientRect();
 const bw=w.bub.offsetWidth; let x=head.x-br.left-bw/2; x=Math.max(2,Math.min(br.width-bw-2,x));
 w.bub.style.transform=`translate(${x.toFixed(0)}px,${(head.y-br.top-w.bub.offsetHeight-8).toFixed(0)}px)`;}
let bi=-1, beat=0;
function nextBubble(){
 const single=tbox.offsetWidth<520; bi=(bi+1)%walkers.length; const w=walkers[bi];
 if(single)walkers.forEach(o=>{o.bub.classList.remove('on');o.on=false;});
 const [en,te]=w.tasks[beat++%w.tasks.length===0?0:1]; w.bub.replaceChildren(Object.assign(document.createElement('b'),{textContent:w.name}),document.createTextNode(lang==='te'?te:en));
 w.on=true; placeBubble(w); w.bub.classList.add('on'); clearTimeout(w.to); w.to=setTimeout(()=>{w.bub.classList.remove('on');setTimeout(()=>{if(!w.bub.classList.contains('on'))w.on=false;},400);},single?2900:4800);}

/* falling leaves (and fireflies at night) */
const fall=document.getElementById('falling');
for(let k=0;k<10;k++){const i=document.createElement('i');i.className='ff';i.style.cssText=`left:${(50+rnd()*48).toFixed(0)}%;top:${(15+rnd()*70).toFixed(0)}%;--d:${(-rnd()*4).toFixed(1)}s`;fall.append(i);}

/* one animation loop, paused when the tree is off screen or the tab is hidden */
let visible=true, last=0;
new IntersectionObserver(es=>{visible=es[0].isIntersecting;},{threshold:0}).observe(tbox);
function frame(ms){
 const time=ms/1000, dt=Math.min(.05,time-(last||time)); last=time;
 if(visible&&!document.hidden){
  if(!reduce){sway.forEach(([els,x,y,amp,ph])=>{const a=(Math.sin(time*(.9+WIND.v/90)+ph)*amp*(1+WIND.v/45)+(WIND.v-16)*.03*amp+Math.sin(time*19+ph)*WIND.shake*3.2).toFixed(2);els.forEach(g=>g.setAttribute('transform',`rotate(${a} ${x} ${y})`));});
   grassEls.forEach((g,k)=>g.setAttribute('transform',`rotate(${(Math.sin(time*2.2+k*.5)*4+WIND.v*.18).toFixed(1)} ${g.dataset.x} 568)`));
   walkers.forEach(w=>{w.t+=w.v*dt;if(w.t>.86||w.t<.34){w.v=-w.v;w.t=Math.max(.34,Math.min(.86,w.t));}});}
  walkers.forEach(w=>{placeBot(w,time);placeBubble(w);});}
 requestAnimationFrame(frame);}
walkers.forEach(w=>placeBot(w,0));
requestAnimationFrame(frame);
setTimeout(()=>tree.classList.add('grown'),reduce?0:2900);
setTimeout(()=>{nextBubble();setInterval(()=>{if(visible&&!document.hidden)nextBubble();},reduce?4500:2600);},reduce?300:3300);

/* the "how it works" vine grows as you read */
const steps=document.querySelector('.steps'), vine=steps.querySelector('.vine i'), stepEls=[...steps.querySelectorAll('.step')];
function grow(){const r=steps.getBoundingClientRect(), mid=innerHeight*.6; const p=Math.max(0,Math.min(1,(mid-r.top)/r.height));
 vine.style.setProperty('--p',p.toFixed(3)); stepEls.forEach(s=>s.classList.toggle('lit',s.getBoundingClientRect().top+20<mid));}
if(!reduce){addEventListener('scroll',grow,{passive:true});grow();}else{stepEls.forEach(s=>s.classList.add('lit'));}


/* ---------- nature sounds (off until tapped; browsers never autoplay): breeze that follows the wind + birdsong.
   Made live with the Web Audio API, so there are no audio files and no licences. ---------- */
const SND=(function(){
 const btn=document.getElementById('snd'); if(!btn||!(window.AudioContext||window.webkitAudioContext)){if(btn)btn.hidden=true;return {on:false,chirp(){},tick(){}};}
 let ctx=null,windG,bp,rust,on=false,next=0;
 function build(){ctx=new (window.AudioContext||window.webkitAudioContext)();
  const len=ctx.sampleRate*3,buf=ctx.createBuffer(1,len,ctx.sampleRate),d=buf.getChannelData(0);let b=0;
  for(let i=0;i<len;i++){b=(b+.02*(Math.random()*2-1))/1.02;d[i]=b*3.5;} // soft brown noise = air
  const src=ctx.createBufferSource();src.buffer=buf;src.loop=true;
  bp=ctx.createBiquadFilter();bp.type='bandpass';bp.frequency.value=420;bp.Q.value=.6;
  windG=ctx.createGain();windG.gain.value=0;src.connect(bp).connect(windG).connect(ctx.destination);
  const hb=ctx.createBufferSource();hb.buffer=buf;hb.loop=true;hb.playbackRate.value=1.7; // leaves rustling on gusts
  const hp=ctx.createBiquadFilter();hp.type='highpass';hp.frequency.value=2600;rust=ctx.createGain();rust.gain.value=0;
  hb.connect(hp).connect(rust).connect(ctx.destination);src.start();hb.start();}
 function chirp(pan){if(!on||!ctx)return;const t0=ctx.currentTime+.02,notes=2+(Math.random()*3|0),f0=2600+Math.random()*1500;
  const p=ctx.createStereoPanner?ctx.createStereoPanner():null;if(p)p.pan.value=Math.max(-1,Math.min(1,pan||0));
  for(let i=0;i<notes;i++){const t=t0+i*(.09+Math.random()*.07),o=ctx.createOscillator(),g=ctx.createGain(),f=f0*(1+(Math.random()-.5)*.15);
   o.type='sine';o.frequency.setValueAtTime(f,t);o.frequency.exponentialRampToValueAtTime(f*1.4,t+.045);o.frequency.exponentialRampToValueAtTime(f*.9,t+.09);
   g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.05,t+.012);g.gain.exponentialRampToValueAtTime(.0001,t+.1);
   o.connect(g);(p?g.connect(p):g).connect(ctx.destination);if(p&&i===0)p.connect(ctx.destination);o.start(t);o.stop(t+.12);}}
 function set(v){on=v;btn.setAttribute('aria-pressed',String(v));
  if(v){if(!ctx)build();ctx.resume();next=performance.now()+1500;chirp(0);}else if(ctx)ctx.suspend();}
 btn.addEventListener('click',()=>set(!on));
 document.addEventListener('visibilitychange',()=>{if(ctx&&on){document.hidden?ctx.suspend():ctx.resume();}});
 return {get on(){return on},chirp,
  tick(now){if(!on||!ctx)return;const v=Math.max(0,WIND.v);
   windG.gain.setTargetAtTime(Math.min(.16,.035+v/700),ctx.currentTime,.4);bp.frequency.setTargetAtTime(320+v*4,ctx.currentTime,.5);
   rust.gain.setTargetAtTime(Math.min(.05,Math.max(0,v-30)/1500),ctx.currentTime,.3);
   if(now>next){chirp(Math.random()*1.6-.8);next=now+5000+Math.random()*9000;}}};
})();
(function soundClock(){function f(now){SND.tick(now);requestAnimationFrame(f);}requestAnimationFrame(f);})();

/* ---------- wind: a gust of leaves when the site opens, leaves drifting down the whole page,
   your finger or mouse pushes them, tap the tree to shake it, tap the sky for a gust ---------- */
(function windLayer(){
 if(reduce) return;
 const cv=document.createElement('canvas'); cv.id='wind'; cv.setAttribute('aria-hidden','true'); document.body.append(cv);
 const cx=cv.getContext('2d'); let W=0,H=0,dpr=1;
 function size(){dpr=Math.min(2,devicePixelRatio||1);W=innerWidth;H=innerHeight;cv.width=W*dpr;cv.height=H*dpr;cx.setTransform(dpr,0,0,dpr,0,0);}
 size(); addEventListener('resize',size);
 let COLS=[]; function cols(){const cs=getComputedStyle(document.documentElement);COLS=['--tl1','--tl2','--tl3','--tl4','--tl5','--gold'].map(v=>cs.getPropertyValue(v).trim()||'#5E9E4C');}
 cols(); matchMedia('(prefers-color-scheme: dark)').addEventListener('change',cols);
 const small=W<700, KEEP=small?12:22; const L=[];
 function leaf(x,y,vx,vy,keep){L.push({x,y,vx,vy,r:Math.random()*6.28,vr:(Math.random()-.5)*4,f:Math.random()*6.28,fs:2+Math.random()*4,s:(small?.8:1)*(7+Math.random()*7),c:COLS[(Math.random()*(Math.random()<.12?6:5))|0],keep,ph:Math.random()*6.28});}
 // the opening gust: leaves sweep in from the left and the top
 const N=small?60:110; for(let i=0;i<N;i++){const fromTop=Math.random()<.45;
  leaf(fromTop?Math.random()*W*.7:-40-Math.random()*W*.5, fromTop?-30-Math.random()*H*.6:Math.random()*H*.8, 260+Math.random()*260, 20+Math.random()*80, false);}
 for(let i=0;i<KEEP;i++) leaf(Math.random()*W,-20-Math.random()*H,20,40,true);
 // one or two small birds cross the sky now and then; tap one and it sings (when sounds are on) and speeds away
 const B=[]; let nextBird=performance.now()+2500;
 function spawnBirds(){const ltr=Math.random()<.6,n=Math.random()<.45?2:1,y=H*(.08+Math.random()*.3),sp=(small?55:75)+Math.random()*35;
  for(let i=0;i<n;i++)B.push({x:ltr?-30-i*46:W+30+i*46,y:y+i*(14+Math.random()*10),vx:ltr?sp:-sp,s:(small?6:8)+Math.random()*3,ph:Math.random()*6.28,glide:0,bob:Math.random()*6.28});
  SND.chirp(ltr?-.7:.7);}
 function drawBird(b,t){const flap=b.glide>0?.25:Math.sin(t*11+b.ph),s=b.s,w=s*(.15+.55*(flap*.5+.5));
  cx.save();cx.translate(b.x,b.y);if(b.vx<0)cx.scale(-1,1);cx.strokeStyle=BIRDC;cx.lineWidth=1.7;cx.lineCap='round';cx.lineJoin='round';
  cx.beginPath();cx.moveTo(-s,-w);cx.quadraticCurveTo(-s*.45,-w*.2,0,0);cx.quadraticCurveTo(s*.45,-w*.2,s,-w);cx.stroke();
  cx.fillStyle=BIRDC;cx.beginPath();cx.ellipse(0,.6,1.8,1.2,0,0,6.28);cx.fill();cx.restore();}
 let BIRDC='#2a3326'; function birdCol(){BIRDC=getComputedStyle(document.documentElement).getPropertyValue('--bird').trim()||BIRDC;} birdCol();
 document.querySelector('.hero').addEventListener('pointerdown',e=>{for(const b of B){if(Math.hypot(e.clientX-b.x,e.clientY-b.y)<34){b.vx*=2.2;b.glide=0;SND.chirp(b.x/W*2-1);}}});
 WIND.gust=280; let px=-1,py=-1,pvx=0,pvy=0,lastP=0,trail=0;
 addEventListener('pointermove',e=>{const t=performance.now(),dt=Math.max(8,t-lastP);if(px>=0){const ix=(e.clientX-px)/dt*1000,iy=(e.clientY-py)/dt*1000;pvx=pvx*.6+ix*.4;pvy=pvy*.6+iy*.4;
   trail+=Math.hypot(e.clientX-px,e.clientY-py); if(trail>140&&e.target.closest&&e.target.closest('.hero')&&L.length<140){trail=0;leaf(e.clientX,e.clientY,pvx*.3,pvy*.3,false);}}
  px=e.clientX;py=e.clientY;lastP=t;},{passive:true});
 // tap the tree (not a fruit): it shakes and showers leaves; tap the sky: a gust
 tree.addEventListener('pointerdown',e=>{if(e.target.closest('.fruit'))return;WIND.shake=1;const r=tbox.getBoundingClientRect();
  for(let i=0;i<(small?16:26);i++)leaf(r.left+r.width*(.2+Math.random()*.6),r.top+r.height*(.12+Math.random()*.45),(Math.random()-.5)*220,-60+Math.random()*120,false);});
 document.querySelector('.hero').addEventListener('pointerdown',e=>{if(e.target.closest('a,button,#tree,input,.tip'))return;WIND.gust=Math.max(WIND.gust,200);
  for(let i=0;i<10;i++){const a=Math.random()*6.28;leaf(e.clientX,e.clientY,Math.cos(a)*180+120,Math.sin(a)*140,false);}});
 function draw(p){cx.save();cx.translate(p.x,p.y);cx.rotate(p.r);cx.scale(Math.max(.18,Math.abs(Math.cos(p.f))),1);const s=p.s;
  cx.fillStyle=p.c;cx.beginPath();cx.moveTo(-s,0);cx.bezierCurveTo(-s*.4,-s*.62,s*.5,-s*.55,s,0);cx.bezierCurveTo(s*.5,s*.55,-s*.4,s*.62,-s,0);cx.fill();
  if(Math.abs(Math.cos(p.f))>.35){cx.strokeStyle='rgba(0,0,0,.16)';cx.lineWidth=1;cx.beginPath();cx.moveTo(-s,0);cx.lineTo(s*.85,0);cx.stroke();}cx.restore();}
 let last=performance.now();
 function tick(now){const dt=Math.min(.05,(now-last)/1000);last=now;const t=now/1000;
  WIND.gust*=Math.pow(.42,dt); WIND.shake*=Math.pow(.25,dt); pvx*=Math.pow(.05,dt); pvy*=Math.pow(.05,dt);
  WIND.v=16+12*Math.sin(t*.45)+6*Math.sin(t*1.3)+WIND.gust;
  if(!document.hidden){cx.clearRect(0,0,W,H);
   for(let i=L.length-1;i>=0;i--){const p=L[i];let wx=WIND.v,wy=0;
    if(px>=0){const dx=p.x-px,dy=p.y-py,d=Math.hypot(dx,dy);if(d<150){const k=(1-d/150);wx+=pvx*k*.9+dx/(d+1)*90*k*Math.min(1,Math.hypot(pvx,pvy)/300);wy+=pvy*k*.9+dy/(d+1)*90*k*Math.min(1,Math.hypot(pvx,pvy)/300);}}
    p.vx+=(wx-p.vx)*Math.min(1,dt*1.6); p.vy+=((34+p.s*2.2+wy)-p.vy)*Math.min(1,dt*1.2);
    p.x+=(p.vx+Math.sin(t*1.7+p.ph)*26)*dt; p.y+=(p.vy+Math.cos(t*2.3+p.ph)*14)*dt; p.r+=(p.vr+p.vx*.004)*dt; p.f+=p.fs*dt;
    if(p.y>H+30||p.x>W+60||p.x<-80&&p.vx<0){ if(p.keep){p.x=Math.random()*W*1.1-W*.15;p.y=-20-Math.random()*60;p.vx=WIND.v;} else {L.splice(i,1);continue;} }
    draw(p);}
   if(now>nextBird&&!B.length){spawnBirds();nextBird=now+9000+Math.random()*12000;}
   for(let i=B.length-1;i>=0;i--){const b=B[i];b.bob+=dt*2;if(b.glide>0)b.glide-=dt;else if(Math.random()<dt*.35)b.glide=.6+Math.random()*1.2;
    b.x+=(b.vx+WIND.v*.15)*dt;b.y+=Math.sin(b.bob)*8*dt-(b.glide>0?-4:2)*dt;
    if(b.x<-80||b.x>W+80){B.splice(i,1);continue;}drawBird(b,t);}}
  requestAnimationFrame(tick);}
 requestAnimationFrame(tick);
})();

setLang(lang);
})();
