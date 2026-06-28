import { describe, expect, it } from "vitest";
import { allMembers, ideologyLabel, memberById } from "./members";

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
});
