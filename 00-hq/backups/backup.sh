#!/usr/bin/env bash
# A310 · Encrypted backup of one Supabase database (public schema) we control ourselves.
# Writes ONE file: <out>.tar.age = age-encrypted tar of
#   dump.pgc     pg_dump custom format of schema "public" (grants kept, owners dropped)
#   auth_ids.csv only the ids of auth.users (no emails/phones), so foreign keys restore
#   counts.tsv   exact row count per public table, taken in the SAME snapshot as the dump
#   acls.tsv     who may do what on each public table (grantor dropped), so a restore that opens tables up is caught
# Usage: DB_URL=... AGE_RECIPIENT=age1... bash backup.sh <out-path-without-extension>
# Env: PG_DUMP (default pg_dump) lets CI use a newer client in Docker. Never prints DB_URL.
set -euo pipefail
OUT=${1:?usage: backup.sh <out-path-without-extension>}
: "${DB_URL:?DB_URL not set}"; : "${AGE_RECIPIENT:?AGE_RECIPIENT not set}"
[[ $AGE_RECIPIENT == age1* ]] || { echo "AGE_RECIPIENT must be an age public key (age1...)"; exit 2; }
PG_DUMP=${PG_DUMP:-pg_dump}
export PGCONNECT_TIMEOUT=${PGCONNECT_TIMEOUT:-20}
WORK=$(mktemp -d); trap 'rm -rf "$WORK"; [[ -n ${PSQ_PID:-} ]] && kill "$PSQ_PID" 2>/dev/null || true' EXIT
chmod 700 "$WORK"

# Sorted grants of a table other than its owner's, without the grantor part ("role=arw"): comparable across servers.
ACL="coalesce((select string_agg(split_part(a::text, '/', 1), ' ' order by a::text) from unnest(coalesce(c.relacl, acldefault('r', c.relowner))) a
  where split_part(a::text, '=', 1) <> pg_get_userbyid(c.relowner)), 'none')"
# One read-only repeatable-read transaction holds the snapshot; counts and pg_dump both read it.
coproc PSQ { psql -X -q -A -t -v ON_ERROR_STOP=1 "$DB_URL" 2>&1; }
# q runs one statement in that session; its one-line answer lands in $R (no $(...): coproc fds don't reach subshells).
q() { echo "$1" >&"${PSQ[1]}" 2>/dev/null && IFS= read -r -t 120 R <&"${PSQ[0]}" || { echo "database did not answer"; exit 3; }; }
q "set statement_timeout = '10min'; select 'ok';"
[[ $R == ok ]] || { echo "could not connect to the database"; exit 3; }
q "begin isolation level repeatable read read only; select pg_export_snapshot();"; SNAP=$R
[[ $SNAP =~ ^[0-9A-F-]+$ ]] || { echo "could not open a snapshot (use a session-mode connection, not a transaction pooler)"; exit 3; }
q "select coalesce(string_agg(format('%s=%s', c.relname,
  (xpath('/row/n/text()', query_to_xml(format('select count(*) as n from public.%I', c.relname), false, true, '')))[1]::text), '|' order by c.relname), '')
  from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relkind in ('r','p');"
tr '|' '\n' <<<"$R" | tr '=' '\t' | sed '/^$/d' > "$WORK/counts.tsv"
q "select coalesce(string_agg(format('%s=%s', c.relname, $ACL), '|' order by c.relname), '') from pg_class c
  join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relkind in ('r','p');"
tr '|' '\n' <<<"$R" | sed 's/=/\t/; /^$/d' > "$WORK/acls.tsv"
q "select coalesce(string_agg(id::text, ','), '') from auth.users;"; tr ',' '\n' <<<"$R" | sed '/^$/d' > "$WORK/auth_ids.csv"

$PG_DUMP --format=custom --schema=public --no-owner --snapshot="$SNAP" --dbname="$DB_URL" > "$WORK/dump.pgc"
q "commit; select 'done';"
[[ -s $WORK/dump.pgc ]] || { echo "empty dump"; exit 4; }

tar -C "$WORK" -cf - dump.pgc auth_ids.csv counts.tsv acls.tsv | age -r "$AGE_RECIPIENT" -o "$OUT.tar.age"
echo "backup ok: $(wc -l < "$WORK/counts.tsv") tables, $(awk -F'\t' '{s+=$2} END {print s+0}' "$WORK/counts.tsv") rows, $(wc -c < "$OUT.tar.age") bytes encrypted"
