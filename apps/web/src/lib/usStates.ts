import statesGeo from "../data/us-states.json";
import { senatorsByState, senateCaucus, type Member } from "./members";
import { partyPatternFill, partyLabel } from "./races";

// Precomputed albers-usa geometry [E1.1, Q6.1] — baked by scripts/gen-us-states.mjs from
// us-atlas (states-albers-10m, AK/HI insets included). 0 runtime topojson; the map component
// just reads these path `d` strings.
export const STATE_GEO = statesGeo as { viewBox: string; paths: Record<string, string> };

// The 50 states, USPS-postal keyed (matches the geometry + roster `state` field).
export const STATE_NAMES: Record<string, string> = {
  AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California",
  CO: "Colorado", CT: "Connecticut", DE: "Delaware", FL: "Florida", GA: "Georgia",
  HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa",
  KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland",
  MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi", MO: "Missouri",
  MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey",
  NM: "New Mexico", NY: "New York", NC: "North Carolina", ND: "North Dakota", OH: "Ohio",
  OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania", RI: "Rhode Island", SC: "South Carolina",
  SD: "South Dakota", TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont",
  VA: "Virginia", WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming",
};
export const STATE_CODES = Object.keys(STATE_NAMES).sort();

// Map fill paints [Q6.2/Q6.3]. Major parties use the shared party tokens; an independent seat
// gets a caucus-tinted grey (blue-tint = caucuses Dem, red-tint = caucuses Rep, neutral grey =
// neither). Party tokens are theme-constant (E0.1), so the tint literals are safe in both modes.
export const MAP_COLORS = {
  D: "var(--color-party-dem)",
  R: "var(--color-party-rep)",
  indDem: "#7c8ea3",
  indRep: "#a38585",
  indNeutral: "#8b929a",
} as const;

// One senator's seat colour.
export function seatColor(m: Pick<Member, "bioguide_id" | "party">): string {
  if (m.party === "D") return MAP_COLORS.D;
  if (m.party === "R") return MAP_COLORS.R;
  const caucus = senateCaucus(m);
  return caucus === "D" ? MAP_COLORS.indDem : caucus === "R" ? MAP_COLORS.indRep : MAP_COLORS.indNeutral;
}

// Human-readable delegation summary, e.g. "2 Democrat", "1 Republican, 1 Independent".
// Party order D, R, then the rest — matches chamberComposition's ordering.
export function describeDelegation(sens: Member[]): string {
  if (sens.length === 0) return "No sitting senators";
  const rank = (p: string) => (p === "D" ? 0 : p === "R" ? 1 : 2);
  const counts = new Map<string, number>();
  for (const s of sens) counts.set(s.party, (counts.get(s.party) ?? 0) + 1);
  return [...counts.entries()]
    .sort((a, b) => rank(a[0]) - rank(b[0]) || a[0].localeCompare(b[0]))
    .map(([p, n]) => `${n} ${partyLabel(p)}`)
    .join(", ");
}

// Injectable per-state fill spec consumed by <USStateMap>. `fill` is any SVG paint (a colour or
// a `url(#…)` reference); `overlay` is an optional second-layer paint (E0.4 texture) for
// grayscale legibility; `title` is the state's accessible <title>; `href` optionally links it.
export interface StateFill {
  fill: string;
  overlay?: string;
  title: string;
  href?: string;
}

// A two-colour diagonal-stripe pattern (a split delegation) — rendered once into the map <defs>.
export interface StripeDef {
  id: string;
  a: string;
  b: string;
}

function stripeId(a: string, b: string): string {
  return `stripe-${[a, b].join("-").replace(/[^a-z0-9]/gi, "")}`;
}

export interface SenateMapData {
  fills: Record<string, StateFill>;
  stripes: StripeDef[];
  rows: { state: string; delegation: string }[];
}

// Build the Senate delegation choropleth data [E1.1]: per-state fill (solid party colour with an
// E0.4 texture overlay, or diagonal two-colour stripes for a split delegation), the set of stripe
// patterns to define, and the equivalent data-table rows. Same-colour pair => solid; differing
// colours => stripes (covers D/R and any independent split). Pure + roster-driven (testable).
export function senateMapData(): SenateMapData {
  const byState = senatorsByState();
  const fills: Record<string, StateFill> = {};
  const stripeMap = new Map<string, StripeDef>();
  const rows: { state: string; delegation: string }[] = [];

  for (const code of STATE_CODES) {
    const name = STATE_NAMES[code];
    const sens = byState[code] ?? [];
    const delegation = describeDelegation(sens);
    const title = `${name}: ${delegation}`;
    rows.push({ state: name, delegation });

    if (sens.length === 0) {
      fills[code] = { fill: "var(--color-surface-2)", title };
      continue;
    }

    const colors = sens.map(seatColor);
    const unique = [...new Set(colors)];
    if (unique.length === 1) {
      // Solid delegation — overlay the shared party's texture (Dem = solid = no overlay).
      fills[code] = { fill: unique[0], overlay: partyPatternFill(sens[0].party), title };
    } else {
      // Split delegation — diagonal stripes of the two seat colours (order-stable).
      const [a, b] = [...unique].sort();
      const id = stripeId(a, b);
      if (!stripeMap.has(id)) stripeMap.set(id, { id, a, b });
      fills[code] = { fill: `url(#${id})`, title };
    }
  }

  return { fills, stripes: [...stripeMap.values()], rows };
}
