"""Builds the voice agent's instructions and tools from a BotBhai setup (pure Python, unit-tested)."""
import json
import pathlib
from datetime import datetime, timedelta, timezone

import os
SETUPS_DIR = pathlib.Path(os.getenv("SETUPS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "setups")
IST = timezone(timedelta(hours=5, minutes=30))
SETUP_DIRS = {"salon": "salon", "realestate": "realestate", "gym": "gym", "examkits": "examkits"}


def load_setup(setup_id: str, overrides: dict | None = None) -> dict:
    d = SETUPS_DIR / SETUP_DIRS[setup_id]
    cfg = json.loads((d / "bot.config.json").read_text())
    meta = json.loads((d / "setup.meta.json").read_text())
    cfg.update(overrides or {})
    cfg["_voice"] = meta["voice"]
    return cfg


def booking_fields(cfg: dict) -> list[dict]:
    """The same fields the WhatsApp flow collects, minus quiz steps."""
    out = []
    if cfg.get("quiz"):  # coaching: on calls we book a free demo class instead of running the quiz
        return [{"field": "service", "type": "choice", "choices": [c["name"] for c in cfg["catalog"]]},
                {"field": "date", "type": "date", "choices": None},
                {"field": "slot", "type": "choice", "choices": ["10:00 AM", "4:00 PM", "6:00 PM"]},
                {"field": "name", "type": "name", "choices": None}]
    for s in cfg["steps"]:
        if s.get("type") == "quiz":
            continue
        choices = [c["name"] for c in cfg["catalog"]] if s.get("choices") == "catalog" else s.get("choices")
        out.append({"field": s["field"], "type": s.get("type", "choice" if choices else "text"), "choices": choices})
    return out


def system_prompt(cfg: dict, now: datetime | None = None) -> str:
    now = now or datetime.now(IST)
    v = cfg["_voice"]
    catalog = "\n".join(f"- {c['name']}: {c['price']}" for c in cfg["catalog"])
    faqs = "\n".join(f"- About {', '.join(f['k'][:3])}: {f['a']}".replace("{phone}", cfg["phone"]) for f in cfg["faqs"])
    fields = "\n".join(
        f"- {f['field']}" + (f" (one of: {', '.join(f['choices'])})" if f["choices"] else " (a date, convert to YYYY-MM-DD)" if f["type"] == "date" else "")
        for f in booking_fields(cfg)
    )
    return f"""You are the voice assistant answering phone calls for {cfg['business']}, acting as the {v['role']}.
Today is {now.strftime('%A %d %B %Y')}, time {now.strftime('%I:%M %p')} IST.
Speak the caller's language: English, Hindi or Telugu, mixing naturally if they do. Keep every reply to one or two short sentences, because this is a phone call. Never use lists, emojis or markdown.

Your goals: {'; '.join(v['goals'])}.
Never: {'; '.join(v['never'])}. If asked anything outside {cfg['business']}'s services, politely say you can only help with {cfg['business']} and offer to connect the team.

Business facts (only use these):
- Address: {cfg['address']}
- Hours: {cfg['hours']}
- Phone: {cfg['phone']}
Prices:
{catalog}
Common questions:
{faqs}

To book, collect these one at a time, confirm them back in one sentence, then call the book tool:
{fields}
If the caller wants a person, or is upset, call the request_callback tool. Before ending, tell them a WhatsApp confirmation is on its way."""


def tools(cfg: dict) -> list[dict]:
    props = {}
    for f in booking_fields(cfg):
        p = {"type": "string", "description": f["field"]}
        if f["choices"]:
            p["enum"] = f["choices"]
        if f["type"] == "date":
            p["description"] = "date in YYYY-MM-DD"
        props[f["field"]] = p
    return [
        {"name": "book", "description": f"Book the {cfg.get('bookWord', 'appointment')} once every field is confirmed.", "properties": props, "required": list(props)},
        {"name": "request_callback", "description": "Ask a human from the team to call back.", "properties": {"reason": {"type": "string"}, "name": {"type": "string"}}, "required": ["reason"]},
    ]


def opening(cfg: dict) -> str:
    return cfg["_voice"]["opening"]
