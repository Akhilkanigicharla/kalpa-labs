/* CEO Room · live robot rooms. Loaded by ceo-room-dashboard.html as files/rooms.js.
   Reads Cloudflare D1 `kalpa-live` (filled by 00-hq/agents/live_status.py): one robot per working agent,
   one machine per GitHub workflow, 8 rooms (HQ + 7 worlds). Data values are shown with textContent only. */
(function(){
 const rowsOf=answer=>{const a=typeof answer==='string'?JSON.parse(answer):answer;
  const first=Array.isArray(a)?a[0]:a; if(!first||!Array.isArray(first.results)) throw new Error('D1 answer had no results');
  return first.results;};
 ['live_agents','live_runs','live_meta'].forEach(id=>dash.loader(id,{description:'Cloudflare D1 answers [{results:[rows]}]; this takes the rows.',fn:({answer})=>rowsOf(answer)}));

 const ROOMS=[['hq','HQ','Kalpa head office'],['b1','BotBhai','WhatsApp bots'],['b2','JobCard','Technician app'],['b3','Kits','Exam kits'],
  ['b4','Extensions','Tab Lifeboat'],['b5','Deals','Telugu deals'],['b6','FinOps','Ledger Peaks'],['b7','Trading','Trading Lab']];
 const LOOK={working:['var(--color-warn)','Working now'],queued:['var(--kx-a,#4a7c59)','Job waiting'],'needs review':['var(--color-ok)','Draft ready, needs review'],
  redo:['var(--color-bad)','Sent back to redo'],done:['var(--color-ok)','Done'],idle:['var(--color-fg-muted)','Resting'],
  ready:['color-mix(in srgb,var(--color-ok) 60%,var(--color-fg-muted))','Ready: runs by itself'],
  'on call':['color-mix(in srgb,var(--color-ok) 30%,var(--color-fg-muted))','On call: Claude runs it when needed'],
  'needs you':['color-mix(in srgb,var(--color-warn) 55%,var(--color-bad))','Needs you (Claude prepares it)'],
  planned:['var(--color-border-line)','Planned, not built yet']};
 const NEXT={working:'It is on the job right now.',queued:'It starts at the next agent run (every hour at :20).',
  'needs review':'Claude checks this draft in the next build session; good ones go to you.',redo:'The checker found problems; it retries on the next run.',
  done:'Finished and accepted.',idle:'No job for it now. New jobs come from the roadmap.',
  ready:'A program or n8n workflow does this job automatically when its trigger fires.',
  'on call':'Claude does this job in a build sprint or scheduled task, following its spec.',
  'needs you':'This step needs Akhil (a login, a signature, a visit); Claude prepares everything first.',
  planned:'Designed in the registry; it gets built when its roadmap item comes up.'};
 const ORDER=['working','queued','needs review','redo','needs you','done','ready','on call','idle','planned'];
 const SHOW=24; const open={};
 const reduce=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
 const h=(tag,cls,t)=>{const e=document.createElement(tag); if(cls) e.className=cls; if(t!=null) e.textContent=t; return e;};
 const NS='http://www.w3.org/2000/svg';
 const s=(tag,attrs,p)=>{const e=document.createElementNS(NS,tag); for(const k in attrs) e.setAttribute(k,attrs[k]); if(p) p.append(e); return e;};
 const ago=iso=>{if(!iso) return '—'; const m=Math.round((Date.now()-new Date(iso).getTime())/60000);
  return m<1?'just now':m<60?m+' min ago':m<1440?Math.round(m/60)+' h ago':Math.round(m/1440)+' d ago';};

 const css=document.createElement('style');
 css.textContent=`
#rooms .lr-head{display:flex;flex-wrap:wrap;gap:.4rem 1rem;align-items:baseline;justify-content:space-between}
#rooms .lr-legend{display:flex;flex-wrap:wrap;gap:.3rem .8rem;margin:.4rem 0 .8rem;font-size:var(--cds-font-size-caption,12px);color:var(--color-fg-muted)}
#rooms .lr-legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:.3rem;vertical-align:-1px}
#rooms .lr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:.7rem}
#rooms .lr-room{border:1px solid var(--color-border-line);border-radius:14px;background:var(--color-panel);padding:.6rem .6rem .5rem;min-width:0}
#rooms .lr-room h4{margin:0;font-size:15px;font-weight:600;color:var(--color-fg)}
#rooms .lr-room .lr-sub{font-size:12px;color:var(--color-fg-muted);margin:0 0 .4rem}
#rooms .lr-floor{display:flex;flex-wrap:wrap;gap:.2rem;min-height:72px;align-items:flex-end;border-bottom:3px solid var(--color-border-line);padding-bottom:.2rem}
#rooms .lr-bot{all:unset;box-sizing:border-box;cursor:pointer;width:52px;min-height:72px;display:flex;flex-direction:column;align-items:center;border-radius:10px}
#rooms .lr-bot:focus-visible{outline:2px solid var(--color-fg);outline-offset:2px}
#rooms .lr-bot[aria-pressed=true]{background:color-mix(in srgb,var(--color-fg) 8%,transparent)}
#rooms .lr-bot svg{width:40px;height:48px;overflow:visible}
#rooms .lr-bot span{font-size:11px;line-height:1.2;color:var(--color-fg);max-width:52px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rooms .lr-empty{font-size:12px;color:var(--color-fg-muted);align-self:center}
#rooms .lr-more{all:unset;box-sizing:border-box;cursor:pointer;min-height:44px;padding:0 .8rem;margin-top:.4rem;border:1px solid var(--color-border-line);border-radius:999px;font-size:13px;color:var(--color-fg);display:inline-flex;align-items:center}
#rooms .lr-more:focus-visible{outline:2px solid var(--color-fg);outline-offset:2px}
#rooms .lr-mach{display:flex;flex-wrap:wrap;gap:.25rem;margin-top:.4rem}
#rooms .lr-m{display:inline-flex;align-items:center;gap:.25rem;font-size:11px;border:1px solid var(--color-border-line);border-radius:999px;padding:.1rem .45rem;color:var(--color-fg)}
#rooms .lr-m b{width:8px;height:8px;border-radius:50%;display:inline-block}
#rooms .lr-roles{font-size:11px;color:var(--color-fg-muted);margin-top:.35rem}
#rooms .lr-card{margin-top:.8rem;border:1px solid var(--color-border-line);border-radius:12px;padding:.7rem .8rem;background:var(--color-bg)}
#rooms .lr-card h4{margin:0 0 .2rem;font-size:15px}
#rooms .lr-card p{margin:.2rem 0;font-size:14px;color:var(--color-fg)}
#rooms .lr-card .lr-mut{color:var(--color-fg-muted);font-size:13px}
#rooms .lr-sum{display:flex;flex-wrap:wrap;gap:.4rem .9rem;font-size:13px;margin:.2rem 0 .2rem;color:var(--color-fg)}
@media (prefers-reduced-motion:no-preference){
 #rooms .lr-working .lr-body{animation:lr-bob 1.1s ease-in-out infinite}
 #rooms .lr-working .lr-ant{animation:lr-ant .8s steps(2) infinite}
 #rooms .lr-working .lr-arm{animation:lr-type .5s ease-in-out infinite alternate;transform-origin:20px 30px}
 #rooms .lr-queued .lr-eye{animation:lr-blink 3.2s infinite;transform-origin:center;transform-box:fill-box}
 #rooms .lr-spin{animation:lr-spin 1.4s linear infinite;transform-origin:center;transform-box:fill-box}
}
@keyframes lr-bob{50%{transform:translateY(-3px)}}
@keyframes lr-ant{50%{opacity:.25}}
@keyframes lr-type{to{transform:rotate(-14deg)}}
@keyframes lr-blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes lr-spin{to{transform:rotate(360deg)}}`;
 document.head.append(css);

 function robot(state){
  const c=(LOOK[state]||LOOK.idle)[0]; const svg=s('svg',{viewBox:'0 0 40 48','aria-hidden':'true'});
  const g=s('g',{class:'lr-body'},svg);
  s('line',{x1:20,y1:3,x2:20,y2:9,stroke:'var(--color-fg-muted)','stroke-width':2},g);
  s('circle',{class:'lr-ant',cx:20,cy:3,r:2.6,fill:c},g);
  s('rect',{x:8,y:9,width:24,height:17,rx:6,fill:'var(--color-panel)',stroke:c,'stroke-width':2.4},g);
  const eyeY=state==='idle'?18:17;
  if(state==='idle'){s('path',{d:'M13 18h5M22 18h5',stroke:'var(--color-fg)','stroke-width':2,'stroke-linecap':'round'},g);}
  else{s('circle',{class:'lr-eye',cx:15,cy:eyeY,r:2.4,fill:'var(--color-fg)'},g); s('circle',{class:'lr-eye',cx:25,cy:eyeY,r:2.4,fill:'var(--color-fg)'},g);}
  if(state==='redo') s('path',{d:'M15 23q5-3 10 0',stroke:'var(--color-fg)','stroke-width':1.6,fill:'none'},g);
  else if(state!=='idle') s('path',{d:'M15 22q5 3 10 0',stroke:'var(--color-fg)','stroke-width':1.6,fill:'none'},g);
  s('rect',{x:11,y:28,width:18,height:13,rx:4,fill:c,opacity:.9},g);
  s('rect',{class:'lr-arm',x:29,y:29,width:4,height:9,rx:2,fill:c},g);
  s('rect',{x:7,y:29,width:4,height:9,rx:2,fill:c},g);
  s('rect',{x:13,y:41,width:5,height:6,rx:2,fill:'var(--color-fg-muted)'},svg);
  s('rect',{x:22,y:41,width:5,height:6,rx:2,fill:'var(--color-fg-muted)'},svg);
  if(state==='needs review'){const b=s('g',{transform:'translate(33,9)'},svg); s('circle',{r:6,fill:'var(--color-ok)'},b);
   s('path',{d:'M-2.6 0 L-.6 2.2 L2.8 -2',stroke:'#fff','stroke-width':1.8,fill:'none','stroke-linecap':'round'},b);}
  if(state==='redo'){const b=s('g',{transform:'translate(33,9)'},svg); s('circle',{r:6,fill:'var(--color-bad)'},b);
   s('path',{d:'M-2.2 -2.2 L2.2 2.2 M2.2 -2.2 L-2.2 2.2',stroke:'#fff','stroke-width':1.8,'stroke-linecap':'round'},b);}
  return svg;
 }

 let picked=null;
 function draw(){
  const root=document.getElementById('lr-grid'), sum=document.getElementById('lr-sum'), upd=document.getElementById('lr-updated'), card=document.getElementById('lr-card');
  if(!root) return;
  const A=dash.data('live_agents'), R=dash.data('live_runs'), M=dash.data('live_meta');
  root.replaceChildren(); sum.replaceChildren();
  if(A.status!=='ok'){upd.textContent='—'; root.append(h('p','lr-empty',A.status==='loading'?'Loading the rooms…':'Rooms not loaded yet.')); card.hidden=true; return;}
  const agents=A.data, runs=R.status==='ok'?R.data:[], meta={}; (M.status==='ok'?M.data:[]).forEach(r=>meta[r.k]=r.v);
  upd.textContent='Updated '+ago(meta.refreshed_at);
  const count=st=>agents.filter(a=>a.state===st).length;
  [['working','working now'],['queued','waiting to start'],['needs review','drafts ready'],['redo','to redo'],['needs you','need you'],['ready','ready'],['on call','on call'],['idle','resting'],['planned','planned']].forEach(([st,label])=>{
   const n=count(st); if(!n&&st!=='working') return; const x=h('span',null); const i=h('i'); i.style.background=(LOOK[st]||LOOK.idle)[0];
   i.style.cssText+=';display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:.3rem'; x.append(i, h('b',null,String(n)), document.createTextNode(' '+label)); sum.append(x);});
  ROOMS.forEach(([id,name,sub])=>{
   const room=h('div','lr-room'); room.id='lr-room-'+id;
   const rank=st=>{const i=ORDER.indexOf(st); return i<0?99:i;};
   const mine=agents.filter(a=>a.room===id).sort((x,y)=>rank(x.state)-rank(y.state)||String(x.name).localeCompare(String(y.name)));
   room.append(h('h4',null,name), h('p','lr-sub',`${sub} · ${mine.length} robot${mine.length===1?'':'s'}`));
   const floor=h('div','lr-floor');
   if(!mine.length) floor.append(h('span','lr-empty','No agent working here yet'));
   const shown=open[id]?mine:mine.slice(0,SHOW);
   if(picked&&!shown.some(a=>a.id===picked)){const p=mine.find(a=>a.id===picked); if(p) shown.push(p);}
   shown.forEach(a=>{const b=h('button','lr-bot lr-'+String(a.state).replace(/\s+/g,'-')); b.type='button';
    b.setAttribute('aria-label',`${a.name}, ${(LOOK[a.state]||[0,a.state])[1]}`); b.setAttribute('aria-pressed',String(picked===a.id));
    b.append(robot(a.state), h('span',null,a.name)); b.addEventListener('click',()=>{picked=picked===a.id?null:a.id; draw();}); floor.append(b);});
   room.append(floor);
   if(mine.length>SHOW){const more=h('button','lr-more',open[id]?'Show fewer':`Show all ${mine.length} robots`); more.type='button';
    more.setAttribute('aria-expanded',String(!!open[id])); more.addEventListener('click',()=>{open[id]=!open[id]; draw();}); room.append(more);}
   const mach=runs.filter(r=>r.room===id);
   if(mach.length){const m=h('div','lr-mach'); mach.forEach(r=>{const running=r.status==='in_progress'||r.status==='queued';
     const col=running?'var(--color-warn)':r.conclusion==='success'?'var(--color-ok)':r.conclusion?'var(--color-bad)':'var(--color-fg-muted)';
     const x=h('span','lr-m'); const dot=h('b',running?'lr-spin':null); dot.style.background=col; x.title=`${r.workflow}: ${running?'running':r.conclusion||r.status} · ${ago(r.started_at)}`;
     x.append(dot, document.createTextNode(r.workflow)); m.append(x);}); room.append(m);}
   root.append(room);});
  const a=agents.find(x=>x.id===picked);
  card.hidden=!a; card.replaceChildren();
  if(a){const room=(ROOMS.find(r=>r[0]===a.room)||[0,a.room])[1];
   card.append(h('h4',null,`${a.name} · ${room}`), h('p',null,(LOOK[a.state]||[0,a.state])[1]+' · '+ago(a.updated_at)),
    h('p',null,a.task||'—'), h('p','lr-mut',NEXT[a.state]||''), h('p','lr-mut',`${a.team} · ${a.runs_as}${a.detail?' · '+a.detail:''}`));
   const close=h('button','kx-btn','Close'); close.type='button'; close.style.minHeight='44px'; close.addEventListener('click',()=>{picked=null; draw();}); card.append(close);}
 }
 const rb=document.getElementById('lr-refresh'); if(rb) rb.addEventListener('click',()=>{ if(rb.disabled) return; rb.disabled=true; rb.textContent='Refreshing…'; // UX 8: one refresh per 5 s
  ['live_agents','live_runs','live_meta'].forEach(id=>dash.refresh(id)); setTimeout(()=>{rb.disabled=false; rb.textContent='Refresh now';},5000);});
 dash.onData(draw);
 setInterval(()=>{const u=document.getElementById('lr-updated'); const M=dash.data('live_meta'); if(u&&M.status==='ok'){const r=M.data.find(x=>x.k==='refreshed_at'); if(r) u.textContent='Updated '+ago(r.v);}},60000);
})();
