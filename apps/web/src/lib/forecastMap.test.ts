import { describe, expect, it } from "vitest";
import {
  chamberSeatSegments,
  majorityMarkerPct,
  raceStatePostal,
  senateForecastMapData,
  winProbColor,
} from "./forecastMap";
import type { ChamberForecast } from "./forecast";

describe("winProbColor (probability→colour ramp)", () => {
  it("picks the party by side of 50%", () => {
    expect(winProbColor(0.9).party).toBe("D");
    expect(winProbColor(0.1).party).toBe("R");
    expect(winProbColor(0.5).party).toBe("D"); // 0.5 counts as Dem side (>=)
  });

  it("intensity is 0 at a toss-up and 1 at the extremes", () => {
    expect(winProbColor(0.5).intensity).toBe(0);
    expect(winProbColor(1).intensity).toBe(1);
    expect(winProbColor(0).intensity).toBe(1);
  });

  it("intensity is symmetric around 0.5 and monotonic in confidence", () => {
    expect(winProbColor(0.7).intensity).toBeCloseTo(winProbColor(0.3).intensity, 10);
    expect(winProbColor(0.9).intensity).toBeGreaterThan(winProbColor(0.6).intensity);
    expect(winProbColor(0.1).intensity).toBeGreaterThan(winProbColor(0.4).intensity);
  });

  it("emits an rgba paint whose alpha rises with confidence", () => {
    const toss = winProbColor(0.5);
    const sure = winProbColor(1);
    expect(toss.fill).toMatch(/^rgba\(44, 111, 179, /); // Dem rgb
    expect(sure.fill).toBe("rgba(44, 111, 179, 0.95)");
    expect(winProbColor(0).fill).toBe("rgba(193, 59, 59, 0.95)"); // Rep rgb at full alpha
    const alpha = (s: string) => Number(s.match(/, ([\d.]+)\)$/)![1]);
    expect(alpha(toss.fill)).toBeCloseTo(0.18, 5); // floor keeps toss-ups visible
    expect(alpha(sure.fill)).toBeGreaterThan(alpha(toss.fill));
  });

  it("clamps out-of-range probabilities", () => {
    expect(winProbColor(1.5).intensity).toBe(1);
    expect(winProbColor(-0.5).intensity).toBe(1);
    expect(winProbColor(1.5).party).toBe("D");
    expect(winProbColor(-0.5).party).toBe("R");
  });
});

describe("raceStatePostal", () => {
  it("extracts the postal code from a race id", () => {
    expect(raceStatePostal("us-senate-2026-TX")).toBe("TX");
    expect(raceStatePostal("us-senate-2026-me")).toBe("ME"); // case-insensitive
  });
  it("returns null for a non-state trailing token", () => {
    expect(raceStatePostal("us-senate-2026-ZZ")).toBeNull();
    expect(raceStatePostal("chamber-senate")).toBeNull();
  });
});

describe("senateForecastMapData", () => {
  const data = senateForecastMapData();

  it("only publishes states that have a baked forecast (no invented fills)", () => {
    expect(data.count).toBe(data.rows.length);
    expect(Object.keys(data.fills).length).toBe(data.count);
    // Whatever is baked, every fill carries a paint + accessible title.
    for (const f of Object.values(data.fills)) {
      expect(f.fill).toMatch(/^rgba\(/);
      expect(f.title).toBeTruthy();
    }
  });

  it("orders the table from most to least Dem-favoured", () => {
    const probs = data.rows.map((r) => Number(r.prob.replace("%", "")));
    for (let i = 1; i < probs.length; i++) {
      expect(probs[i - 1]).toBeGreaterThanOrEqual(probs[i]);
    }
  });
});

describe("chamber seat bar", () => {
  const senate: ChamberForecast = {
    chamber: "Senate",
    as_of: "2026-06-29T03:43:04.719070+00:00",
    n_sims: 10000,
    n_races: 33,
    majority: 51,
    expected_dem_seats: 46.4,
    dem_seat_p10: 45,
    dem_seat_p50: 46,
    dem_seat_p90: 48,
    dem_control_prob: 0.0003,
  };

  it("splits the published Dem expectation against the chamber total complement", () => {
    const segs = chamberSeatSegments(senate)!;
    expect(segs).toHaveLength(2);
    expect(segs[0].party).toBe("D");
    expect(segs[0].value).toBe(46.4);
    expect(segs[1].value).toBeCloseTo(53.6, 5); // 100 - 46.4
  });

  it("places the majority marker at the majority fraction of the chamber", () => {
    expect(majorityMarkerPct(senate)).toBe(51); // 51 / 100
  });

  it("returns null (no invented total) for an unknown chamber", () => {
    const unknown = { ...senate, chamber: "Assembly" };
    expect(chamberSeatSegments(unknown)).toBeNull();
    expect(majorityMarkerPct(unknown)).toBeNull();
  });
});
