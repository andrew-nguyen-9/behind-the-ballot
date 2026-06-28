// Per-race forecast artifacts, baked by the forecast runner [N4a]. Read at build.
// Sample fixtures in src/data/forecast/<raceId>.json until live runs land. Forecast is
// DERIVED — provenance is polls + fundamentals [R14a], surfaced via the methodology link.
const mods = import.meta.glob("../data/forecast/*.json", { eager: true });

export interface RaceForecast {
  win_prob: number; // Dem win probability 0..1
  margin: number; // Dem two-party margin (signed fraction)
  margin_lo: number;
  margin_hi: number;
  as_of: string;
}

export function forecastForRace(raceId: string): RaceForecast | null {
  const m = mods[`../data/forecast/${raceId}.json`] as { default: RaceForecast } | undefined;
  return m ? m.default : null;
}

export interface ChamberForecast {
  chamber: string;
  as_of: string;
  n_sims: number;
  n_races: number;
  majority: number;
  expected_dem_seats: number;
  dem_seat_p10: number;
  dem_seat_p50: number;
  dem_seat_p90: number;
  dem_control_prob: number;
}

export function allChamberForecasts(): ChamberForecast[] {
  return Object.entries(mods)
    .filter(([k]) => k.includes("/chamber-"))
    .map(([, m]) => (m as { default: ChamberForecast }).default)
    .sort((a, b) => a.chamber.localeCompare(b.chamber));
}

// Signed Dem margin fraction -> "D+3.0" / "R+1.5" / "EVEN".
export function marginLabel(margin: number): string {
  const pts = Math.abs(margin) * 100;
  if (pts < 0.05) return "EVEN";
  return `${margin > 0 ? "D" : "R"}+${pts.toFixed(1)}`;
}
