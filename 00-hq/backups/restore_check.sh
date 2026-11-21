#!/usr/bin/env bash
# A310 · Proves a backup made by backup.sh can be brought back. Runs against a THROWAWAY Postgres only.
#  1. decrypt + unpack;  2. full restore on the world's Supabase stub -> every table's row count must equal counts.tsv;
#  3. schema-only restore -> the world's own supabase/test.sql must pass (it inserts its own test rows).
# Usage: AGE_KEY_FILE=key.txt bash restore_check.sh <file.tar.age> <world supabase dir>
# Env: PG_RESTORE (default pg_restore), PSQL; libpq vars (PGHOST, PGUSER...) point at the throwaway server.
set -euo pipefail
BUNDLE=${1:?usage: restore_check.sh <file.tar.age> <supabase dir>}; SB=${2:?supabase dir}
: "${AGE_KEY_FILE:?AGE_KEY_FILE not set}"
PG_RESTORE=${PG_RESTORE:-pg_restore}
PSQL=${PSQL:-"psql -X -q -v ON_ERROR_STOP=1"}
export PGOPTIONS="-c client_min_messages=warning"
# Supabase's own roles that grants in a real dump may name (created empty in the throwaway db).
SUPA_ROLES=${SUPA_ROLES:-"postgres','supabase_admin','authenticator','pgbouncer','supabase_auth_admin','supabase_storage_admin','dashboard_user','supabase_realtime_admin','supabase_read_only_user"}
WORK=$(mktemp -d); A=restore_full_$$; B=restore_schema_$$
cleanup() { rm -rf "$WORK"; for d in $A $B; do $PSQL -d postgres -c "drop database if exists $d" >/dev/null 2>&1 || true; done; }
trap cleanup EXIT
age -d -i "$AGE_KEY_FILE" "$BUNDLE" | tar -C "$WORK" -xf - dump.pgc auth_ids.csv counts.tsv acls.tsv

prep() {  # fresh db with the Supabase stand-in (roles, auth.uid, vault) + the auth ids the rows point at
  $PSQL -d postgres -c "create database $1" >/dev/null
  $PSQL -d "$1" -f "$SB/test-stub.sql" >/dev/null
  $PSQL -d "$1" -c "do \$\$ declare r text; begin foreach r in array array['$SUPA_ROLES'] loop
    if not exists (select 1 from pg_roles where rolname = r) then execute format('create role %I nologin', r); end if; end loop; end \$\$" >/dev/null
  # Supabase (and the stub) grant anon/authenticated ALL on every new table by default. The dump only re-adds its own grants,
  # so without this revoke a restore would leave every table open to anon (found 21 Nov 2026). Same step in a real restore.
  $PSQL -d "$1" -c "alter default privileges in schema public revoke all on tables from anon, authenticated, service_role;
    alter default privileges in schema public revoke all on sequences from anon, authenticated, service_role;
    alter default privileges in schema public revoke all on functions from anon, authenticated, service_role, public" >/dev/null
  $PSQL -d "$1" -c "create schema if not exists $EXT_SCHEMA; create extension if not exists pgcrypto with schema $EXT_SCHEMA" >/dev/null
  [[ ${2:-} == no-ids ]] || $PSQL -d "$1" -c "\copy auth.users (id) from '$WORK/auth_ids.csv'" >/dev/null
}
# Supabase keeps pgcrypto in schema "extensions"; a plain Postgres keeps it in public. Follow what the dump calls.
EXT_SCHEMA=public; $PG_RESTORE -f - --schema-only "$WORK/dump.pgc" | grep -q 'extensions\.gen_random' && EXT_SCHEMA=extensions
# Restore list without the dump's own "CREATE SCHEMA public" (the throwaway db already has it, with pgcrypto inside).
$PG_RESTORE -l "$WORK/dump.pgc" | grep -vE '^[0-9]+; [0-9]+ [0-9]+ (SCHEMA|COMMENT) - (SCHEMA )?public ' > "$WORK/list"
prep $A
$PG_RESTORE --exit-on-error --no-owner -L "$WORK/list" --dbname=$A "$WORK/dump.pgc"
bad=0; n=0
while IFS=$'\t' read -r t want; do
  got=$($PSQL -d $A -tA -c "select count(*) from public.\"$t\"")
  n=$((n+1)); [[ $got == "$want" ]] || { echo "row count differs: $t backup=$want restored=$got"; bad=1; }
done < "$WORK/counts.tsv"
ACL="coalesce((select string_agg(split_part(a::text, '/', 1), ' ' order by a::text) from unnest(coalesce(c.relacl, acldefault('r', c.relowner))) a
  where split_part(a::text, '=', 1) <> pg_get_userbyid(c.relowner)), 'none')"
while IFS=$'\t' read -r t want; do
  got=$($PSQL -d $A -tA -c "select $ACL from pg_class c where c.oid = 'public.\"$t\"'::regclass")
  [[ $got == "$want" ]] || { echo "grants differ: $t backup=[$want] restored=[$got]"; bad=1; }
done < "$WORK/acls.tsv"
[[ $bad == 0 ]] || exit 5
echo "full restore ok: $n tables, row counts and grants match"

prep $B no-ids   # test.sql adds its own auth users
$PG_RESTORE --exit-on-error --no-owner --schema-only -L "$WORK/list" --dbname=$B "$WORK/dump.pgc"
$PSQL -d $B -tA -f "$SB/test.sql" | tail -1
echo "RESTORE CHECK PASSED"
