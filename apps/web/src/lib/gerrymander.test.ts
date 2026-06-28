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

  it("ranks districts by compactness (least compact first)", () => {
    const least = byCompactness(true);
    expect(least[0].polsby_popper).toBeLessThanOrEqual(least[least.length - 1].polsby_popper);
    expect(least[0].geoid).toBe("3903"); // 0.21 is lowest
  });
});
