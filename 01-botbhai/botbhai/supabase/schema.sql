-- BotBhai database (Supabase free tier: 500 MB Postgres — enough for ~1M messages)
-- Run once in Supabase → SQL Editor. Only the server (service-role key in Netlify env) touches these tables.

create extension if not exists pgcrypto;

-- One row per paying business (clinic, salon, agency, gym, exam kit)
create table if not exists clients (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  niche            text not null check (niche in ('salon','realestate','gym','examkits')),
  phone_number_id  text unique,             -- WhatsApp Cloud API "Phone number ID" of this client's number
  owner_whatsapp   text,                    -- owner's number in international format, e.g. 919876543210 (gets booking alerts)
  dashboard_token  text unique not null default encode(gen_random_bytes(18), 'hex'), -- secret link for the owner's dashboard
  config           jsonb not null default '{}'::jsonb,  -- overrides: business, address, hours, phone, catalog, review_link, ads_rules, ads_autopilot, voice_followup…
  waba_id          text,                    -- WhatsApp Business Account ID (for creating templates)
  meta_page_id     text unique,             -- Facebook Page that runs the lead ads
  meta_ad_account_id text,                  -- ad account number without act_
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);

-- Conversation memory: where each customer is in the flow
create table if not exists sessions (
  client_id  uuid references clients(id) on delete cascade,
  contact    text not null,                 -- customer's WhatsApp number (wa_id) or web visitor id
  state      jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (client_id, contact)
);

-- Leads: one row per customer per client, updated as they move cold → warm → hot
create table if not exists leads (
  id          uuid primary key default gen_random_uuid(),
  client_id   uuid references clients(id) on delete cascade,
  contact     text not null,
  name        text,
  score       text not null default 'cold' check (score in ('cold','warm','hot')),
  status      text not null default 'new',  -- new | booked | callback | quiz_done | opted_out | won | lost
  details     jsonb not null default '{}'::jsonb, -- service, date, slot, bhk, budget, goal, score…
  source      text not null default 'whatsapp', -- whatsapp | web | voice | meta_ads
  marketing_opt_in boolean not null default false,  -- replied OFFERS; required for promotional templates (DPDP + WhatsApp policy)
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (client_id, contact)
);
create index if not exists leads_client_updated on leads (client_id, updated_at desc);

-- Message log (for the dashboard's conversation view and for improving FAQs)
create table if not exists messages (
  id         bigserial primary key,
  client_id  uuid references clients(id) on delete cascade,
  contact    text not null,
  direction  text not null check (direction in ('in','out')),
  body       text,
  created_at timestamptz not null default now()
);
create index if not exists messages_client_contact on messages (client_id, contact, created_at);

-- Shared inbox (A04 / P1-W2-02). Column ideas from ArnasDon/wacrm migrations (MIT, © its authors):
-- an explicit bot/human/resolved status next to the engine's humanUntil timer, who owns the chat, and private notes.
-- Safe to re-run on an existing database.
alter table sessions add column if not exists status text not null default 'bot';
alter table sessions add column if not exists assigned_to text;       -- staff first name, e.g. 'Lakshmi'
alter table sessions add column if not exists human_until timestamptz; -- mirror of state.humanUntil (bot paused until)
alter table sessions add column if not exists notes text;              -- private to the salon, never sent to the customer
alter table sessions add column if not exists last_inbound_at timestamptz; -- WhatsApp 24-hour customer-service window
do $$ begin
  alter table sessions add constraint sessions_status_check check (status in ('bot','human','resolved'));
exception when duplicate_object then null; end $$;
update sessions set status = 'human', human_until = (state->>'humanUntil')::timestamptz
  where state->>'humanUntil' is not null and (state->>'humanUntil')::timestamptz > now() and status = 'bot';
create index if not exists sessions_inbox on sessions (client_id, status, updated_at desc);
alter table messages add column if not exists author text not null default 'bot';
do $$ begin
  alter table messages add constraint messages_author_check check (author in ('customer','bot','staff'));
exception when duplicate_object then null; end $$;
update messages set author = 'customer' where direction = 'in' and author = 'bot'; -- rows logged before this column existed

-- Tokens live apart from client data (service role only)
create table if not exists client_secrets (
  client_id        uuid primary key references clients(id) on delete cascade,
  meta_page_token  text,   -- long-lived Page token (leads_retrieval)
  meta_ads_token   text    -- System User token with ads_read / ads_management on the client's ad account
);

-- Daily ad results (ads bot)
create table if not exists ad_stats (
  id bigserial primary key, client_id uuid references clients(id) on delete cascade,
  day date not null, ad_id text, ad_name text, spend numeric, leads int, cpl numeric, verdict text,
  created_at timestamptz not null default now()
);

-- Calendar: one row per booked slot (capacity = config.capacity chairs/trainers per slot)
create table if not exists bookings (
  id uuid primary key default gen_random_uuid(), client_id uuid references clients(id) on delete cascade,
  contact text not null, name text, service text, date_iso date not null, slot text not null,
  status text not null default 'confirmed' check (status in ('confirmed','rescheduled','cancelled','completed','no_show')),
  source text not null default 'whatsapp',        -- whatsapp | web | voice
  confirmed_at timestamptz,                      -- customer replied 1/Confirm to the reminder
  created_at timestamptz not null default now()
);

-- Webhook idempotency: Meta retries deliveries; each message id / lead id is processed once
create table if not exists processed (wamid text primary key, at timestamptz not null default now());

-- Atomic booking: capacity is checked under a per-slot lock, so two customers can never take the last chair.
create or replace function book_slot(p_client uuid, p_contact text, p_name text, p_service text, p_date date, p_slot text,
                                     p_capacity int, p_source text default 'whatsapp', p_replaces_date date default null, p_replaces_slot text default null)
returns boolean language plpgsql security definer set search_path = public as $$
declare taken int;
begin
  perform pg_advisory_xact_lock(hashtext(p_client::text || p_date::text || p_slot));
  select count(*) into taken from bookings
   where client_id = p_client and date_iso = p_date and slot = p_slot and status = 'confirmed'
     and not (p_replaces_date = p_date and p_replaces_slot = p_slot and contact = p_contact);
  if taken >= greatest(p_capacity, 1) then return false; end if;
  if p_replaces_date is not null then
    update bookings set status = 'rescheduled'
     where client_id = p_client and contact = p_contact and date_iso = p_replaces_date and slot = p_replaces_slot and status = 'confirmed';
  end if;
  insert into bookings (client_id, contact, name, service, date_iso, slot, status, source)
  values (p_client, p_contact, p_name, p_service, p_date, p_slot, 'confirmed', p_source);
  return true;
end $$;
revoke execute on function book_slot from public, anon, authenticated;
create index if not exists bookings_slot on bookings (client_id, date_iso, slot) where status = 'confirmed';

-- Rate limiter for the public website chat (anyone on the internet can call it).
-- rate_hit returns false once a key has had p_max hits inside the last p_window_s seconds.
create table if not exists rate_hits (key text not null, at timestamptz not null default now());
create index if not exists rate_hits_key_at on rate_hits (key, at);
create or replace function rate_hit(p_key text, p_window_s int, p_max int)
returns boolean language plpgsql security definer set search_path = public as $$
declare n int;
begin
  perform pg_advisory_xact_lock(hashtext(p_key));
  select count(*) into n from rate_hits where key = p_key and at > now() - make_interval(secs => p_window_s);
  if n >= p_max then return false; end if;
  insert into rate_hits (key) values (p_key);
  return true;
end $$;
revoke execute on function rate_hit from public, anon, authenticated;

-- Members / students with an expiry or fee date (gym renewals, coaching instalments). Import from Excel via Supabase table editor.
create table if not exists members (
  id uuid primary key default gen_random_uuid(), client_id uuid references clients(id) on delete cascade,
  phone text not null, name text, plan text, expires_on date, opted_out boolean not null default false, marketing_opt_in boolean not null default false,
  reminders jsonb not null default '{}'::jsonb, unique (client_id, phone)
);

-- Work queue for agents that run elsewhere (voice caller)
create table if not exists jobs (
  id bigserial primary key, client_id uuid references clients(id) on delete cascade,
  type text not null, payload jsonb not null, run_at timestamptz not null default now(),
  status text not null default 'queued', result jsonb, created_at timestamptz not null default now()
);

-- Billing (A05 / P1-W2-06): Kalpa Labs → salon invoices. "Invoice" (no GST: CGST Act s.32(1)), Udyam on every invoice,
-- one series per financial year KL/26-27/001 (≤ 16 characters). Rules + sources: 01-botbhai/research/billing-scan.md
create table if not exists invoice_counters (fy text primary key, last int not null default 0);
create table if not exists invoices (
  id          uuid primary key default gen_random_uuid(),
  client_id   uuid not null references clients(id) on delete restrict,  -- invoices outlive a cancelled client (books)
  number      text unique not null check (number ~ '^KL/[0-9]{2}-[0-9]{2}/[0-9]{3,6}$' and length(number) <= 16),
  issued_on   date not null default (now() at time zone 'Asia/Kolkata')::date,
  due_on      date,
  period      text,                               -- e.g. 'Nov 2026'
  bill_to     jsonb not null,                     -- name/address/phone as they were on the invoice date
  lines       jsonb not null,                     -- [{desc, qty, rate_paise}]
  total_paise bigint not null check (total_paise > 0),
  status      text not null default 'due' check (status in ('due','paid','void')),  -- void keeps the number: never delete
  paid_on     date,
  paid_ref    text,                               -- UPI reference (UTR) typed by Akhil; never a bank account number
  view_key    text unique not null default encode(gen_random_bytes(16), 'hex'),       -- the salon's no-login link
  sent_at     timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists invoices_client on invoices (client_id, issued_on desc);
-- Number + insert in one transaction, so the series never skips or repeats.
create or replace function create_invoice(p_client uuid, p_issued date, p_due date, p_period text, p_bill_to jsonb, p_lines jsonb, p_total bigint)
returns invoices language plpgsql security definer set search_path = public as $$
declare v_fy text; v_seq int; v_row invoices;
begin
  v_fy := to_char(p_issued - interval '3 months', 'YY') || '-' || to_char(p_issued + interval '9 months', 'YY');
  insert into invoice_counters (fy, last) values (v_fy, 1)
    on conflict (fy) do update set last = invoice_counters.last + 1 returning last into v_seq;
  insert into invoices (client_id, number, issued_on, due_on, period, bill_to, lines, total_paise)
  values (p_client, 'KL/' || v_fy || '/' || lpad(v_seq::text, 3, '0'), p_issued, p_due, p_period, p_bill_to, p_lines, p_total)
  returning * into v_row;
  return v_row;
end $$;
revoke execute on function create_invoice from public, anon, authenticated;

-- Lock everything down: no public access. The anon key can read nothing.
alter table clients  enable row level security;
alter table sessions enable row level security;
alter table leads    enable row level security;
alter table messages enable row level security;
alter table client_secrets enable row level security;
alter table ad_stats enable row level security;
alter table members enable row level security;
alter table jobs enable row level security;
alter table bookings enable row level security;
alter table processed enable row level security;
alter table rate_hits enable row level security;
alter table invoice_counters enable row level security;
alter table invoices enable row level security;
-- housekeeping (daily): delete from rate_hits where at < now() - interval '1 day';
-- housekeeping (monthly): delete from processed where at < now() - interval '30 days';

-- Data retention (DPDP Act 2023: keep only what you need). Run monthly, or schedule with pg_cron:
-- delete from messages where created_at < now() - interval '180 days';

-- Example client (edit, then run):
-- insert into clients (name, niche, phone_number_id, owner_whatsapp, config)
-- values ('Glow Studio', 'salon', '123456789012345', '919876543210',
--         '{"business":"Glow Studio","address":"Jubilee Hills","phone":"+91 98765 43210","review_link":"https://g.page/r/..."}');
-- select name, dashboard_token from clients;   -- → https://<site>/dashboard.html#key=<dashboard_token>  (owner dashboard + inbox; the #key part never reaches a server)
-- Shared inbox for the same client: https://<site>/inbox.html#key=<dashboard_token>  (the #key part never reaches a server;
-- the page saves it on that phone and wipes it from the address bar). Optional config: "inbox_hold_hours" (default 12).
