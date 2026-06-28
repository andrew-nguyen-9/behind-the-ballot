import statesJson from "../data/gerrymander/states.json";
import districtsJson from "../data/gerrymander/districts.json";

// Gerrymander metrics, computed offline (GeoPandas/Shapely) from TIGER geometry [L6a].
// Multi-metric, presented WITH caveats and no single verdict [L8a].
export interface StateFairness {
  state: string;
  efficiency_gap: number;
  mean_median: number;
  dem_seat_share: number;
  dem_vote_share: number;
}
export interface DistrictCompactness {
  geoid: string;
  state: string;
  district: number;
  polsby_popper: number;
  reock: number;
  convex_hull_ratio: number;
}

export const stateFairness = () =>
  [...(statesJson as StateFairness[])].sort((a, b) => a.state.localeCompare(b.state));

export const districtCompactness = () => districtsJson as DistrictCompactness[];

// Efficiency gap sign convention [L3a]: positive favors REP (Dems waste more).
export function efficiencyGapLabel(eg: number): string {
  const pts = Math.abs(eg) * 100;
  if (pts < 1) return "balanced";
  return `${pts.toFixed(1)} pts toward ${eg > 0 ? "Republicans" : "Democrats"}`;
}

// Leaderboard by Polsby-Popper (1 = perfectly compact). asc=least compact first.
export function byCompactness(asc = false): DistrictCompactness[] {
  return [...districtCompactness()].sort((a, b) =>
    asc ? a.polsby_popper - b.polsby_popper : b.polsby_popper - a.polsby_popper,
  );
}
