import { describe, expect, it } from "vitest";
import {
  stateSnapshotTable,
  districtSnapshotTable,
  nationalTotals,
  hasChangeData,
  stateChanges,
  changeMetadata,
  fmtDelta,
  fmtPct,
  pctBarWidth,
} from "./demographicChange";

describe("demographic snapshot (committed, real ACS)", () => {
  it("loads per-state + per-CD tables", () => {
    expect(stateSnapshotTable.acs_release).toMatch(/ACS/);
    expect(stateSnapshotTable.rows.length).toBeGreaterThan(40); // 50 states + DC
    expect(districtSnapshotTable.rows.length).toBeGreaterThan(400); // ~435 CDs
    const tx = stateSnapshotTable.rows.find((r) => r.area === "Texas");
    expect(tx!.population).toBeGreaterThan(20_000_000);
  });

  it("computes national totals (sum pop, pop-weighted income)", () => {
    const t = nationalTotals();
    expect(t.population).toBeGreaterThan(300_000_000);
    expect(t.median_income).toBeGreaterThan(0);
  });
});

describe("change layer (absent until a >=2-endpoint bake)", () => {
  it("is honestly empty when no change data is committed", () => {
    expect(hasChangeData()).toBe(false);
    expect(stateChanges()).toEqual([]);
    expect(changeMetadata()).toBeNull();
  });
});

describe("delta formatting", () => {
  it("signs absolute deltas", () => {
    expect(fmtDelta(12430)).toBe("+12,430");
    expect(fmtDelta(-3001)).toBe("-3,001");
    expect(fmtDelta(null)).toBe("—");
  });
  it("signs percentages", () => {
    expect(fmtPct(2.4)).toBe("+2.4%");
    expect(fmtPct(-0.8)).toBe("-0.8%");
    expect(fmtPct(null)).toBe("—");
  });
  it("scales bar width to a cap and clamps at 100", () => {
    expect(pctBarWidth(5, 10)).toBe(50);
    expect(pctBarWidth(-5, 10)).toBe(50); // magnitude
    expect(pctBarWidth(20, 10)).toBe(100); // clamped
    expect(pctBarWidth(null)).toBe(0);
  });
});
