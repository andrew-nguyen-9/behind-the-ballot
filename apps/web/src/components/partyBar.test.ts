import { describe, expect, it } from "vitest";
import { computeSegments } from "./partyBar";

describe("computeSegments", () => {
  it("normalises against the segment sum when no max is given (stacked)", () => {
    const out = computeSegments([
      { party: "D", value: 3 },
      { party: "R", value: 1 },
    ]);
    expect(out.map((s) => s.pct)).toEqual([75, 25]);
  });

  it("scales against an explicit max (single-fill)", () => {
    const out = computeSegments([{ party: "D", value: 25 }], 100);
    expect(out[0].pct).toBe(25);
  });

  it("clamps values above max to 100", () => {
    const out = computeSegments([{ party: "R", value: 150 }], 100);
    expect(out[0].pct).toBe(100);
  });

  it("floors negatives to 0", () => {
    const out = computeSegments([{ party: "D", value: -5 }], 100);
    expect(out[0].pct).toBe(0);
  });

  it("returns 0 widths when the total is 0 (no divide-by-zero)", () => {
    const out = computeSegments([{ party: "D", value: 0 }, { party: "R", value: 0 }]);
    expect(out.map((s) => s.pct)).toEqual([0, 0]);
  });

  it("preserves party and label passthrough", () => {
    const out = computeSegments([{ party: "I", value: 1, label: "Ind" }], 4);
    expect(out[0]).toMatchObject({ party: "I", label: "Ind", pct: 25 });
  });
});
