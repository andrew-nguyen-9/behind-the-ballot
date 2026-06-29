/** v1.8.7 snapshot store, verified against an in-process pglite Postgres (no live Neon). */
import { describe, it, expect, beforeEach } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { PGlite } from "@electric-sql/pglite";
import { drizzle } from "drizzle-orm/pglite";
import { forecastSnapshots } from "./schema";
import { writeSnapshot, recentSnapshots, type Snapshot } from "./snapshots";

const migDir = fileURLToPath(new URL("../../../drizzle", import.meta.url));

async function freshDb() {
  const pg = new PGlite();
  // Apply the generated migration — same SQL deploy runs, so the test tracks the real schema.
  const sql = readdirSync(migDir)
    .filter((f) => f.endsWith(".sql"))
    .sort()
    .map((f) => readFileSync(`${migDir}/${f}`, "utf8"))
    .join("\n");
  for (const stmt of sql.split("--> statement-breakpoint")) {
    if (stmt.trim()) await pg.exec(stmt);
  }
  return drizzle(pg);
}

describe("snapshot store", () => {
  let db: Awaited<ReturnType<typeof freshDb>>;
  beforeEach(async () => {
    db = await freshDb();
  });

  it("writes and reads back, filtered by unit", async () => {
    await writeSnapshot(db as never, { cycle: 2026, unitId: "OH-Sen", payload: { p: 0.6 } });
    await writeSnapshot(db as never, { cycle: 2026, unitId: "senate", payload: { ctrl: 0.5 } });
    const oh = await recentSnapshots(db as never, "OH-Sen");
    expect(oh).toHaveLength(1);
    expect((oh[0] as Snapshot).payload).toEqual({ p: 0.6 });
  });

  it("returns most-recent first, capped by limit", async () => {
    const t = (h: number) => new Date(Date.UTC(2026, 0, 1, h));
    await db.insert(forecastSnapshots).values([
      { cycle: 2026, unitId: "senate", capturedAt: t(1), payload: { n: "old" } },
      { cycle: 2026, unitId: "senate", capturedAt: t(3), payload: { n: "new" } },
      { cycle: 2026, unitId: "senate", capturedAt: t(2), payload: { n: "mid" } },
    ]);
    const rows = await recentSnapshots(db as never, "senate", 2);
    expect(rows.map((r) => (r.payload as { n: string }).n)).toEqual(["new", "mid"]);
  });
});
