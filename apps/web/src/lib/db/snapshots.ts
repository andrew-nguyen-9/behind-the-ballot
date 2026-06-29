/**
 * Snapshot store [v1.8.7] — append-only forecast-run history → trend sparklines.
 * `db` is injected (prod: getDb(); tests: a pglite-backed drizzle), so the logic is
 * verifiable without a live Neon. Hot pages read baked JSON; this runs from the cron writer.
 */
import { desc, eq } from "drizzle-orm";
import { forecastSnapshots } from "./schema";

// Structural type: any drizzle db bound to our schema. Avoids leaking the concrete driver type.
type Store = {
  insert: (t: typeof forecastSnapshots) => { values: (v: NewSnapshot) => Promise<unknown> };
  select: () => {
    from: (t: typeof forecastSnapshots) => {
      where: (c: unknown) => {
        orderBy: (c: unknown) => { limit: (n: number) => Promise<Snapshot[]> };
      };
    };
  };
};

export type NewSnapshot = { cycle: number; unitId: string; payload: unknown };
export type Snapshot = NewSnapshot & { id: number; capturedAt: Date };

export function writeSnapshot(db: Store, s: NewSnapshot): Promise<unknown> {
  return db.insert(forecastSnapshots).values(s);
}

/** Most-recent-first history for one unit (race id or chamber), capped for sparkline use. */
export function recentSnapshots(db: Store, unitId: string, limit = 30): Promise<Snapshot[]> {
  return db
    .select()
    .from(forecastSnapshots)
    .where(eq(forecastSnapshots.unitId, unitId))
    .orderBy(desc(forecastSnapshots.capturedAt))
    .limit(limit);
}
