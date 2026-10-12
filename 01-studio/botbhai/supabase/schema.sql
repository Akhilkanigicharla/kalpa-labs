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
  source      text not null default 'whatsapp', -- whatsapp | web | voice
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

-- Members / students with an expiry or fee date (gym renewals, coaching instalments). Import from Excel via Supabase table editor.
create table if not exists members (
  id uuid primary key default gen_random_uuid(), client_id uuid references clients(id) on delete cascade,
  phone text not null, name text, plan text, expires_on date, opted_out boolean not null default false,
  reminders jsonb not null default '{}'::jsonb, unique (client_id, phone)
);

-- Work queue for agents that run elsewhere (voice caller)
create table if not exists jobs (
  id bigserial primary key, client_id uuid references clients(id) on delete cascade,
  type text not null, payload jsonb not null, run_at timestamptz not null default now(),
  status text not null default 'queued', result jsonb, created_at timestamptz not null default now()
);

-- Lock everything down: no public access. The anon key can read nothing.
alter table clients  enable row level security;
alter table sessions enable row level security;
alter table leads    enable row level security;
alter table messages enable row level security;
alter table client_secrets enable row level security;
alter table ad_stats enable row level security;
alter table members enable row level security;
alter table jobs enable row level security;

-- Data retention (DPDP Act 2023: keep only what you need). Run monthly, or schedule with pg_cron:
-- delete from messages where created_at < now() - interval '180 days';

-- Example client (edit, then run):
-- insert into clients (name, niche, phone_number_id, owner_whatsapp, config)
-- values ('Glow Studio', 'salon', '123456789012345', '919876543210',
--         '{"business":"Glow Studio","address":"Jubilee Hills","phone":"+91 98765 43210","review_link":"https://g.page/r/..."}');
-- select name, dashboard_token from clients;   -- → https://<site>/dashboard.html?token=<dashboard_token>
