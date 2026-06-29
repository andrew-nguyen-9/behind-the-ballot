import { describe, expect, it } from "vitest";
import { allChamberForecasts, forecastForRace, marginLabel } from "./forecast";

describe("forecast", () => {
  it("labels signed Dem margins", () => {
    expect(marginLabel(0.031)).toBe("D+3.1");
    expect(marginLabel(-0.015)).toBe("R+1.5");
    expect(marginLabel(0.0)).toBe("EVEN");
    expect(marginLabel(0.0003)).toBe("EVEN"); // < 0.05pt rounds to even
  });

  // Per-race forecast is live (export_forecast on real MEDSL PVI). Assert invariants over whatever
  // races are baked, not specific values; an unknown race id is null and the page hides the section.
  it("serves bounded per-race forecasts; null for unknown races", () => {
    expect(forecastForRace("no-such-race-9999")).toBeNull();
    const tx = forecastForRace("us-senate-2026-TX");
    if (tx) {
      expect(tx.win_prob).toBeGreaterThanOrEqual(0);
      expect(tx.win_prob).toBeLessThanOrEqual(1);
      expect(tx.margin_lo).toBeLessThanOrEqual(tx.margin_hi);
      expect(tx.as_of).toBeTruthy();
    }
  });

  // Chamber forecast: real Senate control math (holdovers + 51-seat threshold). Every figure must
  // be sourced-traceable (as_of) and a bounded probability/seat count [R14a].
  it("publishes a bounded, sourced chamber forecast", () => {
    for (const c of allChamberForecasts()) {
      expect(c.as_of).toBeTruthy();
      expect(c.dem_control_prob).toBeGreaterThanOrEqual(0);
      expect(c.dem_control_prob).toBeLessThanOrEqual(1);
      expect(c.expected_dem_seats).toBeGreaterThanOrEqual(0);
      expect(c.expected_dem_seats).toBeLessThanOrEqual(100);
      expect(c.dem_seat_p10).toBeLessThanOrEqual(c.dem_seat_p90);
    }
  });
});
