import { describe, expect, it } from "vitest";
import { demographicsForRace, fmtIncome, fmtPop } from "./demographics";

describe("demographics", () => {
  it("loads the seeded OH demographics artifact", () => {
    const d = demographicsForRace("us-senate-2026-OH");
    expect(d).not.toBeNull();
    expect(d!.area).toBe("Ohio");
    expect(d!.urbanization).toBe("suburban");
  });

  it("returns null when absent", () => {
    expect(demographicsForRace("us-house-2026-PA-05")).toBeNull();
  });

  it("formats population and income", () => {
    expect(fmtPop(11799448)).toBe("11,799,448");
    expect(fmtIncome(66990)).toBe("$66,990");
  });
});
