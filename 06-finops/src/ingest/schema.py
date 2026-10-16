"""One usage record shape for every source, mirroring OTel `gen_ai.*` attributes.

Metadata only: token counts, model, provider, a feature tag and a *hashed*
customer id. Importers never copy prompt or completion text into a record.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import asdict, dataclass
from decimal import Decimal

DEV_SALT = "ledger-peaks-dev-salt"  # tests only (LP_ALLOW_DEV_SALT=1); real runs must set LP_HASH_SALT


class MissingSaltError(RuntimeError):
    """The public dev salt would make 'anonymised' ids reversible, so real runs refuse to start without a salt."""


def resolve_salt(salt: str | None = None) -> str:
    if salt:
        return salt
    if os.environ.get("LP_HASH_SALT"):
        return os.environ["LP_HASH_SALT"]
    if os.environ.get("LP_ALLOW_DEV_SALT") == "1":
        return DEV_SALT
    raise MissingSaltError(
        "LP_HASH_SALT is not set. Set a long random secret (per client) before importing or scanning; "
        "without it, hashed phone numbers and ids could be reversed.")


@dataclass
class UsageRecord:
    ts: str                      # ISO-8601 UTC timestamp or date of the call / bucket
    provider: str                # gen_ai.provider.name (normalised)
    model: str                   # gen_ai.request.model
    input_tokens: int = 0        # gen_ai.usage.input_tokens, INCLUDING cache read + write
    output_tokens: int = 0       # gen_ai.usage.output_tokens
    cache_read_tokens: int = 0   # gen_ai.usage.cache_read.input_tokens
    cache_write_tokens: int = 0  # gen_ai.usage.cache_creation.input_tokens
    reasoning_tokens: int = 0    # subset of output_tokens, informational
    requests: int = 1
    customer: str | None = None  # HMAC hash of the customer id, never the raw id
    feature: str | None = None
    batch: bool = False
    served_from_cache: bool = False   # gateway cache hit: no provider bill
    reported_cost_usd: Decimal | None = None  # cost the source itself claimed
    source: str = ""
    source_row: int = 0

    def to_otel(self) -> dict:
        return {
            "gen_ai.provider.name": self.provider,
            "gen_ai.request.model": self.model,
            "gen_ai.usage.input_tokens": self.input_tokens,
            "gen_ai.usage.output_tokens": self.output_tokens,
            "gen_ai.usage.cache_read.input_tokens": self.cache_read_tokens,
            "gen_ai.usage.cache_creation.input_tokens": self.cache_write_tokens,
            "gen_ai.usage.reasoning.output_tokens": self.reasoning_tokens,
            "ledger.customer_id_hash": self.customer,
            "ledger.feature": self.feature,
            "ledger.requests": self.requests,
            "ledger.batch": self.batch,
            "ledger.ts": self.ts,
        }

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["reported_cost_usd"] is not None:
            d["reported_cost_usd"] = str(d["reported_cost_usd"])
        return d


def hash_id(value: str | None, salt: str | None = None) -> str | None:
    """Stable pseudonymous id: HMAC-SHA256(salt, value), first 16 hex chars."""
    if value is None or str(value).strip() == "":
        return None
    key = resolve_salt(salt).encode()
    digest = hmac.new(key, str(value).strip().encode(), hashlib.sha256).hexdigest()
    return "c_" + digest[:16]


PROVIDER_ALIASES = {
    "openai": "openai", "azure": "azure", "azure_openai": "azure",
    "anthropic": "anthropic", "claude": "anthropic",
    "google": "google", "gemini": "google", "vertex_ai": "google", "vertex": "google",
    "google_ai_studio": "google", "bedrock": "aws", "aws": "aws",
    "groq": "groq", "mistral": "mistral", "deepseek": "deepseek", "xai": "x-ai", "x-ai": "x-ai",
    "openrouter": "openrouter", "together_ai": "together", "together": "together",
    "fireworks_ai": "fireworks", "cohere": "cohere", "perplexity": "perplexity",
}


def split_model(provider: str | None, model: str) -> tuple[str, str]:
    """Normalise ('', 'gemini/gemini-2.5-flash') -> ('google', 'gemini-2.5-flash')."""
    model = (model or "").strip()
    prov = (provider or "").strip().lower()
    if "/" in model:
        head, tail = model.split("/", 1)
        if head.lower() in PROVIDER_ALIASES:
            prov = prov or head.lower()
            model = tail
    prov = PROVIDER_ALIASES.get(prov, prov)
    if not prov:
        m = model.lower()
        if m.startswith(("gpt-", "o1", "o3", "o4", "text-embedding", "chatgpt", "gpt5")):
            prov = "openai"
        elif m.startswith("claude"):
            prov = "anthropic"
        elif m.startswith(("gemini", "gemma")):
            prov = "google"
    return prov, model
