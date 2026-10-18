"""The 20 DPDP readiness questions (our own wording; a checklist, not legal advice)."""
from __future__ import annotations

import json
from pathlib import Path

QUESTIONS = [
    "Do you have a written list of every AI feature that touches personal data?",
    "Is the purpose of each AI feature written in your privacy notice?",
    "Does the notice name the AI providers you send data to?",
    "Is there a consent or other lawful basis recorded for each purpose?",
    "Can a user withdraw consent as easily as they gave it?",
    "Do you strip phone numbers, Aadhaar and PAN before prompts leave India?",
    "Do you know which provider regions (US, EU, India) receive your data?",
    "Do provider contracts say they won't train on your data?",
    "Are prompts and outputs deleted on a fixed schedule?",
    "Is the retention period written down per feature?",
    "Can you find and delete one user's data across AI logs on request?",
    "Is there a named person who answers data requests (grievance officer)?",
    "Do you log who accessed AI logs and when?",
    "Is access to raw prompts limited to named staff?",
    "Do you have a breach plan that covers your AI provider leaking data?",
    "Could you tell the Data Protection Board and users within 72 hours?",
    "Do you tell users when they are talking to an AI, not a person?",
    "Are children's accounts blocked or handled with parental consent?",
    "Have you checked whether you could be a Significant Data Fiduciary?",
    "Is this checklist reviewed at least once a year?",
]


def load_answers(path: str | Path | None) -> list[bool | None]:
    """JSON list of 20 true/false/null, or {"answers": [...]}. No file = nothing answered yet."""
    if path is None:
        return [None] * len(QUESTIONS)
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    ans = obj["answers"] if isinstance(obj, dict) else obj
    if len(ans) != len(QUESTIONS) or any(a not in (True, False, None) for a in ans):
        raise ValueError(f"DPDP answers must be {len(QUESTIONS)} values of true, false or null")
    return list(ans)


def section(answers: list[bool | None]) -> dict:
    return {"score": sum(1 for a in answers if a is True), "of": len(QUESTIONS),
            "answered": sum(1 for a in answers if a is not None),
            "questions": [{"q": q, "ok": a} for q, a in zip(QUESTIONS, answers)]}
