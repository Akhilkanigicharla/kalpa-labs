#!/usr/bin/env bash
# Applies schema.sql to a throwaway database on a local Postgres 16 and runs the RLS tests.
# Usage: bash 02-jobcard/supabase/test.sh   (needs psql + a local server; PSQL can override the command)
set -euo pipefail
cd "$(dirname "$0")"
export PGOPTIONS="-c client_min_messages=warning"
PSQL=${PSQL:-"psql -X -q -v ON_ERROR_STOP=1"}
DB=jobcard_test_$$
$PSQL -d postgres -c "create database $DB" >/dev/null
trap '$PSQL -d postgres -c "drop database if exists $DB" >/dev/null' EXIT
$PSQL -d $DB -f test-stub.sql >/dev/null
$PSQL -d $DB -f schema.sql >/dev/null
$PSQL -d $DB -f schema.sql >/dev/null   # idempotent: a second apply must not fail
$PSQL -d $DB -tA -f test.sql | tail -1
