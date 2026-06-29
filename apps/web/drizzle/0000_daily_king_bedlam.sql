CREATE TABLE "forecast_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle" integer NOT NULL,
	"unit_id" text NOT NULL,
	"captured_at" timestamp with time zone DEFAULT now() NOT NULL,
	"payload" jsonb NOT NULL
);
--> statement-breakpoint
CREATE INDEX "snap_unit_time" ON "forecast_snapshots" USING btree ("unit_id","captured_at");--> statement-breakpoint
CREATE INDEX "snap_cycle" ON "forecast_snapshots" USING btree ("cycle");