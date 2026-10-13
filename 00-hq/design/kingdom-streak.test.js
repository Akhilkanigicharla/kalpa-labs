// Run: node 00-hq/design/kingdom-streak.test.js  (re-extract the streak block from kingdom-control-room.html if it changes)

function streakOf(days,nowIso){const RealNow=Date.now;Date.now=()=>Date.parse(nowIso)-5.5*3600e3;try{
  let streak=0,rests=0,lastRest=null,firstRest=null;const d=new Date(Date.now()+5.5*3600e3);
  const key=()=>d.toISOString().slice(0,10);
  if(!days.has(key()))d.setUTCDate(d.getUTCDate()-1);
  for(let guard=0;guard<400;guard++){
    if(days.has(key())){streak++;d.setUTCDate(d.getUTCDate()-1);continue;}
    const prev=new Date(d);prev.setUTCDate(prev.getUTCDate()-1);
    const canRest=streak>0&&days.has(prev.toISOString().slice(0,10))&&(lastRest===null||streak-lastRest>=6);
    if(!canRest)break;
    rests++;if(firstRest===null)firstRest=streak;lastRest=streak;d.setUTCDate(d.getUTCDate()-1);
  }
  const restUsedThisWeek=firstRest!==null&&firstRest<7;
return {streak,rests,restUsedThisWeek};}finally{Date.now=RealNow;}}
const D=(...a)=>new Set(a);
const t=(name,got,want)=>{const ok=JSON.stringify(got)===JSON.stringify(want);console.log(ok?"ok  ":"FAIL",name,JSON.stringify(got));if(!ok)process.exitCode=1;};
t("3 straight days",streakOf(D("2026-10-11","2026-10-12","2026-10-13"),"2026-10-13T12:00:00Z"),{streak:3,rests:0,restUsedThisWeek:false});
t("today not yet done",streakOf(D("2026-10-11","2026-10-12"),"2026-10-13T12:00:00Z"),{streak:2,rests:0,restUsedThisWeek:false});
t("one gap is a rest day",streakOf(D("2026-10-09","2026-10-10","2026-10-12","2026-10-13"),"2026-10-13T12:00:00Z"),{streak:4,rests:1,restUsedThisWeek:true});
t("two gaps in a week break it",streakOf(D("2026-10-08","2026-10-10","2026-10-12","2026-10-13"),"2026-10-13T12:00:00Z"),{streak:3,rests:1,restUsedThisWeek:true});
t("two-day gap breaks it",streakOf(D("2026-10-09","2026-10-12","2026-10-13"),"2026-10-13T12:00:00Z"),{streak:2,rests:0,restUsedThisWeek:false});
t("rest 6 days ago counts this week",streakOf(D(...["01","02","03","04","05","06","08","09","10","11","12","13"].map(x=>"2026-10-"+x)),"2026-10-13T12:00:00Z"),{streak:12,rests:1,restUsedThisWeek:true});
t("rest 8 days ago is last week",streakOf(D(...["01","02","03","06","07","08","09","10","11","12","13"].map(x=>"2026-10-"+x)),"2026-10-13T12:00:00Z"),{streak:8,rests:0,restUsedThisWeek:false});
t("two rests a week apart",streakOf(D(...["01","02","03","05","06","07","08","09","10","12","13"].map(x=>"2026-10-"+x)),"2026-10-13T12:00:00Z"),{streak:11,rests:2,restUsedThisWeek:true});
t("nothing",streakOf(D(),"2026-10-13T12:00:00Z"),{streak:0,rests:0,restUsedThisWeek:false});
