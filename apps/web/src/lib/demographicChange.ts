// Demographic-change data [E2.4]. Two layers, both from Census ACS via the pipeline:
//   1. Snapshot  — the latest per-state + per-CD ACS figures (committed, real).
//   2. Change    — population/income deltas between two ACS end-years (present only once a
//                  multi-year bake lands via `acs.run_years`; absent => the page shows an
//                  honest empty state, never placeholder numbers).
import { fmtIncome, fmtPop } from "./demographics";

export { fmtIncome, fmtPop };

// --- Snapshot (always committed) -------------------------------------------------------
import stateSnapshot from "../data/demographics/states.json";
import districtSnapshot from "../data/demographics/districts.json";

export interface SnapshotRow {
  state: string | null;
  area?: string;
  geoid?: string;
  district?: string | null;
  name?: string | null;
  population: number | null;
  median_income: number | null;
}
export interface SnapshotTable {
  acs_release: string;
  geometry_as_of: string;
  rows: SnapshotRow[];
}

export const stateSnapshotTable = stateSnapshot as SnapshotTable;
export const districtSnapshotTable = districtSnapshot as SnapshotTable;

/** National totals from the state snapshot: summed population, population-weighted median income. */
export function nationalTotals(rows: SnapshotRow[] = stateSnapshotTable.rows) {
  let population = 0;
  let incWeighted = 0;
  let incPop = 0;
  for (const r of rows) {
    const p = r.population ?? 0;
    population += p;
    if (r.median_income != null && p) {
      incWeighted += r.median_income * p;
      incPop += p;
    }
  }
  return {
    population,
    median_income: incPop ? Math.round(incWeighted / incPop) : null,
  };
}

// --- Change (present only after a >=2-endpoint bake) ------------------------------------
const changeStates = import.meta.glob("../data/demographics-change/states.json", { eager: true });
const changeDistricts = import.meta.glob("../data/demographics-change/districts.json", { eager: true });
const changeMeta = import.meta.glob("../data/demographics-change/meta.json", { eager: true });

export interface ChangeRow {
  state: string | null;
  area?: string;
  geoid?: string;
  district?: string | null;
  name?: string | null;
  early_year: number;
  late_year: number;
  population_early: number | null;
  population_late: number | null;
  population_delta: number | null;
  population_pct: number | null;
  median_income_early: number | null;
  median_income_late: number | null;
  median_income_delta: number | null;
  median_income_pct: number | null;
}
export interface ChangeMeta {
  state_early_year: number;
  state_late_year: number;
  cd_early_year: number;
  cd_late_year: number;
  acs_release_state_early: string;
  acs_release_cd_early: string;
  acs_release_late: string;
  state_crosses_redistricting: boolean;
  geometry_as_of: string;
}

function load<T>(mods: Record<string, unknown>, path: string): T | null {
  const m = mods[path] as { default: T } | undefined;
  return m ? m.default : null;
}

export function stateChanges(): ChangeRow[] {
  return load<ChangeRow[]>(changeStates, "../data/demographics-change/states.json") ?? [];
}
export function districtChanges(): ChangeRow[] {
  return load<ChangeRow[]>(changeDistricts, "../data/demographics-change/districts.json") ?? [];
}
export function changeMetadata(): ChangeMeta | null {
  return load<ChangeMeta>(changeMeta, "../data/demographics-change/meta.json");
}
export function hasChangeData(): boolean {
  return changeMetadata() !== null && stateChanges().length > 0;
}

// --- Formatting ------------------------------------------------------------------------
/** Signed absolute delta, e.g. "+12,430" / "-3,001" / "0". */
export function fmtDelta(n: number | null): string {
  if (n == null) return "—";
  const s = n.toLocaleString("en-US");
  return n > 0 ? `+${s}` : s;
}
/** Signed percent, e.g. "+2.4%" / "-0.8%". */
export function fmtPct(n: number | null): string {
  if (n == null) return "—";
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}
/** Bar width (0–100) for a percent magnitude, scaled so `cap`% fills the bar. */
export function pctBarWidth(pct: number | null, cap = 10): number {
  if (pct == null) return 0;
  return Math.min(100, Math.round((Math.abs(pct) / cap) * 100));
}
