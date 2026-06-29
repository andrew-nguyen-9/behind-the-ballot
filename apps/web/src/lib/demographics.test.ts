import { describe, expect, it } from "vitest";
import { demographicsForRace, fmtIncome, fmtPop } from "./demographics";

describe("demographics", () => {
  it("loads the OH demographics artifact with real figures", () => {
    const d = demographicsForRace("us-senate-2026-OH");
    expect(d).not.toBeNull();
    expect(d!.area).toBe("Ohio");
    expect(d!.population).toBeGreaterThan(10_000_000); // real OH ~11.8M
    expect(d!.median_income).toBeGreaterThan(0);
  });

  it("returns null when absent", () => {
    expect(demographicsForRace("no-such-race-9999")).toBeNull();
  });

  it("formats population and income", () => {
    expect(fmtPop(11799448)).toBe("11,799,448");
    expect(fmtIncome(66990)).toBe("$66,990");
  });
});
