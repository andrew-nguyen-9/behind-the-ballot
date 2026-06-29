/**
 * Neon Postgres schema [ADR 0002]. Postgres holds ONLY small queryable state; bulk/derived
 * data is baked JSON on the CDN + R2. For V1 the one writer is the snapshot store [v1.8.7],
 * so this is the one table. Add others (feed items, etc.) when a feature actually needs them.
 */
import { pgTable, serial, integer, text, timestamp, jsonb, index } from "drizzle-orm/pg-core";

/** Append-only forecast-run history → trend sparklines. Partitioned by `cycle` [ADR 0002, L843]. */
export const forecastSnapshots = pgTable(
  "forecast_snapshots",
  {
    id: serial("id").primaryKey(),
    cycle: integer("cycle").notNull(), // partition key (e.g. 2026)
    unitId: text("unit_id").notNull(), // race id ("OH-Sen") or chamber ("senate"/"house")
    capturedAt: timestamp("captured_at", { withTimezone: true }).notNull().defaultNow(),
    payload: jsonb("payload").notNull(), // forecast bundle: win prob, margin, 80% range, seats
  },
  (t) => [index("snap_unit_time").on(t.unitId, t.capturedAt), index("snap_cycle").on(t.cycle)],
);
