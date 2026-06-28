import { describe, expect, it } from "vitest";
import { financeForRace, fmtUSD } from "./finance";

describe("finance", () => {
  it("formats USD compactly", () => {
    expect(fmtUSD(4_200_000)).toBe("$4.2M");
    expect(fmtUSD(700_000)).toBe("$700K");
    expect(fmtUSD(500)).toBe("$500");
  });

  it("loads the seeded OH finance artifact and joins by FEC id", () => {
    const rows = financeForRace("us-senate-2026-OH");
    expect(rows).not.toBeNull();
    expect(rows!.map((r) => r.candidate_id)).toContain("S0OH00100");
  });

  it("returns null for a race with no finance artifact", () => {
    expect(financeForRace("us-house-2026-PA-05")).toBeNull();
  });
});
