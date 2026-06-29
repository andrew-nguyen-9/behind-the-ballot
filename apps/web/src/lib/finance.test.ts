import { describe, expect, it } from "vitest";
import { financeForRace, fmtUSD } from "./finance";

describe("finance", () => {
  it("formats USD compactly", () => {
    expect(fmtUSD(4_200_000)).toBe("$4.2M");
    expect(fmtUSD(700_000)).toBe("$700K");
    expect(fmtUSD(500)).toBe("$500");
  });

  it("loads a real per-race finance artifact joined by FEC id", () => {
    const rows = financeForRace("us-senate-2026-TX");
    expect(rows).not.toBeNull();
    expect(rows!.length).toBeGreaterThan(0);
    expect(rows!.every((r) => typeof r.candidate_id === "string" && r.receipts >= 0)).toBe(true);
  });

  it("returns null for a race with no finance artifact", () => {
    expect(financeForRace("no-such-race-9999")).toBeNull();
  });
});
