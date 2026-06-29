// Demographics artifacts (per race geography), pre-aggregated from Census ACS [I7a].
// Read at build. Sample fixtures until live ACS runs land.
const mods = import.meta.glob("../data/demographics/*.json", { eager: true });

export interface Demographics {
  area: string;
  population: number;
  median_income: number;
  urbanization: string | null; // null when not classified (ACS gold has no urban/rural split yet)
  acs_release: string;
  geometry_as_of: string;
}

export function demographicsForRace(raceId: string): Demographics | null {
  const m = mods[`../data/demographics/${raceId}.json`] as { default: Demographics } | undefined;
  return m ? m.default : null;
}

export const fmtPop = (n: number) => n.toLocaleString("en-US");
export const fmtIncome = (n: number) => `$${n.toLocaleString("en-US")}`;
