# CEO Room data refresh (4 Nov 2026): builds kl_tasks / kl_queue / agents / n8n_workflows / n8n_runs JSON from the GitHub agent queues and Actions.
# Usage: gh api ".../actions/workflows?per_page=100" > OUT/wf.json; gh api ".../actions/runs?per_page=30" > OUT/runs.json; python3 00-hq/tools/ceo_room_data.py OUT
# Then upload each JSON as an asset to the CEO Room artifact and point datasets/<id>.source.url at it.
import json,glob,os,re,sys
S=sys.argv[1]
wf=json.load(open(S+"/wf.json"))["workflows"]
desc={"agents":"All 8 worlds' agents work their task lists in parallel, hourly (free Groq/OpenRouter, Vigil checks)",
 "daily-brief":"9 PM IST Telegram brief to Akhil with alerts first","n8n-keepalive":"Keeps self-hosted n8n awake 6 AM-midnight",
 "n8n-sync":"Pushes workflows + keys from GitHub into self-hosted n8n","sloplint":"Hallmark design check on the website"}
rows=[{"id":"n8n-councils","name":"n8n · Kalpa Morning Councils (all worlds)","description":"Self-hosted n8n, 7:30 AM IST: each world's council, one Telegram message","active":True}]
for w in wf:
    n=os.path.basename(w["path"]).replace(".yml","")
    rows.append({"id":str(w["id"]),"name":"GitHub · "+w["name"],"description":desc.get(n,""),"active":w["state"]=="active"})
json.dump(rows,open(S+"/n8n_workflows.json","w"))
runs=json.load(open(S+"/runs.json"))["workflow_runs"]
rr=[{"id":str(r["id"]),"workflowId":str(r["workflow_id"]),"startedAt":r["run_started_at"],"mode":r["event"],"status":{"success":"success","failure":"error","cancelled":"canceled"}.get(r["conclusion"] or "", r["status"])} for r in runs[:20]]
json.dump(rr,open(S+"/n8n_runs.json","w"))
tasks=[]
for f in glob.glob("00-hq/tasks/*.json"):
    for t in json.load(open(f)):
        summ=""
        if t.get("output") and os.path.exists(t["output"]):
            body=open(t["output"]).read().split("\n",3)[-1]
            summ=re.sub(r"[#*_>|`\-]+"," ",body)
            summ=re.sub(r"\s+"," ",summ)[:400].strip()
        elif t.get("vigil_notes"): summ="Vigil: "+re.sub(r"\s+"," ",t["vigil_notes"])[:300]
        tasks.append({"id":t["id"],"title":t["title"],"owner_agent":t.get("owner",""),"stream":t["world"],"status":t["status"],"priority":t["priority"],"output_summary":summ,"updatedAt":t.get("updated",t["created"])})
tasks.sort(key=lambda t:t["updatedAt"],reverse=True)
json.dump(tasks,open(S+"/kl_tasks.json","w"))
json.dump([{"status":"todo","n":sum(t["status"]=="todo" for t in tasks)}],open(S+"/kl_queue.json","w"))
ow={}
for t in tasks: ow.setdefault(t["owner_agent"],t["updatedAt"])
json.dump([{"id":o,"name":o+" ("+", ".join(sorted({x['stream'] for x in tasks if x['owner_agent']==o}))+")","updatedAt":u,"published":True} for o,u in ow.items()],open(S+"/agents.json","w"))
print(len(rows),"automations",len(rr),"runs",len(tasks),"tasks",sum(t['status']=='review' for t in tasks),"review",len(ow),"agents")
