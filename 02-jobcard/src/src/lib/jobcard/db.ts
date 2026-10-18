// Local database: the phone is the source of truth, so the app works on a terrace with no signal.
// Only the four expo-sqlite methods we need, so tests can run on Node's own SQLite.
import * as SQLite from 'expo-sqlite';

export type SQLParam = string | number | null;
export type LocalDb = {
  execAsync: (sql: string) => Promise<void>;
  runAsync: (sql: string, ...params: SQLParam[]) => Promise<{ lastInsertRowId: number; changes: number }>;
  getAllAsync: <T>(sql: string, ...params: SQLParam[]) => Promise<T[]>;
  getFirstAsync: <T>(sql: string, ...params: SQLParam[]) => Promise<T | null>;
};

export const SCHEMA_VERSION = 1;

export async function migrate(db: LocalDb): Promise<void> {
  await db.execAsync(`
    pragma journal_mode = wal;
    create table if not exists jobs (
      id          text primary key,           -- uuid made on the phone, same id on the server
      card        text not null,              -- the parsed job card (JSON)
      invoice_no  text,
      audio_uri   text,                       -- the saved voice note (expo-speech-recognition persist)
      created_at  integer not null
    );
    create table if not exists outbox (       -- writes waiting for signal, sent in order
      id          integer primary key autoincrement,
      kind        text not null check (kind in ('customer','job_card','invoice','voice')),
      row_id      text not null,
      payload     text not null,
      attempts    integer not null default 0,
      next_at     integer not null default 0,
      last_error  text,
      created_at  integer not null
    );
    create table if not exists counters (     -- offline invoice series per financial year
      fy          text primary key,
      last_seq    integer not null
    );
    pragma user_version = ${SCHEMA_VERSION};
  `);
}

export async function openLocalDb(): Promise<LocalDb> {
  const db = await SQLite.openDatabaseAsync('jobcard.db');
  await migrate(db as unknown as LocalDb);
  return db as unknown as LocalDb;
}
