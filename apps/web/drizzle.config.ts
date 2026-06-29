import { defineConfig } from "drizzle-kit";

// Migrations are generated from the schema (no DB connection needed for `generate`).
// `push`/`migrate` use DATABASE_URL at deploy time.
export default defineConfig({
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
});
