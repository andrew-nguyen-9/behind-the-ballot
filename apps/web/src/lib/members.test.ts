import { describe, expect, it } from "vitest";
import { allMembers, chamberComposition, CLASS_II_2026_STATES, ideologyLabel, memberById, membersForRace } from "./members";

describe("members", () => {
  it("loads + sorts the roster by name", () => {
    const ms = allMembers();
    expect(ms.length).toBeGreaterThanOrEqual(3);
    const names = ms.map((m) => m.name);
    expect([...names]).toEqual([...names].sort());
  });

  it("finds a member by bioguide id", () => {
    expect(memberById("D000001")?.state).toBe("OH");
    expect(memberById("nope")).toBeNull();
  });

  it("bands DW-NOMINATE into plain language", () => {
    expect(ideologyLabel(-0.6)).toBe("Strongly liberal");
    expect(ideologyLabel(-0.3)).toBe("Center-left");
    expect(ideologyLabel(0.0)).toBe("Centrist");
    expect(ideologyLabel(0.42)).toBe("Center-right");
    expect(ideologyLabel(0.7)).toBe("Strongly conservative");
    expect(ideologyLabel(null)).toBe("Not yet scored");
  });

  it("computes chamber composition with party counts summing to the total", () => {
    const comp = chamberComposition();
    const sen = comp.find((c) => c.chamber === "sen");
    expect(sen?.total).toBe(2); // 1 D + 1 I in the sample roster
    expect(sen?.byParty.reduce((s, p) => s + p.count, 0)).toBe(sen?.total);
    // D sorts before I.
    expect(sen?.byParty[0]?.party).toBe("D");
  });

  it("lists 33 Class II Senate seats for 2026, deduped", () => {
    expect(CLASS_II_2026_STATES.length).toBe(33);
    expect(new Set(CLASS_II_2026_STATES).size).toBe(33);
  });

  it("matches members to a race seat by state/district", () => {
    // OH senate → the OH senator; not the PA-05 rep.
    expect(membersForRace("OH", "senate", null).map((m) => m.bioguide_id)).toEqual(["D000001"]);
    // PA house district 5 → the PA-05 rep; wrong district → none.
    expect(membersForRace("PA", "house", 5).map((m) => m.bioguide_id)).toEqual(["R000002"]);
    expect(membersForRace("PA", "house", 99)).toEqual([]);
    // governor → no congressional seat.
    expect(membersForRace("OH", "governor", null)).toEqual([]);
  });
});
