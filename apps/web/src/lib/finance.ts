// Finance gold artifacts (per race), baked by the pipeline [G13a]. Read at build (SSG).
// Sample fixtures live in src/data/finance/<raceId>.json until live FEC runs land.
const mods = import.meta.glob("../data/finance/*.json", { eager: true });

export interface FinanceRow {
  candidate_id: string;
  party: string | null;
  receipts: number;
  disbursements: number;
  cash_on_hand: number;
  burn_rate: number | null;
  coverage_end_date: string | null;
}

export function financeForRace(raceId: string): FinanceRow[] | null {
  const m = mods[`../data/finance/${raceId}.json`] as { default: FinanceRow[] } | undefined;
  return m ? m.default : null;
}

// Compact USD for finance figures, e.g. 4200000 -> "$4.2M".
export function fmtUSD(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}
