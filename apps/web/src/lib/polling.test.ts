import { describe, expect, it } from "vitest";
import { pollingForRace } from "./polling";

describe("polling", () => {
  it("loads the seeded OH polling artifact", () => {
    const p = pollingForRace("us-senate-2026-OH");
    expect(p).not.toBeNull();
    expect(p!.as_of).toBe("2026-03-15");
    expect(p!.averages.map((a) => a.party)).toEqual(["D", "R"]);
  });

  it("returns null when a race has no polling artifact", () => {
    expect(pollingForRace("us-house-2026-PA-05")).toBeNull();
  });
});
