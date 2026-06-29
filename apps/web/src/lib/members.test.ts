import { describe, expect, it } from "vitest";
import { allMembers, chamberComposition, CLASS_II_2026_STATES, ideologyLabel, memberById, membersForRace } from "./members";

describe("members", () => {
  it("loads + sorts the roster by name", () => {
    const ms = allMembers();
    expect(ms.length).toBeGreaterThanOrEqual(3);
    // sorted by the same comparator allMembers uses (localeCompare), not default .sort()
    for (let i = 1; i < ms.length; i++) {
      expect(ms[i - 1].name.localeCompare(ms[i].name)).toBeLessThanOrEqual(0);
    }
  });

  it("finds a member by bioguide id", () => {
    const first = allMembers()[0];
    expect(memberById(first.bioguide_id)?.bioguide_id).toBe(first.bioguide_id);
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
    const senCount = allMembers().filter((m) => m.chamber === "sen").length;
    expect(sen?.total).toBe(senCount);
    expect(sen?.byParty.reduce((s, p) => s + p.count, 0)).toBe(sen?.total);
    expect((sen?.total ?? 0)).toBeGreaterThan(0);
  });

  it("lists 33 Class II Senate seats for 2026, deduped", () => {
    expect(CLASS_II_2026_STATES.length).toBe(33);
    expect(new Set(CLASS_II_2026_STATES).size).toBe(33);
  });

  it("matches members to a race seat by state/district", () => {
    // pick a real sitting senator + house member from the roster, derive expectations
    const sen = allMembers().find((m) => m.chamber === "sen")!;
    const senSeat = membersForRace(sen.state, "senate", null);
    expect(senSeat.map((m) => m.bioguide_id)).toContain(sen.bioguide_id);
    expect(senSeat.every((m) => m.chamber === "sen" && m.state === sen.state)).toBe(true);

    const rep = allMembers().find((m) => m.chamber === "rep" && m.district != null)!;
    const houseSeat = membersForRace(rep.state, "house", rep.district);
    expect(houseSeat.map((m) => m.bioguide_id)).toEqual([rep.bioguide_id]);
    expect(membersForRace(rep.state, "house", 999)).toEqual([]);
    // governor → no congressional seat.
    expect(membersForRace(sen.state, "governor", null)).toEqual([]);
  });
});
