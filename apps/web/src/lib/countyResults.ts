// County-level election results [E-R9], mirrors results.ts but adds the county dimension.
// Baked per state by the pipeline (aggregate_to_county -> county rollup, E-F2) ONLY once a
// real SoS feed reports. Read at build (SSG, 0-JS). Until a state has reported there is NO
// file and the /results page shows its honest "no results yet" state (repo rule: never
// fabricated numbers). Provisional until certification flips is_certified.
import { partyLabel, partyPatternFill } from "./races";

const mods = import.meta.glob("../data/county-results/*.json", { eager: true });

export interface CountyCandidate {
  candidate: string;
  party: string | null; // "D" | "R" | ... (partyLabel maps it)
  votes: number;
  pct: number | null; // share within this county's race, 0–100
}

export interface CountyResult {
  county: string; // 5-digit county FIPS (joins az-counties.json geometry)
  pct_reporting: number | null; // 0–100, null when the feed omits precinct counts
  candidates: CountyCandidate[]; // sorted by votes desc by the exporter
}

export interface CountyRaceResults {
  race_id: string;
  office: string; // "governor" | "house" | ...
  district: number | null;
  election_type: string; // "primary" | "general"
  counties: CountyResult[];
}

// A state's whole county rollup: one file, all its contested races' per-county breakdowns.
export interface StateCountyResults {
  state: string; // USPS postal
  as_of: string; // ISO-8601 UTC of the latest pull
  is_certified: boolean; // false while provisional (SoS live)
  is_called: boolean;
  called_by: string | null;
  call_source: string | null;
  source_url: string;
  races: CountyRaceResults[];
}

export function countyResultsForState(state: string): StateCountyResults | null {
  const m = mods[`../data/county-results/${state}.json`] as
    | { default: StateCountyResults }
    | undefined;
  return m ? m.default : null;
}

// Provisional vs certified — same copy as the race page's unofficial banner [E3.1].
export function countyCertificationLabel(r: Pick<StateCountyResults, "is_certified">): string {
  return r.is_certified ? "Certified" : "Unofficial — provisional";
}

// "36.7% of precincts reporting" / honest gap — mirrors results.reportingLabel.
export function countyReportingLabel(pctReporting: number | null): string {
  return pctReporting === null
    ? "Precincts reporting not reported"
    : `${pctReporting}% of precincts reporting`;
}

// Leading candidate in a county (candidates arrive votes-desc). Honest-empty: a county with no
// candidates, or with zero counted votes, has NO leader (null) — never a fabricated winner.
export function leadingCandidate(c: CountyResult): CountyCandidate | null {
  const top = c.candidates[0];
  return top && top.votes > 0 ? top : null;
}

// Margin (percentage points) between the top two candidates; null when there is no contest to
// compare (fewer than two candidates, or missing pct). Drives the choropleth intensity + table.
export function countyMargin(c: CountyResult): number | null {
  const [a, b] = c.candidates;
  if (!a || !b || a.pct === null || b.pct === null) return null;
  return Math.round((a.pct - b.pct) * 10) / 10;
}

// Theme-constant party RGBs (mirror --color-party-* + forecastMap literals) — the fill is an
// rgba() that composites over the page background, so it reads in both light and dark modes.
const PARTY_RGB: Record<string, [number, number, number]> = {
  D: [44, 111, 179], // #2c6fb3
  R: [193, 59, 59], // #c13b3b
};
const IND_RGB: [number, number, number] = [139, 146, 154]; // neutral grey for third parties
const ALPHA_MIN = 0.3; // a leader with a razor-thin margin still reads as filled
const ALPHA_MAX = 0.95; // leaves headroom for the E0.4 hatch overlay on top
const MARGIN_FULL = 40; // ≥40-pt margin = full saturation

// leading party + margin -> rgba paint. Colour encodes the leader (hue) and confidence (alpha);
// the party pattern overlay carries the party redundantly for grayscale/colourblind a11y.
export function marginFill(party: string | null, margin: number | null): string {
  const [r, g, b] = (party && PARTY_RGB[party]) || IND_RGB;
  const m = Math.max(0, Math.min(1, (margin ?? 0) / MARGIN_FULL));
  const alpha = ALPHA_MIN + m * (ALPHA_MAX - ALPHA_MIN);
  return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`;
}

// Injectable per-county fill spec consumed by <CountyMap> (mirrors usStates.StateFill).
export interface CountyFill {
  fill: string;
  overlay?: string; // pattern overlay (url(#pf-…)) for grayscale legibility
  title: string; // the county's accessible <title>
}

// A type alias (not interface) so it satisfies DataTable's Record<string, unknown> row type.
export type CountyMapRow = {
  county: string; // county name
  leader: string; // "Jane Doe (Democrat)" or honest "No leader yet"
  margin: string; // "+12.3" or "—"
  reporting: string; // "36.7%" or "Not reported"
};

export interface CountyMapData {
  fills: Record<string, CountyFill>; // keyed by FIPS
  rows: CountyMapRow[]; // the map's accessible data-table twin
}

// Build the county choropleth [E-R9] for one race: per-county fill (leader hue, margin-scaled
// alpha, party pattern overlay) plus the equivalent data-table rows. `names` maps FIPS -> county
// name (from az-counties.json). Pure + roster-driven so the colouring is unit-testable. A county
// with no leader gets NO fill entry (CountyMap paints emptyFill — honest "nothing reported").
export function countyMapData(
  race: CountyRaceResults,
  names: Record<string, string>,
): CountyMapData {
  const fills: Record<string, CountyFill> = {};
  const rows: CountyMapRow[] = [];
  const ordered = [...race.counties].sort((a, b) =>
    (names[a.county] ?? a.county).localeCompare(names[b.county] ?? b.county),
  );

  for (const c of ordered) {
    const name = names[c.county] ?? c.county;
    const lead = leadingCandidate(c);
    const margin = countyMargin(c);

    if (lead) {
      fills[c.county] = {
        fill: marginFill(lead.party, margin),
        overlay: partyPatternFill(lead.party ?? "?"),
        title:
          `${name}: ${lead.candidate} leads` +
          (margin !== null ? ` by ${margin.toFixed(1)} pts` : "") +
          (c.pct_reporting !== null ? ` · ${c.pct_reporting}% reporting` : ""),
      };
    }

    rows.push({
      county: name,
      leader: lead ? `${lead.candidate} (${partyLabel(lead.party ?? "?")})` : "No leader yet",
      margin: margin !== null ? `+${margin.toFixed(1)}` : "—",
      reporting: c.pct_reporting !== null ? `${c.pct_reporting}%` : "Not reported",
    });
  }

  return { fills, rows };
}

// Statewide totals for a race — sum each candidate's votes across all reported counties and
// re-derive their share. Honest by construction: only counties present in the rollup contribute
// (untagged/unreported counties never invent a bucket). Sorted votes-desc for the totals list.
export function statewideTotals(race: CountyRaceResults): CountyCandidate[] {
  const byCand = new Map<string, { candidate: string; party: string | null; votes: number }>();
  for (const c of race.counties) {
    for (const cand of c.candidates) {
      const e = byCand.get(cand.candidate) ?? {
        candidate: cand.candidate,
        party: cand.party,
        votes: 0,
      };
      e.votes += cand.votes;
      byCand.set(cand.candidate, e);
    }
  }
  const total = [...byCand.values()].reduce((s, c) => s + c.votes, 0);
  return [...byCand.values()]
    .map((c) => ({ ...c, pct: total ? Math.round((c.votes / total) * 1000) / 10 : null }))
    .sort((a, b) => b.votes - a.votes || a.candidate.localeCompare(b.candidate));
}
