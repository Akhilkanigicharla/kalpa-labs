#!/usr/bin/env bash
# A310 tests on a local Postgres (no network, no real data): for BotBhai and JobCard, seed a source db from the world's
# own schema + tests, back it up, restore-check it, then prove the failure paths fail.
# Usage: bash 00-hq/backups/test.sh   (needs psql/pg_dump/pg_restore + a local server, and age)
set -euo pipefail
cd "$(dirname "$0")"; ROOT=$(cd ../.. && pwd)
export PGOPTIONS="-c client_min_messages=warning"
PSQL="psql -X -q -v ON_ERROR_STOP=1"
T=$(mktemp -d); SRC=bk_src_$$; pass=0
trap '$PSQL -d postgres -c "drop database if exists $SRC" >/dev/null 2>&1; rm -rf "$T"' EXIT
age-keygen -o "$T/key.txt" 2>/dev/null; REC=$(age-keygen -y "$T/key.txt")
age-keygen -o "$T/other.txt" 2>/dev/null
ok() { echo "  ok: $1"; pass=$((pass+1)); }
expect_fail() { local what=$1; shift; if "$@" >"$T/out" 2>&1; then echo "  FAIL: $what should have failed"; exit 1; fi; ok "$what"; }
URL="postgresql:///$SRC${PGHOST:+?host=$PGHOST}"

for world in botbhai jobcard; do
  SB=$ROOT/01-botbhai/botbhai/supabase; [[ $world == jobcard ]] && SB=$ROOT/02-jobcard/supabase
  echo "$world:"
  $PSQL -d postgres -c "drop database if exists $SRC" -c "create database $SRC" >/dev/null
  $PSQL -d $SRC -f "$SB/test-stub.sql" >/dev/null
  $PSQL -d $SRC -f "$SB/schema.sql" >/dev/null
  for f in "$SB"/migrations/*.sql; do [[ -e $f ]] && $PSQL -d $SRC -f "$f" >/dev/null; done
  $PSQL -d $SRC -f "$SB/test.sql" >/dev/null   # leaves real-looking rows behind (clients, invoices / job cards)
  if [[ $world == botbhai ]]; then   # worst-case text survives the round trip
    $PSQL -d $SRC -c "insert into clients (name, niche) values (E'Ravi''s 💇‍♀️ సెలూన్ \"; drop table x;--\\t', 'salon')" >/dev/null
  fi
  rows=$($PSQL -d $SRC -tA -c "select sum((xpath('/row/n/text()', query_to_xml(format('select count(*) as n from public.%I', relname), false, true, '')))[1]::text::int) from pg_stat_user_tables where schemaname='public'")
  [[ $rows -gt 0 ]] || { echo "  FAIL: seed left no rows"; exit 1; }

  DB_URL=$URL AGE_RECIPIENT=$REC bash backup.sh "$T/$world" | sed 's/^/  /'
  head -c 400 "$T/$world.tar.age" | grep -q "age-encryption.org" && ok "file is age-encrypted"
  ! grep -aq "Glow Studio\|Sita Devi" "$T/$world.tar.age" && ok "no plain customer text in the file"
  AGE_KEY_FILE=$T/key.txt bash restore_check.sh "$T/$world.tar.age" "$SB" | sed 's/^/  /'
  [[ ${PIPESTATUS[0]} == 0 ]] && ok "restore check passes ($rows source rows)"
  if [[ $world == botbhai ]]; then
    age -d -i "$T/key.txt" "$T/$world.tar.age" | tar -xOf - dump.pgc > "$T/d.pgc"
    pg_restore -f - --data-only -t clients "$T/d.pgc" | grep -q "సెలూన్" && ok "emoji + Telugu + quote text kept"
  fi
done

echo "failure paths:"
expect_fail "wrong key" env AGE_KEY_FILE=$T/other.txt bash restore_check.sh "$T/botbhai.tar.age" "$ROOT/01-botbhai/botbhai/supabase"
cp "$T/botbhai.tar.age" "$T/bad.tar.age"; printf 'X' | dd of="$T/bad.tar.age" bs=1 seek=300 conv=notrunc 2>/dev/null
expect_fail "tampered file" env AGE_KEY_FILE=$T/key.txt bash restore_check.sh "$T/bad.tar.age" "$ROOT/01-botbhai/botbhai/supabase"
mkdir "$T/x"; age -d -i "$T/key.txt" "$T/botbhai.tar.age" | tar -C "$T/x" -xf -
cp "$T/x/counts.tsv" "$T/x/counts.tsv.orig"; sed -i '1s/\t[0-9]*$/\t999999/' "$T/x/counts.tsv"; tar -C "$T/x" -cf - dump.pgc auth_ids.csv counts.tsv acls.tsv | age -r "$REC" -o "$T/lie.tar.age"
expect_fail "row count mismatch" env AGE_KEY_FILE=$T/key.txt bash restore_check.sh "$T/lie.tar.age" "$ROOT/01-botbhai/botbhai/supabase"
grep -q "row count differs" "$T/out" && ok "mismatch is named"
cp "$T/x/counts.tsv.orig" "$T/x/counts.tsv" 2>/dev/null || true
sed -i '1s/\t.*$/\tanon=arwdDxt/' "$T/x/acls.tsv"; tar -C "$T/x" -cf - dump.pgc auth_ids.csv counts.tsv acls.tsv | age -r "$REC" -o "$T/acl.tar.age"
expect_fail "grants mismatch" env AGE_KEY_FILE=$T/key.txt bash restore_check.sh "$T/acl.tar.age" "$ROOT/01-botbhai/botbhai/supabase"
grep -q "grants differ" "$T/out" && ok "grant mismatch is named"
expect_fail "no DB_URL" env -u DB_URL AGE_RECIPIENT=$REC bash backup.sh "$T/n"
expect_fail "bad recipient" env DB_URL=$URL AGE_RECIPIENT=hunter2 bash backup.sh "$T/n"
expect_fail "unreachable db" env DB_URL="postgresql://u:secretpw@127.0.0.1:1/x" PGCONNECT_TIMEOUT=2 AGE_RECIPIENT=$REC bash backup.sh "$T/n"
! grep -q secretpw "$T/out" && ok "password never printed on failure"
[[ ! -e $T/n.tar.age ]] && ok "no file left after a failed backup"
echo "BACKUP TESTS PASSED ($pass checks)"
