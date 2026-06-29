import { defineConfig } from "drizzle-kit";

// Migrations are generated from the schema (no DB connection needed for `generate`).
// `push`/`migrate` use DATABASE_URL at deploy time.
export default defineConfig({
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  // Only used by push/migrate (not generate). Empty string keeps `generate` working with no env.
  dbCredentials: { url: process.env.DATABASE_URL ?? "" },
});
