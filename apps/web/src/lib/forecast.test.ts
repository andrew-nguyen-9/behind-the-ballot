import { describe, expect, it } from "vitest";
import { allChamberForecasts, forecastForRace, marginLabel } from "./forecast";

describe("forecast", () => {
  it("labels signed Dem margins", () => {
    expect(marginLabel(0.031)).toBe("D+3.1");
    expect(marginLabel(-0.015)).toBe("R+1.5");
    expect(marginLabel(0.0)).toBe("EVEN");
    expect(marginLabel(0.0003)).toBe("EVEN"); // < 0.05pt rounds to even
  });

  it("loads the seeded OH forecast artifact", () => {
    const f = forecastForRace("us-senate-2026-OH");
    expect(f).not.toBeNull();
    expect(f!.win_prob).toBeCloseTo(0.62);
  });

  it("returns null for a race with no forecast", () => {
    expect(forecastForRace("us-house-2026-PA-05")).toBeNull();
  });

  it("loads chamber forecasts", () => {
    const chambers = allChamberForecasts();
    expect(chambers.length).toBeGreaterThanOrEqual(1);
    const senate = chambers.find((c) => c.chamber === "Senate");
    expect(senate?.dem_control_prob).toBeCloseTo(0.48);
  });
});
