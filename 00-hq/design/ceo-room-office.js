/* CEO Room · live robot office (A137). Loaded by ceo-room-dashboard.html as files/office.js.
   Reads KL Tasks (n8n) and decorates the office drawn by the main script:
   real job bubbles, verdict badges, couriers walking drafts to Vigil, the council table,
   tap-a-robot job list and live counters. Data values are shown with textContent only. */
(function(){
 dash.loader('kl_queue',{description:'The table\'s own count of jobs waiting (status todo), as one row.',
  fn:({answer})=>{const a=typeof answer==='string'?JSON.parse(answer):answer;
   if(!a||typeof a.count!=='number') throw new Error('n8n answer had no count: '+Object.keys(a||{}).join(', '));
   return [{status:'todo',n:a.count}];}});
 dash.calc('kl_done_by_day',{inputs:['kl_tasks'],title:'Jobs checked by Vigil per day',
  description:'Latest 100 KL Tasks jobs: passed (review/done) and sent back (rejected), by the IST date of their last change.',
  fn:(kl_tasks)=>{const m={}; kl_tasks.forEach(t=>{const ok=t.status==='review'||t.status==='done', bad=t.status==='rejected'; if(!ok&&!bad) return;
   const day=new Date(new Date(t.updatedAt).getTime()+19800000).toISOString().slice(0,10); const o=m[day]||(m[day]={day,passed:0,redo:0}); if(ok) o.passed++; else o.redo++;});
   return Object.keys(m).sort().map(d=>m[d]);}});
 dash.calc('team_models',{inputs:['roster'],title:'Free models on the team',description:'Each free model in the agent roster and how many agents run on it.',
  fn:(roster)=>{const m={}; roster.forEach(r=>{const k=r.model||r.host||'unknown'; m[k]=(m[k]||0)+1;}); return Object.keys(m).map(model=>({model,agents:m[model]})).sort((a,b)=>b.agents-a.agents);}});
 dash.calc('office_kpis',{inputs:['kl_queue','team_models'],title:'Office counters',description:'Jobs waiting in KL Tasks, and how many free models the team runs on.',
  fn:(kl_queue,team_models)=>[{metric:'queue',value:kl_queue.length?kl_queue[0].n:0},{metric:'models',value:team_models.length}]});

 const NS='http://www.w3.org/2000/svg';
 const reduce=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
 const istDay=d=>new Date(new Date(d).getTime()+19800000).toISOString().slice(0,10);
 const istHour=d=>new Date(new Date(d).getTime()+19800000).getUTCHours();
 const fmt=d=>new Date(d).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:false});
 const el=(tag,attrs,parent)=>{const e=document.createElementNS(NS,tag); for(const k in attrs) e.setAttribute(k,attrs[k]); if(parent) parent.append(e); return e;};
 const h=(tag,cls,t)=>{const e=document.createElement(tag); if(cls) e.className=cls; if(t!=null) e.textContent=t; return e;};
 const clean=t=>String(t||'').replace(/^(\s*\([^)]*\)\s*)+/,'').replace(/\s+/g,' ').trim();
 const short=(t,n)=>{t=clean(t); return t.length>n?t.slice(0,n-1).trimEnd()+'…':t;};
 const STATUS={todo:['Queued',''],doing:['Working','p-warn'],review:['Passed Vigil','p-ok'],done:['Done','p-ok'],rejected:['Redo','p-bad']};
 const word=s=>(STATUS[s]||[s||'—',''])[0];
 const verdict=s=>s==='review'||s==='done'?'ok':s==='rejected'?'bad':null;
 const tasks=()=>{const d=dash.data('kl_tasks'); return d.status==='ok'?d.data:null;};
 const roster=()=>{const d=dash.data('agent_board'); return d.status==='ok'?d.data.map(r=>r.agent):[];};
 const jobsOf=(rows,name)=>rows.filter(t=>t.owner_agent===name);
 const pos=g=>{const m=/translate\(([-\d.]+)[ ,]+([-\d.]+)\)/.exec(g.getAttribute('transform')||''); return m?[+m[1],+m[2]]:null;};

 function badge(parent,x,y,v){const g=el('g',{'data-kx':'',transform:`translate(${x},${y})`},parent);
  el('circle',{r:7.5,fill:v==='ok'?'var(--color-ok)':'var(--color-bad)'},g);
  el('path',{d:v==='ok'?'M-3.4 0.2 L-1 2.6 L3.6 -2.4':'M-2.8 -2.8 L2.8 2.8 M2.8 -2.8 L-2.8 2.8',stroke:'#fff','stroke-width':2,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'},g); return g;}

 let litNow=null;
 function decorate(){
  const svg=document.querySelector('#scene svg'); if(!svg) return;
  svg.querySelectorAll('[data-kx]').forEach(n=>n.remove());
  const rows=tasks(); if(!rows) return;
  const latest={}; rows.forEach(t=>{const p=latest[t.owner_agent]; if(!p||t.updatedAt>p.updatedAt) latest[t.owner_agent]=t;});
  const labels=svg.lastElementChild, things=labels.previousElementSibling;
  // 1. speech bubbles say the robot's real latest job
  const fresh=Object.values(latest).sort((a,b)=>a.updatedAt<b.updatedAt?1:-1).map(t=>t.owner_agent);
  const shown=fresh.filter(n=>svg.querySelector(`g.bubble[data-agent="${CSS.escape(n)}"]`)).slice(0,4);
  svg.querySelectorAll('g.bubble[data-agent]').forEach(bu=>{const name=bu.getAttribute('data-agent'), t=latest[name], tx=bu.querySelector('text'), r=bu.querySelector('rect'); if(!t||!tx||!r) return;
   const line=word(t.status)+': '+short(t.title,30); tx.textContent=line; r.setAttribute('width',String(line.length*6.1+20));
   if(reduce) bu.style.opacity=shown.includes(name)?'1':'0';});
  // 2. a green tick or red redo beside each robot whose last job Vigil checked
  const bots={}; svg.querySelectorAll('g.bot[data-agent]').forEach(g=>{bots[g.getAttribute('data-agent')]=pos(g);});
  Object.keys(bots).forEach(name=>{const t=latest[name], v=t&&verdict(t.status), p=bots[name]; if(!v||!p) return; const w=Math.max(46,name.length*6.4+24); badge(labels,p[0]+w/2+9,p[1]-91.5,v);});
  // 3. couriers walk finished drafts to Vigil's desk, who stamps them
  const vig=bots.Vigil;
  if(vig&&!reduce&&window.kxBot){
   const sent=fresh.filter(n=>n!=='Vigil'&&bots[n]&&verdict(latest[n].status)).slice(0,4);
   sent.forEach((name,k)=>{const a=bots[name], v=verdict(latest[name].status), dest=[vig[0]-34+k*20,vig[1]+26];
    const len=Math.hypot(dest[0]-a[0],dest[1]-a[1]), dur=Math.max(6,len/28*2).toFixed(1)+'s', begin=(-k*2.3).toFixed(1)+'s';
    const g=el('g',{'data-kx':''},things); window.kxBot(g,'var(--kv-gold)',{walk:true,carry:true,delay:k*.2});
    el('animateMotion',{dur,begin,repeatCount:'indefinite',path:`M${a[0]},${a[1]+6} L${dest[0]},${dest[1]} L${a[0]},${a[1]+6}`},g);
    const b=badge(labels,dest[0],dest[1]-86,v); b.setAttribute('opacity','0');
    el('animate',{attributeName:'opacity',values:'0;0;1;1;0;0',keyTimes:'0;0.44;0.5;0.66;0.72;1',dur,begin,repeatCount:'indefinite'},b);});
  }
  // 4. the council table, lit while the 06:00 IST council sits (or a seat filed in the last hour)
  const known=new Set(roster()), seats=Object.keys(latest).filter(n=>!known.has(n)).sort((a,b)=>a==='Council'?-1:b==='Council'?1:(latest[a].updatedAt<latest[b].updatedAt?1:-1)).slice(0,8);
  const now=Date.now(), last=seats.map(n=>latest[n].updatedAt).sort().pop();
  const lit=istHour(now)===6||!!(last&&now-new Date(last)<36e5); litNow=lit;
  const cx=330,cy=612, T=el('g',{'data-kx':'',class:'kx-council'+(lit?' lit':''),id:'council-table'},things);
  if(lit) el('ellipse',{cx,cy,rx:156,ry:64,class:'kx-council-glow'},T);
  el('ellipse',{cx,cy:cy+9,rx:118,ry:46,fill:'color-mix(in srgb,var(--kv-bark) 70%,#000)'},T);
  el('ellipse',{cx,cy,rx:118,ry:46,fill:'var(--kv-bark)'},T);
  el('ellipse',{cx,cy,rx:100,ry:36,fill:'none',stroke:'var(--kv-gold)','stroke-width':1.4,opacity:lit?.95:.4},T);
  seats.forEach((n,i)=>{const ang=-Math.PI/2+i*(2*Math.PI/seats.length), sx=cx+Math.cos(ang)*136, sy=cy+Math.sin(ang)*58;
   const v=verdict(latest[n].status), s=el('g',{class:'bot','data-agent':n,transform:`translate(${sx.toFixed(1)},${sy.toFixed(1)}) scale(.62)`,tabindex:'0',role:'button','aria-label':n+': latest job '+word(latest[n].status)},T);
   if(window.kxBot) window.kxBot(s,v==='ok'?'var(--color-ok)':v==='bad'?'var(--color-bad)':'var(--kv-gold)',{delay:(i*.3).toFixed(1)});
   const open=()=>openJobs(n); s.addEventListener('click',open); s.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault(); open();}});
   const tag=el('text',{x:sx,y:sy+14,'text-anchor':'middle',class:'sign-s','data-kx':''},labels); tag.textContent=short(n,14);});
  const sign=(lit?'Council in session':'Council table · sits 06:00 IST')+(last?' · last '+fmt(last):'');
  const sw=sign.length*6.6+28; el('rect',{x:cx-sw/2,y:cy+86,width:sw,height:24,rx:12,class:'sign','data-kx':''},labels);
  const st=el('text',{x:cx,y:cy+102,'text-anchor':'middle',class:'sign-t','data-kx':''},labels); st.textContent=sign;
 }

 function jobList(ol,name){
  const rows=tasks(); if(!rows){ol.replaceChildren(h('li','kx-note','—')); return;}
  const mine=jobsOf(rows,name).slice(0,5);
  ol.replaceChildren(...(mine.length?mine.map(t=>{const li=h('li'); li.dataset.key=String(t.id); const [lbl,cls]=STATUS[t.status]||[t.status,''];
   const top=h('div','kx-job-top'); const p=h('span','kx-pill '+cls); p.append(document.createElement('i'),document.createTextNode(lbl)); top.append(p,h('span','kx-sub',fmt(t.updatedAt)+' IST'));
   const d=h('details'); d.append(h('summary',null,clean(t.title)),h('p','kx-job-sum',t.output_summary?String(t.output_summary):'No draft yet.'));
   li.append(top,d); return li;}):[h('li','kx-note','No jobs for '+name+' among the latest 100.')]));
 }
 function openJobs(name){
  const box=document.getElementById('office-jobs'); if(!box) return;
  box.hidden=false; box.dataset.agent=name; document.getElementById('oj-name').textContent=name+' · last 5 jobs';
  document.getElementById('oj-team').hidden=!roster().includes(name);
  jobList(document.getElementById('oj-list'),name); box.scrollIntoView({block:'nearest',behavior:reduce?'auto':'smooth'});
 }
 window.kxOpenJobs=openJobs;
 document.getElementById('oj-close').addEventListener('click',()=>{document.getElementById('office-jobs').hidden=true;});
 document.getElementById('oj-team').addEventListener('click',()=>{const n=document.getElementById('office-jobs').dataset.agent; if(n&&window.kxShowTeam) window.kxShowTeam(n);});

 function counters(){
  const d=dash.data('kl_done_by_day'), today=istDay(Date.now());
  [['oc-passed','passed'],['oc-redo','redo']].forEach(([id,f])=>{const e=document.getElementById(id); if(!e) return;
   if(d.status!=='ok'){e.textContent='—'; return;}
   const r=d.data.find(x=>x.day===today);
   if(r){e.setAttribute('data-field',f); e.setAttribute('data-where','day='+today); e.textContent=String(r[f]);} else {e.removeAttribute('data-field'); e.removeAttribute('data-where'); e.textContent='0';}});
  const k=dash.data('office_kpis');
  document.querySelectorAll('#office-counters [data-source=office_kpis]').forEach(e=>{const m=e.getAttribute('data-where').split('=')[1]; const r=k.status==='ok'?k.data.find(x=>x.metric===m):null; e.textContent=r?String(r.value):'—';});
  const tm=dash.data('team_models'), sub=document.getElementById('oc-models');
  if(sub) sub.textContent=tm.status==='ok'&&tm.data.length?'free models: '+tm.data.map(r=>String(r.model).split('/').pop()).join(' · '):'free models in use';
 }
 function refresh(){
  counters(); decorate();
  const box=document.getElementById('office-jobs'); if(box&&!box.hidden&&box.dataset.agent) jobList(document.getElementById('oj-list'),box.dataset.agent);
  const bd=document.getElementById('bd-jobs'), nm=document.getElementById('bd-name');
  if(bd&&nm&&!nm.closest('[hidden]')) jobList(bd,nm.textContent.split(' · ')[0]);
 }
 const scene=document.getElementById('scene');
 new MutationObserver(()=>decorate()).observe(scene,{childList:true});
 const nm=document.getElementById('bd-name');
 if(nm) new MutationObserver(()=>{const bd=document.getElementById('bd-jobs'); if(bd) jobList(bd,nm.textContent.split(' · ')[0]);}).observe(nm,{childList:true,characterData:true,subtree:true});
 dash.onData(refresh);
 // once a minute: counters (a new IST day) and the council light; redraw only when the light changes, so walkers keep walking
 setInterval(()=>{counters(); const rows=tasks(); if(!rows) return; const known=new Set(roster());
  const last=rows.filter(t=>!known.has(t.owner_agent)).map(t=>t.updatedAt).sort().pop(), now=Date.now();
  if((istHour(now)===6||!!(last&&now-new Date(last)<36e5))!==litNow) decorate();},60000);
})();
