(function(){
const NS='http://www.w3.org/2000/svg';
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.append(e);return e;};
/* humanoid mini robot */
function bot(g,color,mode,prop){
 // Kalpa helper bot: cream head with a screen face, body in its world colour, leaf antenna, ink outline like the tree
 const INK='var(--ink)', CR='#F7F1E1', SC='#16201B';
 el('ellipse',{cx:0,cy:1,rx:13,ry:3.4,fill:'#000',opacity:.16},g);
 const r=el('g',{class:mode||'working'},g);
 [[-5,'leg-a'],[5,'leg-b']].forEach(([x,c])=>{const L=el('g',{class:'limb '+c},r);el('rect',{x:x-3,y:-14,width:6,height:12,rx:3,fill:color,stroke:INK,'stroke-width':1.1},L);el('rect',{x:x-4.2,y:-4,width:8.4,height:4.6,rx:2.3,fill:SC,stroke:INK,'stroke-width':1},L);});
 const T=el('g',{class:'torso'},r);
 [[-13,'arm-a'],[13,'arm-b']].forEach(([x,c])=>{const A=el('g',{class:'limb '+c},T);el('rect',{x:x-3,y:-35,width:6,height:15,rx:3,fill:color,stroke:INK,'stroke-width':1.1},A);el('circle',{cx:x,cy:-20,r:3.6,fill:CR,stroke:INK,'stroke-width':1},A);
  if(c==='arm-b'&&prop)PROPS[prop](A,x,-20);});
 el('rect',{x:-11,y:-37,width:22,height:24,rx:8,fill:color,stroke:INK,'stroke-width':1.3},T);
 el('rect',{x:-7,y:-32,width:14,height:12,rx:4,fill:CR,opacity:.92},T);
 el('path',{d:'M-3.5-24.5C-2-29 2-29 3.5-27.5C2-23.5-2-23-3.5-24.5Z',fill:'var(--leaf)'},T);
 const H=el('g',{class:'head'},T);
 el('path',{d:'M0-52V-60',stroke:INK,'stroke-width':1.4,'stroke-linecap':'round'},H);
 el('path',{class:'glow',d:'M0-60C-5-63-5-69 0-71C5-69 5-63 0-60Z',fill:'var(--gold)',stroke:INK,'stroke-width':1},H);
 [-14,14].forEach(x=>el('circle',{cx:x,cy:-44,r:3.2,fill:color,stroke:INK,'stroke-width':1},H));
 el('rect',{x:-13,y:-55,width:26,height:21,rx:9,fill:CR,stroke:INK,'stroke-width':1.3},H);
 el('rect',{x:-9.5,y:-51,width:19,height:12.5,rx:5,fill:SC},H);
 const E=el('g',{class:'eyes'},H);[-4.2,4.2].forEach(x=>el('rect',{x:x-1.9,y:-48.5,width:3.8,height:5,rx:1.9,fill:color==='#25D366'?'#7CF0A8':'#9FE3C2'},E));
 el('path',{d:'M-2.6-41.6Q0-39.8 2.6-41.6',fill:'none',stroke:'#9FE3C2','stroke-width':1.1,'stroke-linecap':'round'},H);
 el('circle',{cx:-8.5,cy:-38,r:1.4,fill:'#E59A8C',opacity:.7},H);el('circle',{cx:8.5,cy:-38,r:1.4,fill:'#E59A8C',opacity:.7},H);
}
const PROPS={ // small things each bot holds, drawn at its right hand
 chat:(p,x,y)=>{el('rect',{x:x+1,y:y-15,width:15,height:11,rx:3,fill:'#fff',stroke:'var(--ink)','stroke-width':1},p);el('path',{d:`M${x+4} ${y-4}l-1 4 4-4`,fill:'#fff',stroke:'var(--ink)','stroke-width':1,'stroke-linejoin':'round'},p);[4.5,8.5,12.5].forEach(d=>el('circle',{class:'dot',cx:x+d,cy:y-9.5,r:1.2,fill:'#25D366'},p));},
 wrench:(p,x,y)=>el('path',{d:`M${x} ${y}l9-11m-2-2a4 4 0 1 0 5 5l-3-1-1-3z`,fill:'none',stroke:'var(--ink)','stroke-width':2,'stroke-linecap':'round','stroke-linejoin':'round'},p),
 pen:(p,x,y)=>{el('path',{d:`M${x} ${y+1}l10-14 3 2-10 14-4 1z`,fill:'var(--gold)',stroke:'var(--ink)','stroke-width':1,'stroke-linejoin':'round'},p);},
 calc:(p,x,y)=>{el('rect',{x:x+1,y:y-16,width:11,height:14,rx:2,fill:'#F7F1E1',stroke:'var(--ink)','stroke-width':1},p);el('rect',{x:x+3,y:y-14,width:7,height:3,fill:'#16201B'},p);[0,1].forEach(r=>[0,1,2].forEach(c=>el('rect',{x:x+3+c*2.6,y:y-9.5+r*3.2,width:1.8,height:2,fill:'var(--ink)'},p)));},
 lens:(p,x,y)=>{el('path',{d:`M${x} ${y}l5-6`,stroke:'var(--ink)','stroke-width':2.2,'stroke-linecap':'round'},p);el('circle',{cx:x+8.5,cy:y-10,r:5.5,fill:'#DDF1F3',stroke:'var(--ink)','stroke-width':1.6},p);}};
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
const TE={nav_live:'లైవ్ AI',tip_go:'వివరాలు చూడండి',tree_note:'ఆ ఉత్పత్తిని చూడటానికి పండును ట్యాప్ చేయండి.',d_h:'ఇప్పుడే మా AIతో మాట్లాడండి',d_p:'Kalpa Bhai నిజమైన AI, BotBhai మీ సెలూన్‌లో పెట్టేది ఇలాంటిదే. సహాయం చేయలేకపోతే, అఖిల్ కాల్ చేయడానికి మీ నంబర్ అడుగుతుంది.',d_l1:'ధరలు, ఉచిత పైలట్ లేదా సెటప్ ఎలా జరుగుతుందో అడగండి',d_l2:'తెలుగు, హిందీ, ఇంగ్లీష్ లేదా కలిపి టైప్ చేయండి',d_l3:'"కాల్ చేయండి" అని చెప్పి మీ నంబర్ ఇవ్వండి',nav_products:'ఉత్పత్తులు',nav_how:'ఎలా పనిచేస్తుంది',nav_prices:'ధరలు',nav_faq:'ప్రశ్నలు',cta_salon:'ఉచిత 14 రోజుల పైలట్',cta_demo:'AIతో చాట్ చేయండి',
h1:'మీ కస్టమర్లకు <em>తెలుగు, హిందీ, ఇంగ్లీష్‌లో</em> రాత్రి 11 గంటలకైనా జవాబు.',
lead:'BotBhai జిమ్‌లు, సెలూన్లు, రియల్ ఎస్టేట్ ఏజెంట్ల కస్టమర్లకు 5 భాషల్లో జవాబిస్తుంది, స్లాట్ లేదా సైట్ విజిట్ బుక్ చేస్తుంది, గుర్తు చేస్తుంది, అవసరమైనప్పుడు మీకు అప్పగిస్తుంది. 14 రోజుల ఉచిత పైలట్; మీరు అవును అనే వరకు చెల్లింపు లేదు.',
trust1:'అధికారిక WhatsApp APIపై నిర్మించబడింది',trust2:'యాప్ ఇన్‌స్టాల్ అవసరం లేదు',trust3:'ఉద్యమ్ నమోదిత MSME',online:'AI సహాయకుడు · 5 భాషలు',demo_note:'ఇది నిజమైన AI, BotBhai మీ సెలూన్‌లో పెట్టేది ఇలాంటిదే. ఏదైనా అడగండి, లేదా కాల్ బ్యాక్ అడగండి.',
st_products:'ఒకే చెట్టుపై పెరుగుతున్న ఉత్పత్తులు',st_try:'BotBhaiని 14 రోజులు ప్రయత్నించడానికి',st_agents:'జవాబులు, మీ షాప్ మూసిన తర్వాత కూడా',st_langs:'భాషలు: ఇంగ్లీష్, తెలుగు, హిందీ, టెంగ్లీష్, హింగ్లీష్',
p_h:'నిజమైన భారతీయ పనికి చిన్న, నిజాయితీ గల టూల్స్',p_p:'ప్రతి ఉత్పత్తి ఒక పనిని బాగా చేస్తుంది. ధరలు రూపాయల్లో, ఎలాంటి బంధనం లేదు.',
h_h:'"స్లాట్ ఉందా?" నుంచి కన్ఫర్మ్ బుకింగ్ వరకు',s1h:'కస్టమర్ మెసేజ్',s1p:'WhatsApp లేదా వెబ్‌సైట్‌లో, తెలుగు, హిందీ, ఇంగ్లీష్ లేదా కలిపి. "రేపు" అంటే రేపే అని అర్థం చేసుకుంటుంది.',
s2h:'BotBhai జవాబు',s2p:'మీ సెలూన్ వివరాల నుంచే ధరలు, సమయాలు, ఖాళీ స్లాట్లు. ధరను ఎప్పుడూ ఊహించదు; సందేహం ఉంటే మీ సిబ్బందికి పంపుతుంది.',s3h:'నియంత్రణ మీదే',s3p:'బుకింగ్ కన్ఫర్మ్, 24 గం, 2 గం ముందు రిమైండర్లు, యజమానికి రోజువారీ జాబితా. ఏ చాట్‌నైనా ఒక్క ట్యాప్‌తో మీరు తీసుకోవచ్చు.',

f_h:'స్టాండర్డ్: 14 రోజుల ఉచిత పైలట్, తర్వాత నెలకు ₹1,499',f_per:' / నెల',f1:'₹2,999 ఒక్కసారి సెటప్, మేమే చేస్తాం',f2:'WhatsApp బాట్, బుకింగ్స్, రిమైండర్లు, యజమాని అలర్ట్స్, డాష్‌బోర్డ్',f3:'తెలుగు, హిందీ, ఇంగ్లీష్',f4:'ఐచ్ఛిక సోషల్ టీమ్ యాడ్-ఆన్: ₹999 / నెల',f_cta:'పైలట్ అడగండి',f_small:'పైలట్ ముగిసి మీరు అవును అనే వరకు చెల్లింపు లేదు.',
s_h:'నెలవారీ ప్లాన్‌కి ఇంకా సిద్ధంగా లేరా?',s_per:' ఒక్కసారి',s_p:'స్టార్టర్ ప్యాక్: WhatsApp చాట్ లింక్, మీ కౌంటర్ కోసం QR పోస్టర్, సిద్ధంగా ఉన్న త్వరిత జవాబులు, మీ Google Business ప్రొఫైల్ సరిదిద్దడం. నెలవారీ రుసుము లేదు.',s_lite:'లైట్ ప్లాన్: ₹1,999 సెటప్ + నెలకు ₹999; బుకింగ్‌లు, రిమైండర్‌లు, యజమానికి అలర్ట్‌లు, డాష్‌బోర్డ్‌తో WhatsApp బాట్.',s_cta:'స్టార్టర్ లేదా లైట్ గురించి అడగండి',
g_h:'మీకేం కావాలో చెప్పండి. అఖిల్ స్వయంగా జవాబిస్తారు.',g_p:'మీ నంబర్‌ను ఈ విషయంపై జవాబివ్వడానికి మాత్రమే వాడతాం. స్పామ్ లేదు, ఎవరితోనూ పంచుకోం.',
l_interest:'నాకు ఆసక్తి ఉన్నది',o_salon:'నా జిమ్/సెలూన్/రియల్ ఎస్టేట్ కోసం BotBhai (ఉచిత పైలట్)',o_kits:'పరీక్ష / డబ్బు కిట్స్',o_other:'ఇంకేదైనా',l_name:'మీ పేరు',l_phone:'WhatsApp నంబర్',l_consent:'ఈ విషయం గురించి Kalpa Labs నన్ను WhatsAppలో సంప్రదించడానికి అంగీకరిస్తున్నాను. నా డేటాను ఎప్పుడైనా తొలగించమని అడగవచ్చు.',l_send:'పంపండి',
q_h:'సూటిగా జవాబులు',q1:'ఇది బాట్ అని కస్టమర్లకు తెలుస్తుందా?',a1:'అవును. చాట్ మొదట్లోనే ఇది ఆటోమేటెడ్ సహాయకుడు అని చెబుతుంది, అడిగినప్పుడల్లా మీ సిబ్బందికి అప్పగిస్తుంది.',q2:'తప్పు జవాబిస్తే?',a2:'మీరు ఇచ్చిన ధరలు, సమయాలే వాడుతుంది. ఖచ్చితంగా తెలియకపోతే లేదా కస్టమర్ కోపంగా ఉంటే, ఊహించకుండా మీకు అప్పగిస్తుంది.',q3:'కంప్యూటర్ లేదా కొత్త నంబర్ కావాలా?',a3:'కంప్యూటర్, కొత్త నంబర్ అవసరం లేదు. ఇప్పుడు మీ వెబ్‌సైట్ చాట్, టెలిగ్రామ్‌లో పనిచేస్తుంది; Meta మీ నంబర్‌ను ఆమోదించగానే WhatsAppలో కూడా. పైలట్‌లో అంతా మీతో కలిసి సెటప్ చేస్తాం.',q4:'నా కస్టమర్ల డేటా సురక్షితమా?',a4:'భారత DPDP చట్టాన్ని పాటిస్తాం: మీ సూచనల మేరకే పనిచేస్తాం, డేటా మేము మీ సెలూన్ కోసం నడిపే సురక్షిత డేటాబేస్‌లో, మీరు అడిగితే తొలగిస్తాం. అనుమతి ఇచ్చిన కస్టమర్లకే మెసేజ్‌లు.',q5:'మీరు కొత్తవారు. ఎందుకు నమ్మాలి?',a5:'న్యాయమైన ప్రశ్న. ప్రతి వ్యాపారం ఉచిత 14 రోజుల పైలట్‌తో మొదలవుతుంది, కాబట్టి ఏమైనా చెల్లించే ముందే ఫలితాలు చూస్తారు. ఎప్పుడైనా ఆపవచ్చు, అడిగితే మీ డేటా తొలగిస్తాం.',
fo_h:'"మా ఇరుగుపొరుగు దుకాణాలకు ఉండాలనుకున్న టూల్స్ నేను తయారు చేస్తాను."',fo_p:'అఖిల్ కనిగిచర్ల, వ్యవస్థాపకుడు. Kalpa Labs పేరు కల్పవృక్షం నుంచి వచ్చింది: ఒక చెట్టు, ఎన్నో కొమ్మలు, ప్రతి కొమ్మ రోజువారీ వ్యాపారానికి ఒక సులభమైన సాధనం. హైదరాబాద్‌లో ఉన్నాం.',
ft0:'ఒక చెట్టు, అనేక శాఖలు, అందరికీ పండ్లు',ft1:'హైదరాబాద్, తెలంగాణ · ఉద్యమ్ నమోదిత MSME (ప్రొప్రైటర్‌షిప్)',ft2:'స్పష్టమైన ధరలు. దాచిన ఛార్జీలు లేవు.',mb1:'AIతో చాట్ చేయండి',mb2:'ఉచిత సెలూన్ పైలట్'};
const EN={}; document.querySelectorAll('[data-i]').forEach(e=>{EN[e.dataset.i]=e.dataset.html?e.innerHTML:e.textContent;});
let lang='en'; try{lang=localStorage.getItem('kl-lang')||'en';}catch(e){}
function setLang(l){lang=l;document.documentElement.lang=l==='te'?'te':'en';document.body.className=l;
 document.querySelectorAll('[data-i]').forEach(e=>{const k=e.dataset.i;const v=(l==='te'?TE[k]:null)??EN[k];if(v==null)return;if(e.dataset.html)e.innerHTML=v;else e.textContent=v;});
 document.querySelectorAll('.lang button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===l)));
 {const sb=document.getElementById('snd');if(sb){sb.setAttribute('aria-label',l==='te'?'ప్రకృతి శబ్దాలు':'Nature sounds');sb.title=l==='te'?'గాలి, పక్షుల శబ్దాలు':'Breeze and birds';}}
 try{localStorage.setItem('kl-lang',l);}catch(e){}
 renderProducts(); resetChat(); if(typeof renderTeam==='function')renderTeam(); if(typeof formLang==='function')formLang(); closeTip();}
document.querySelectorAll('.lang button').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang)));

/* ---------- countdown ---------- */


/* ---------- products ---------- */
const CHK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
const P=[
 {id:'botbhai',c:'--l1',name:'BotBhai',st:['Free 14-day pilot','ఉచిత 14 రోజుల పైలట్'],stc:'--ok',
  for:['For salons, gyms and coaching centres','సెలూన్లు, జిమ్‌లు, కోచింగ్ సెంటర్ల కోసం'],
  pts:[['WhatsApp + website chat in 5 languages','5 భాషల్లో WhatsApp + వెబ్‌సైట్ చాట్'],['Bookings, 24 h and 2 h reminders','బుకింగ్స్, 24 గం, 2 గం రిమైండర్లు'],['Owner alerts and a one-tap shared inbox','యజమాని అలర్ట్స్, ఒక ట్యాప్ షేర్డ్ ఇన్‌బాక్స్']],
  price:['Free pilot, then ₹1,499/mo','ఉచిత పైలట్, తర్వాత ₹1,499/నెల'],cta:'#founding',art:'chat'},
 {id:'kits',c:'--l3',name:'Exam & Money Kits',st:['Coming soon','త్వరలో'],stc:'--l0',
  for:['For GATE aspirants and salaried savers','GATE అభ్యర్థులు, జీతం పొందేవారి కోసం'],
  pts:[['GATE 2027 120-day tracker in Google Sheets','Google Sheetsలో GATE 2027 120 రోజుల ట్రాకర్'],['Tax regime + SIP goal planner FY 2026-27','పన్ను విధానం + SIP లక్ష్య ప్లానర్ 2026-27'],['GATE Study Coach skill pack for Claude','Claude కోసం GATE స్టడీ కోచ్ స్కిల్ ప్యాక్']],
  price:['From ₹199','₹199 నుంచి'],cta:'#signup',art:'sheet'},
 {id:'deals',c:'--l5',name:'Telugu Deals',st:['Coming soon','త్వరలో'],stc:'--l0',
  for:['For smart shoppers who read Telugu','తెలుగు చదివే తెలివైన కొనుగోలుదారుల కోసం'],
  pts:[['Checked deals on Telegram (channel coming soon)','టెలిగ్రామ్‌లో చెక్ చేసిన డీల్స్ (ఛానల్ త్వరలో)'],['Free tax, SIP, EMI calculators in Telugu','తెలుగులో ఉచిత పన్ను, SIP, EMI కాలిక్యులేటర్లు'],['Every affiliate link marked #ad','ప్రతి అఫిలియేట్ లింక్‌కి #ad గుర్తు']],
  price:['Free','ఉచితం'],cta:'#signup',art:'tag'},
 {id:'jobcard',c:'--l2',name:'Mobile App',st:['Coming soon','త్వరలో'],stc:'--l0',
  for:['Phone apps for everyday work','రోజువారీ పని కోసం ఫోన్ యాప్‌లు'],
  pts:[['Made for Indian phones and languages','భారతీయ ఫోన్లు, భాషల కోసం తయారు'],['Simple enough to use on day one','మొదటి రోజే వాడేంత సులభం'],['Join the list to hear first','ముందుగా తెలుసుకోవడానికి లిస్ట్‌లో చేరండి']],
  price:['Coming soon','త్వరలో'],cta:'#signup',art:'card'},
 {id:'lifeboat',c:'--l4',name:'Tab Lifeboat',st:['Coming soon to Chrome','త్వరలో Chromeలో'],stc:'--l0',
  for:['For people with 100 browser tabs','100 బ్రౌజర్ ట్యాబ్స్ ఉండేవారి కోసం'],
  pts:[['Save and restore every tab, with groups','గ్రూప్‌లతో సహా ప్రతి ట్యాబ్ సేవ్, రీస్టోర్'],['Auto-saves every 5 minutes','ప్రతి 5 నిమిషాలకు ఆటో-సేవ్'],['Planned: import from OneTab','ప్లాన్: OneTab నుంచి దిగుమతి']],
  price:['Free','ఉచితం'],cta:'#signup',art:'tabs'},
 {id:'ledger',c:'--l6',name:'Ledger Peaks',st:['Early access','ముందస్తు ప్రవేశం'],stc:'--l0',
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
 en:['How does BotBhai help my salon?','Is the pilot really free?','What does it cost?','Please call me back'],
 te:['BotBhai నా సెలూన్‌కి ఎలా సహాయం చేస్తుంది?','పైలట్ నిజంగా ఉచితమా?','దీని ధర ఎంత?','నాకు కాల్ చేయండి']};
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
  // up to 3 tries with exponential backoff (1 s, 2 s + jitter) when the server is busy or the network blips
  let d=null;
  for(let n=0;n<3&&!d;n++){
   if(n) await new Promise(r=>setTimeout(r,1000*2**(n-1)+Math.random()*400));
   const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(),30000);
   try{const r=await fetch(CHAT_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:sid,chatInput:text,history:HIST.slice(-8)}),signal:ctrl.signal});
    if(r.status===429){d=await r.json().catch(()=>null);break;}       // too fast: show the server's polite message, don't retry
    if(r.ok) d=await r.json(); else if(r.status<500) break;            // 4xx won't fix itself
   }catch(e){} finally{clearTimeout(to);}
  }
  if(!d) throw new Error('unavailable');
  reply=clean(Array.isArray(d)?d[0]?.output:(d.output??d.text));
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

/* ---------- form (UX-PATTERNS 6 autosave, 8 throttle, 9 smart validation, 20 graceful errors) ---------- */
document.querySelectorAll('[data-pick]').forEach(a=>a.addEventListener('click',()=>{document.getElementById('interest').value=a.dataset.pick;saveDraft();}));
const form=document.querySelector('form.signup'), msg=document.getElementById('formmsg'), retry=document.getElementById('formretry');
const fBtn=form.querySelector('button[type=submit]'), DRAFT='kalpa_pilot_draft';
const FM={en:{name:'Please write your name.',phone:'Please enter a 10-digit Indian mobile number, like 98765 43210.',consent:'Please tick the box so we may reply on WhatsApp.',
  sending:'Sending…',send:'Send',ok:'Thank you! Akhil will reply on WhatsApp soon.',offline:'You are offline. Your details are saved here; tap Send when you are back online.',
  fail:'That did not send. Your details are safe on this page.',retry:'Try again'},
 te:{name:'దయచేసి మీ పేరు రాయండి.',phone:'దయచేసి 10 అంకెల మొబైల్ నంబర్ ఇవ్వండి, ఉదా. 98765 43210.',consent:'WhatsAppలో జవాబు ఇవ్వడానికి బాక్స్ టిక్ చేయండి.',
  sending:'పంపుతున్నాం…',send:'పంపండి',ok:'ధన్యవాదాలు! అఖిల్ త్వరలో WhatsAppలో జవాబిస్తారు.',offline:'మీరు ఆఫ్‌లైన్‌లో ఉన్నారు. మీ వివరాలు ఇక్కడే ఉన్నాయి; నెట్ వచ్చాక పంపండి నొక్కండి.',
  fail:'పంపడం కాలేదు. మీ వివరాలు ఈ పేజీలోనే భద్రంగా ఉన్నాయి.',retry:'మళ్లీ ప్రయత్నించండి'}};
const T=k=>(FM[lang]||FM.en)[k];
function mobile(v){let d=String(v||'').replace(/\D/g,'');if(d.length===12&&d.startsWith('91'))d=d.slice(2);if(d.length===11&&d.startsWith('0'))d=d.slice(1);return /^[6-9]\d{9}$/.test(d)?d:'';}
function fieldErr(el,id,bad,key){const e=document.getElementById(id);e.hidden=!bad;e.textContent=bad?T(key):'';if(el)el.setAttribute('aria-invalid',String(bad));return bad;}
const checks={name:()=>fieldErr(form.name,'name-err',form.name.value.trim().length<2,'name'),
 phone:()=>fieldErr(form.phone,'phone-err',!mobile(form.phone.value),'phone'),
 consent:()=>fieldErr(form.consent,'consent-err',!form.consent.checked,'consent')};
form.name.addEventListener('blur',()=>{if(form.name.value)checks.name();});
form.phone.addEventListener('blur',()=>{if(form.phone.value)checks.phone();});
form.consent.addEventListener('change',()=>{if(form.consent.checked)checks.consent();});
function saveDraft(){if(!form.name.value&&!form.phone.value)return;try{localStorage.setItem(DRAFT,JSON.stringify({name:form.name.value,phone:form.phone.value,interest:form.interest.value}));}catch(e){}}
let draftT; form.addEventListener('input',()=>{clearTimeout(draftT);draftT=setTimeout(saveDraft,250);});
try{const d=JSON.parse(localStorage.getItem(DRAFT)||'null');if(d){if(d.name)form.name.value=d.name;if(d.phone)form.phone.value=d.phone;if(d.interest)form.interest.value=d.interest;}}catch(e){}
function say(text,good){msg.style.color=good?'var(--ok)':'var(--madder)';msg.textContent=text;}
async function sendForm(){
 if(fBtn.disabled) return;
 const bad=['name','phone','consent'].filter(k=>checks[k]());
 if(bad.length){form[bad[0]].focus();return;}
 const fd=new FormData(form); if(fd.get('company')) return;
 retry.hidden=true; saveDraft();
 if(navigator.onLine===false){say(T('offline'),false);return;}
 fBtn.disabled=true; fBtn.textContent=T('sending'); msg.textContent='';
 let ok=false;
 try{const r=await fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(fd).toString()});ok=r.ok;}catch(e){}
 fBtn.disabled=false; fBtn.textContent=T('send');
 if(ok){say(T('ok'),true);clearTimeout(draftT);form.reset();try{localStorage.removeItem(DRAFT);}catch(e){}} /* a pending autosave must not bring the draft back */
 else{say(T('fail'),false);retry.textContent=T('retry');retry.hidden=false;retry.focus();}
}
form.addEventListener('submit',e=>{e.preventDefault();sendForm();});
retry.addEventListener('click',sendForm);
function formLang(){['name','phone','consent'].forEach(k=>{if(!document.getElementById(k+'-err').hidden)checks[k]();});if(!retry.hidden)retry.textContent=T('retry');}

/* ---------- the living Kalpa tree: branches = products, robots act out what each product does for a customer ---------- */
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
const LEAF='M0 0C5-8 17-9 26 0C17 9 5 8 0 0Z', VEIN='M2 0H23M8 0l4-3.5M8 0l4 3.5M14 0l4-3M14 0l4 3';
function leaf(par,attrs){const g=el('g',Object.assign({class:'lf'},attrs),par);el('path',{d:LEAF},g);el('path',{class:'vein',d:VEIN},g);return g;}
function cluster(par,cx,cy,R,n){
 for(let k=0;k<4;k++)el('circle',{class:'blob',cx:cx+(rnd()-.5)*R*.9,cy:cy+(rnd()-.5)*R*.6,r:R*(.42+.2*rnd()),fill:'url(#blob'+(1+(k%2))+')',style:'animation-delay:'+(1.2+Math.hypot(cx-300,cy-560)/600*1.2).toFixed(2)+'s'},par);
 for(let k=0;k<n;k++){const a=rnd()*6.283,rr=R*Math.sqrt(rnd()),x=cx+Math.cos(a)*rr,y=cy+Math.sin(a)*rr*.8;
  const g=el('g',{transform:`translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${(a*57.3+(rnd()-.5)*70).toFixed(0)}) scale(${(.7+rnd()*.6).toFixed(2)})`},par);
  const d=(1.1+Math.hypot(x-300,y-560)/600*1.2+rnd()*.3).toFixed(2);
  leaf(g,{fill:'var(--tl'+(1+Math.floor(rnd()*5))+')',style:'animation-delay:'+d+'s'});}
 for(let k=0;k<Math.round(n/9);k++){const a=rnd()*6.283,rr=R*.85*Math.sqrt(rnd());bloom(par,cx+Math.cos(a)*rr,cy+Math.sin(a)*rr*.8,3+rnd()*1.6,(2+rnd()).toFixed(2));}}
// wish-tree blossoms: five cream petals around a gold heart
function bloom(par,x,y,r,delay){const g=el('g',{class:'blos',transform:`translate(${x.toFixed(1)} ${y.toFixed(1)})`,style:'animation-delay:'+delay+'s'},par);
 for(let k=0;k<5;k++)el('ellipse',{cx:0,cy:-r,rx:r*.62,ry:r,transform:`rotate(${k*72})`},g); el('circle',{class:'hb',r:r*.45},g);}
// a branch as a filled, tapering shape (thick at the trunk, thin at the tip), with a sunlit upper edge
function limbShape(par,p,w0,w1,cls){const L=p.getTotalLength(),N=22,lft=[],rgt=[],top=[];
 for(let k=0;k<=N;k++){const t=k/N,a=p.getPointAtLength(L*t),b=p.getPointAtLength(Math.min(L,L*t+.5)),c=k===N?p.getPointAtLength(L*t-.5):a;
  let dx=b.x-a.x,dy=b.y-a.y; if(k===N){dx=a.x-c.x;dy=a.y-c.y;} const m=Math.hypot(dx,dy)||1,nx=-dy/m,ny=dx/m,w=(w0+(w1-w0)*Math.pow(t,.8))/2;
  lft.push([a.x+nx*w,a.y+ny*w]); rgt.push([a.x-nx*w,a.y-ny*w]); top.push(ny<0?[a.x+nx*w*.55,a.y+ny*w*.55]:[a.x-nx*w*.55,a.y-ny*w*.55]);}
 const P=pts=>pts.map(q=>q[0].toFixed(1)+' '+q[1].toFixed(1)).join('L'), tip=p.getPointAtLength(L);
 const d='M'+P(lft)+`Q${tip.x.toFixed(1)} ${tip.y.toFixed(1)} `+P(rgt.reverse())+'Z';
 el('path',{class:cls||'limb-s',d},par); el('path',{class:'limb-lit',d:'M'+P(top.slice(0,N-2))},par); return d;}

const sway=[]; // groups that move in the wind: [elements, baseX, baseY, amp, phase]
const crown=el('g',{},tback); cluster(crown,300,190,100,85); cluster(crown,300,275,82,55); sway.push([[crown],300,320,.6,0]);
const fruits=[], paths=[], tlimbs=document.getElementById('tlimbs');
BR.forEach(([d,w,id,name,col],i)=>{
 const back=el('g',{},tback), front=el('g',{},tfront);
 const limbs=el('g',{class:'limbs',style:'animation-delay:'+(.75+i*.09)+'s'},tlimbs);
 const p=el('path',{d,class:'guide'},front); const L=p.getTotalLength(); paths.push(p); // invisible: robots, birds and fruit follow it
 limbShape(limbs,p,w*1.9,w*.42);
 const e=p.getPointAtLength(L), m=p.getPointAtLength(L*.55);
 cluster(back,e.x,e.y-6,i===6?58:i<2?60:54,i<2?52:46); cluster(back,m.x,m.y-14,34,20);
 // twigs fork off the branch, alternating sides, each ending in a small spray of leaves
 [.42,.64,.84].forEach((t,k)=>{if(i===6&&k===0)return;const a=p.getPointAtLength(L*t),b=p.getPointAtLength(L*t+1),ang=Math.atan2(b.y-a.y,b.x-a.x)+(k%2?.75:-.75)*(i%2?-1:1),len=22+rnd()*14;
  const ex=a.x+Math.cos(ang)*len,ey=a.y+Math.sin(ang)*len-6,tw=el('path',{d:`M${a.x.toFixed(1)} ${a.y.toFixed(1)}Q${((a.x+ex)/2).toFixed(1)} ${((a.y+ey)/2-6).toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`},front);
  tw.setAttribute('class','guide'); limbShape(front,tw,w*.55,1.4,'limb-s twig'); tw.remove();
  for(let j=0;j<6;j++){const g=el('g',{transform:`translate(${(ex+(rnd()-.5)*10).toFixed(1)} ${(ey+(rnd()-.5)*8).toFixed(1)}) rotate(${(ang*57.3+(j-2.5)*34).toFixed(0)}) scale(${(.6+rnd()*.25).toFixed(2)})`},front);
   leaf(g,{fill:'var(--tl'+(3+j%3)+')',style:'animation-delay:'+(1.6+i*.1+j*.05).toFixed(2)+'s'});}});
 // a little foliage in front of the tip, so the branch disappears into the leaves instead of ending like a stick
 for(let j=0;j<10;j++){const a=rnd()*6.283,rr=(i===6?34:30)*Math.sqrt(rnd()),g=el('g',{transform:`translate(${(e.x+Math.cos(a)*rr).toFixed(1)} ${(e.y-8+Math.sin(a)*rr*.7).toFixed(1)}) rotate(${(a*57.3+(rnd()-.5)*60).toFixed(0)}) scale(${(.65+rnd()*.3).toFixed(2)})`},front);
  leaf(g,{fill:'var(--tl'+(4+j%2)+')',style:'animation-delay:'+(1.9+i*.1).toFixed(2)+'s'});}
 if(i<2)bloom(front,e.x+(i?-22:22),e.y-24,4.4,'2.2'); 
 const fx=e.x, fy=e.y+(i===6?-6:20);
 const f=el('g',{class:'fruit',tabindex:'0',role:'button','aria-label':name,style:'animation-delay:'+(2.3+i*.12)+'s'},front);
 if(i!==6)el('path',{d:`M${e.x} ${e.y}L${fx} ${fy-12}`,stroke:'var(--bark)','stroke-width':2.5},f);
 el('circle',{class:'halo',cx:fx,cy:fy,r:24},f);
 const fb=el('g',{class:'fb'},f);
 el('circle',{class:'dots',cx:fx,cy:fy,r:21},fb);
 for(let k=0;k<8;k++)el('ellipse',{class:'petal',cx:fx,cy:fy-17,rx:3.2,ry:5,transform:`rotate(${k*45} ${fx} ${fy})`},fb);
 el('circle',{class:'ring',cx:fx,cy:fy,r:15,fill:'var(--gold)',stroke:'var('+col+')','stroke-width':3.5},fb);
 el('circle',{cx:fx,cy:fy,r:8,fill:'none',stroke:'var(--ink)','stroke-width':1,'stroke-opacity':.5},fb);
 el('circle',{cx:fx-5,cy:fy-5,r:4,fill:'#fff',opacity:.55},fb);
 leaf(fb,{class:'',fill:'var(--tl3)',stroke:'var(--ink)','stroke-width':1.4,transform:`translate(${fx} ${fy-20}) rotate(-35) scale(.55)`});
 const t=el('text',{class:'flabel',x:fx,y:fy+(i===6?-26:38)},f); t.textContent=SHORT[id]||name;
 f.addEventListener('click',ev=>{ev.stopPropagation();openTip(i);});
 f.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();openTip(i);}});
 fruits.push(f); sway.push([[back,front,limbs],+d.split(' ')[0].slice(1),+d.split(' ')[1].split('C')[0],1.1+(i%3)*.3,i*1.3]);
});
// grass tufts along the ground
const grassEls=[];for(let k=0;k<30;k++){const x=(60+k*16+rnd()*8).toFixed(0),h=(8+rnd()*12).toFixed(0);const g=el('path',{class:'grass','data-x':x,d:`M${x} 568q-3-${h} -6-${+h+3}M${x} 568q1-${+h+2} 4-${+h+4}`},document.getElementById('grass'));grassEls.push(g);}

/* Peacocks: a real fan of eye feathers that opens, shivers and folds, a bobbing head, stepping legs.
   Tap one and it displays. Drawn once; the shared animation loop moves them. */
const PEA=[];
function peacock(par,x,y,face,k){
 const root=el('g',{class:'pea',transform:`translate(${x} ${y}) scale(${face*1.2} 1.2)`},par);
 el('circle',{cx:-10,cy:-26,r:34,fill:'transparent'},root); // tap target
 const walk=el('g',{},root), train=el('g',{},walk), feathers=[];
 const ROWS=[[13,64],[11,52],[8,40]]; // three layers of feathers, longest at the back
 ROWS.forEach(([n,len],row)=>{for(let i=0;i<n;i++){const fg=el('g',{},train);
  el('path',{d:`M0 0Q${len*.5} ${row%2?2:-2} ${len-7} 0`,fill:'none',stroke:'var(--ink)','stroke-width':.9,'stroke-opacity':.6},fg);
  el('path',{class:'tl',d:`M${len*.35} 0C${len*.55}-4.5 ${len*.75}-4 ${len-6} 0C${len*.75} 4 ${len*.55} 4.5 ${len*.35} 0Z`},fg);
  el('ellipse',{cx:len-2,cy:0,rx:6.4,ry:5.2,fill:'var(--tl2)',stroke:'var(--ink)','stroke-width':.8},fg);
  el('ellipse',{class:'eye',cx:len-1.5,cy:0,rx:4.4,ry:3.6},fg); el('ellipse',{cx:len-1,cy:0,rx:2.4,ry:2,fill:'#123B66'},fg);
  feathers.push({g:fg,s:n>1?i/(n-1)-.5:0,row,spread:[168,150,128][row]});}});
 const body=el('g',{},walk);
 const legs=[-3,4].map((lx,j)=>{const L=el('g',{class:'limb'},body);el('path',{d:`M${lx}-6l1 10l4 1M${lx+1} 4l-3 1`,fill:'none',stroke:'var(--ink)','stroke-width':1.5,'stroke-linecap':'round','stroke-linejoin':'round'},L);return L;});
 el('path',{class:'bd',d:'M-16-14C-18-22-8-28 2-27C9-26 12-20 11-13C10-6 2-3-6-4C-12-5-15-9-16-14Z'},body);
 el('path',{d:'M-12-18C-8-23 0-24 5-21C2-15-6-12-12-18Z',fill:'#8C6B3A',stroke:'var(--ink)','stroke-width':.8,opacity:.9},body); // wing coverts
 for(let j=0;j<3;j++)el('path',{d:`M${-9+j*4}-19l2 2`,stroke:'#F4EEDC','stroke-width':.8,'stroke-linecap':'round'},body);
 const neck=el('g',{},body);
 el('path',{class:'bd',d:'M3-25C6-32 7-40 9-46L15-45C14-38 12-30 11-21Z'},neck);
 const head=el('g',{},neck);
 el('circle',{class:'bd',cx:13,cy:-47,r:5},head);
 el('path',{d:'M10.5-48.5Q13-50 15.5-48.5',stroke:'#F4EEDC','stroke-width':1.3,fill:'none','stroke-linecap':'round'},head);
 el('circle',{cx:14,cy:-47.3,r:1.1,fill:'#111'},head);
 el('path',{class:'bk',d:'M17.5-47L22-45.6L17.5-44.6Z'},head);
 [[-8,0],[0,1],[8,2]].forEach(([a])=>{const c=el('g',{transform:`rotate(${a} 13 -51)`},head);el('path',{d:'M13-51V-58',stroke:'var(--ink)','stroke-width':.8},c);el('circle',{cx:13,cy:-59,r:1.6,fill:'#1F5B6E'},c);});
 const p={root,walk,feathers,legs,neck,head,face,open:0,want:0,until:0,next:6+k*9,ph:k*2.1};
 root.addEventListener('pointerdown',e=>{e.stopPropagation();p.until=performance.now()/1000+5;try{SND.chirp(face<0?.6:-.6);}catch(_){}});
 return p;}
function peaFrame(p,t,dt){
 if(!reduce){ if(t>p.next){p.until=t+5;p.next=t+16+Math.random()*10;} }
 p.want=reduce||t<p.until?1:0;
 p.open=reduce?1:p.open+(p.want-p.open)*Math.min(1,dt*(p.want?2.2:1.4));
 const o=p.open, shiver=reduce?0:o>.9?Math.sin(t*38)*1.6:0;
 p.feathers.forEach(f=>{const s=f.s; // -0.5..0.5 across its row
  const closed=174+s*12+f.row*3, opened=270+s*f.spread;
  f.g.setAttribute('transform',`translate(-12 -12) rotate(${(closed+(opened-closed)*o+shiver*(f.row?-1:1)).toFixed(1)}) scale(${(.92+.08*o).toFixed(3)})`);});
 if(reduce)return;
 const walking=o<.2, step=Math.sin(t*3+p.ph);
 const dx=walking?Math.sin(t*.25+p.ph)*9:0;
 p.walk.setAttribute('transform',`translate(${dx.toFixed(1)} ${walking?(-Math.abs(step)*.8).toFixed(2):0})`);
 p.legs.forEach((L,j)=>L.setAttribute('transform',`rotate(${walking?(j?-step:step)*14:0})`));
 const peck=walking&&Math.sin(t*.9+p.ph)>.93; // now and then it dips to peck
 p.head.setAttribute('transform',`translate(${(walking?step*1.2:0).toFixed(2)} 0)`);
 p.neck.setAttribute('transform',peck?'rotate(38 7 -24)':'rotate(0)');}

/* Kalamkari base: a lotus pond and two peacocks facing the tree */
(()=>{const pd=document.getElementById('pond');
 el('ellipse',{class:'pond',cx:300,cy:574,rx:96,ry:13},pd);
 ['M228 574q8-4 16 0t16 0','M318 576q8-4 16 0t16 0','M268 580q8-4 16 0'].forEach(d=>el('path',{class:'wave',d},pd));
 [[252,571],[352,573]].forEach(([x,y])=>{el('ellipse',{class:'pad',cx:x-14,cy:y+3,rx:11,ry:3.5},pd);
  [-50,-25,0,25,50].forEach(a=>el('path',{class:'lotus',d:`M${x} ${y}c-4-6-4-13 0-19c4 6 4 13 0 19z`,transform:`rotate(${a} ${x} ${y})`},pd));});
 PEA.push(...[[104,1],[496,-1]].map(([x,f],k)=>peacock(pd,x,556,f,k)));
})();

/* hanging garlands: gold beads and a little bell, swinging with their branch */
[[0,.62],[0,.8],[1,.6],[1,.78]].forEach(([b,at],k)=>{const p=paths[b],q=p.getPointAtLength(p.getTotalLength()*at),n=4+k%2,g=el('g',{class:'garland','aria-hidden':'true'},tfront.children[b]);
 el('path',{d:`M${q.x.toFixed(1)} ${(q.y+3).toFixed(1)}v${n*7+4}`,stroke:'var(--gold)','stroke-width':1,opacity:.8},g);
 for(let j=1;j<=n;j++)el('circle',{cx:q.x.toFixed(1),cy:(q.y+3+j*7).toFixed(1),r:j===n?0:2,class:'bead'},g);
 el('path',{class:'bell',d:`M${(q.x-4).toFixed(1)} ${(q.y+n*7+12).toFixed(1)}q4-12 8 0z`},g);});

/* product tip */
const tip=document.getElementById('tip'); let tipFor=-1;
function closeTip(){if(!tip)return;tip.hidden=true;fruits.forEach(f=>f.classList.remove('on'));tipFor=-1;}
function openTip(i){
 if(tipFor===i){closeTip();return;} closeTip(); tipFor=i; const [, , id, name, col]=BR[i]; const L=lang==='te'?1:0; const p=P.find(x=>x.id===id);
 tip.style.setProperty('--c','var('+col+')'); document.getElementById('tipname').textContent=name;
 const st=document.getElementById('tipst'); st.style.setProperty('--pc','var('+(p?p.stc:'--l0')+')');
 st.querySelector('span').textContent=p?p.st[L]:(L?'త్వరలో':'Coming soon');
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
const WALK=[ // branch, name, tool, tasks [en, te]; colour comes from the branch's world
 [0,'Chitti','chat',[['Booking a 6 PM haircut','సాయంత్రం 6 గంటల హెయిర్‌కట్ బుక్ చేస్తోంది'],['Replying to a customer at 11 PM','రాత్రి 11 గంటలకు కస్టమర్‌కు జవాబిస్తోంది']]],
 [1,'Mistri','wrench',[['Turning a voice note into an invoice','వాయిస్ నోట్‌ను ఇన్‌వాయిస్‌గా మారుస్తోంది'],['Sending a job card to a customer','కస్టమర్‌కు జాబ్ కార్డ్ పంపుతోంది']]],
 [2,'Kavi','pen',[['Planning a GATE study week','GATE చదువు వారాన్ని ప్లాన్ చేస్తోంది'],['Working out a SIP goal','SIP లక్ష్యాన్ని లెక్కిస్తోంది']]],
 [3,'Forge','wrench',[['Saving 40 open tabs','40 ఓపెన్ ట్యాబ్‌లను సేవ్ చేస్తోంది'],['Bringing tabs back after a crash','క్రాష్ తర్వాత ట్యాబ్‌లను తిరిగి తెస్తోంది']]],
 [4,'Vigil','lens',[['Checking a price twice','ధరను రెండుసార్లు సరిచూస్తోంది'],['Checking a deal is real','డీల్ నిజమో కాదో చూస్తోంది']]],
 [5,'Ganaka','calc',[['Finding savings in a cloud bill','క్లౌడ్ బిల్లులో ఆదా వెతుకుతోంది'],['Finding a cheaper server plan','చౌకైన సర్వర్ ప్లాన్ వెతుకుతోంది']]]];
const bubbles=document.getElementById('bubbles');
/* birds resting in the tree: tap one (or shake the tree) and they fly off; they come back after a while */
const PERCH=[[0,.24,1],[1,.22,-1],[6,.62,1]].map(([b,at,face],k)=>{
 const pt=paths[b].getPointAtLength(paths[b].getTotalLength()*at);
 const g=el('g',{class:'perch','aria-hidden':'true',transform:`translate(${pt.x.toFixed(1)} ${(pt.y-4).toFixed(1)}) scale(${face*1.15} 1.15)`,style:'--pd:'+(k*1.3)+'s'},tfront);
 el('circle',{cx:0,cy:-12,r:30,fill:'transparent'},g); // 44 px tap target on a phone
 el('path',{class:'bd',d:'M-9-8L-19-4L-9-5Z'},g);                       // tail
 el('ellipse',{class:'bd',cx:-1,cy:-9,rx:10,ry:6.5,transform:'rotate(-14 -1 -9)'},g); // body
 el('path',{d:'M-6-10Q0-15 6-9',fill:'none',stroke:'var(--panel)','stroke-opacity':'.35','stroke-width':1.6,'stroke-linecap':'round'},g); // wing line
 el('path',{d:'M-2-3L-3 1M2-3L2 1',stroke:'var(--bird)','stroke-width':1.4,'stroke-linecap':'round'},g); // legs
 const hd=el('g',{class:'hd'},g); el('circle',{class:'bd',cx:8,cy:-15,r:5},hd); el('path',{class:'bk',d:'M12.5-16.2L17.5-15L12.5-13.6Z'},hd); el('circle',{class:'ey',cx:9.6,cy:-16.2,r:1.2},hd);
 return {g,face,away:false};});
const BIRDS={fly:null}; // the wind layer fills this in when motion is allowed
function scare(list){list.forEach(p=>{if(p.away)return;p.away=true;p.g.classList.add('away');
 const r=p.g.getBoundingClientRect(); if(BIRDS.fly)BIRDS.fly(p,r.left+r.width/2,r.top+r.height/2);
 else setTimeout(()=>{p.away=false;p.g.classList.remove('away');},6000);});}
PERCH.forEach(p=>p.g.addEventListener('pointerdown',e=>{e.stopPropagation();scare([p]);}));
const walkers=WALK.map(([b,name,tool,tasks],k)=>{ const col='var('+BR[b][4]+')';
 const front=tfront.children[b], p=paths[b], L=p.getTotalLength();
 const g=el('g',{class:'walker'},front); const inner=el('g',{},g); bot(inner,col,'working',tool);
 const bub=document.createElement('div'); bub.className='bub'; bub.style.setProperty('--c',col); bubbles.append(bub);
 return {g,p,L,t:.42+k*.08,v:(k%2?-1:1)*.045,name,tasks,n:k,bub,on:false};});
function placeBot(w,time){
 const pt=w.p.getPointAtLength(w.L*w.t), a=w.p.getPointAtLength(Math.min(w.L,w.L*w.t+1)), dir=a.x>=pt.x?1:-1, face=w.v*dir>0?1:-1;
 const bob=reduce?0:Math.abs(Math.sin(time*6+w.n))*1.6;
 w.g.setAttribute('transform',`translate(${pt.x.toFixed(1)} ${(pt.y-5-bob).toFixed(1)}) scale(${face} 1)`);}
function placeBubble(w){
 if(!w.on)return; const m=w.g.getScreenCTM(); if(!m)return; const head=new DOMPoint(0,-74).matrixTransform(m), br=tbox.getBoundingClientRect();
 const bw=w.bub.offsetWidth; let x=head.x-br.left-bw/2; x=Math.max(2,Math.min(br.width-bw-2,x));
 w.bub.style.transform=`translate(${x.toFixed(0)}px,${(head.y-br.top-w.bub.offsetHeight-8).toFixed(0)}px)`;}
let bi=-1, beat=0;
function nextBubble(){
 const single=true; /* one bubble at a time, so two never overlap */ bi=(bi+1)%walkers.length; const w=walkers[bi];
 const wasOn=walkers.some(o=>o.bub.classList.contains('on'));
 if(single)walkers.forEach(o=>{o.bub.classList.remove('on');o.on=false;});
 const [en,te]=w.tasks[beat++%w.tasks.length===0?0:1]; w.bub.replaceChildren(Object.assign(document.createElement('b'),{textContent:w.name}),document.createTextNode(lang==='te'?te:en));
 w.on=true; placeBubble(w); setTimeout(()=>w.bub.classList.add('on'),wasOn?160:0); /* let the old bubble leave first */ clearTimeout(w.to); w.to=setTimeout(()=>{w.bub.classList.remove('on');setTimeout(()=>{if(!w.bub.classList.contains('on'))w.on=false;},400);},single?2900:4800);}

/* falling leaves (and fireflies at night) */
const fall=document.getElementById('falling');
for(let k=0;k<10;k++){const i=document.createElement('i');i.className='ff';i.style.cssText=`left:${(50+rnd()*48).toFixed(0)}%;top:${(15+rnd()*70).toFixed(0)}%;--d:${(-rnd()*4).toFixed(1)}s`;fall.append(i);}

/* one animation loop, paused when the tree is off screen or the tab is hidden */
let visible=true, last=0;
new IntersectionObserver(es=>{visible=es[0].isIntersecting;},{threshold:0}).observe(tbox);
function frame(ms){
 const time=ms/1000, dt=Math.min(.05,time-(last||time)); last=time;
 if(visible&&!document.hidden){
  PEA.forEach(p=>peaFrame(p,time,dt));
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
  cx.save();cx.globalAlpha=overText(b.x,b.y)?.15:1;cx.translate(b.x,b.y);if(b.vx<0)cx.scale(-1,1);cx.strokeStyle=BIRDC;cx.lineWidth=1.7;cx.lineCap='round';cx.lineJoin='round';
  cx.beginPath();cx.moveTo(-s,-w);cx.quadraticCurveTo(-s*.45,-w*.2,0,0);cx.quadraticCurveTo(s*.45,-w*.2,s,-w);cx.stroke();
  cx.fillStyle=BIRDC;cx.beginPath();cx.ellipse(0,.6,1.8,1.2,0,0,6.28);cx.fill();cx.restore();}
 let BIRDC='#2a3326'; function birdCol(){BIRDC=getComputedStyle(document.documentElement).getPropertyValue('--bird').trim()||BIRDC;} birdCol();
 // a startled bird climbs away from the tree; 14-24 s later it flies back in from the edge and lands on its branch
 BIRDS.fly=(p,x,y)=>{const dir=p.face*(Math.random()<.3?-1:1);B.push({x,y,vx:dir*(small?120:150),vy:-120,s:small?7:8.5,ph:Math.random()*6.28,glide:0,bob:0,up:1});SND.chirp(x/W*2-1);
  setTimeout(()=>{const r=p.g.getBoundingClientRect();
   if(document.hidden||r.bottom<0||r.top>H){p.away=false;p.g.classList.remove('away');return;}
   const ltr=Math.random()<.5;B.push({x:ltr?-30:W+30,y:Math.max(20,r.top-H*.25),vx:0,vy:0,s:small?7:8.5,ph:Math.random()*6.28,glide:0,bob:0,land:p});},14000+Math.random()*10000);};
 // text zones: leaves fade almost away while they pass over words, so nothing is ever hard to read
 const TXT=[...document.querySelectorAll('h1,h2,h3,p,li,label,.btn,.stat,.flabel,.bub,.trust span,input,select,textarea')]; let ZONES=[],zt=0;
 function zones(){ZONES=[];for(const e of TXT){const r=e.getBoundingClientRect();if(r.bottom>-20&&r.top<H+20&&r.width)ZONES.push([r.left-6,r.top-6,r.right+6,r.bottom+6]);}}
 const overText=(x,y)=>ZONES.some(z=>x>z[0]&&x<z[2]&&y>z[1]&&y<z[3]);
 document.querySelector('.hero').addEventListener('pointerdown',e=>{for(const b of B){if(Math.hypot(e.clientX-b.x,e.clientY-b.y)<34){b.vx*=2.2;b.glide=0;SND.chirp(b.x/W*2-1);}}});
 WIND.gust=280; let px=-1,py=-1,pvx=0,pvy=0,lastP=0,trail=0;
 addEventListener('pointermove',e=>{const t=performance.now(),dt=Math.max(8,t-lastP);if(px>=0){const ix=(e.clientX-px)/dt*1000,iy=(e.clientY-py)/dt*1000;pvx=pvx*.6+ix*.4;pvy=pvy*.6+iy*.4;
   trail+=Math.hypot(e.clientX-px,e.clientY-py); if(trail>140&&e.target.closest&&e.target.closest('.hero')&&L.length<140){trail=0;leaf(e.clientX,e.clientY,pvx*.3,pvy*.3,false);}}
  px=e.clientX;py=e.clientY;lastP=t;},{passive:true});
 // tap the tree (not a fruit): it shakes and showers leaves; tap the sky: a gust
 tree.addEventListener('pointerdown',e=>{if(e.target.closest('.fruit,.perch'))return;WIND.shake=1;scare(PERCH);const r=tbox.getBoundingClientRect();
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
  if(!document.hidden){cx.clearRect(0,0,W,H); if(now-zt>250){zt=now;zones();}
   for(let i=L.length-1;i>=0;i--){const p=L[i];let wx=WIND.v,wy=0;
    if(px>=0){const dx=p.x-px,dy=p.y-py,d=Math.hypot(dx,dy);if(d<150){const k=(1-d/150);wx+=pvx*k*.9+dx/(d+1)*90*k*Math.min(1,Math.hypot(pvx,pvy)/300);wy+=pvy*k*.9+dy/(d+1)*90*k*Math.min(1,Math.hypot(pvx,pvy)/300);}}
    p.vx+=(wx-p.vx)*Math.min(1,dt*1.6); p.vy+=((34+p.s*2.2+wy)-p.vy)*Math.min(1,dt*1.2);
    p.x+=(p.vx+Math.sin(t*1.7+p.ph)*26)*dt; p.y+=(p.vy+Math.cos(t*2.3+p.ph)*14)*dt; p.r+=(p.vr+p.vx*.004)*dt; p.f+=p.fs*dt;
    if(p.y>H+30||p.x>W+60||p.x<-80&&p.vx<0){ if(p.keep){p.x=Math.random()*W*1.1-W*.15;p.y=-20-Math.random()*60;p.vx=WIND.v;} else {L.splice(i,1);continue;} }
    p.a=(p.a??1)+((overText(p.x,p.y)?.08:1)-(p.a??1))*Math.min(1,dt*9); cx.globalAlpha=p.a; draw(p); cx.globalAlpha=1;}
   if(now>nextBird&&!B.length){spawnBirds();nextBird=now+9000+Math.random()*12000;}
   for(let i=B.length-1;i>=0;i--){const b=B[i];b.bob+=dt*2;if(b.glide>0)b.glide-=dt;else if(Math.random()<dt*.35)b.glide=.6+Math.random()*1.2;
    if(b.land){const r=b.land.g.getBoundingClientRect(),tx=r.left+r.width/2,ty=r.top+r.height/2,dx=tx-b.x,dy=ty-b.y,d=Math.hypot(dx,dy);
     const sp=Math.min(small?150:190,40+d*1.6); b.vx+=(dx/(d||1)*sp-b.vx)*Math.min(1,dt*3); b.vy+=(dy/(d||1)*sp-b.vy)*Math.min(1,dt*3); b.glide=d<60?1:b.glide;
     b.x+=b.vx*dt; b.y+=b.vy*dt; if(d<8){b.land.away=false;b.land.g.classList.remove('away');B.splice(i,1);continue;} drawBird(b,t); continue;}
    if(b.up){b.vy-=60*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;if(b.y<-60||b.x<-80||b.x>W+80){B.splice(i,1);continue;}drawBird(b,t);continue;}
    b.x+=(b.vx+WIND.v*.15)*dt;b.y+=Math.sin(b.bob)*8*dt-(b.glide>0?-4:2)*dt;
    if(b.x<-80||b.x>W+80){B.splice(i,1);continue;}drawBird(b,t);}}
  requestAnimationFrame(tick);}
 requestAnimationFrame(tick);
})();

setLang(lang);
})();

/* "Chat with our AI" must open the chat, not just scroll near it (bug 7 Nov 2026: on phones the
   typing box sat under the bottom bar, so taps did nothing visible). */
document.querySelectorAll('a[href="#demo"]').forEach(a=>a.addEventListener('click',e=>{
  const box=document.getElementById('askin'); if(!box) return;
  e.preventDefault();
  document.getElementById('ask').scrollIntoView({behavior:'smooth',block:'center'});
  setTimeout(()=>box.focus({preventScroll:true}),350);
  history.replaceState(null,'','#demo');
}));

/* Netlify's free-plan badge is a fixed frame in the bottom-right corner that our CSS cannot touch.
   While it is on screen, lift the phone bottom bar above it; when it goes, the bar drops back. */
(()=>{const root=document.documentElement;
 const fit=()=>{const f=document.getElementById('nl-badge-frame');const r=f&&f.getBoundingClientRect();
  const h=r&&r.height>0&&r.bottom>=innerHeight-8?Math.ceil(innerHeight-r.top):0;
  root.style.setProperty('--badge-h',h+'px')};
 new MutationObserver(fit).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['style','hidden']});
 addEventListener('resize',fit);fit();setTimeout(fit,1500);})();
