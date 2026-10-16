#!/usr/bin/env bash
# Applies schema.sql (twice: it must be safe to re-run) to a throwaway database on a local Postgres 16 and runs test.sql,
# then fires 40 invoices at once to prove the series never repeats or skips.
# Usage: bash 01-botbhai/botbhai/supabase/test.sh   (needs psql + a running local server; PSQL can override the command)
set -euo pipefail
cd "$(dirname "$0")"
export PGOPTIONS="-c client_min_messages=warning"
PSQL=${PSQL:-"psql -X -q -v ON_ERROR_STOP=1"}
DB=botbhai_test_$$
$PSQL -d postgres -c "create database $DB" >/dev/null
trap '$PSQL -d postgres -c "drop database if exists $DB" >/dev/null' EXIT
$PSQL -d $DB -f test-stub.sql >/dev/null
$PSQL -d $DB -f schema.sql >/dev/null
$PSQL -d $DB -f schema.sql >/dev/null
$PSQL -d $DB -tA -f test.sql | tail -1
C=$($PSQL -d $DB -tA -c "insert into clients (name, niche) values ('Race Salon', 'salon') returning id")
for i in $(seq 1 40); do
  $PSQL -d $DB -tA -c "select number from create_invoice('$C', '2028-06-01', null, null, '{}', '[]', 100)" > "/tmp/bb_inv_$$_$i" &
done; wait
GOT=$(cat /tmp/bb_inv_$$_* | sort | tr '\n' ' '); rm -f /tmp/bb_inv_$$_*
WANT=$(for i in $(seq 1 40); do printf 'KL/28-29/%03d ' "$i"; done)
[ "$GOT" = "$WANT" ] || { echo "parallel numbering broken: $GOT"; exit 1; }
echo "40 parallel invoices: KL/28-29/001…040, no gaps or repeats"
echo "BOTBHAI SCHEMA TESTS PASSED"
