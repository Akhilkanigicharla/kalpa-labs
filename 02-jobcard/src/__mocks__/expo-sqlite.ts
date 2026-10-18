// The app's tests use Node's own SQLite through src/lib/jobcard/test-db.ts instead.
export const openDatabaseAsync = jest.fn(async () => { throw new Error('use memoryDb() in tests'); });
