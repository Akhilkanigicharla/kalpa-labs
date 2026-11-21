# Backups we control (A310)

Nightly encrypted copy of the BotBhai and JobCard Supabase databases, kept by us in GitHub Actions, plus a monthly proof that the copy really comes back.

| File | Does |
|---|---|
| `backup.sh` | One read-only snapshot → `pg_dump` of schema `public` + exact row counts + table grants + auth user ids (ids only, no emails or phones) → one `age`-encrypted file. Never prints the connection string. |
| `restore_check.sh` | Decrypts into a throwaway Postgres: full restore must match every row count and every table's grants; a schema-only restore must pass the world's own `supabase/test.sql`. |
| `test.sh` | Local proof on made-up data (both worlds, emoji/Telugu/quote text, wrong key, tampered file, row-count lie, grant lie, missing secret, bad key, unreachable DB, password never printed). `bash 00-hq/backups/test.sh` |
| `.github/workflows/db-backup.yml` | 02:11 IST nightly backup (7-day artifact); 02:47 IST on the 1st: backup + restore check; self-test on every change. |

## Why it is encrypted
The repo is public, so its Actions artifacts can be downloaded by anyone with read access, which on a public repo means everyone. The file is useless without the private key, which lives only in Akhil's GitHub secret and his own safe place. `age` is BSD-3-Clause.

## Secrets Akhil adds (repo → Settings → Secrets and variables → Actions)
1. `BOTBHAI_DB_URL`, `JOBCARD_DB_URL`: Supabase dashboard → Connect → **Session pooler** string (port 5432, user `postgres.<project-ref>`). Not the direct one: that is IPv6 unless you buy the IPv4 add-on, and GitHub's runners are IPv4 (Supabase docs, fetched 21 Nov 2026 + Supabase KB "IPv4 and IPv6 compatibility"). Not the transaction pooler (6543): the snapshot needs one session.
2. `BACKUP_AGE_RECIPIENT` and `BACKUP_AGE_KEY`: a key pair made in a Codespace or Cloud Shell with `age-keygen` (public line `age1…` → recipient; the whole `AGE-SECRET-KEY-…` line → key). Keep a copy of the private key offline too: lose it and every backup is lost.
Until these exist the workflow skips with a yellow warning (no red runs).

## Real restore into a new Supabase project (disaster day)
1. Download the artifact, `age -d -i key.txt db-….tar.age | tar -x`.
2. In the new project's SQL editor, first run the revoke block from `restore_check.sh` (`alter default privileges … revoke all …`). **Supabase grants anon/authenticated everything on new tables by default; a plain `pg_restore` would leave every table open to anon.** The restore check proves the grants come back exactly (`acls.tsv`).
3. `pg_restore --no-owner --exit-on-error -d "<session pooler url>" dump.pgc` (skip the `SCHEMA public` line, as the script does with `-L`).
4. Auth users are not in this backup (only their ids, so rows keep their links). People sign in again with their phone or email.
