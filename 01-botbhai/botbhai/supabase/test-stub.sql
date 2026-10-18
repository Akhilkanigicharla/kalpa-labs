-- Local stand-in for the parts of Supabase the schema relies on (tests only). Roles/auth same as 02-jobcard/supabase/test-stub.sql;
-- plus a Vault stand-in (A51) with the same functions and view names as Supabase's supabase_vault extension.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin; end if;
end $$;
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant usage on schema auth to authenticated, anon;
grant execute on function auth.uid() to authenticated, anon;

-- Vault stand-in: real Vault encrypts with libsodium; here the stored value is only base64 of the reversed text, enough to
-- prove the schema goes through vault.create_secret/update_secret and vault.decrypted_secrets rather than a plain column.
create schema if not exists vault;
create table if not exists vault.secrets (id uuid primary key default gen_random_uuid(), name text unique, description text not null default '',
  secret text not null, created_at timestamptz not null default now(), updated_at timestamptz not null default now());
create or replace function vault.create_secret(new_secret text, new_name text default null, new_description text default '', new_key_id uuid default null)
returns uuid language sql as $$
  insert into vault.secrets (name, description, secret) values (new_name, coalesce(new_description, ''), encode(convert_to(reverse(new_secret), 'UTF8'), 'base64')) returning id $$;
create or replace function vault.update_secret(secret_id uuid, new_secret text default null, new_name text default null, new_description text default null, new_key_id uuid default null)
returns void language sql as $$
  update vault.secrets set secret = coalesce(encode(convert_to(reverse(new_secret), 'UTF8'), 'base64'), secret), name = coalesce(new_name, name),
    description = coalesce(new_description, description), updated_at = now() where id = secret_id $$;
create or replace view vault.decrypted_secrets as
  select id, name, description, secret, reverse(convert_from(decode(secret, 'base64'), 'UTF8')) as decrypted_secret, created_at, updated_at from vault.secrets;
