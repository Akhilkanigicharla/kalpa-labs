-- Ledger Peaks usage schema (F-03, roadmap A28). Supabase / Postgres 16. Safe to apply twice.
-- Metadata only: token counts, model, provider, feature tag, HMAC-hashed customer id.
-- No prompt or completion text is ever stored. Raw events are kept 30 days, then only daily totals stay.
-- Fields mirror OpenTelemetry gen_ai.* semantic conventions (see 06-finops/src/ingest/schema.py).
-- Who can do what:
--   service_role (the ingest API, server side only): writes events, runs rollup_daily and purge_raw.
--   authenticated members of a tenant: READ their own tenant's rows only (RLS). No writes.
--   anon: nothing.

create table if not exists public.tenant (
  id          uuid primary key default gen_random_uuid(),
  name        text not null check (length(name) between 1 and 120),
  region      text not null default 'ap-south-1',          -- Mumbai: data stays in India by default
  created_at  timestamptz not null default now()
);

create table if not exists public.tenant_member (
  tenant_id   uuid not null references public.tenant(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        text not null default 'viewer' check (role in ('owner', 'viewer')),
  primary key (tenant_id, user_id)
);

create table if not exists public.usage_event (
  id                  bigint generated always as identity primary key,
  tenant_id           uuid not null references public.tenant(id) on delete cascade,
  ts                  timestamptz not null,                    -- ledger.ts
  provider            text not null check (length(provider) between 1 and 40),   -- gen_ai.provider.name
  model               text not null check (length(model) between 1 and 120),     -- gen_ai.request.model
  input_tokens        bigint not null default 0 check (input_tokens >= 0),       -- gen_ai.usage.input_tokens (incl. cache)
  output_tokens       bigint not null default 0 check (output_tokens >= 0),      -- gen_ai.usage.output_tokens
  cache_read_tokens   bigint not null default 0 check (cache_read_tokens >= 0),  -- gen_ai.usage.cache_read.input_tokens
  cache_write_tokens  bigint not null default 0 check (cache_write_tokens >= 0), -- gen_ai.usage.cache_creation.input_tokens
  reasoning_tokens    bigint not null default 0 check (reasoning_tokens >= 0),   -- gen_ai.usage.reasoning.output_tokens
  requests            integer not null default 1 check (requests >= 1),
  customer_id_hash    text check (customer_id_hash ~ '^c_[0-9a-f]{16}$'),         -- HMAC, never the raw id
  feature             text check (length(feature) <= 80),
  batch               boolean not null default false,
  served_from_cache   boolean not null default false,
  cost_paise          bigint check (cost_paise >= 0),          -- null = unpriced model, never shown as Rs 0
  source              text not null default '' check (length(source) <= 40),
  ingested_at         timestamptz not null default now(),
  constraint reasoning_within_output check (reasoning_tokens <= output_tokens)
);
create index if not exists usage_event_tenant_ts on public.usage_event (tenant_id, ts);

create table if not exists public.usage_daily (
  tenant_id           uuid not null references public.tenant(id) on delete cascade,
  day                 date not null,                           -- IST calendar day
  customer_id_hash    text check (customer_id_hash ~ '^c_[0-9a-f]{16}$'),
  feature             text,
  provider            text not null,
  model               text not null,
  requests            bigint not null default 0,
  input_tokens        bigint not null default 0,
  output_tokens       bigint not null default 0,
  cache_read_tokens   bigint not null default 0,
  cache_write_tokens  bigint not null default 0,
  reasoning_tokens    bigint not null default 0,
  cost_paise          bigint not null default 0,               -- priced requests only
  unpriced_requests   bigint not null default 0                -- shown as "unpriced spend", not Rs 0
);
create unique index if not exists usage_daily_key on public.usage_daily
  (tenant_id, day, coalesce(customer_id_hash, ''), coalesce(feature, ''), provider, model);

-- Which IST days have been rolled up, and which have had their raw rows purged.
create table if not exists public.usage_rollup_day (
  day     date primary key,
  purged  boolean not null default false,
  at      timestamptz not null default now()
);

-- ---------- access ----------
create or replace function public.is_member(t uuid) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select exists (select 1 from public.tenant_member m where m.tenant_id = t and m.user_id = auth.uid())
$$;
revoke all on function public.is_member(uuid) from public;
grant execute on function public.is_member(uuid) to authenticated, service_role;

alter table public.tenant           enable row level security;
alter table public.tenant_member    enable row level security;
alter table public.usage_event      enable row level security;
alter table public.usage_daily      enable row level security;
alter table public.usage_rollup_day enable row level security;

revoke all on public.tenant, public.tenant_member, public.usage_event, public.usage_daily,
              public.usage_rollup_day from anon, authenticated;
grant select on public.tenant, public.tenant_member, public.usage_event, public.usage_daily to authenticated;
grant all on public.tenant, public.tenant_member, public.usage_event, public.usage_daily,
             public.usage_rollup_day to service_role;

drop policy if exists tenant_read on public.tenant;
create policy tenant_read on public.tenant for select to authenticated using (public.is_member(id));
drop policy if exists member_read on public.tenant_member;
create policy member_read on public.tenant_member for select to authenticated using (public.is_member(tenant_id));
drop policy if exists event_read on public.usage_event;
create policy event_read on public.usage_event for select to authenticated using (public.is_member(tenant_id));
drop policy if exists daily_read on public.usage_daily;
create policy daily_read on public.usage_daily for select to authenticated using (public.is_member(tenant_id));

-- ---------- roll-up and retention (service_role only) ----------
create or replace function public.rollup_daily(from_day date, to_day date) returns integer
language plpgsql security definer set search_path = public, pg_temp as $$
declare n integer;
begin
  -- recompute whole days so the function can run again safely; purged days keep their totals
  delete from public.usage_daily d
   where d.day between from_day and to_day
     and not exists (select 1 from public.usage_rollup_day r where r.day = d.day and r.purged);
  insert into public.usage_daily (tenant_id, day, customer_id_hash, feature, provider, model, requests,
         input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
         cost_paise, unpriced_requests)
  select e.tenant_id, (e.ts at time zone 'Asia/Kolkata')::date, e.customer_id_hash, e.feature, e.provider, e.model,
         sum(e.requests), sum(e.input_tokens), sum(e.output_tokens), sum(e.cache_read_tokens),
         sum(e.cache_write_tokens), sum(e.reasoning_tokens),
         coalesce(sum(e.cost_paise), 0), sum(case when e.cost_paise is null then e.requests else 0 end)
    from public.usage_event e
   where (e.ts at time zone 'Asia/Kolkata')::date between from_day and to_day
     and not exists (select 1 from public.usage_rollup_day r
                      where r.day = (e.ts at time zone 'Asia/Kolkata')::date and r.purged)
   group by 1, 2, 3, 4, 5, 6;
  get diagnostics n = row_count;
  insert into public.usage_rollup_day (day)
  select g::date from generate_series(from_day, to_day, interval '1 day') g
  on conflict (day) do update set at = now();
  return n;
end $$;

create or replace function public.purge_raw(keep_days integer default 30) returns integer
language plpgsql security definer set search_path = public, pg_temp as $$
declare n integer; cutoff date := ((now() at time zone 'Asia/Kolkata')::date - keep_days);
begin
  if keep_days < 0 then raise exception 'keep_days must be >= 0'; end if;
  -- only days that were rolled up lose their raw rows
  delete from public.usage_event e
   using public.usage_rollup_day r
   where r.day = (e.ts at time zone 'Asia/Kolkata')::date and r.day < cutoff;
  get diagnostics n = row_count;
  update public.usage_rollup_day set purged = true where day < cutoff;
  return n;
end $$;

revoke all on function public.rollup_daily(date, date) from public;
revoke all on function public.purge_raw(integer) from public;
grant execute on function public.rollup_daily(date, date) to service_role;
grant execute on function public.purge_raw(integer) to service_role;
