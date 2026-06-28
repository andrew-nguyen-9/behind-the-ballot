import { z } from "zod";

// Config-driven unit contract [F4c,S2a]: a race/state/module = one config file the
// build loop fills, no code fork. Config files are JSON so both TS (zod, here) and the
// Python pipeline (pydantic, later) read the same source of truth [R7a].
//
// ponytail: only `race` is fleshed out now — it's the first unit the loop grinds
// (tracker, phase 2). `state` and `module` kinds get added when their phases need them;
// the discriminated union below makes that a one-variant addition.

export const UspsState = z
  .string()
  .regex(/^[A-Z]{2}$/, "USPS 2-letter state code, uppercase");

// Party as a small known set + passthrough for minor parties. Color/CVD encoding lives
// in the design system [C5a], not here — config stores identity only.
export const Party = z.enum(["D", "R", "I", "L", "G", "other"]);

export const Office = z.enum(["senate", "house", "governor"]);

export const Candidate = z.object({
  id: z.string().min(1), // stable slug, e.g. "jane-doe"
  name: z.string().min(1),
  party: Party,
  incumbent: z.boolean().default(false),
  fecCandidateId: z.string().optional(), // links to finance [G12a]
  bioguideId: z.string().optional(), // links to member analytics [M1a]
});

// Which data modules feed this unit — every published figure must trace to a
// DATA_SOURCES row [R14a]; this declares the bindings the integrity check verifies.
export const SourceBinding = z.enum([
  "fec",
  "polling",
  "forecast",
  "demographics",
  "members",
]);

const baseUnit = z.object({
  id: z.string().min(1), // globally unique, e.g. "us-senate-2026-OH"
  cycle: z.number().int().gte(2024),
  title: z.string().min(1),
  sources: z.array(SourceBinding).default([]),
});

// Plain object (no refinement) so it can be a discriminatedUnion member. Cross-field
// rules live on UnitConfig below — z.discriminatedUnion rejects ZodEffects.
export const RaceConfig = baseUnit.extend({
  kind: z.literal("race"),
  office: Office,
  state: UspsState,
  district: z.number().int().positive().nullable().default(null), // house only
  senateClass: z.union([z.literal(1), z.literal(2), z.literal(3)]).nullable().default(null),
  status: z.enum(["upcoming", "primary", "general", "called"]).default("upcoming"),
  candidates: z.array(Candidate).default([]),
});

// Open for `state` / `module` kinds — add as union members when those phases land.
// Cross-field validation applied here (after the discriminated parse).
export const UnitConfig = z
  .discriminatedUnion("kind", [RaceConfig])
  .superRefine((u, ctx) => {
    if (u.kind !== "race") return;
    if (u.office === "house" && u.district === null)
      ctx.addIssue({ code: "custom", message: "house race needs a district", path: ["district"] });
    if (u.office !== "house" && u.district !== null)
      ctx.addIssue({ code: "custom", message: "only house races have a district", path: ["district"] });
    if (u.office === "senate" && u.senateClass === null)
      ctx.addIssue({ code: "custom", message: "senate race needs a class", path: ["senateClass"] });
  });

export type RaceConfig = z.infer<typeof RaceConfig>;
export type UnitConfig = z.infer<typeof UnitConfig>;

/** Parse + validate a unit config (throws ZodError on invalid). */
export function parseUnit(data: unknown): UnitConfig {
  return UnitConfig.parse(data);
}
