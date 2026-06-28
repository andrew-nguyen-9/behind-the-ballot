import { describe, expect, it } from "vitest";
import { allRaces, partyColorClass, partyLabel } from "./races";

describe("races", () => {
  it("loads + validates all seeded race configs", () => {
    const races = allRaces();
    expect(races.length).toBeGreaterThanOrEqual(2);
    // all valid race kind, sorted by id
    expect(races.every((r) => r.kind === "race")).toBe(true);
    const ids = races.map((r) => r.id);
    expect([...ids]).toEqual([...ids].sort());
  });

  it("maps party to colorblind-safe token classes", () => {
    expect(partyColorClass("D")).toBe("bg-party-dem");
    expect(partyColorClass("R")).toBe("bg-party-rep");
    expect(partyColorClass("L")).toBe("bg-party-ind"); // fallback
  });

  it("labels parties", () => {
    expect(partyLabel("D")).toBe("Democrat");
    expect(partyLabel("X")).toBe("Other");
  });
});
