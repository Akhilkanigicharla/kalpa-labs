"""Importers: OpenAI usage, Anthropic usage, LiteLLM spend logs, Langfuse observations,
generic CSV/JSONL. Each returns an ImportResult whose rows_in == records + skipped.

Only whitelisted metadata fields are read. Prompt/completion text (Langfuse `input`/
`output`, LiteLLM `messages`/`response`) is never touched.

Field names follow the providers' public usage APIs (checked 2026-10):
- OpenAI  GET /v1/organization/usage/completions  (bucket.results[]: input_tokens,
  output_tokens, input_cached_tokens, num_model_requests, model, project_id, batch ...)
- Anthropic GET /v1/organizations/usage_report/messages (results[]: uncached_input_tokens,
  cache_creation.{ephemeral_5m,ephemeral_1h}_input_tokens, cache_read_input_tokens,
  output_tokens, model, workspace_id, api_key_id, service_tier). The Console CSV
  download is accepted when its headers use these names or the long `token_type` form;
  verify against a real export before the first X-ray (see README).
- LiteLLM  LiteLLM_SpendLogs table / `/spend/logs` (model, custom_llm_provider,
  prompt_tokens, completion_tokens, spend, startTime, end_user, request_tags, metadata, cache_hit)
- Langfuse GET /api/public/observations (type, startTime, model, usageDetails,
  costDetails / calculatedTotalCost, userId, name, metadata)
"""
from __future__ import annotations

from pathlib import Path

from .common import (ImportResult, flatten_buckets, maybe_json, pick, read_rows,
                     to_bool, to_dec, to_int, to_iso)
from .schema import UsageRecord, hash_id, split_model


def _finish(res: ImportResult, i: int, build):
    try:
        rec = build()
    except (ValueError, KeyError, TypeError) as e:
        res.skipped.append((i, f"unparseable: {e}"))
        return
    if rec is None:
        return
    if not rec.model:
        res.skipped.append((i, "no model"))
    elif rec.input_tokens == 0 and rec.output_tokens == 0 and rec.requests == 0:
        res.skipped.append((i, "zero usage"))
    else:
        rec.source_row = i
        res.records.append(rec)


# ---------------------------------------------------------------- OpenAI
def import_openai(path, salt=None, feature_field="project_name") -> ImportResult:
    rows = flatten_buckets(read_rows(path))
    res = ImportResult("openai", str(path), rows_in=len(rows))
    for i, r in enumerate(rows, 1):
        def build(r=r):
            prov, model = split_model("openai", pick(r, "model", "model_name", "snapshot_id"))
            return UsageRecord(
                ts=to_iso(pick(r, "start_time_iso", "start_time", "__bucket_time", "date", "timestamp")),
                provider=prov, model=model,
                input_tokens=to_int(pick(r, "input_tokens", "n_context_tokens_total", "prompt_tokens")),
                output_tokens=to_int(pick(r, "output_tokens", "n_generated_tokens_total", "completion_tokens")),
                cache_read_tokens=to_int(pick(r, "input_cached_tokens", "cached_tokens")),
                requests=to_int(pick(r, "num_model_requests", "n_requests", "requests", default=1)),
                feature=pick(r, feature_field, "project_name", "project_id", "api_key_name"),
                customer=hash_id(pick(r, "customer_id", "end_user"), salt),
                batch=to_bool(pick(r, "batch", default=False)),
                source="openai")
        _finish(res, i, build)
    return res


# ---------------------------------------------------------------- Anthropic
def import_anthropic(path, salt=None) -> ImportResult:
    rows = flatten_buckets(read_rows(path))
    if rows and "token_type" in {k.lower() for k in rows[0]}:
        return _anthropic_long(path, rows, salt)
    res = ImportResult("anthropic", str(path), rows_in=len(rows))
    for i, r in enumerate(rows, 1):
        def build(r=r):
            cc = r.get("cache_creation") if isinstance(r.get("cache_creation"), dict) else {}
            cw = (to_int(cc.get("ephemeral_5m_input_tokens")) + to_int(cc.get("ephemeral_1h_input_tokens"))
                  + to_int(pick(r, "cache_creation_ephemeral_5m_input_tokens"))
                  + to_int(pick(r, "cache_creation_ephemeral_1h_input_tokens"))
                  + to_int(pick(r, "cache_creation_input_tokens")))
            cr = to_int(pick(r, "cache_read_input_tokens"))
            unc = to_int(pick(r, "uncached_input_tokens", "input_tokens"))
            prov, model = split_model("anthropic", pick(r, "model"))
            tier = str(pick(r, "service_tier", default="")).lower()
            return UsageRecord(
                ts=to_iso(pick(r, "starting_at", "__bucket_time", "usage_date_utc", "date")),
                provider=prov, model=model, input_tokens=unc + cw + cr,
                output_tokens=to_int(pick(r, "output_tokens")),
                cache_read_tokens=cr, cache_write_tokens=cw,
                requests=to_int(pick(r, "requests", default=1)),
                feature=pick(r, "workspace_name", "workspace_id", "api_key_name", "api_key_id"),
                batch=tier == "batch", source="anthropic")
        _finish(res, i, build)
    return res


def _anthropic_long(path, rows, salt) -> ImportResult:
    """Long form: one row per (date, model, workspace, token_type, tokens). Grouped back
    into one record per (date, model, workspace, key); grouped rows are not 'lost', they
    are merged, and the result records how many input rows each record came from."""
    res = ImportResult("anthropic", str(path), rows_in=len(rows))
    groups: dict[tuple, dict] = {}
    for i, r in enumerate(rows, 1):
        try:
            key = (to_iso(pick(r, "usage_date_utc", "date", "starting_at")), pick(r, "model"),
                   pick(r, "workspace", "workspace_name", default=""), pick(r, "api_key", "api_key_name", default=""))
            tt = str(pick(r, "token_type")).lower()
            n = to_int(pick(r, "usage", "tokens", "token_count", "value"))
        except ValueError as e:
            res.skipped.append((i, f"unparseable: {e}"))
            continue
        g = groups.setdefault(key, {"rows": [], "unc": 0, "cw": 0, "cr": 0, "out": 0})
        g["rows"].append(i)
        if "cache_read" in tt:
            g["cr"] += n
        elif "cache_creation" in tt or "cache_write" in tt:
            g["cw"] += n
        elif "output" in tt:
            g["out"] += n
        elif "input" in tt:
            g["unc"] += n
        else:
            g["rows"].pop()
            res.skipped.append((i, f"unknown token_type {tt!r}"))
    for (ts, model, ws, key), g in groups.items():
        if not g["rows"]:
            continue
        prov, m = split_model("anthropic", model)
        rec = UsageRecord(ts=ts, provider=prov, model=m, input_tokens=g["unc"] + g["cw"] + g["cr"],
                          output_tokens=g["out"], cache_read_tokens=g["cr"], cache_write_tokens=g["cw"],
                          feature=ws or key or None, source="anthropic", source_row=g["rows"][0])
        rec.requests = 0  # the long export carries no request counts
        res.records.append(rec)
        res.merged.extend((j, g["rows"][0]) for j in g["rows"][1:])
    return res


# ---------------------------------------------------------------- LiteLLM
def import_litellm(path, salt=None, feature_tag_prefix="feature:") -> ImportResult:
    rows = read_rows(path)
    res = ImportResult("litellm", str(path), rows_in=len(rows))
    for i, r in enumerate(rows, 1):
        def build(r=r):
            meta = maybe_json(r.get("metadata")) or {}
            tags = maybe_json(r.get("request_tags")) or []
            feature = next((t[len(feature_tag_prefix):] for t in tags
                            if isinstance(t, str) and t.startswith(feature_tag_prefix)), None)
            feature = feature or (tags[0] if tags else None) or meta.get("feature")
            cust = pick(r, "end_user", "user") or meta.get("customer_id") or meta.get("user_api_key_end_user_id")
            prov, model = split_model(pick(r, "custom_llm_provider"), pick(r, "model", "model_group"))
            usage = meta.get("usage_object") if isinstance(meta.get("usage_object"), dict) else {}
            ptd = usage.get("prompt_tokens_details") or {}
            return UsageRecord(
                ts=to_iso(pick(r, "startTime", "start_time", "starttime")),
                provider=prov, model=model,
                input_tokens=to_int(pick(r, "prompt_tokens")),
                output_tokens=to_int(pick(r, "completion_tokens")),
                cache_read_tokens=to_int(ptd.get("cached_tokens") or usage.get("cache_read_input_tokens")),
                cache_write_tokens=to_int(usage.get("cache_creation_input_tokens")),
                customer=hash_id(cust, salt), feature=feature,
                served_from_cache=to_bool(pick(r, "cache_hit", default=False)),
                reported_cost_usd=to_dec(pick(r, "spend")), source="litellm")
        _finish(res, i, build)
    return res


# ---------------------------------------------------------------- Langfuse
def import_langfuse(path, salt=None, input_excludes_cache=True) -> ImportResult:
    """Langfuse observations. Only GENERATION rows carry model usage; others are skipped
    with a reason. With input_excludes_cache=True (Langfuse's usageDetails convention for
    Anthropic and its OpenAI integration), cache tokens are added back to input."""
    rows = read_rows(path)
    res = ImportResult("langfuse", str(path), rows_in=len(rows))
    for i, r in enumerate(rows, 1):
        if str(r.get("type", "GENERATION")).upper() != "GENERATION":
            res.skipped.append((i, f"not a generation ({r.get('type')})"))
            continue

        def build(r=r):
            ud = maybe_json(r.get("usageDetails")) or maybe_json(r.get("usage")) or {}
            cr = sum(to_int(v) for k, v in ud.items() if "cache_read" in k or "cached" in k)
            cw = sum(to_int(v) for k, v in ud.items() if "cache_creation" in k or "cache_write" in k)
            inp = to_int(ud.get("input", ud.get("promptTokens", 0)))
            if input_excludes_cache:
                inp += cr + cw
            meta = maybe_json(r.get("metadata")) or {}
            cost = maybe_json(r.get("costDetails")) or {}
            reported = to_dec(cost.get("total")) if cost else to_dec(r.get("calculatedTotalCost"))
            prov, model = split_model(meta.get("provider") or meta.get("ls_provider"), pick(r, "model", "providedModelName"))
            return UsageRecord(
                ts=to_iso(pick(r, "startTime", "start_time", "timestamp")),
                provider=prov, model=model, input_tokens=inp,
                output_tokens=to_int(ud.get("output", ud.get("completionTokens", 0))),
                cache_read_tokens=cr, cache_write_tokens=cw,
                customer=hash_id(r.get("userId") or meta.get("customer_id"), salt),
                feature=meta.get("feature") or r.get("name") or r.get("traceName"),
                reported_cost_usd=reported, source="langfuse")
        _finish(res, i, build)
    return res


# ---------------------------------------------------------------- generic
def import_generic(path, salt=None) -> ImportResult:
    """Our own documented CSV/JSONL columns (or OTel attribute names)."""
    rows = read_rows(path)
    res = ImportResult("generic", str(path), rows_in=len(rows))
    for i, r in enumerate(rows, 1):
        def build(r=r):
            prov, model = split_model(pick(r, "provider", "gen_ai.provider.name", "gen_ai.system"),
                                      pick(r, "model", "gen_ai.request.model", "gen_ai.response.model"))
            return UsageRecord(
                ts=to_iso(pick(r, "ts", "timestamp", "time", "date", "ledger.ts")),
                provider=prov, model=model,
                input_tokens=to_int(pick(r, "input_tokens", "prompt_tokens", "gen_ai.usage.input_tokens")),
                output_tokens=to_int(pick(r, "output_tokens", "completion_tokens", "gen_ai.usage.output_tokens")),
                cache_read_tokens=to_int(pick(r, "cache_read_tokens", "gen_ai.usage.cache_read.input_tokens")),
                cache_write_tokens=to_int(pick(r, "cache_write_tokens", "gen_ai.usage.cache_creation.input_tokens")),
                requests=to_int(pick(r, "requests", default=1)),
                customer=hash_id(pick(r, "customer", "customer_id", "user", "tenant"), salt),
                feature=pick(r, "feature", "tag", "ledger.feature"),
                batch=to_bool(pick(r, "batch", default=False)),
                reported_cost_usd=to_dec(pick(r, "cost_usd", "cost")), source="generic")
        _finish(res, i, build)
    return res


IMPORTERS = {"openai": import_openai, "anthropic": import_anthropic, "litellm": import_litellm,
             "langfuse": import_langfuse, "generic": import_generic}


def detect_format(path) -> str:
    rows = flatten_buckets(read_rows(path))
    if not rows:
        return "generic"
    keys = {str(k).lower() for k in rows[0]}
    if {"spend", "prompt_tokens"} <= keys or "custom_llm_provider" in keys or "request_tags" in keys:
        return "litellm"
    if "usagedetails" in keys or "traceid" in keys or ("type" in keys and "starttime" in keys):
        return "langfuse"
    if "uncached_input_tokens" in keys or "cache_read_input_tokens" in keys or "token_type" in keys:
        return "anthropic"
    if "num_model_requests" in keys or "input_cached_tokens" in keys or "project_id" in keys:
        return "openai"
    return "generic"


def load(path, fmt: str = "auto", salt=None) -> ImportResult:
    fmt = detect_format(path) if fmt == "auto" else fmt
    return IMPORTERS[fmt](Path(path), salt=salt)
