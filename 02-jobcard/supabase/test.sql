-- RLS + numbering tests. Runs as the table owner first (setup), then as `authenticated` users A and B.
\set ON_ERROR_STOP on
insert into auth.users values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000b');
insert into public.technicians (id, name, phone) values
  ('00000000-0000-0000-0000-00000000000a', 'Ravi', '9000022222'),
  ('00000000-0000-0000-0000-00000000000b', 'Imran', '9000044444');

set role authenticated;
-- ---- technician A
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
insert into public.customers (name, phone) values ('Sita Devi', '9848012345');
insert into public.job_cards (customer_id, appliance, issues, parts)
  select id, 'split_ac', '{gas_leak}', '[{"desc":"Gas refill","rate":2500}]' from public.customers where phone = '9848012345';
do $$ declare n1 text; n2 text; n3 text; begin
  n1 := public.next_invoice_no('2026-10-13'); n2 := public.next_invoice_no('2027-03-31'); n3 := public.next_invoice_no('2027-04-01');
  assert n1 = 'JC/26-27/0001', n1; assert n2 = 'JC/26-27/0002', n2; assert n3 = 'JC/27-28/0001', n3;
  insert into public.invoices (number, fy, kind, lines, taxable_paise, payable_paise) values (n1, '26-27', 'unregistered', '[{"desc":"Gas refill"}]', 250000, 250000);
end $$;
-- unregistered invoices may not carry GST
do $$ begin
  begin insert into public.invoices (number, fy, kind, lines, taxable_paise, cgst_paise, payable_paise) values ('JC/26-27/0009', '26-27', 'unregistered', '[{}]', 100, 9, 109);
        raise exception 'GST on an unregistered bill was accepted';
  exception when check_violation then null; end;
  begin insert into public.invoices (number, fy, kind, lines, taxable_paise, payable_paise) values ('JC/26-27/0001', '26-27', 'unregistered', '[{}]', 1, 1);
        raise exception 'duplicate invoice number accepted';
  exception when unique_violation then null; end;
  begin insert into public.invoices (number, fy, kind, lines, taxable_paise, payable_paise) values ('JOBCARD/2026-27/1', '26-27', 'unregistered', '[{}]', 1, 1);
        raise exception '17-character number accepted';
  exception when check_violation then null; end;
end $$;

-- ---- audit fixes (REA, 16 Oct 2026): A cannot self-upgrade, invoices are permanent except "paid"
do $$ declare c int; begin
  begin update public.technicians set plan = 'pro'; raise exception 'self-upgrade to pro accepted';
  exception when insufficient_privilege then null; end;
  update public.technicians set business_name = 'Ravi Cooling'; get diagnostics c = row_count; assert c = 1, 'profile edit blocked';
  update public.invoices set paid = true; get diagnostics c = row_count; assert c = 1, 'marking paid blocked';
  begin update public.invoices set payable_paise = 1; raise exception 'invoice amount edited after issue';
  exception when insufficient_privilege then null; end;
  begin delete from public.invoices; raise exception 'invoice deleted';
  exception when insufficient_privilege then null; end;
end $$;

-- ---- technician B sees nothing of A's and cannot write into A's account
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000b', false);
do $$ declare c int; a_customer uuid; begin
  select count(*) into c from public.customers; assert c = 0, 'B can see A''s customers';
  select count(*) into c from public.job_cards; assert c = 0, 'B can see A''s job cards';
  select count(*) into c from public.invoices;  assert c = 0, 'B can see A''s invoices';
  select count(*) into c from public.technicians; assert c = 1, 'B sees other profiles';
  select count(*) into c from public.invoice_counters; assert c = 0, 'B sees A''s counters';
  assert public.next_invoice_no('2026-10-13') = 'JC/26-27/0001', 'B''s series is not separate';
  begin insert into public.customers (technician_id, name) values ('00000000-0000-0000-0000-00000000000a', 'spoof');
        raise exception 'B wrote a row into A''s account';
  exception when insufficient_privilege then null; end;
  update public.job_cards set status = 'cancelled'; get diagnostics c = row_count; assert c = 0, 'B updated A''s job card';
  begin delete from public.invoices; raise exception 'B deleted an invoice';
  exception when insufficient_privilege then null; end;   -- nobody can delete invoices (GST), so B can't either
  begin insert into public.invoice_counters values ('00000000-0000-0000-0000-00000000000b', '26-27', 100);
        raise exception 'B wrote its own counter directly';
  exception when insufficient_privilege then null; end;
end $$;
-- B cannot attach A's customer to B's job card (customer id guessed)
reset role;
create temp table a_cust as select id from public.customers where phone = '9848012345';
grant select on a_cust to authenticated;
set role authenticated;
do $$ begin
  begin insert into public.job_cards (customer_id, appliance) select id, 'ac' from a_cust;
        raise exception 'B linked A''s customer';
  exception when raise_exception then if sqlerrm like 'B linked%' then raise; end if; end;
end $$;

-- B cannot point an invoice at A's job card, nor an AMC at A's customer
reset role;
create temp table a_job as select id from public.job_cards limit 1;
grant select on a_job to authenticated;
set role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000b', false);
do $$ begin
  begin insert into public.invoices (job_card_id, number, fy, kind, lines, taxable_paise, payable_paise) select id, 'JC/26-27/0050', '26-27', 'unregistered', '[{}]', 1, 1 from a_job;
        raise exception 'B billed A''s job card';
  exception when raise_exception then if sqlerrm like 'B billed%' then raise; end if; end;
  begin insert into public.amc_contracts (customer_id, starts_on, ends_on, price_paise) select id, '2026-11-01', '2027-11-01', 100 from a_cust;
        raise exception 'B made an AMC for A''s customer';
  exception when raise_exception then if sqlerrm like 'B made%' then raise; end if; end;
  begin insert into public.technicians (id, name, phone, plan) values ('00000000-0000-0000-0000-00000000000c', 'X', '9000055555', 'pro');
        raise exception 'new profile created as pro';
  exception when insufficient_privilege then null; end;
end $$;

-- ---- no signed-in user: nothing visible, no numbers
select set_config('request.jwt.claim.sub', '', false);
do $$ declare c int; begin
  select count(*) into c from public.job_cards; assert c = 0;
  begin perform public.next_invoice_no(); raise exception 'anonymous got an invoice number';
  exception when raise_exception then if sqlerrm like 'anonymous%' then raise; end if; end;
end $$;
-- ---- bot-only tables and functions (A35): closed to the app, open to the server
set role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
do $$ begin
  begin perform public.next_invoice_no_for('00000000-0000-0000-0000-00000000000b'); raise exception 'app took another technician''s number';
  exception when insufficient_privilege then null; end;
  begin perform public.add_usage('00000000-0000-0000-0000-00000000000a', -999); raise exception 'app reset its own meter';
  exception when insufficient_privilege then null; end;
  begin perform count(*) from public.bot_sessions; raise exception 'app read bot sessions';
  exception when insufficient_privilege then null; end;
  begin insert into public.reminder_sends values ('00000000-0000-0000-0000-00000000000a', current_date, 5); raise exception 'app wrote reminder log';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
set role service_role;
do $$ declare n text; s int; begin
  n := public.next_invoice_no_for('00000000-0000-0000-0000-00000000000b', '2026-10-13');
  assert n like 'JC/26-27/%', n;
  s := public.add_usage('00000000-0000-0000-0000-00000000000b', 40);
  s := public.add_usage('00000000-0000-0000-0000-00000000000b', 50); assert s = 90, s::text;
  insert into public.wa_processed (id) values ('wamid.1');
  begin insert into public.wa_processed (id) values ('wamid.1'); raise exception 'duplicate message id accepted';
  exception when unique_violation then null; end;
end $$;
reset role;
select 'ALL JOBCARD SCHEMA TESTS PASSED' as result;
