/**
 * Neon HTTP client [ADR 0002, O8a]. Lazy: only built when a query runs, so SSG/build without
 * DATABASE_URL stays green (no DB on the hot path — pages read baked JSON). ponytail: throws on
 * a missing secret like the FEC connector — an explicit "secret absent" beats a silent nil client.
 */
import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import * as schema from "./schema";

export function getDb() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL not set — see docs/SETUP_SECRETS.md");
  return drizzle(neon(url), { schema });
}
