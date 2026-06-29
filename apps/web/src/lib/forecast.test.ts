import { describe, expect, it } from "vitest";
import { allChamberForecasts, forecastForRace, marginLabel } from "./forecast";

describe("forecast", () => {
  it("labels signed Dem margins", () => {
    expect(marginLabel(0.031)).toBe("D+3.1");
    expect(marginLabel(-0.015)).toBe("R+1.5");
    expect(marginLabel(0.0)).toBe("EVEN");
    expect(marginLabel(0.0003)).toBe("EVEN"); // < 0.05pt rounds to even
  });

  // Per-race forecast is not wired yet (export_forecast pending — needs the engine run on real
  // PVI/finance inputs). Until then forecastForRace is null and the race page hides the section.
  it("returns null per-race until export_forecast lands", () => {
    expect(forecastForRace("us-senate-2026-TX")).toBeNull();
    expect(forecastForRace("no-such-race-9999")).toBeNull();
  });

  it("loads chamber forecasts", () => {
    const chambers = allChamberForecasts();
    expect(chambers.length).toBeGreaterThanOrEqual(1);
    const senate = chambers.find((c) => c.chamber === "Senate");
    expect(senate?.dem_control_prob).toBeCloseTo(0.48);
  });
});
