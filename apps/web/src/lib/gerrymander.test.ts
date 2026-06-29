import { describe, expect, it } from "vitest";
import { byCompactness, efficiencyGapLabel, stateFairness } from "./gerrymander";

describe("gerrymander", () => {
  it("loads + sorts state fairness", () => {
    const s = stateFairness();
    expect(s.map((x) => x.state)).toEqual(["OH", "PA"]);
  });

  it("labels efficiency gap with direction + magnitude", () => {
    expect(efficiencyGapLabel(0.12)).toBe("12.0 pts toward Republicans");
    expect(efficiencyGapLabel(-0.03)).toBe("3.0 pts toward Democrats");
    expect(efficiencyGapLabel(0.005)).toBe("balanced");
  });

  // Real TIGER compactness (441 districts). Assert invariants over live data, not sample geoids.
  it("ranks districts by compactness (least compact first)", () => {
    const least = byCompactness(true);
    expect(least.length).toBeGreaterThan(400); // ~435 CDs + DC/PR
    // ascending: each <= next, and the head is the global minimum
    for (let i = 1; i < least.length; i++) {
      expect(least[i - 1].polsby_popper).toBeLessThanOrEqual(least[i].polsby_popper);
    }
    expect(least[0].polsby_popper).toBe(Math.min(...least.map((d) => d.polsby_popper)));
    // every metric is a bounded ratio in (0, 1]
    for (const d of least) {
      for (const k of ["polsby_popper", "reock", "convex_hull_ratio"] as const) {
        expect(d[k]).toBeGreaterThan(0);
        expect(d[k]).toBeLessThanOrEqual(1);
      }
    }
  });
});
