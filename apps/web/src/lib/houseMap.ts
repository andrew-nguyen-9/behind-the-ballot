import { allRaces } from "./races";
import { forecastForRace, marginLabel, type RaceForecast } from "./forecast";
import { districtShape, type DistrictShape } from "./geo";
import { STATE_NAMES, MAP_COLORS, type StateFill } from "./usStates";
import { partyPatternFill } from "./races";

// House-by-state district map data [E2.3]. House race ids are `us-house-2026-{ST}-{DD}` and do NOT
// end in a state postal (E2.2), so we key everything off the config's own `state` + `district`.
// Colour is by FORECAST lean, not by the (selection-only) competitiveness rating — the E2.2
// hand-off is explicit about that. Pure logic (unit-tested); the page supplies the SVG + table.

export type Lean = "D" | "R" | null;

export interface HouseDistrict {
  id: string; // race id
  state: string; // USPS postal
  district: number;
  seat: string; // "PA-07"
  forecast: RaceForecast | null;
  lean: Lean; // sign of the forecast Dem margin (null when EVEN / no forecast)
  marginText: string; // "D+2.1" / "R+0.4" / "EVEN" / "—"
  shape: DistrictShape | null;
}

export interface HouseStateGroup {
  state: string; // USPS postal
  name: string; // full state name
  districts: HouseDistrict[]; // sorted by district number
}

// Signed Dem margin -> lean. Treat a hair either side of zero as EVEN (matches marginLabel).
function leanOf(f: RaceForecast | null): Lean {
  if (!f) return null;
  if (Math.abs(f.margin) * 100 < 0.05) return null;
  return f.margin > 0 ? "D" : "R";
}

// One row per competitive House race, id-sorted.
export function houseDistricts(): HouseDistrict[] {
  return allRaces()
    .filter((r) => r.office === "house")
    .map((r) => {
      const forecast = forecastForRace(r.id);
      const district = r.district ?? 0;
      return {
        id: r.id,
        state: r.state,
        district,
        seat: `${r.state}-${String(district).padStart(2, "0")}`,
        forecast,
        lean: leanOf(forecast),
        marginText: forecast ? marginLabel(forecast.margin) : "—",
        shape: districtShape(r.id),
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
}

// Group the districts by state, sorted by full state name; districts sorted by number.
export function houseByState(districts = houseDistricts()): HouseStateGroup[] {
  const groups = new Map<string, HouseDistrict[]>();
  for (const d of districts) {
    const list = groups.get(d.state) ?? [];
    list.push(d);
    groups.set(d.state, list);
  }
  return [...groups.entries()]
    .map(([state, list]) => ({
      state,
      name: STATE_NAMES[state] ?? state,
      districts: list.sort((a, b) => a.district - b.district),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

// SVG paint for a district by its forecast lean: party colour + E0.4 texture overlay for
// grayscale legibility. No forecast / EVEN => neutral surface fill, no overlay.
export function leanFill(lean: Lean): { fill: string; overlay?: string } {
  if (lean === "D") return { fill: MAP_COLORS.D, overlay: partyPatternFill("D") };
  if (lean === "R") return { fill: MAP_COLORS.R, overlay: partyPatternFill("R") };
  return { fill: "var(--color-surface-2)" };
}

// National overview fills for <USStateMap>: highlight each state that has competitive House races,
// coloured by which lean is the majority of its districts (tie / all-even => neutral grey). The
// title summarises the state's competitive set; href jumps to that state's section on the page.
export function houseStateFills(groups = houseByState()): Record<string, StateFill> {
  const fills: Record<string, StateFill> = {};
  for (const g of groups) {
    let d = 0;
    let r = 0;
    for (const dist of g.districts) {
      if (dist.lean === "D") d++;
      else if (dist.lean === "R") r++;
    }
    const majority: Lean = d > r ? "D" : r > d ? "R" : null;
    const { fill, overlay } = leanFill(majority);
    const n = g.districts.length;
    fills[g.state] = {
      fill,
      overlay,
      title: `${g.name}: ${n} competitive House ${n === 1 ? "race" : "races"} (${d} lean D, ${r} lean R)`,
      href: `/house#${g.state}`,
    };
  }
  return fills;
}
