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
select 'schema checks passed';
