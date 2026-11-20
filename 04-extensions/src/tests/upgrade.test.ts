// A231: version 1 → 2 upgrade must keep every saved session (users update in place)
import "fake-indexeddb/auto";
import { openDB } from "idb";
import { expect, it } from "vitest";

it("upgrading the database to v2 keeps v1 sessions and adds Recently deleted", async () => {
  const v1 = await openDB("tab-lifeboat", 1, { upgrade(d) { const s = d.createObjectStore("sessions", { keyPath: "id" }); s.createIndex("createdAt", "createdAt"); s.createIndex("kind", "kind"); } });
  await v1.put("sessions", { id: "old", name: "From v1 🚀", kind: "manual", createdAt: 5, windows: [] }); v1.close();
  const { listSessions, trashSession, listTrash } = await import("../lib/store");
  expect((await listSessions()).map((s) => s.name)).toEqual(["From v1 🚀"]);
  expect(await trashSession("old", 10)).toBe(true);
  expect((await listTrash(10)).map((s) => s.id)).toEqual(["old"]);
});
