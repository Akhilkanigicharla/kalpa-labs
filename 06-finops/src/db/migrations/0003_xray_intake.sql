-- A203: free X-ray intake rows (company, work email, usage export + consent time).
-- Only the service role (the intake function) reads or writes: RLS on, no policies for anon/authenticated.
-- Rows are deleted 14 days after the X-ray unless the client signs up (landing page promise): purge_xray_intake().
create table if not exists xray_intake (
  id            uuid primary key default gen_random_uuid(),
  company       text not null check (char_length(company) between 2 and 120),
  email         text not null check (char_length(email) <= 254),
  filename      text not null,
  bytes         integer not null check (bytes between 1 and 5242880),
  sha256        text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  export_text   text not null,
  consent_at    timestamptz not null,
  delete_after  timestamptz not null,
  created_at    timestamptz not null default now()
);
alter table xray_intake enable row level security;
revoke all on xray_intake from anon, authenticated;
create index if not exists xray_intake_delete_after on xray_intake (delete_after);

create or replace function purge_xray_intake() returns integer
language sql security definer set search_path = public as $$
  with gone as (delete from xray_intake where delete_after < now() returning 1) select count(*)::int from gone;
$$;
revoke all on function purge_xray_intake() from public, anon, authenticated;
