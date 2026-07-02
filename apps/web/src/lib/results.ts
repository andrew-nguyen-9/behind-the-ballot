// Election-results gold, baked per race by the pipeline's export_results [E3.2]. Read at
// build (SSG, 0-JS). Committed only when a real state SoS feed has reported — until then
// there is NO file for a race and the page shows its honest "no results yet" state (repo
// rule: never fabricated numbers). Provisional until MEDSL certification flips is_certified.
const mods = import.meta.glob("../data/results/*.json", { eager: true });

export interface ResultCandidate {
  candidate: string;
  party: string | null; // "D" | "R" | ... (partyLabel/partyColorClass map it)
  votes: number;
  pct: number | null; // share of the race, 0–100
}

export interface RaceResults {
  race_id: string;
  election_type: string; // "primary" | "general"
  as_of: string; // ISO-8601 UTC of the latest pull
  is_certified: boolean; // false while provisional (SoS live); true after MEDSL backfill
  pct_reporting: number | null; // 0–100, may be null when a feed omits precinct counts
  is_called: boolean;
  called_by: string | null; // candidate the race is called for (Wikipedia layer)
  call_source: string | null; // e.g. "Wikipedia" — call status is always borrowed [E3.1]
  source_url: string;
  candidates: ResultCandidate[]; // sorted by votes desc by the exporter
}

export function resultsForRace(raceId: string): RaceResults | null {
  const m = mods[`../data/results/${raceId}.json`] as { default: RaceResults } | undefined;
  return m ? m.default : null;
}

// Whole-number vote count, grouped, e.g. 1234567 -> "1,234,567".
export function fmtVotes(n: number): string {
  return n.toLocaleString("en-US");
}

// Provisional vs certified label — drives the unofficial banner every result carries [E3.1].
export function certificationLabel(r: RaceResults): string {
  return r.is_certified ? "Certified" : "Unofficial — provisional";
}

// "62% of precincts reporting" / "Precincts reporting not reported" — honest about gaps.
export function reportingLabel(r: RaceResults): string {
  return r.pct_reporting === null
    ? "Precincts reporting not reported"
    : `${r.pct_reporting}% of precincts reporting`;
}

// ISO timestamp -> "Aug 4, 2026, 11:30 PM UTC" for the as-of stamp.
export function fmtAsOf(iso: string): string {
  const d = new Date(iso);
  return `${d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  })} UTC`;
}
