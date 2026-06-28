import rosterJson from "../data/members/roster.json";

// Member roster (congress-legislators + Congress.gov) joined with Voteview ideology
// [M1a,M3a], baked by the pipeline. Sample fixture until live runs land.
export interface Member {
  bioguide_id: string;
  name: string;
  party: string;
  state: string;
  chamber: "sen" | "rep";
  district: number | null;
  nominate_dim1: number | null;
}

const roster = rosterJson as Member[];

export function allMembers(): Member[] {
  return [...roster].sort((a, b) => a.name.localeCompare(b.name));
}

export function memberById(id: string): Member | null {
  return roster.find((m) => m.bioguide_id === id) ?? null;
}

export const chamberLabel = (c: Member["chamber"]) => (c === "sen" ? "U.S. Senate" : "U.S. House");

// Chamber composition: seat counts per party, computed from the roster [J?a].
export interface Composition {
  chamber: Member["chamber"];
  label: string;
  total: number;
  byParty: { party: string; count: number }[];
}

// D first, R second, everything else after (alphabetical). Missing → after, not before.
const rank = (party: string) => (party === "D" ? 0 : party === "R" ? 1 : 2);

export function chamberComposition(): Composition[] {
  const chambers: Member["chamber"][] = ["sen", "rep"];
  return chambers.map((chamber) => {
    const group = roster.filter((m) => m.chamber === chamber);
    const counts = new Map<string, number>();
    for (const m of group) counts.set(m.party, (counts.get(m.party) ?? 0) + 1);
    return {
      chamber,
      label: chamberLabel(chamber),
      total: group.length,
      // Party order D, R, then the rest (I/other) alphabetical, for stable display.
      byParty: [...counts.entries()]
        .map(([party, count]) => ({ party, count }))
        .sort((a, b) => rank(a.party) - rank(b.party) || a.party.localeCompare(b.party)),
    };
  });
}

// Senate Class II seats — the rota up for election in 2026 [J?a]. Fixed Senate-rules fact,
// not derivable from the sample roster (no term-end field), so it lives as a constant.
// ponytail: static rota list; a live roster with term-end dates would compute this instead.
export const CLASS_II_2026_STATES = [
  "AL", "AK", "AR", "CO", "DE", "GA", "ID", "IL", "IA", "KS", "KY", "LA", "ME",
  "MA", "MI", "MN", "MS", "MT", "NE", "NH", "NJ", "NM", "NC", "OK", "OR", "RI",
  "SC", "SD", "TN", "TX", "VA", "WV", "WY",
] as const;

// DW-NOMINATE dim1: negative = liberal, positive = conservative [M3a]. Plain-language band.
export function ideologyLabel(dim1: number | null): string {
  if (dim1 === null) return "Not yet scored";
  if (dim1 <= -0.5) return "Strongly liberal";
  if (dim1 < -0.15) return "Center-left";
  if (dim1 <= 0.15) return "Centrist";
  if (dim1 < 0.5) return "Center-right";
  return "Strongly conservative";
}
