"""LiteLLM -> Ledger Peaks callback (F-11). Sends counts only, never prompt or response text.

In the client's LiteLLM proxy config:
    litellm_settings:
      callbacks: ledger_peaks.litellm_callback.handler
Env on the client's side: LP_API_KEY (their tenant key), LP_HASH_SALT (their own secret),
optional LP_API_URL. Customer ids are HMAC-hashed with the client's salt before they leave.
Feature tag: request metadata tag "feature:<name>" (same rule as the spend-log importer).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingest.schema import hash_id  # noqa: E402

try:  # real base class when LiteLLM is installed; plain object in tests
    from litellm.integrations.custom_logger import CustomLogger
except Exception:  # pragma: no cover
    CustomLogger = object


def to_event(slo: dict, salt: str | None = None) -> dict:
    """LiteLLM StandardLoggingPayload -> one /v1/events event."""
    meta = slo.get("metadata") or {}
    tags = meta.get("tags") or slo.get("request_tags") or []
    feature = next((t.split(":", 1)[1] for t in tags if isinstance(t, str) and t.startswith("feature:")), None)
    user = slo.get("end_user") or meta.get("user_api_key_end_user_id")
    details = slo.get("prompt_tokens_details") or {}
    ev = {
        "ts": slo.get("startTime"),
        "provider": slo.get("custom_llm_provider") or "unknown",
        "model": slo.get("model") or "unknown",
        "input_tokens": int(slo.get("prompt_tokens") or 0),
        "output_tokens": int(slo.get("completion_tokens") or 0),
        "cache_read_tokens": int(details.get("cached_tokens") or 0),
        "served_from_cache": bool(slo.get("cache_hit")),
    }
    if feature:
        ev["feature"] = feature
    h = hash_id(user, salt)
    if h:
        ev["customer"] = h
    return ev


class LedgerPeaksLogger(CustomLogger):
    def __init__(self, api_key=None, url=None, batch_size=200, salt=None, post=None):
        self.key = api_key or os.environ.get("LP_API_KEY", "")
        self.url = url or os.environ.get("LP_API_URL", "https://ledger-peaks.invalid/v1/events")
        self.salt, self.batch_size, self.buf = salt, batch_size, []
        self.lock = threading.Lock()
        self._post = post or self._http_post

    def _http_post(self, events):
        req = urllib.request.Request(self.url, data=json.dumps({"events": events}).encode(), method="POST",
                                     headers={"authorization": f"Bearer {self.key}", "content-type": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()

    def add(self, slo: dict):
        with self.lock:
            self.buf.append(to_event(slo, self.salt))
            full = len(self.buf) >= self.batch_size
        if full:
            self.flush()

    def flush(self):
        with self.lock:
            events, self.buf = self.buf, []
        if events:
            try:
                self._post(events)
            except Exception:   # never break the client's LLM call; keep events for the next flush
                with self.lock:
                    self.buf = (events + self.buf)[-10 * self.batch_size:]   # bounded: drop oldest

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        slo = kwargs.get("standard_logging_object")
        if slo:
            self.add(slo)

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self.log_success_event(kwargs, response_obj, start_time, end_time)


handler = None if os.environ.get("LP_HASH_SALT") is None else LedgerPeaksLogger()
