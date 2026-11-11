-- Ledger Peaks security hardening (engineering checklist, 12 Nov 2026). Safe to apply twice.
-- 1. Least privilege: Supabase grants EXECUTE on every new public function to anon + authenticated by default, so
--    "revoke ... from public" in 0001 left rollup_daily / purge_raw callable by any signed-in user (purge_raw(0) wiped raw
--    usage). Revoke them from the browser roles by name; only service_role runs them.
-- 2. Idempotent ingest: an optional client event_id, unique per tenant, so a retried batch is never billed twice.
-- 3. Audit log for keys, members and tenants (who changed what, when); a revoked key can never be un-revoked.

revoke all on function public.rollup_daily(date, date) from public, anon, authenticated;
revoke all on function public.purge_raw(integer) from public, anon, authenticated;
revoke all on function public.is_member(uuid) from public, anon;
grant execute on function public.is_member(uuid) to authenticated, service_role;
grant execute on function public.rollup_daily(date, date), public.purge_raw(integer) to service_role;
-- no browser access to the bookkeeping table or the identity sequences
revoke all on public.usage_rollup_day from anon, authenticated;
do $$ declare s text; begin
  for s in select quote_ident(sequence_schema) || '.' || quote_ident(sequence_name) from information_schema.sequences
            where sequence_schema = 'public' loop
    execute 'revoke all on sequence ' || s || ' from anon, authenticated';
  end loop;
end $$;

-- ---------- 2. idempotent ingest
alter table public.usage_event add column if not exists event_id text;
do $$ begin
  alter table public.usage_event add constraint usage_event_event_id_format check (event_id is null or event_id ~ '^[A-Za-z0-9._:-]{8,80}$');
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.usage_event add constraint usage_event_tenant_event_id unique (tenant_id, event_id);  -- NULLs never clash
exception when duplicate_object or duplicate_table then null; end $$;

-- ---------- 3. audit log (append-only; service_role writes through triggers, tenant owners read their own tenant's rows)
create table if not exists public.audit_log (
  id         bigint generated always as identity primary key,
  at         timestamptz not null default now(),
  tenant_id  uuid,                     -- no FK: the trail must outlive a deleted tenant
  table_name text not null,
  row_ref    text not null,
  action     text not null check (action in ('INSERT','UPDATE','DELETE')),
  actor      text not null,            -- database role + JWT subject when there is one
  changes    jsonb not null default '{}'::jsonb   -- changed columns only; key hashes are never copied here
);
create index if not exists audit_log_tenant_at on public.audit_log (tenant_id, at desc);
alter table public.audit_log enable row level security;
revoke all on public.audit_log from anon, authenticated;
grant select on public.audit_log to authenticated;
grant select, insert on public.audit_log to service_role;
drop policy if exists audit_owner_read on public.audit_log;
create policy audit_owner_read on public.audit_log for select to authenticated using (
  exists (select 1 from public.tenant_member m where m.tenant_id = audit_log.tenant_id and m.user_id = auth.uid() and m.role = 'owner'));

create or replace function public.audit_row() returns trigger
language plpgsql security definer set search_path = public, pg_temp as $$
declare o jsonb := case when tg_op <> 'INSERT' then to_jsonb(old) else '{}'::jsonb end;
        n jsonb := case when tg_op <> 'DELETE' then to_jsonb(new) else '{}'::jsonb end;
        d jsonb := '{}'::jsonb; k text; ref text; tid uuid;
begin
  for k in select jsonb_object_keys(o || n) loop
    if k = 'key_hash' then continue; end if;
    if (o -> k) is distinct from (n -> k) then d := d || jsonb_build_object(k, jsonb_build_object('old', o -> k, 'new', n -> k)); end if;
  end loop;
  ref := coalesce(n ->> 'id', o ->> 'id', concat_ws(':', coalesce(n ->> 'tenant_id', o ->> 'tenant_id'), coalesce(n ->> 'user_id', o ->> 'user_id')));
  tid := coalesce(n ->> 'tenant_id', o ->> 'tenant_id', case when tg_table_name = 'tenant' then coalesce(n ->> 'id', o ->> 'id') end)::uuid;
  insert into public.audit_log (tenant_id, table_name, row_ref, action, actor, changes)
  values (tid, tg_table_name, ref, tg_op, session_user || coalesce(':' || nullif(current_setting('request.jwt.claim.sub', true), ''), ''), d);
  return coalesce(new, old);
end $$;
revoke all on function public.audit_row() from public, anon, authenticated;

drop trigger if exists audit_api_key on public.api_key;
create trigger audit_api_key after insert or update or delete on public.api_key for each row execute function public.audit_row();
drop trigger if exists audit_tenant_member on public.tenant_member;
create trigger audit_tenant_member after insert or update or delete on public.tenant_member for each row execute function public.audit_row();
drop trigger if exists audit_tenant on public.tenant;
create trigger audit_tenant after insert or update or delete on public.tenant for each row execute function public.audit_row();

-- the trail is append-only, even for the server
create or replace function public.audit_append_only() returns trigger language plpgsql set search_path = public, pg_temp as $$
begin raise exception 'audit_log is append-only' using errcode = 'insufficient_privilege'; end $$;
revoke all on function public.audit_append_only() from public, anon, authenticated;
drop trigger if exists audit_log_append_only on public.audit_log;
create trigger audit_log_append_only before update or delete on public.audit_log for each row execute function public.audit_append_only();

-- a revoked key stays revoked, and a key's hash or tenant never changes after creation
create or replace function public.api_key_guard() returns trigger language plpgsql set search_path = public, pg_temp as $$
begin
  if old.revoked_at is not null and new.revoked_at is distinct from old.revoked_at then
    raise exception 'a revoked key cannot be restored; make a new key' using errcode = 'insufficient_privilege'; end if;
  if new.key_hash <> old.key_hash or new.tenant_id <> old.tenant_id then
    raise exception 'key hash and tenant are fixed' using errcode = 'insufficient_privilege'; end if;
  return new;
end $$;
revoke all on function public.api_key_guard() from public, anon, authenticated;
drop trigger if exists api_key_guard on public.api_key;
create trigger api_key_guard before update on public.api_key for each row execute function public.api_key_guard();
