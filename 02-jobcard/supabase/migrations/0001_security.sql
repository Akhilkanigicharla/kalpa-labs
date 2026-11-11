-- JobCard security hardening (engineering checklist, 12 Nov 2026). Run AFTER schema.sql, every time schema.sql is run.
-- Safe to apply twice. Tests: bash 02-jobcard/supabase/test.sh
-- 1. Least privilege: Supabase grants every new table/function to anon by default. The app only ever signs in, so anon
--    gets nothing; a technician can't delete his own profile (that cascaded away his GST invoices).
-- 2. Fixed search_path on every function (Supabase linter "function_search_path_mutable").
-- 3. Mass assignment on invoices: the app sends kind, number, fy and amounts, so the database checks them: the GST kind
--    must be the technician's own registration (an unregistered technician can't issue a GST bill), the number must be a
--    JC/yy-yy/nnnn number of the same financial year as fy, and payable must equal taxable + taxes within the 50 paise
--    round-off.
-- 4. Bills keep their buyer: a customer or job card that has an invoice can't be deleted (it used to null the link).
-- 5. Audit log (append-only) for invoices, plan/GST changes and customer deletes; a technician reads only his own rows.

-- ---------- 1. least privilege
revoke all on all tables in schema public from anon;
revoke all on all sequences in schema public from anon;
revoke execute on function public.next_invoice_no(date) from anon;
revoke delete on public.technicians from authenticated;

-- ---------- 2. fixed search_path
alter function public.fy_of(date) set search_path = public, pg_temp;
alter function public.same_owner_check() set search_path = public, pg_temp;
alter function public.invoice_owner_check() set search_path = public, pg_temp;
alter function public.plan_guard() set search_path = public, pg_temp;

-- ---------- 3. invoice integrity (runs for the app and the bot alike)
create or replace function public.invoice_integrity() returns trigger language plpgsql set search_path = public, pg_temp as $$
declare v_kind text;
begin
  if new.number !~ '^JC/[0-9]{2}-[0-9]{2}/[0-9]{4,6}$' or split_part(new.number, '/', 2) <> new.fy then
    raise exception 'invoice number must be JC/<fy>/<serial> of the same financial year' using errcode = 'check_violation';
  end if;
  select t.gst_kind into v_kind from public.technicians t where t.id = new.technician_id;
  if v_kind is distinct from new.kind then
    raise exception 'invoice kind % does not match the technician''s GST registration', new.kind using errcode = 'check_violation';
  end if;
  if abs(new.payable_paise - (new.taxable_paise + new.cgst_paise + new.sgst_paise + new.igst_paise)) > 50 then
    raise exception 'payable must equal taxable + GST (round-off up to 50 paise)' using errcode = 'check_violation';
  end if;
  if least(new.cgst_paise, new.sgst_paise, new.igst_paise) < 0 then
    raise exception 'negative tax' using errcode = 'check_violation';
  end if;
  return new;
end $$;
revoke all on function public.invoice_integrity() from public, anon, authenticated;
drop trigger if exists invoices_integrity on public.invoices;
create trigger invoices_integrity before insert on public.invoices for each row execute function public.invoice_integrity();

-- ---------- 4. an invoice keeps its customer and job card (NO ACTION: still lets a whole account be removed by the server)
alter table public.invoices drop constraint if exists invoices_customer_id_fkey;
alter table public.invoices add constraint invoices_customer_id_fkey foreign key (customer_id) references public.customers(id) on delete no action;
alter table public.invoices drop constraint if exists invoices_job_card_id_fkey;
alter table public.invoices add constraint invoices_job_card_id_fkey foreign key (job_card_id) references public.job_cards(id) on delete no action;

-- ---------- 5. audit log
create table if not exists public.audit_log (
  id            bigint generated always as identity primary key,
  at            timestamptz not null default now(),
  technician_id uuid,                -- no FK: the trail outlives the rows it describes
  table_name    text not null,
  row_id        text not null,
  action        text not null check (action in ('INSERT','UPDATE','DELETE')),
  actor         text not null,       -- database role + JWT subject
  changes       jsonb not null default '{}'::jsonb
);
create index if not exists audit_log_tech_at on public.audit_log (technician_id, at desc);
alter table public.audit_log enable row level security;
revoke all on public.audit_log from anon, authenticated;
grant select on public.audit_log to authenticated;
drop policy if exists own_audit on public.audit_log;
create policy own_audit on public.audit_log for select to authenticated using (technician_id = auth.uid());

-- Only the columns that changed are kept; a deleted customer keeps just its id (DPDP: the erasure itself stays erased).
create or replace function public.audit_row() returns trigger language plpgsql security definer set search_path = public, pg_temp as $$
declare o jsonb := case when tg_op <> 'INSERT' then to_jsonb(old) else '{}'::jsonb end;
        n jsonb := case when tg_op <> 'DELETE' then to_jsonb(new) else '{}'::jsonb end;
        d jsonb := '{}'::jsonb; k text;
begin
  if tg_table_name <> 'customers' then
    for k in select jsonb_object_keys(o || n) loop
      if k = 'transcript' then continue; end if;
      if (o -> k) is distinct from (n -> k) then d := d || jsonb_build_object(k, jsonb_build_object('old', o -> k, 'new', n -> k)); end if;
    end loop;
    if tg_op = 'UPDATE' and d = '{}'::jsonb then return new; end if;
  end if;
  insert into public.audit_log (technician_id, table_name, row_id, action, actor, changes)
  values (coalesce(n ->> 'technician_id', o ->> 'technician_id', n ->> 'id', o ->> 'id')::uuid, tg_table_name,
          coalesce(n ->> 'id', o ->> 'id'), tg_op,
          session_user || coalesce(':' || nullif(current_setting('request.jwt.claim.sub', true), ''), ''), d);
  return coalesce(new, old);
end $$;
revoke all on function public.audit_row() from public, anon, authenticated;
drop trigger if exists audit_invoices on public.invoices;
create trigger audit_invoices after insert or update on public.invoices for each row execute function public.audit_row();
drop trigger if exists audit_technicians on public.technicians;
create trigger audit_technicians after update of plan, gst_kind, gstin or delete on public.technicians for each row execute function public.audit_row();
drop trigger if exists audit_customers on public.customers;
create trigger audit_customers after delete on public.customers for each row execute function public.audit_row();

create or replace function public.audit_append_only() returns trigger language plpgsql set search_path = public, pg_temp as $$
begin raise exception 'audit_log is append-only' using errcode = 'insufficient_privilege'; end $$;
revoke all on function public.audit_append_only() from public, anon, authenticated;
drop trigger if exists audit_log_append_only on public.audit_log;
create trigger audit_log_append_only before update or delete on public.audit_log for each row execute function public.audit_append_only();

-- functions created above must not be callable by anon either (Supabase default grants)
revoke execute on all functions in schema public from anon;
