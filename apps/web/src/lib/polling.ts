// Polling aggregate artifacts (per race), baked by the pipeline [H1a]. Read at build.
// Sample fixtures in src/data/polling/<raceId>.json until live 538 runs land.
const mods = import.meta.glob("../data/polling/*.json", { eager: true });

export interface PollAverage {
  party: string;
  avg_pct: number;
  n_polls: number;
  latest_end_date: string | null;
}
export interface PollingArtifact {
  as_of: string;
  averages: PollAverage[];
}

export function pollingForRace(raceId: string): PollingArtifact | null {
  const m = mods[`../data/polling/${raceId}.json`] as { default: PollingArtifact } | undefined;
  return m ? m.default : null;
}
