// Run: node 00-hq/design/kingdom-launch.test.js  (A63: runs the launch block of kingdom-control-room.html as-is)
const fs=require("fs"),path=require("path");
const html=fs.readFileSync(path.join(__dirname,"kingdom-control-room.html"),"utf8");
const block=html.slice(html.indexOf("// ---- launch:start ----"),html.indexOf("// ---- launch:end ----"));
const tasksSrc=html.slice(html.indexOf("const T=("),html.indexOf("\n];\n",html.indexOf("const TASKS=["))+4);
const L=new Function(tasksSrc+block+"return {TASKS,GATES,LAUNCH_QUESTS,daysTo,countdownText,gateProgress,readinessRows};")();
let fails=0;const t=(name,ok,got)=>{console.log(ok?"ok  ":"FAIL",name,ok?"":JSON.stringify(got));if(!ok)fails++;};
const all=[...L.TASKS,...L.LAUNCH_QUESTS],ids=all.map(x=>x.id);
t("quest ids unique",new Set(ids).size===ids.length,ids.filter((x,i)=>ids.indexOf(x)!==i));
L.GATES.forEach(g=>{
  t(`${g.id}: every needed quest exists`,g.needs.every(id=>ids.includes(id)),g.needs.filter(id=>!ids.includes(id)));
  const boss=all.find(x=>x.id===g.gate);t(`${g.id}: gate is a boss fight`,!!boss&&boss.g===true,boss);
});
t("launch boss needs the pilot boss",L.GATES[1].needs.includes("LP"));
t("exactly two boss gates in launch quests",L.LAUNCH_QUESTS.filter(x=>x.g).length===2);
t("dates match SOFT-LAUNCH.md",["16 Nov 2026","13 Dec 2026"].every(d=>fs.readFileSync(path.join(__dirname,"../SOFT-LAUNCH.md"),"utf8").includes(d))&&L.GATES[0].at.startsWith("2026-11-16")&&L.GATES[1].at.startsWith("2026-12-13T06:12"));
const now=Date.parse("2026-10-22T23:00:00+05:30");
t("25 days to Pilot Day from 22 Oct night",L.daysTo(L.GATES[0].at,now)===25,L.daysTo(L.GATES[0].at,now));
t("52 days to Soft launch",L.daysTo(L.GATES[1].at,now)===52,L.daysTo(L.GATES[1].at,now));
t("1 day uses singular",L.countdownText(L.GATES[0],Date.parse("2026-11-15T10:00:00+05:30"))==="1 day to Mon 16 Nov");
t("past date never negative",L.daysTo(L.GATES[0].at,Date.parse("2026-12-01T00:00:00Z"))===0&&/day reached/.test(L.countdownText(L.GATES[0],Date.parse("2026-12-01T00:00:00Z"))));
const st=Object.fromEntries(L.GATES[0].needs.map(id=>[id,"done"]));
t("gate ready when all done",L.gateProgress(L.GATES[0],id=>st[id]||"todo").ready===true);
t("gate not ready with one open",L.gateProgress(L.GATES[1],id=>id==="LP"?"done":"todo").done===1);
t("no readiness yet",L.readinessRows(null).known===false&&L.readinessRows({}).known===false);
const r=L.readinessRows({generated_at:"2026-10-22T23:09:32+05:30",rows:[{id:"O1",label:"BotBhai",ok:false,checks:[{kind:"roadmap",ok:true},{kind:"env",ok:false,reason:"env not set: X"}]},{id:"R3",label:"Audit",ok:true,checks:[]}]});
t("readiness rows: first red reason",r.known&&r.green===1&&r.total===2&&r.rows[0].why==="env not set: X"&&r.rows[1].why==="",r);
// the real board output parses
const {execFileSync}=require("child_process");
let real=null;try{real=JSON.parse(execFileSync("python3",[path.join(__dirname,"../launch/check.py"),"--json"],{encoding:"utf8"}));}catch(e){real=e.stdout?JSON.parse(e.stdout):null;}
const rr=L.readinessRows(real);t("check.py --json renders 11 rows",rr.known&&rr.total===11,rr.total);
process.exitCode=fails?1:0;
