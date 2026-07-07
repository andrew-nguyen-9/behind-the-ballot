import { describe, expect, it } from "vitest";
import { chronological, ideologyPosition, sparkline, type TrendPoint } from "./forecastTrend";

const P = (as_of: string, win_prob: number): TrendPoint => ({ as_of, win_prob });

describe("chronological", () => {
  it("sorts newest-first input into oldest→newest", () => {
    const out = chronological([P("2026-03-01", 0.5), P("2026-01-01", 0.3), P("2026-02-01", 0.4)]);
    expect(out.map((p) => p.as_of)).toEqual(["2026-01-01", "2026-02-01", "2026-03-01"]);
  });
  it("does not mutate the input", () => {
    const src = [P("2026-02-01", 0.4), P("2026-01-01", 0.3)];
    chronological(src);
    expect(src[0].as_of).toBe("2026-02-01");
  });
});

describe("sparkline", () => {
  it("returns null for <2 points (one reading is not a trend)", () => {
    expect(sparkline([])).toBeNull();
    expect(sparkline([P("2026-01-01", 0.5)])).toBeNull();
  });

  it("maps endpoints to the padded x-range and inverts y with probability", () => {
    const s = sparkline([P("2026-01-01", 0), P("2026-02-01", 1)], 260, 56, 6);
    expect(s).not.toBeNull();
    const [a, b] = s!.points;
    expect(a.x).toBe(6); // first at left pad
    expect(b.x).toBe(254); // last at width - pad
    expect(a.y).toBe(50); // prob 0 → bottom (height - pad)
    expect(b.y).toBe(6); // prob 1 → top (pad)
  });

  it("clamps out-of-range probabilities and rounds pct + slices the date", () => {
    const s = sparkline([P("2026-01-01T09:00:00Z", -0.2), P("2026-02-01T00:00Z", 1.4)]);
    expect(s!.points[0].pct).toBe(0);
    expect(s!.points[1].pct).toBe(100);
    expect(s!.points[0].date).toBe("2026-01-01");
  });

  it("builds a closed area path anchored on the baseline", () => {
    const s = sparkline([P("2026-01-01", 0.5), P("2026-02-01", 0.6)], 260, 56, 6);
    expect(s!.area.startsWith("M")).toBe(true);
    expect(s!.area.trimEnd().endsWith("Z")).toBe(true);
    expect(s!.line.split(" ")).toHaveLength(2);
  });
});

describe("ideologyPosition", () => {
  it("maps −1→0%, 0→50%, +1→100% and clamps beyond", () => {
    expect(ideologyPosition(-1)).toBe(0);
    expect(ideologyPosition(0)).toBe(50);
    expect(ideologyPosition(1)).toBe(100);
    expect(ideologyPosition(-1.5)).toBe(0);
    expect(ideologyPosition(2)).toBe(100);
  });
});
