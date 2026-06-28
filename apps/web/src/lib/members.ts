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

// DW-NOMINATE dim1: negative = liberal, positive = conservative [M3a]. Plain-language band.
export function ideologyLabel(dim1: number | null): string {
  if (dim1 === null) return "Not yet scored";
  if (dim1 <= -0.5) return "Strongly liberal";
  if (dim1 < -0.15) return "Center-left";
  if (dim1 <= 0.15) return "Centrist";
  if (dim1 < 0.5) return "Center-right";
  return "Strongly conservative";
}
