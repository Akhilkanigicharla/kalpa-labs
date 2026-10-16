-- JobCard (b2) database schema for Supabase Postgres, with row-level security (A34 / b2.q10).
-- Every row belongs to one technician (auth.users.id). A technician sees and changes only their own rows.
-- Invoice numbers follow the GST rules: unique per technician per financial year, <= 16 characters,
-- series JC/26-27/0001 restarting every 1 April (CGST Rule 46(b) / 49).
-- Apply: Supabase SQL editor, or `psql -f schema.sql` (tests: supabase/test.sh on a local Postgres).

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- tables
create table if not exists public.technicians (
  id            uuid primary key references auth.users(id) on delete cascade,
  name          text not null,
  phone         text not null check (phone ~ '^[6-9][0-9]{9}$'),
  business_name text,
  address       text,
  gst_kind      text not null default 'unregistered' check (gst_kind in ('unregistered','composition','regular')),
  gstin         text check (gstin is null or gstin ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'),
  udyam         text,
  upi_vpa       text,
  state         text not null default 'Telangana',
  language      text not null default 'te' check (language in ('te','hi','en')),
  plan          text not null default 'free' check (plan in ('free','pro')),
  created_at    timestamptz not null default now(),
  check (gst_kind = 'unregistered' or gstin is not null)
);

create table if not exists public.customers (
  id            uuid primary key default gen_random_uuid(),
  technician_id uuid not null default auth.uid() references public.technicians(id) on delete cascade,
  name          text not null,
  phone         text check (phone is null or phone ~ '^[6-9][0-9]{9}$'),
  address       text,
  area          text,
  state         text not null default 'Telangana',
  gstin         text,
  opted_in_whatsapp boolean not null default false,  -- WhatsApp Business policy: reminders only with opt-in
  created_at    timestamptz not null default now(),
  unique (technician_id, phone)
);

create table if not exists public.job_cards (
  id            uuid primary key default gen_random_uuid(),
  technician_id uuid not null default auth.uid() references public.technicians(id) on delete cascade,
  customer_id   uuid references public.customers(id) on delete set null,
  status        text not null default 'open' check (status in ('open','done','invoiced','cancelled')),
  appliance     text check (appliance in ('split_ac','window_ac','cassette_ac','ac','fridge','washing_machine','other')),
  brand         text,
  capacity_tons numeric(3,1),
  issues        text[] not null default '{}',
  parts         jsonb not null default '[]'::jsonb check (jsonb_typeof(parts) = 'array'),
  transcript    text,                         -- the technician's own voice note text (their data)
  next_service  date,
  visited_at    timestamptz not null default now(),
  created_at    timestamptz not null default now()
);

create table if not exists public.invoice_counters (
  technician_id uuid not null references public.technicians(id) on delete cascade,
  fy            text not null check (fy ~ '^[0-9]{2}-[0-9]{2}$'),
  last_seq      int  not null default 0,
  primary key (technician_id, fy)
);

create table if not exists public.invoices (
  id            uuid primary key default gen_random_uuid(),
  technician_id uuid not null default auth.uid() references public.technicians(id) on delete cascade,
  job_card_id   uuid references public.job_cards(id) on delete set null,
  customer_id   uuid references public.customers(id) on delete set null,
  number        text not null check (length(number) <= 16),
  fy            text not null,
  kind          text not null check (kind in ('unregistered','composition','regular')),
  issued_on     date not null default (now() at time zone 'Asia/Kolkata')::date,
  lines         jsonb not null check (jsonb_typeof(lines) = 'array' and jsonb_array_length(lines) > 0),
  taxable_paise bigint not null check (taxable_paise >= 0),
  cgst_paise    bigint not null default 0,
  sgst_paise    bigint not null default 0,
  igst_paise    bigint not null default 0,
  payable_paise bigint not null check (payable_paise >= 0),
  place_of_supply text not null default 'Telangana',
  paid          boolean not null default false,
  created_at    timestamptz not null default now(),
  unique (technician_id, number),
  check (kind = 'regular' or (cgst_paise = 0 and sgst_paise = 0 and igst_paise = 0)),  -- no GST unless registered regular
  check (not (cgst_paise > 0 and igst_paise > 0))
);

create table if not exists public.amc_contracts (
  id            uuid primary key default gen_random_uuid(),
  technician_id uuid not null default auth.uid() references public.technicians(id) on delete cascade,
  customer_id   uuid not null references public.customers(id) on delete cascade,
  starts_on     date not null,
  ends_on       date not null,
  visits_per_year int not null default 3 check (visits_per_year between 1 and 12),
  price_paise   bigint not null check (price_paise >= 0),
  created_at    timestamptz not null default now(),
  check (ends_on > starts_on)
);

create table if not exists public.usage_minutes (   -- voice minutes for the free-plan quota
  technician_id uuid not null references public.technicians(id) on delete cascade,
  month         date not null check (extract(day from month) = 1),
  seconds       int  not null default 0 check (seconds >= 0),
  primary key (technician_id, month)
);

create index if not exists job_cards_tech_visited on public.job_cards (technician_id, visited_at desc);
create index if not exists job_cards_next_service on public.job_cards (technician_id, next_service) where next_service is not null;
create index if not exists invoices_tech_issued on public.invoices (technician_id, issued_on desc);

-- ---------------------------------------------------------------- invoice numbering
create or replace function public.fy_of(d date) returns text language sql immutable as $$
  select to_char(case when extract(month from d) >= 4 then d else d - interval '1 year' end, 'YY') || '-' ||
         to_char(case when extract(month from d) >= 4 then d + interval '1 year' else d end, 'YY')
$$;

-- Atomically takes the next number for the caller (no gaps from races, fresh series each 1 April).
create or replace function public.next_invoice_no(p_date date default (now() at time zone 'Asia/Kolkata')::date)
returns text language plpgsql security definer set search_path = public as $$
declare v_fy text := public.fy_of(p_date); v_seq int; v_tech uuid := auth.uid();
begin
  if v_tech is null then raise exception 'not signed in'; end if;
  insert into public.invoice_counters (technician_id, fy, last_seq) values (v_tech, v_fy, 1)
  on conflict (technician_id, fy) do update set last_seq = invoice_counters.last_seq + 1
  returning last_seq into v_seq;
  return 'JC/' || v_fy || '/' || lpad(v_seq::text, 4, '0');
end $$;
revoke all on function public.next_invoice_no(date) from public;
grant execute on function public.next_invoice_no(date) to authenticated;

-- ---------------------------------------------------------------- row-level security
alter table public.technicians     enable row level security;
alter table public.customers       enable row level security;
alter table public.job_cards       enable row level security;
alter table public.invoices        enable row level security;
alter table public.amc_contracts   enable row level security;
alter table public.usage_minutes   enable row level security;
alter table public.invoice_counters enable row level security;

drop policy if exists own_profile on public.technicians;
create policy own_profile on public.technicians for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

do $$ declare t text; begin
  foreach t in array array['customers','job_cards','invoices','amc_contracts'] loop
    execute format('drop policy if exists own_rows on public.%I', t);
    execute format('create policy own_rows on public.%I for all to authenticated using (technician_id = auth.uid()) with check (technician_id = auth.uid())', t);
  end loop;
end $$;

-- usage and counters: read-only to the technician; written by server functions only
drop policy if exists own_usage on public.usage_minutes;
create policy own_usage on public.usage_minutes for select to authenticated using (technician_id = auth.uid());
drop policy if exists own_counters on public.invoice_counters;
create policy own_counters on public.invoice_counters for select to authenticated using (technician_id = auth.uid());

-- a job card can only point at the same technician's customer
create or replace function public.same_owner_check() returns trigger language plpgsql as $$
begin
  if new.customer_id is not null and not exists (select 1 from public.customers c where c.id = new.customer_id and c.technician_id = new.technician_id) then
    raise exception 'customer belongs to another technician';
  end if;
  return new;
end $$;
drop trigger if exists job_cards_same_owner on public.job_cards;
create trigger job_cards_same_owner before insert or update on public.job_cards for each row execute function public.same_owner_check();
-- an invoice's customer AND job card must both be the same technician's
create or replace function public.invoice_owner_check() returns trigger language plpgsql as $$
begin
  if new.customer_id is not null and not exists (select 1 from public.customers c where c.id = new.customer_id and c.technician_id = new.technician_id) then
    raise exception 'customer belongs to another technician';
  end if;
  if new.job_card_id is not null and not exists (select 1 from public.job_cards j where j.id = new.job_card_id and j.technician_id = new.technician_id) then
    raise exception 'job card belongs to another technician';
  end if;
  return new;
end $$;
drop trigger if exists invoices_same_owner on public.invoices;
create trigger invoices_same_owner before insert or update on public.invoices for each row execute function public.invoice_owner_check();
drop trigger if exists amc_same_owner on public.amc_contracts;
create trigger amc_same_owner before insert or update on public.amc_contracts for each row execute function public.same_owner_check();

-- the paid plan is set only by the server (after payment), never by the technician's own app
create or replace function public.plan_guard() returns trigger language plpgsql as $$
begin
  if current_user in ('authenticated', 'anon') and
     ((tg_op = 'INSERT' and new.plan <> 'free') or (tg_op = 'UPDATE' and new.plan is distinct from old.plan)) then
    raise exception 'plan can only be changed by the server' using errcode = 'insufficient_privilege';
  end if;
  return new;
end $$;
drop trigger if exists technicians_plan_guard on public.technicians;
create trigger technicians_plan_guard before insert or update on public.technicians for each row execute function public.plan_guard();

grant usage on schema public to authenticated;
grant select, insert, update, delete on public.technicians, public.customers, public.job_cards, public.amc_contracts to authenticated;
-- issued invoices are permanent (GST): the app may add them and mark them paid, never edit amounts or delete.
-- To undo a bill, issue a credit note (a new invoice row) instead.
revoke update, delete on public.invoices from authenticated;
grant select, insert on public.invoices to authenticated;
grant update (paid) on public.invoices to authenticated;
grant select on public.usage_minutes, public.invoice_counters to authenticated;
