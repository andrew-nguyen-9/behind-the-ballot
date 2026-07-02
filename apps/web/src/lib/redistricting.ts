import dataset from "../data/redistricting/states.json";
import { STATE_CODES, STATE_NAMES, type StateFill } from "./usStates";

// Curated 2026 redistricting tracker [E2.5, Q7.6]. The per-state map STATUS + active court
// cases are editorial, sourced to the redistricting trackers (see lib/sources "Redistricting
// status" row) and carry a dataset-level `as_of` for the integrity contract [R14a,R5a].
// Partisan-FAIRNESS numbers are deliberately NOT joined here — that live-join stays deferred;
// the page shows an honest pending-state instead of fabricated figures (Q7.6 ⭐a).

export type RedistrictingStatus = "settled" | "litigation" | "redrawn" | "at-large";

export interface CourtCase {
  name: string; // case caption or short descriptor
  court: string; // deciding court / venue
  issue: string; // one-line description of the dispute
  status: string; // procedural status, e.g. "pending", "decided; remedial map in use"
}

export interface RedistrictingState {
  state: string; // USPS postal code
  status: RedistrictingStatus;
  summary: string; // one-line, human-readable status summary
  cases: CourtCase[];
}

export interface RedistrictingDataset {
  as_of: string; // ISO date of the curated snapshot (freshness stamp)
  source: string; // key into the DATA_SOURCES contract
  note: string;
  states: RedistrictingState[];
}

export const REDISTRICTING = dataset as RedistrictingDataset;

// The source key every row traces to [R14a] — mirrors the lib/sources "Redistricting status"
// row and the DATA_SOURCES.md contract. Exposed so a test can assert the binding.
export const REDISTRICTING_SOURCE = "redistricting";

// Status presentation: reader-facing label, a short blurb, and the map paint. Fills are
// theme-constant literals (like the E1.1 caucus tints) so they read the same in light/dark;
// two statuses carry an E0.4 texture overlay for grayscale legibility (the two greys separate
// by lightness + the text equivalent). Order = most-active first for legend + summary.
export const STATUS_META: Record<
  RedistrictingStatus,
  { label: string; blurb: string; fill: string; overlay?: string }
> = {
  redrawn: {
    label: "Redrawn mid-decade",
    blurb: "New congressional lines enacted or court-ordered for this decade.",
    fill: "#7c6cae",
    overlay: "url(#pf-hatch)",
  },
  litigation: {
    label: "Active litigation",
    blurb: "A pending court case could still change the 2026 map.",
    fill: "#e0a458",
    overlay: "url(#pf-dots)",
  },
  settled: {
    label: "Map settled for 2026",
    blurb: "Post-2020 map in place with no active mid-decade change.",
    fill: "#9aa5ad",
  },
  "at-large": {
    label: "Single at-large district",
    blurb: "One statewide U.S. House seat — nothing to redistrict.",
    fill: "#cfd6db",
  },
};

export const STATUS_ORDER: RedistrictingStatus[] = [
  "redrawn",
  "litigation",
  "settled",
  "at-large",
];

// Curated records keyed by postal code. States absent from the dataset default to "settled".
function byCode(): Map<string, RedistrictingState> {
  return new Map(REDISTRICTING.states.map((s) => [s.state, s]));
}

// The resolved status of every one of the 50 states (dataset override, else "settled"),
// sorted by state name — the authoritative per-state list behind the map + text table.
export function redistrictingStates(): (RedistrictingState & { name: string })[] {
  const map = byCode();
  return STATE_CODES.map((code) => {
    const rec = map.get(code);
    const name = STATE_NAMES[code];
    return {
      name,
      state: code,
      status: rec?.status ?? "settled",
      summary: rec?.summary ?? STATUS_META.settled.blurb,
      cases: rec?.cases ?? [],
    };
  }).sort((a, b) => a.name.localeCompare(b.name));
}

// Count of states in each status bucket (for the legend + summary tiles).
export function statusCounts(): Record<RedistrictingStatus, number> {
  const counts: Record<RedistrictingStatus, number> = {
    redrawn: 0,
    litigation: 0,
    settled: 0,
    "at-large": 0,
  };
  for (const s of redistrictingStates()) counts[s.status] += 1;
  return counts;
}

// Per-state fills for <USStateMap>: status colour + optional grayscale texture + a <title>
// naming the state, its status, and any active-case count. Every code is filled (no empties).
export function redistrictingMapData(): { fills: Record<string, StateFill> } {
  const fills: Record<string, StateFill> = {};
  for (const s of redistrictingStates()) {
    const meta = STATUS_META[s.status];
    const caseNote =
      s.cases.length > 0
        ? ` (${s.cases.length} active case${s.cases.length > 1 ? "s" : ""})`
        : "";
    fills[s.state] = {
      fill: meta.fill,
      overlay: meta.overlay,
      title: `${s.name}: ${meta.label}${caseNote}`,
    };
  }
  return { fills };
}

// Every active court case, flattened + state-tagged, ordered by state name. Drives the
// case table; states with no case are omitted.
export function activeCases(): (CourtCase & { state: string })[] {
  const out: (CourtCase & { state: string })[] = [];
  for (const s of redistrictingStates()) {
    for (const c of s.cases) {
      out.push({ ...c, state: s.name });
    }
  }
  return out;
}

// States with an active redraw or litigation (i.e. not settled / at-large), for the
// detail table. Ordered most-active first, then by name.
export function activeStates(): (RedistrictingState & { name: string })[] {
  const rank = (st: RedistrictingStatus) => STATUS_ORDER.indexOf(st);
  return redistrictingStates()
    .filter((s) => s.status === "redrawn" || s.status === "litigation")
    .sort((a, b) => rank(a.status) - rank(b.status) || a.name.localeCompare(b.name));
}
