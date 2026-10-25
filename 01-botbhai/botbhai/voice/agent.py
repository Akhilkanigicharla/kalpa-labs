"""
BotBhai voice agent — answers (and, for consented leads, places) real phone calls.

Stack (open source + free tiers): Pipecat 1.13 · Sarvam STT/TTS (Indian languages, Hinglish) ·
Groq LLM · Silero VAD · telephony by Plivo or Exotel (paid per minute, billed to the client).

Run:   pip install -r requirements.txt && uvicorn agent:app --host 0.0.0.0 --port 8080
Env:   RECORDED_TTS (voice notes: parler | sarvam, see recorded_tts.py), SARVAM_API_KEY, GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WA_ACCESS_TOKEN,
       PUBLIC_HOST (e.g. voice.example.com), PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN (for Plivo)
Calls: Plivo number → Answer URL https://PUBLIC_HOST/plivo/answer?client=<client uuid>
       Exotel → Voicebot applet → wss://PUBLIC_HOST/ws?client=<client uuid>
"""
import asyncio
import base64
import logging
import os
from datetime import datetime

import aiohttp
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
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

import json
from pathlib import Path
import prompt as P
import recorded_tts as R
import turns as T

# A85: model names live in one file (core/models.json, copied next to this file in the Docker image)
_MODELS = next((p for p in (Path(__file__).with_name("models.json"), Path(__file__).resolve().parent.parent / "core" / "models.json") if p.exists()), None)
GROQ_CHAT_MODEL = json.loads(_MODELS.read_text())["groq_chat"] if _MODELS else "openai/gpt-oss-120b"

SB_URL, SB_KEY = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
app = FastAPI(title="BotBhai voice agent")


async def sb(session: aiohttp.ClientSession, path: str, method="GET", body=None, prefer="return=representation"):
    async with session.request(method, f"{SB_URL}/rest/v1/{path}", json=body,
                               headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Prefer": prefer}) as r:
        r.raise_for_status()
        if method == "PATCH" or r.content_length == 0:
            return None
        return await r.json(content_type=None)


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
        FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True),  # VAD lives in the user aggregator (turns.py)
        transport_type, call_data)
    vp = P.voice_profile(cfg)
    specs = P.tools(cfg)
    schemas = [FunctionSchema(name=t["name"], description=t["description"], properties=t["properties"], required=t["required"]) for t in specs]
    gemini = os.getenv("VOICE_ENGINE") == "gemini_live"
    if gemini:
        # Speech-to-speech: the most natural turn-taking and interruptions. Free tier trains on data → demos only.
        from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
        llm = GeminiLiveLLMService(api_key=os.getenv("GOOGLE_API_KEY"), voice_id=os.getenv("GEMINI_VOICE", "Aoede"),
                                   system_instruction=P.system_prompt(cfg), tools=ToolsSchema(standard_tools=schemas))
    else:
        # codemix: understands Tenglish/Hinglish the way people actually speak. saaras:v4 + keyterms (Pipecat 1.13):
        # the business name, services and areas are biased so "Glow Studio" / "hair spa" are heard right.
        stt = SarvamSTTService(api_key=os.getenv("SARVAM_API_KEY"), mode="codemix", keyterms=T.stt_keyterms(cfg),
                               settings=SarvamSTTService.Settings(model=T.STT_MODEL))
        tts = SarvamTTSService(api_key=os.getenv("SARVAM_API_KEY"), settings=SarvamTTSService.Settings(model="bulbul:v3", voice=vp["voice"], language=T.pipecat_language(cfg), pace=vp["pace"], temperature=vp["temperature"]))
        llm = GroqLLMService(api_key=os.getenv("GROQ_API_KEY"), settings=GroqLLMService.Settings(model=GROQ_CHAT_MODEL))

    context = LLMContext(messages=[{"role": "system", "content": P.system_prompt(cfg)}], tools=ToolsSchema(standard_tools=schemas))
    agg = LLMContextAggregatorPair(context, user_params=T.user_params())  # VAD 0.2 s + smart-turn v3.2 (1.2 s cap)

    async def book(params):
        a = dict(params.arguments)
        details = {k: v for k, v in a.items() if k != "name"}
        date_iso = details.get("date")
        if date_iso:
            details["date_iso"] = date_iso
            details["date"] = datetime.fromisoformat(date_iso).strftime("%a, %d %b")
        contact = caller or f"call:{datetime.now().timestamp():.0f}"
        # same atomic, capacity-checked booking as WhatsApp and the website (no double booking across channels)
        booked = await sb(http, "rpc/book_slot", "POST", {
            "p_client": client["id"], "p_contact": contact, "p_name": a.get("name"), "p_service": details.get("service") or details.get("goal"),
            "p_date": date_iso, "p_slot": details.get("slot"), "p_capacity": (client.get("config") or {}).get("capacity", 1), "p_source": "voice"})
        if booked is False:
            await params.result_callback({"status": "slot_taken", "say": "That time was just taken. Offer the caller another time."})
            return
        await sb(http, "leads?on_conflict=client_id,contact", "POST", {
            "client_id": client["id"], "contact": contact, "name": a.get("name"),
            "score": "hot", "status": "booked", "source": "voice", "details": dict(details, customer_name=a.get("name")),
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

    stages = [transport.input(), agg.user(), llm, transport.output(), agg.assistant()] if gemini else [transport.input(), stt, agg.user(), llm, tts, transport.output(), agg.assistant()]
    pipeline = Pipeline(stages)
    task = PipelineWorker(pipeline, params=PipelineParams(audio_in_sample_rate=8000, audio_out_sample_rate=8000, enable_metrics=True))

    @transport.event_handler("on_client_connected")
    async def greet(_t, _c):
        if not gemini:
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
          try:
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
                        "answer_url": f"https://{os.getenv('PUBLIC_HOST')}/plivo/answer?client={client['id']}", "answer_method": "POST",
                        "machine_detection": "hangup"}) as r:  # voicemail → hang up; we follow up on WhatsApp instead
                        await sb(http, f"jobs?id=eq.{j['id']}", "PATCH", {"status": "called" if r.status < 300 else "failed", "result": {"http": r.status}}, prefer="return=minimal")
          except Exception:  # one bad job or network blip must never stop the caller for good
            logging.exception("outbound worker")
          await asyncio.sleep(30)


@app.on_event("startup")
async def start_worker():
    asyncio.create_task(outbound_worker())


# ---- WhatsApp voice-note replies: the customer spoke, so the business answers in a human voice too
@app.post("/voicenote")
async def voicenote(request: Request):
    if request.headers.get("X-BotBhai-Key", "") != os.getenv("VOICE_SERVER_KEY", "") or not os.getenv("VOICE_SERVER_KEY"):
        return Response(status_code=401)
    b = await request.json()
    lang = {"te": "te-IN", "te-latn": "te-IN", "hi": "hi-IN", "hi-latn": "hi-IN"}.get(b.get("lang"), "en-IN")
    cfg = P.load_setup(b.get("setup", "salon"))
    vp = P.voice_profile(cfg)
    text = " ".join(line for line in b["text"].replace("*", "").splitlines() if line.strip() and not line.strip().startswith(("http", "🗺")))[:480]
    async with aiohttp.ClientSession() as http:
        if R.provider() == "sarvam":  # paid, optional (A56)
            async with http.post("https://api.sarvam.ai/text-to-speech", headers={"api-subscription-key": os.getenv("SARVAM_API_KEY")},
                                 json={"text": text, "target_language_code": lang, "speaker": vp["voice"], "model": "bulbul:v3", "pace": vp["pace"], "temperature": vp["temperature"]}) as r:
                wav = base64.b64decode((await r.json())["audios"][0])
        else:  # free Indic Parler-TTS on this machine's CPU; needs requirements-parler.txt + HF_TOKEN
            gender = P.PERSONAS.get(cfg.get("id"), ("", "female"))[1]
            wav = await asyncio.to_thread(R.parler_wav, text, cfg.get("parler_speaker") or R.speaker_for(lang, gender))
        ogg = await to_ogg_opus(wav)
        form = aiohttp.FormData(); form.add_field("messaging_product", "whatsapp"); form.add_field("type", "audio/ogg")
        form.add_field("file", ogg, filename="reply.ogg", content_type="audio/ogg")
        tok = {"Authorization": f"Bearer {os.getenv('WA_ACCESS_TOKEN')}"}
        async with http.post(f"https://graph.facebook.com/v21.0/{b['phone_number_id']}/media", headers=tok, data=form) as r:
            media_id = (await r.json())["id"]
        async with http.post(f"https://graph.facebook.com/v21.0/{b['phone_number_id']}/messages", headers=tok,
                             json={"messaging_product": "whatsapp", "to": b["to"], "type": "audio", "audio": {"id": media_id}}) as r:
            return {"sent": r.status < 300}


async def to_ogg_opus(wav: bytes) -> bytes:
    """WhatsApp voice notes must be OGG/Opus; convert with ffmpeg (installed in the Docker image)."""
    proc = await asyncio.create_subprocess_exec("ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-c:a", "libopus", "-b:a", "32k", "-f", "ogg", "pipe:1",
                                                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate(wav)
    return out


@app.get("/health")
async def health():
    return {"ok": True}
