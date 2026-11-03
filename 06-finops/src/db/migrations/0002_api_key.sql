-- Ledger Peaks F-11: per-tenant ingest keys. Only a SHA-256 hash of each key is stored;
-- the key itself is shown once to the tenant owner and never saved.
create table if not exists public.api_key (
  id          bigint generated always as identity primary key,
  tenant_id   uuid not null references public.tenant(id) on delete cascade,
  key_hash    text not null unique check (key_hash ~ '^[0-9a-f]{64}$'),
  label       text not null default '' check (length(label) <= 60),
  created_at  timestamptz not null default now(),
  revoked_at  timestamptz
);
create index if not exists api_key_tenant on public.api_key (tenant_id);
alter table public.api_key enable row level security;
revoke all on public.api_key from anon, authenticated;
grant all on public.api_key to service_role;
-- members may see their own tenant's key labels and dates (not usable: hash only)
grant select (id, tenant_id, label, created_at, revoked_at) on public.api_key to authenticated;
drop policy if exists key_read on public.api_key;
create policy key_read on public.api_key for select to authenticated using (public.is_member(tenant_id));
