-- Ledger Peaks schema tests (A28 / F-03). Setup as owner, then act as service_role, tenant A, tenant B and anon.
\set ON_ERROR_STOP on
insert into auth.users values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000b'),
                              ('00000000-0000-0000-0000-0000000000a2');
insert into public.tenant (id, name) values
  ('10000000-0000-0000-0000-00000000000a', 'Acme AI'), ('10000000-0000-0000-0000-00000000000b', 'Beta Bots');
insert into public.tenant_member (tenant_id, user_id, role) values
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'owner'),
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a2', 'viewer'),
  ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'owner');

-- ---- the ingest API writes as service_role
set role service_role;
insert into public.usage_event (tenant_id, ts, provider, model, input_tokens, output_tokens, cache_read_tokens,
                                customer_id_hash, feature, cost_paise, source) values
  ('10000000-0000-0000-0000-00000000000a', now() - interval '40 days', 'openai', 'gpt-4.1-mini', 1000, 200, 0, 'c_00000000000000aa', 'chat', 120, 'test'),
  ('10000000-0000-0000-0000-00000000000a', now() - interval '40 days', 'openai', 'gpt-4.1-mini', 3000, 100, 500, 'c_00000000000000aa', 'chat', 180, 'test'),
  ('10000000-0000-0000-0000-00000000000a', now() - interval '1 day', 'anthropic', 'claude-haiku-4-5', 500, 50, 0, null, 'summary', null, 'test'),
  ('10000000-0000-0000-0000-00000000000b', now() - interval '1 day', 'google', 'gemini-2.5-flash', 9000, 900, 0, 'c_00000000000000bb', 'search', 400, 'test');
do $$ begin
  begin insert into public.usage_event (tenant_id, ts, provider, model, input_tokens) values
        ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x', -1);
        raise exception 'negative tokens accepted';
  exception when check_violation then null; end;
  begin insert into public.usage_event (tenant_id, ts, provider, model, customer_id_hash) values
        ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x', '9848012345');
        raise exception 'raw (unhashed) customer id accepted';
  exception when check_violation then null; end;
  begin insert into public.usage_event (tenant_id, ts, provider, model, output_tokens, reasoning_tokens) values
        ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'o4', 10, 11);
        raise exception 'reasoning > output accepted';
  exception when check_violation then null; end;
end $$;
-- daily roll-up: totals must equal the raw events
do $$ declare n int; r record; begin
  n := public.rollup_daily((now() - interval '40 days')::date, now()::date);
  assert n = 3, 'expected 3 daily rows, got ' || n;
  n := public.rollup_daily((now() - interval '40 days')::date, now()::date);   -- idempotent
  select count(*), sum(requests), sum(input_tokens), sum(cost_paise), sum(unpriced_requests)
    into r from public.usage_daily;
  assert r.count = 3 and r.sum = 4, 'rollup rows/requests wrong';
  assert (select sum(input_tokens) from public.usage_daily) = 13500, 'rollup tokens wrong';
  assert (select sum(cost_paise) from public.usage_daily) = 700, 'rollup paise wrong';
  assert (select unpriced_requests from public.usage_daily where feature = 'summary') = 1, 'unpriced not counted';
  -- purge keeps the daily totals, drops raw rows older than 30 days
  n := public.purge_raw(30);
  assert n = 2, 'purge removed ' || n;
  assert (select count(*) from public.usage_event) = 2, 'recent raw rows were purged';
  assert (select sum(cost_paise) from public.usage_daily) = 700, 'purge changed the daily totals';
end $$;
reset role;

-- ---- tenant A owner: sees only A, cannot write usage
set role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
do $$ declare c int; begin
  select count(*) into c from public.usage_event;  assert c = 1, 'A sees ' || c || ' events';
  select count(*) into c from public.usage_daily;  assert c = 2, 'A sees ' || c || ' daily rows';
  select count(*) into c from public.tenant;       assert c = 1, 'A sees other tenants';
  select count(*) into c from public.tenant_member; assert c = 2, 'A sees other tenants'' members';
  begin insert into public.usage_event (tenant_id, ts, provider, model) values
        ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x');
        raise exception 'a user wrote usage directly (only the ingest API may)';
  exception when insufficient_privilege then null; end;
  begin update public.usage_daily set cost_paise = 0; raise exception 'user edited daily totals';
  exception when insufficient_privilege then null; end;
  begin perform public.rollup_daily(now()::date, now()::date); raise exception 'user ran the rollup';
  exception when insufficient_privilege then null; end;
  begin perform public.purge_raw(0); raise exception 'user ran the purge';
  exception when insufficient_privilege then null; end;
  begin insert into public.tenant_member values ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000a', 'owner');
        raise exception 'A joined tenant B';
  exception when insufficient_privilege then null; end;
end $$;

-- ---- A's viewer sees A's data too
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a2', false);
do $$ begin assert (select count(*) from public.usage_daily) = 2, 'viewer cannot read its tenant'; end $$;

-- ---- tenant B cannot read A
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000b', false);
do $$ declare c int; begin
  select count(*) into c from public.usage_event; assert c = 1, 'B sees ' || c || ' events';
  select count(*) into c from public.usage_daily where tenant_id = '10000000-0000-0000-0000-00000000000a';
  assert c = 0, 'B can read A''s daily totals';
  select count(*) into c from public.usage_event where tenant_id = '10000000-0000-0000-0000-00000000000a';
  assert c = 0, 'B can read A''s events';
end $$;
reset role;

-- ---- anon sees nothing
set role anon;
select set_config('request.jwt.claim.sub', '', false);
do $$ begin
  begin perform count(*) from public.usage_event; raise exception 'anon can query usage';
  exception when insufficient_privilege then null; end;
end $$;
reset role;

-- ---- metadata only: no column may hold prompt or completion text
do $$ declare c int; begin
  select count(*) into c from information_schema.columns
   where table_schema = 'public' and table_name in ('usage_event', 'usage_daily')
     and column_name ~ '(prompt|completion|content|message|text|input$|output$)';
  assert c = 0, 'a text-carrying column exists';
  select count(*) into c from pg_tables where schemaname = 'public'
     and tablename in ('tenant', 'tenant_member', 'usage_event', 'usage_daily') and rowsecurity;
  assert c = 4, 'RLS is off on a table';
end $$;
-- ---- F-11 api_key: hash only, tenant-scoped, key_hash hidden from members
insert into public.api_key (tenant_id, key_hash, label) values
  ('10000000-0000-0000-0000-00000000000a', repeat('a', 64), 'prod'),
  ('10000000-0000-0000-0000-00000000000b', repeat('b', 64), 'prod');
do $$ begin
  begin insert into public.api_key (tenant_id, key_hash) values ('10000000-0000-0000-0000-00000000000a', 'lp_rawkey');
        raise exception 'raw key stored';
  exception when check_violation then null; end;
end $$;
set role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
do $$ declare c int; begin
  select count(*) into c from public.api_key; assert c = 1, 'A sees ' || c || ' keys';
  begin perform key_hash from public.api_key; raise exception 'member can read key hashes';
  exception when insufficient_privilege then null; end;
  begin insert into public.api_key (tenant_id, key_hash) values ('10000000-0000-0000-0000-00000000000a', repeat('c', 64));
        raise exception 'member created a key directly';
  exception when insufficient_privilege then null; end;
end $$;
reset role;

-- ---- security hardening (0003_security.sql, 12 Nov 2026)
-- least privilege: under Supabase's default grants, the browser roles must still not run the roll-up or purge
do $$ begin
  if has_function_privilege('authenticated', 'public.purge_raw(integer)', 'execute')
     or has_function_privilege('anon', 'public.purge_raw(integer)', 'execute')
     or has_function_privilege('authenticated', 'public.rollup_daily(date,date)', 'execute')
     or has_function_privilege('anon', 'public.rollup_daily(date,date)', 'execute')
  then raise exception 'browser roles can run rollup_daily/purge_raw'; end if;
  if has_table_privilege('anon', 'public.usage_event', 'select') or has_table_privilege('anon', 'public.audit_log', 'select')
     or has_table_privilege('authenticated', 'public.usage_rollup_day', 'select')
  then raise exception 'anon/authenticated have table access they do not need'; end if;
  if exists (select 1 from information_schema.role_table_grants where table_schema = 'public' and grantee in ('anon', 'authenticated')
             and privilege_type in ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'))
  then raise exception 'a browser role can write a Ledger Peaks table'; end if;
end $$;
-- idempotent ingest: the same event_id for the same tenant lands once; another tenant may reuse it; bad ids are refused
set role service_role;
do $$ declare c int; begin
  insert into public.usage_event (tenant_id, ts, provider, model, event_id) values ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x', 'evt-0001-retry');
  insert into public.usage_event (tenant_id, ts, provider, model, event_id) values ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x', 'evt-0001-retry')
    on conflict (tenant_id, event_id) do nothing;
  select count(*) into c from public.usage_event where event_id = 'evt-0001-retry'; assert c = 1, 'retried event stored ' || c || ' times';
  insert into public.usage_event (tenant_id, ts, provider, model, event_id) values ('10000000-0000-0000-0000-00000000000b', now(), 'openai', 'gpt-x', 'evt-0001-retry');
  begin insert into public.usage_event (tenant_id, ts, provider, model, event_id) values ('10000000-0000-0000-0000-00000000000a', now(), 'openai', 'gpt-x', 'x y');
        raise exception 'malformed event_id accepted';
  exception when check_violation then null; end;
end $$;
-- audit log: key creation and revocation are recorded (never the hash); a revoked key cannot come back; the log is append-only
do $$ declare k bigint; c int; begin
  insert into public.api_key (tenant_id, key_hash, label) values ('10000000-0000-0000-0000-00000000000a', repeat('d', 64), 'audit test') returning id into k;
  update public.api_key set revoked_at = now() where id = k;
  select count(*) into c from public.audit_log where table_name = 'api_key' and row_ref = k::text; assert c = 2, 'audit rows for key: ' || c;
  assert not exists (select 1 from public.audit_log where changes::text like '%dddddddd%'), 'key hash copied into the audit log';
  assert exists (select 1 from public.audit_log where row_ref = k::text and action = 'UPDATE' and changes ? 'revoked_at'), 'revocation not audited';
  begin update public.api_key set revoked_at = null where id = k; raise exception 'revoked key restored';
  exception when insufficient_privilege then null; end;
  begin delete from public.audit_log; raise exception 'audit log deleted';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
-- owners read their own tenant's audit trail; viewers and other tenants see nothing
set role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
do $$ declare c int; begin
  select count(*) into c from public.audit_log; assert c >= 2, 'owner sees ' || c || ' audit rows';
  assert not exists (select 1 from public.audit_log where tenant_id <> '10000000-0000-0000-0000-00000000000a'), 'owner sees another tenant''s audit';
  begin perform public.purge_raw(0); raise exception 'member purged raw usage';
  exception when insufficient_privilege then null; end;
end $$;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a2', false);
do $$ declare c int; begin select count(*) into c from public.audit_log; assert c = 0, 'viewer sees audit rows'; end $$;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000b', false);
do $$ declare c int; begin
  select count(*) into c from public.audit_log where tenant_id = '10000000-0000-0000-0000-00000000000a'; assert c = 0, 'B sees A''s audit';
end $$;
reset role;

select 'ALL LEDGER PEAKS SCHEMA TESTS PASSED';
