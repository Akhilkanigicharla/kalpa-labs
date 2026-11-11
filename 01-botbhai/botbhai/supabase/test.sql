-- BotBhai schema tests on a real Postgres 16 (run by test.sh). Every check raises on failure.
\set ON_ERROR_STOP 1
do $$
declare c uuid; r invoices; n text; ok boolean;
begin
  insert into clients (name, niche, owner_whatsapp) values ('Glow Studio', 'salon', '919000000000') returning id into c;

  -- A05: numbering per financial year (IST date passed in), padded to 3 digits
  r := create_invoice(c, '2026-10-16', '2026-10-23', 'Oct 2026', '{"name":"Glow Studio"}', '[{"desc":"Setup","qty":1,"rate_paise":299900}]', 299900);
  if r.number <> 'KL/26-27/001' then raise exception 'first number %', r.number; end if;
  if r.status <> 'due' or length(r.view_key) <> 32 then raise exception 'defaults % %', r.status, r.view_key; end if;
  r := create_invoice(c, '2027-03-31', null, null, '{}', '[]', 100);
  if r.number <> 'KL/26-27/002' then raise exception '31 Mar → %', r.number; end if;
  r := create_invoice(c, '2027-04-01', null, null, '{}', '[]', 100);
  if r.number <> 'KL/27-28/001' then raise exception '1 Apr → %', r.number; end if;
  r := create_invoice(c, '2027-01-15', null, null, '{}', '[]', 100);
  if r.number <> 'KL/26-27/003' then raise exception 'Jan → %', r.number; end if;

  -- constraints
  begin insert into invoices (client_id, number, bill_to, lines, total_paise) values (c, 'KL/26-27/999', '{}', '[]', 0); raise exception 'zero total accepted';
  exception when check_violation then null; end;
  begin insert into invoices (client_id, number, bill_to, lines, total_paise) values (c, 'INV-1', '{}', '[]', 5); raise exception 'bad number accepted';
  exception when check_violation then null; end;
  begin insert into invoices (client_id, number, bill_to, lines, total_paise) values (c, 'KL/26-27/001', '{}', '[]', 5); raise exception 'duplicate number accepted';
  exception when unique_violation then null; end;
  begin update invoices set status = 'refunded' where number = 'KL/26-27/001'; raise exception 'bad status accepted';
  exception when check_violation then null; end;
  begin delete from clients where id = c; raise exception 'client with invoices deleted';
  exception when foreign_key_violation then null; end;

  -- A04: inbox columns and checks
  insert into sessions (client_id, contact, state) values (c, '919812345678', '{}');
  select status = 'bot' into ok from sessions where contact = '919812345678'; if not ok then raise exception 'session default status'; end if;
  begin update sessions set status = 'snoozed'; raise exception 'bad session status accepted';
  exception when check_violation then null; end;
  insert into messages (client_id, contact, direction, body, author) values (c, '919812345678', 'out', 'hi', 'staff');
  begin insert into messages (client_id, contact, direction, body, author) values (c, '919812345678', 'out', 'hi', 'robot'); raise exception 'bad author accepted';
  exception when check_violation then null; end;

  -- lock-down: every table has RLS, no policies, and the browser roles can't call the server functions
  select string_agg(relname, ', ') into n from pg_class where relnamespace = 'public'::regnamespace and relkind = 'r' and not relrowsecurity;
  if n is not null then raise exception 'tables without RLS: %', n; end if;
  if has_function_privilege('anon', 'create_invoice(uuid,date,date,text,jsonb,jsonb,bigint)', 'execute')
     or has_function_privilege('authenticated', 'book_slot(uuid,text,text,text,date,text,integer,text,date,text)', 'execute')
  then raise exception 'browser roles can execute server-only functions'; end if;
end $$;
-- A51 (REA audit #8): Meta tokens live only in Supabase Vault; the server reads them through client_token() alone.
do $$
declare c uuid; c2 uuid;
begin
  insert into clients (name, niche) values ('Vault Salon', 'salon') returning id into c;
  insert into clients (name, niche) values ('Old Salon', 'salon') returning id into c2;
  perform set_client_token(c, 'meta_page', 'EAAG-page-1');
  perform set_client_token(c, 'meta_ads', 'EAAG-ads-1');
  if client_token(c, 'meta_page') is distinct from 'EAAG-page-1' or client_token(c, 'meta_ads') is distinct from 'EAAG-ads-1'
  then raise exception 'vault read back %', client_token(c, 'meta_page'); end if;
  perform set_client_token(c, 'meta_page', 'EAAG-page-2'); -- rotate: same secret row, new value
  if client_token(c, 'meta_page') <> 'EAAG-page-2' or (select count(*) from vault.secrets where name = 'client:' || c || ':meta_page') <> 1
  then raise exception 'rotation broke'; end if;
  if client_token(c2, 'meta_page') is not null then raise exception 'token leaked across clients'; end if;
  perform vault.create_secret('other-app-secret', 'client:' || c || ':smtp', 'not ours');
  if client_token(c, 'smtp') is not null then raise exception 'client_token reads secrets outside meta_page/meta_ads'; end if;
  perform set_client_token(c, 'meta_ads', null); -- clearing removes the secret
  if client_token(c, 'meta_ads') is not null then raise exception 'cleared token still readable'; end if;
  begin perform set_client_token(c, 'whatsapp', 'x'); raise exception 'unknown kind accepted'; exception when invalid_parameter_value then null; end;
  begin perform set_client_token(gen_random_uuid(), 'meta_page', 'x'); raise exception 'unknown client accepted'; exception when foreign_key_violation then null; end;

  -- no plain-text token anywhere outside the Vault
  if to_regclass('public.client_secrets') is not null then raise exception 'client_secrets table still exists'; end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public' and column_name in ('meta_page_token', 'meta_ads_token'))
  then raise exception 'plain-text token column in public schema'; end if;
  if exists (select 1 from vault.secrets where secret like '%EAAG%') then raise exception 'vault row stores plain text'; end if;

  -- only the server (service_role) may read; nobody but the SQL editor may write
  if has_function_privilege('anon', 'client_token(uuid,text)', 'execute') or has_function_privilege('authenticated', 'client_token(uuid,text)', 'execute')
  then raise exception 'browser roles can read tokens'; end if;
  if not has_function_privilege('service_role', 'client_token(uuid,text)', 'execute') then raise exception 'server cannot read tokens'; end if;
  if has_function_privilege('service_role', 'set_client_token(uuid,text,text)', 'execute') or has_function_privilege('anon', 'set_client_token(uuid,text,text)', 'execute')
     or has_function_privilege('service_role', 'migrate_client_secrets()', 'execute')
  then raise exception 'token writer callable from the API'; end if;

  -- migration: an old plain-text client_secrets table moves into the Vault and is dropped
  create table client_secrets (client_id uuid primary key references clients(id) on delete cascade, meta_page_token text, meta_ads_token text);
  insert into client_secrets values (c2, 'OLD-page', 'OLD-ads');
  perform migrate_client_secrets();
  if client_token(c2, 'meta_page') <> 'OLD-page' or client_token(c2, 'meta_ads') <> 'OLD-ads' then raise exception 'migration lost tokens'; end if;
  if to_regclass('public.client_secrets') is not null then raise exception 'migration kept the plain table'; end if;

  -- deleting a client deletes its secrets
  delete from clients where id = c2;
  if exists (select 1 from vault.secrets where name like 'client:' || c2 || ':%') then raise exception 'orphan secrets after client delete'; end if;
end $$;
-- Security hardening (migrations/0001_security.sql, 12 Nov 2026)
do $$
declare c uuid; r invoices; n text;
begin
  -- least privilege: under Supabase's default grants, browser roles still hold no table, sequence or server-function rights
  select string_agg(distinct table_name, ', ') into n from information_schema.role_table_grants
   where table_schema = 'public' and grantee in ('anon', 'authenticated');
  if n is not null then raise exception 'browser roles have table grants on: %', n; end if;
  if has_function_privilege('anon', 'rate_hit(text,integer,integer)', 'execute') or has_function_privilege('authenticated', 'create_invoice(uuid,date,date,text,jsonb,jsonb,bigint)', 'execute')
  then raise exception 'browser roles can run server functions'; end if;
  if not has_function_privilege('service_role', 'book_slot(uuid,text,text,text,date,text,integer,text,date,text)', 'execute')
     or not has_function_privilege('service_role', 'rate_hit(text,integer,integer)', 'execute')
  then raise exception 'server lost access to its functions'; end if;
  if obj_description('public.leads'::regclass) not like 'service-role only%' then raise exception 'leads not marked service-role only'; end if;

  -- validation the API can't skip
  insert into clients (name, niche) values ('Guard Salon', 'salon') returning id into c;
  begin perform book_slot(c, repeat('9', 81), 'X', 'Cut', '2028-01-05', '10:00', 1); raise exception 'oversized contact booked';
  exception when check_violation then null; end;
  begin perform book_slot(c, '919800000001', 'X', 'Cut', '2028-01-05', '10:00', 1, 'sms'); raise exception 'unknown booking source accepted';
  exception when check_violation then null; end;
  if not book_slot(c, '919800000001', 'Asha', 'Cut', '2028-01-05', '10:00', 1, 'telegram') then raise exception 'valid telegram booking refused'; end if;
  begin perform rate_hit(repeat('k', 201), 60, 5); raise exception 'oversized rate key accepted';
  exception when check_violation then null; end;
  begin perform create_invoice(c, '2030-05-01', null, null, '[]', '[]', 100); raise exception 'bill_to array accepted';
  exception when check_violation then null; end;

  -- invoices are permanent: no delete, no edits to money fields, status only due -> paid | void
  r := create_invoice(c, '2030-05-02', null, 'May 2030', '{"name":"Guard Salon"}', '[{"desc":"Plan","qty":1,"rate_paise":149900}]', 149900);
  begin delete from invoices where id = r.id; raise exception 'invoice deleted';
  exception when insufficient_privilege then null; end;
  begin update invoices set total_paise = 1 where id = r.id; raise exception 'invoice amount edited';
  exception when insufficient_privilege then null; end;
  begin update invoices set number = 'KL/30-31/999' where id = r.id; raise exception 'invoice renumbered';
  exception when insufficient_privilege then null; end;
  update invoices set sent_at = now() where id = r.id;                                    -- allowed: sent
  update invoices set status = 'paid', paid_on = '2030-05-03', paid_ref = 'UTR123456' where id = r.id;  -- allowed: due -> paid
  begin update invoices set status = 'due' where id = r.id; raise exception 'paid invoice reopened';
  exception when insufficient_privilege then null; end;
  begin update invoices set status = 'void' where id = r.id; raise exception 'paid invoice voided';
  exception when insufficient_privilege then null; end;

  -- audit trail: invoice life and client changes are logged, secrets never copied, log is append-only
  if (select count(*) from audit_log where row_id = r.id::text) < 3 then raise exception 'invoice changes not audited'; end if;
  if not exists (select 1 from audit_log where row_id = r.id::text and changes -> 'status' ->> 'new' = 'paid') then raise exception 'paid not audited'; end if;
  update clients set active = false where id = c;
  if not exists (select 1 from audit_log where table_name = 'clients' and row_id = c::text and changes ? 'active') then raise exception 'client deactivation not audited'; end if;
  if exists (select 1 from audit_log a join clients k on a.changes::text like '%' || k.dashboard_token || '%') then raise exception 'dashboard token copied into audit log'; end if;
  if exists (select 1 from audit_log a join invoices i on a.changes::text like '%' || i.view_key || '%') then raise exception 'invoice view key copied into audit log'; end if;
  begin delete from audit_log; raise exception 'audit log erased';
  exception when insufficient_privilege then null; end;
end $$;
select 'schema checks passed';
