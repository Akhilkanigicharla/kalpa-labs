"""Optional Presidio backend, pattern-only (no spaCy model download).

Presidio (MIT, Microsoft; now github.com/data-privacy-stack/presidio) needs an
NlpEngine. We pass a stub that returns empty NLP artifacts, so only the
regex+checksum recognizers run. This avoids the ~400 MB spaCy model and the
noisy PERSON/ORGANIZATION tags that the small model produces on log text.
"""
from __future__ import annotations

from typing import Iterator

from .recognizers import Finding

# Presidio entity -> our entity name. Entities without a builtin twin keep
# Presidio's name (IN_VOTER, IN_PASSPORT, IN_VEHICLE_REGISTRATION).
ENTITY_MAP = {
    "IN_AADHAAR": "AADHAAR",
    "IN_PAN": "PAN",
    "IN_GSTIN": "GSTIN",
    "EMAIL_ADDRESS": "EMAIL",
    "CREDIT_CARD": "CARD",
}
SCORE_THRESHOLD = 0.5  # IN_PAN's weak pattern scores 0.01 and matches any 10 chars


def available() -> bool:
    try:
        import presidio_analyzer  # noqa: F401
    except Exception:
        return False
    return True


def version() -> str | None:
    try:
        from importlib.metadata import version as v
        return v("presidio-analyzer")
    except Exception:
        return None


_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine
    from presidio_analyzer.predefined_recognizers import (
        CreditCardRecognizer, EmailRecognizer, InAadhaarRecognizer, InGstinRecognizer,
        InPanRecognizer, InPassportRecognizer, InVehicleRegistrationRecognizer,
        InVoterRecognizer,
    )

    class _NoNlp(NlpEngine):
        def load(self): pass
        def is_loaded(self): return True
        def process_text(self, text, language):
            return NlpArtifacts(entities=[], tokens=[], tokens_indices=[], lemmas=[],
                                nlp_engine=self, language=language)
        def process_batch(self, texts, language, **kwargs):
            for t in texts:
                yield t, self.process_text(t, language)
        def is_stopword(self, word, language): return False
        def is_punct(self, word, language): return False
        def get_supported_entities(self): return []
        def get_supported_languages(self): return ["en"]

    registry = RecognizerRegistry(recognizers=[
        InAadhaarRecognizer(), InPanRecognizer(), InGstinRecognizer(), InVoterRecognizer(),
        InPassportRecognizer(), InVehicleRegistrationRecognizer(), EmailRecognizer(),
        CreditCardRecognizer(),
    ])
    _ENGINE = AnalyzerEngine(registry=registry, nlp_engine=_NoNlp(), supported_languages=["en"])
    return _ENGINE


def _norm(entity: str, raw: str) -> str:
    if entity in ("AADHAAR", "CARD"):
        return "".join(c for c in raw if c.isdigit())
    if entity == "EMAIL":
        return raw.lower()
    return raw.upper().replace(" ", "")


def find(text: str) -> Iterator[Finding]:
    for r in _engine().analyze(text=text, language="en", score_threshold=SCORE_THRESHOLD):
        ent = ENTITY_MAP.get(r.entity_type, r.entity_type)
        yield Finding(ent, r.start, r.end, _norm(ent, text[r.start:r.end]))
