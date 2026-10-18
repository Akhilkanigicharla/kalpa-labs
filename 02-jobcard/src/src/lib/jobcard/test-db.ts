// Node's built-in SQLite behind the same 4 methods as expo-sqlite, so tests run real SQL (tests only).
import type { LocalDb, SQLParam } from './db';

export function memoryDb(): LocalDb {
  const { DatabaseSync } = require('node:sqlite');
  const d = new DatabaseSync(':memory:');
  return {
    execAsync: async (sql: string) => { d.exec(sql); },
    runAsync: async (sql: string, ...p: SQLParam[]) => { const r = d.prepare(sql).run(...p); return { lastInsertRowId: Number(r.lastInsertRowid), changes: Number(r.changes) }; },
    getAllAsync: async <T>(sql: string, ...p: SQLParam[]) => d.prepare(sql).all(...p) as T[],
    getFirstAsync: async <T>(sql: string, ...p: SQLParam[]) => (d.prepare(sql).get(...p) ?? null) as T | null,
  };
}
