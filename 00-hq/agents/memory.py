"""Lesson memory for the free-model agents (A171).

Each world keeps a plain-text JSONL file of lessons (mostly Vigil's fixes) in 00-hq/agents/memory/.
Before a task the runner recalls the few lessons that share the most words with the task; after Vigil
it stores the new lesson. Text files keep git diffs readable; personal data is scrubbed before saving.
Same idea as Mnemosyne/Hindsight (MIT agent memories), without a server or an extra dependency at our size.
"""
import json
import math
import os
import re
from datetime import datetime, timezone

DIR = "00-hq/agents/memory"
STOP = set("the a an and or of to in on for with is are be it this that as at by from not no your you we our".split())
PII = [(re.compile(r"\b(?:sk-[\w-]{16,}|gsk_\w{16,}|AIza[\w-]{20,}|gh[pousr]_\w{20,}|hf_\w{20,}|xox[abp]-[\w-]{10,})"), "[key]"),
       (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
       (re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"), "[phone]")]


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP}


def scrub(text):
    for rx, sub in PII:
        text = rx.sub(sub, text)
    return text


def _path(world, root):
    return os.path.join(root, DIR, f"{world}.jsonl")


def _load(world, root):
    p = _path(world, root)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def store(world, task_id, lesson, root):
    lesson = scrub(" ".join(lesson.split()))[:400]
    if not lesson:
        return
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    row = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "task": task_id, "lesson": lesson}
    with open(_path(world, root), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def recall(world, query, k=5, root="."):
    rows = _load(world, root)
    q = _words(query)
    if not rows or not q:
        return []
    df = {}
    for r in rows:
        for w in _words(r["lesson"]):
            df[w] = df.get(w, 0) + 1
    scored, seen = [], set()
    for i, r in enumerate(rows):
        if r["lesson"] in seen:
            continue
        seen.add(r["lesson"])
        score = sum(math.log(1 + len(rows) / df[w]) for w in _words(r["lesson"]) & q)
        if score > 0:
            scored.append((score, i, r["lesson"]))  # newer wins a tie
    scored.sort(key=lambda s: (-s[0], -s[1]))
    return [s[2] for s in scored[:k]]


def lesson_from_verdict(verdict):
    if not verdict or verdict.strip().upper().startswith("PASS"):
        return ""
    body = re.sub(r"^\s*FIX:?", "", verdict.strip(), flags=re.I)
    bullets = [b.strip(" -*•\t") for b in body.splitlines() if b.strip(" -*•\t")]
    return "Vigil asked: " + "; ".join(bullets[:5])
