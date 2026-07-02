import { allRaceForecasts, marginLabel, type ChamberForecast, type RaceForecast } from "./forecast";
import { STATE_NAMES, type StateFill } from "./usStates";
import { partyPatternFill } from "./races";
import type { BarSegment } from "../components/partyBar";

// Forecast data-viz logic [E1.3]. Pure + unit-tested so the choropleth ramp and the seat bar
// are verifiable and reusable. The probability→colour ramp is the tested seam.

// Theme-constant party RGBs (mirror the --color-party-* tokens in global.css). Kept as literals
// because the map paints with rgba() at a confidence-scaled alpha — the transparent fill
// composites over the page background, so it reads correctly in both light and dark modes.
const PARTY_RGB = {
  D: [44, 111, 179], // #2c6fb3
  R: [193, 59, 59], // #c13b3b
} as const;

// Alpha floor keeps a toss-up faintly tinted (still visible); the ceiling avoids pure opaque so
// the E0.4 hatch overlay stays legible on top.
const ALPHA_MIN = 0.18;
const ALPHA_MAX = 0.95;

export interface ProbColor {
  party: "D" | "R"; // which side of 50% (party the colour implies)
  intensity: number; // 0 = toss-up, 1 = certain
  fill: string; // rgba() paint, alpha scaled by intensity
}

// Probability→colour ramp [Q6.5a]. `winProb` is the Dem win probability (0..1). Diverging ramp:
// blue toward 1, red toward 0, near-neutral (faint) at 0.5. Colour intensity encodes confidence;
// party (hue) is redundantly carried by the E0.4 pattern overlay for grayscale a11y.
export function winProbColor(winProb: number): ProbColor {
  const p = Math.max(0, Math.min(1, winProb));
  const party: "D" | "R" = p >= 0.5 ? "D" : "R";
  const intensity = Math.min(1, Math.abs(p - 0.5) * 2);
  const [r, g, b] = PARTY_RGB[party];
  const alpha = ALPHA_MIN + intensity * (ALPHA_MAX - ALPHA_MIN);
  return { party, intensity, fill: `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})` };
}

// Race id -> USPS postal code (e.g. "us-senate-2026-TX" -> "TX"). Null if the trailing token
// is not one of the 50 states (defensive; keeps unknown ids off the map).
export function raceStatePostal(raceId: string): string | null {
  const seg = (raceId.split("-").pop() ?? "").toUpperCase();
  return STATE_NAMES[seg] ? seg : null;
}

export interface ForecastMapData {
  fills: Record<string, StateFill>;
  rows: { state: string; prob: string; margin: string; range: string }[];
  count: number; // number of states with a published forecast
}

// Build the win-probability choropleth [E1.3, Q6.5a] from the baked per-race forecasts. Each
// contested state is filled by its Dem win probability (ramp above) with the party's E0.4 texture
// overlaid; states without a published forecast are simply absent (USStateMap paints emptyFill —
// "not up this cycle"). No invented numbers. Sorted safe-Dem → toss-up → safe-Rep for the table.
export function senateForecastMapData(): ForecastMapData {
  const entries = allRaceForecasts()
    .map(({ raceId, forecast }) => ({ code: raceStatePostal(raceId), forecast }))
    .filter((e): e is { code: string; forecast: RaceForecast } => e.code !== null)
    .sort((a, b) => b.forecast.win_prob - a.forecast.win_prob);

  const fills: Record<string, StateFill> = {};
  const rows: ForecastMapData["rows"] = [];

  for (const { code, forecast } of entries) {
    const name = STATE_NAMES[code];
    const c = winProbColor(forecast.win_prob);
    const prob = `${Math.round(forecast.win_prob * 100)}%`;
    const margin = marginLabel(forecast.margin);
    const range = `${marginLabel(forecast.margin_lo)} – ${marginLabel(forecast.margin_hi)}`;
    fills[code] = {
      fill: c.fill,
      overlay: partyPatternFill(c.party),
      title: `${name}: Dem win ${prob}, forecast ${margin}`,
    };
    rows.push({ state: name, prob, margin, range });
  }

  return { fills, rows, count: entries.length };
}

// Total seats per chamber — constitutional constants, not forecast figures. Used only to derive
// the complement of the published expected Dem seats for the composition bar. Chambers absent here
// get no seat bar (the caller falls back to the StatBlocks) rather than an invented total.
export const CHAMBER_SEATS: Record<string, number> = { Senate: 100, House: 435 };

// Seat-distribution bar segments [Q6.5b]: expected Dem seats vs the rest, out of the chamber size.
// Returns null when the chamber size is unknown (no invented total). The Rep/other value is the
// mathematical complement of the published expected Dem seats — derived, not invented.
export function chamberSeatSegments(c: ChamberForecast): BarSegment[] | null {
  const total = CHAMBER_SEATS[c.chamber];
  if (!total) return null;
  const dem = c.expected_dem_seats;
  const rep = Math.max(0, total - dem);
  return [
    { party: "D", value: dem, label: `Democrats: expected ${dem.toFixed(1)} of ${total} seats` },
    { party: "R", value: rep, label: `Republicans / others: expected ${rep.toFixed(1)} of ${total} seats` },
  ];
}

// Majority threshold as a percent-from-left, for the marker line over the seat bar. Null when the
// chamber size is unknown (matches chamberSeatSegments).
export function majorityMarkerPct(c: ChamberForecast): number | null {
  const total = CHAMBER_SEATS[c.chamber];
  if (!total) return null;
  return Math.max(0, Math.min(100, (c.majority / total) * 100));
}
