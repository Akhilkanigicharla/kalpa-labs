"""
BotBhai voice agent — answers (and, for consented leads, places) real phone calls.

Stack (open source + free tiers): Pipecat 1.12 · Sarvam STT/TTS (Indian languages, Hinglish) ·
Groq LLM · Silero VAD · telephony by Plivo or Exotel (paid per minute, billed to the client).

Run:   pip install -r requirements.txt && uvicorn agent:app --host 0.0.0.0 --port 8080
Env:   SARVAM_API_KEY, GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WA_ACCESS_TOKEN,
       PUBLIC_HOST (e.g. voice.example.com), PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN (for Plivo)
Calls: Plivo number → Answer URL https://PUBLIC_HOST/plivo/answer?client=<client uuid>
       Exotel → Voicebot applet → wss://PUBLIC_HOST/ws?client=<client uuid>
"""
import asyncio
import os
from datetime import datetime

import aiohttp
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.utils import _create_telephony_transport, parse_telephony_websocket
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

import prompt as P

SB_URL, SB_KEY = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
app = FastAPI(title="BotBhai voice agent")


async def sb(session: aiohttp.ClientSession, path: str, method="GET", body=None, prefer="return=representation"):
    async with session.request(method, f"{SB_URL}/rest/v1/{path}", json=body,
                               headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Prefer": prefer}) as r:
        r.raise_for_status()
        return await r.json() if r.content_length != 0 and method != "PATCH" else None


async def whatsapp(session, phone_number_id: str, to: str, text: str):
    if not (phone_number_id and to):
        return
    async with session.post(f"https://graph.facebook.com/v21.0/{phone_number_id}/messages",
                            headers={"Authorization": f"Bearer {os.getenv('WA_ACCESS_TOKEN')}"},
                            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}) as r:
        return r.status


@app.post("/plivo/answer")
async def plivo_answer(request: Request):
    client = request.query_params.get("client", "")
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><Response><Stream bidirectional="true" keepCallAlive="true" '
           f'contentType="audio/x-mulaw;rate=8000">wss://{os.getenv("PUBLIC_HOST")}/ws?client={client}</Stream></Response>')
    return Response(content=xml, media_type="application/xml")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    client_id = websocket.query_params.get("client", "")
    transport_type, call_data = await parse_telephony_websocket(websocket)
    caller = "".join(ch for ch in str(call_data.get("from_number") or call_data.get("body", {}).get("from", "")) if ch.isdigit())
    async with aiohttp.ClientSession() as http:
        rows = await sb(http, f"clients?id=eq.{client_id}&active=eq.true&select=*")
        if not rows:
            await websocket.close()
            return
        client = rows[0]
        cfg = P.load_setup(client["niche"], client.get("config") or {})
        await run_call(websocket, transport_type, call_data, http, client, cfg, caller)


async def run_call(websocket, transport_type, call_data, http, client, cfg, caller):
    transport = await _create_telephony_transport(
        websocket,
        FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True, vad_analyzer=SileroVADAnalyzer()),
        transport_type, call_data)
    stt = SarvamSTTService(api_key=os.getenv("SARVAM_API_KEY"), settings=SarvamSTTService.Settings(model="saaras:v3"))
    tts = SarvamTTSService(api_key=os.getenv("SARVAM_API_KEY"), settings=SarvamTTSService.Settings(model="bulbul:v3", voice="priya" if client["niche"] in ("salon", "examkits") else "rahul"))
    llm = GroqLLMService(api_key=os.getenv("GROQ_API_KEY"), settings=GroqLLMService.Settings(model="llama-3.3-70b-versatile"))

    specs = P.tools(cfg)
    schemas = [FunctionSchema(name=t["name"], description=t["description"], properties=t["properties"], required=t["required"]) for t in specs]
    context = LLMContext(messages=[{"role": "system", "content": P.system_prompt(cfg)}], tools=ToolsSchema(standard_tools=schemas))
    agg = LLMContextAggregatorPair(context)

    async def book(params):
        a = dict(params.arguments)
        details = {k: v for k, v in a.items() if k != "name"}
        if "date" in details:
            details["date_iso"] = details["date"]
            details["date"] = datetime.fromisoformat(details["date"]).strftime("%a, %d %b")
        await sb(http, "leads?on_conflict=client_id,contact", "POST", {
            "client_id": client["id"], "contact": caller or f"call:{datetime.now().timestamp():.0f}", "name": a.get("name"),
            "score": "hot", "status": "booked", "source": "voice", "details": details,
            "updated_at": datetime.utcnow().isoformat() + "Z"}, prefer="resolution=merge-duplicates")
        summary = ", ".join(f"{k}: {v}" for k, v in details.items() if k != "date_iso")
        await whatsapp(http, client.get("phone_number_id"), caller, f"✅ Booked with {cfg['business']} — {summary}. Reply here if anything changes.")
        await whatsapp(http, client.get("phone_number_id"), client.get("owner_whatsapp"), f"📞 Voice booking: {a.get('name')} ({caller}) — {summary}")
        await params.result_callback({"status": "booked", "confirmation": summary})

    async def request_callback(params):
        await sb(http, "leads?on_conflict=client_id,contact", "POST", {
            "client_id": client["id"], "contact": caller or "call:unknown", "name": params.arguments.get("name"),
            "score": "warm", "status": "callback", "source": "voice", "details": {"reason": params.arguments.get("reason")},
            "updated_at": datetime.utcnow().isoformat() + "Z"}, prefer="resolution=merge-duplicates")
        await whatsapp(http, client.get("phone_number_id"), client.get("owner_whatsapp"), f"🙋 Call back {caller}: {params.arguments.get('reason')}")
        await params.result_callback({"status": "team will call back"})

    llm.register_function("book", book)
    llm.register_function("request_callback", request_callback)

    pipeline = Pipeline([transport.input(), stt, agg.user(), llm, tts, transport.output(), agg.assistant()])
    task = PipelineWorker(pipeline, params=PipelineParams(audio_in_sample_rate=8000, audio_out_sample_rate=8000, enable_metrics=True))

    @transport.event_handler("on_client_connected")
    async def greet(_t, _c):
        await task.queue_frames([TTSSpeakFrame(P.opening(cfg))])

    @transport.event_handler("on_client_disconnected")
    async def bye(_t, _c):
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)


# ---- Outbound caller: consented Meta leads only, 9 AM – 9 PM IST, via Plivo
async def outbound_worker():
    if not os.getenv("PLIVO_AUTH_ID"):
        return
    async with aiohttp.ClientSession() as http:
        while True:
            hour = datetime.now(P.IST).hour
            if 9 <= hour < 21:
                jobs = await sb(http, "jobs?type=eq.voice_call&status=eq.queued&order=run_at.asc&limit=5&select=*")
                for j in jobs or []:
                    client = (await sb(http, f"clients?id=eq.{j['client_id']}&select=*"))[0]
                    frm = (client.get("config") or {}).get("voice_number")
                    if not frm:
                        await sb(http, f"jobs?id=eq.{j['id']}", "PATCH", {"status": "skipped", "result": {"why": "no voice_number"}}, prefer="return=minimal")
                        continue
                    auth = aiohttp.BasicAuth(os.getenv("PLIVO_AUTH_ID"), os.getenv("PLIVO_AUTH_TOKEN"))
                    async with http.post(f"https://api.plivo.com/v1/Account/{os.getenv('PLIVO_AUTH_ID')}/Call/", auth=auth, json={
                        "from": frm, "to": j["payload"]["to"],
                        "answer_url": f"https://{os.getenv('PUBLIC_HOST')}/plivo/answer?client={client['id']}", "answer_method": "POST"}) as r:
                        await sb(http, f"jobs?id=eq.{j['id']}", "PATCH", {"status": "called" if r.status < 300 else "failed", "result": {"http": r.status}}, prefer="return=minimal")
            await asyncio.sleep(30)


@app.on_event("startup")
async def start_worker():
    asyncio.create_task(outbound_worker())


@app.get("/health")
async def health():
    return {"ok": True}
