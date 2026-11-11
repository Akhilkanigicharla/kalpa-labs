-- BotBhai security hardening (engineering checklist, 12 Nov 2026). Run AFTER schema.sql, every time schema.sql is run.
-- Safe to apply twice. Tests: bash 01-botbhai/botbhai/supabase/test.sh
-- 1. Least privilege: every BotBhai table is service-role only (the Netlify functions). RLS was on with no policies, but
--    Supabase still grants anon/authenticated full table privileges by default; take them away so a future policy or a
--    switched-off RLS can't expose customer data. Same for sequences and functions.
-- 2. Server-side validation the API can't skip: lengths on public-chat inputs, booking source, invoice JSON shapes.
-- 3. Money table: an invoice is never deleted, its number/amount/lines/client never change, and status only moves
--    due -> paid | void (void keeps the number, per GST practice).
-- 4. Append-only audit log for invoices and clients (secrets such as dashboard_token / view_key are never copied).

-- ---------- 1. least privilege
revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke execute on all functions in schema public from anon, authenticated;
do $$ begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    grant execute on function public.book_slot(uuid, text, text, text, date, text, integer, text, date, text),
                              public.rate_hit(text, integer, integer),
                              public.create_invoice(uuid, date, date, text, jsonb, jsonb, bigint),
                              public.client_token(uuid, text) to service_role;
  end if;
end $$;
do $$ declare t text; begin
  foreach t in array array['clients','sessions','leads','messages','ad_stats','bookings','processed','rate_hits','members','jobs',
                           'invoice_counters','invoices'] loop
    execute format('comment on table public.%I is %L', t, 'service-role only: RLS on, no policies, no anon/authenticated grants');
  end loop;
end $$;

-- ---------- 2. validation (NOT VALID: enforced for every new or changed row; old rows are left as they are)
do $$ begin
  alter table public.rate_hits add constraint rate_hits_key_len check (length(key) <= 200) not valid;
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.bookings add constraint bookings_input_len check (length(contact) <= 80 and length(slot) <= 40
    and coalesce(length(name), 0) <= 120 and coalesce(length(service), 0) <= 120) not valid;
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.bookings add constraint bookings_source_check check (source in ('whatsapp','web','voice','telegram')) not valid;
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.invoices add constraint invoices_json_shape check (jsonb_typeof(lines) = 'array' and jsonb_typeof(bill_to) = 'object') not valid;
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.messages add constraint messages_body_len check (coalesce(length(body), 0) <= 8000) not valid;
exception when duplicate_object then null; end $$;

-- ---------- 3. invoices are permanent
create or replace function public.invoice_guard() returns trigger language plpgsql set search_path = public, pg_temp as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'invoices are never deleted; void it instead' using errcode = 'insufficient_privilege';
  end if;
  if new.number <> old.number or new.client_id <> old.client_id or new.total_paise <> old.total_paise
     or new.lines <> old.lines or new.bill_to <> old.bill_to or new.issued_on <> old.issued_on or new.view_key <> old.view_key then
    raise exception 'an issued invoice can''t be edited; void it and issue a new one' using errcode = 'insufficient_privilege';
  end if;
  if new.status <> old.status and new.status in ('due', 'paid', 'void')  -- unknown values: the CHECK constraint answers
     and not (old.status = 'due' and new.status in ('paid', 'void')) then
    raise exception 'invoice status can''t go from % to %', old.status, new.status using errcode = 'insufficient_privilege';
  end if;
  return new;
end $$;
revoke all on function public.invoice_guard() from public, anon, authenticated;
drop trigger if exists invoices_guard on public.invoices;
create trigger invoices_guard before update or delete on public.invoices for each row execute function public.invoice_guard();

-- ---------- 4. audit log
create table if not exists public.audit_log (
  id         bigint generated always as identity primary key,
  at         timestamptz not null default now(),
  client_id  uuid,                   -- no FK: the trail outlives a deleted client
  table_name text not null,
  row_id     text not null,
  action     text not null check (action in ('INSERT','UPDATE','DELETE')),
  actor      text not null,
  changes    jsonb not null default '{}'::jsonb
);
create index if not exists audit_log_client_at on public.audit_log (client_id, at desc);
alter table public.audit_log enable row level security;
revoke all on public.audit_log from anon, authenticated;
comment on table public.audit_log is 'service-role only: RLS on, no policies, no anon/authenticated grants';

create or replace function public.audit_row() returns trigger language plpgsql security definer set search_path = public, pg_temp as $$
declare o jsonb := case when tg_op <> 'INSERT' then to_jsonb(old) else '{}'::jsonb end;
        n jsonb := case when tg_op <> 'DELETE' then to_jsonb(new) else '{}'::jsonb end;
        d jsonb := '{}'::jsonb; k text;
begin
  for k in select jsonb_object_keys(o || n) loop
    if (o -> k) is distinct from (n -> k) then
      d := d || jsonb_build_object(k, case when k in ('dashboard_token', 'view_key') then '"(changed)"'::jsonb
                                           else jsonb_build_object('old', o -> k, 'new', n -> k) end);
    end if;
  end loop;
  insert into public.audit_log (client_id, table_name, row_id, action, actor, changes)
  values (coalesce(n ->> 'client_id', o ->> 'client_id', case when tg_table_name = 'clients' then coalesce(n ->> 'id', o ->> 'id') end)::uuid,
          tg_table_name, coalesce(n ->> 'id', o ->> 'id'), tg_op, session_user, d);
  return coalesce(new, old);
end $$;
revoke all on function public.audit_row() from public, anon, authenticated;
drop trigger if exists audit_invoices on public.invoices;
create trigger audit_invoices after insert or update on public.invoices for each row execute function public.audit_row();
drop trigger if exists audit_clients on public.clients;
create trigger audit_clients after insert or update or delete on public.clients for each row execute function public.audit_row();

create or replace function public.audit_append_only() returns trigger language plpgsql set search_path = public, pg_temp as $$
begin raise exception 'audit_log is append-only' using errcode = 'insufficient_privilege'; end $$;
revoke all on function public.audit_append_only() from public, anon, authenticated;
drop trigger if exists audit_log_append_only on public.audit_log;
create trigger audit_log_append_only before update or delete on public.audit_log for each row execute function public.audit_append_only();
