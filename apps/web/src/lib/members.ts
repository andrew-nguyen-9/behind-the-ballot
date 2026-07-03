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

// Sitting members for a race's seat — geographic link [M8a]. House: same state + district;
// Senate: the state's senators. Joins on real state/district fields (no FEC↔bioguide
// identity crosswalk, which needs live data). ponytail: identity-level finance link lands
// with that crosswalk; this is the source-honest geographic crosslink until then.
export function membersForRace(state: string, office: string, district: number | null): Member[] {
  if (office === "house") {
    return allMembers().filter((m) => m.chamber === "rep" && m.state === state && m.district === district);
  }
  if (office === "senate") {
    return allMembers().filter((m) => m.chamber === "sen" && m.state === state);
  }
  return []; // governor: no congressional seat
}

// Chamber composition: seat counts per party, computed from the roster [J?a].
export interface Composition {
  chamber: Member["chamber"];
  label: string;
  total: number;
  byParty: { party: string; count: number }[];
}

// D first, R second, everything else after (alphabetical). Missing → after, not before.
const rank = (party: string) => (party === "D" ? 0 : party === "R" ? 1 : 2);

// The U.S. House has 435 voting seats; a majority is 218. Fixed constitutional facts.
export const HOUSE_SEATS = 435;

// The 6 House delegates (DC + 5 territories) sit in the roster but hold no floor vote, so they
// are not House "seats" — excluded from chamber composition and the hemicycle [E4.2 QA].
const NON_VOTING_HOUSE_STATES = new Set(["DC", "PR", "GU", "VI", "AS", "MP"]);

export function chamberComposition(): Composition[] {
  const chambers: Member["chamber"][] = ["sen", "rep"];
  return chambers.map((chamber) => {
    const group = roster.filter(
      (m) => m.chamber === chamber && !(chamber === "rep" && NON_VOTING_HOUSE_STATES.has(m.state)),
    );
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

// Senate caucus [Q6.3]. The sample roster has no caucus field, so a small source-honest map
// covers the sitting independents: both Sanders (VT) and King (ME) caucus with the Democrats.
// Major-party members caucus with their own party; an unmapped independent caucuses with
// neither (null) => neutral grey on the map. ponytail: a live roster with a caucus field
// would replace this constant.
const SENATE_CAUCUS: Record<string, "D" | "R"> = {
  S000033: "D", // Bernard Sanders (VT-I)
  K000383: "D", // Angus S. King, Jr. (ME-I)
};

export function senateCaucus(member: Pick<Member, "bioguide_id" | "party">): "D" | "R" | null {
  if (member.party === "D" || member.party === "R") return member.party;
  return SENATE_CAUCUS[member.bioguide_id] ?? null;
}

// Senators grouped by state (postal code -> the state's sitting senators, name-sorted) [E1.1].
// The read-side source of truth for the Senate delegation map's colouring.
export function senatorsByState(): Record<string, Member[]> {
  const byState: Record<string, Member[]> = {};
  for (const m of allMembers()) {
    if (m.chamber !== "sen") continue;
    (byState[m.state] ??= []).push(m);
  }
  return byState;
}

// DW-NOMINATE dim1: negative = liberal, positive = conservative [M3a]. Plain-language band.
export function ideologyLabel(dim1: number | null): string {
  if (dim1 === null) return "Not yet scored";
  if (dim1 <= -0.5) return "Strongly liberal";
  if (dim1 < -0.15) return "Center-left";
  if (dim1 <= 0.15) return "Centrist";
  if (dim1 < 0.5) return "Center-right";
  return "Strongly conservative";
}
