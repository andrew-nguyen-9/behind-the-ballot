import { describe, expect, it } from "vitest";
import { houseByState, houseDistricts, houseStateFills, leanFill } from "./houseMap";
import { MAP_COLORS } from "./usStates";

describe("houseDistricts", () => {
  const districts = houseDistricts();

  it("returns only House races, id-sorted, with seat + shape", () => {
    expect(districts.length).toBeGreaterThan(0);
    for (const d of districts) {
      expect(d.id.startsWith("us-house-2026-")).toBe(true);
      expect(d.seat).toBe(`${d.state}-${String(d.district).padStart(2, "0")}`);
      // Baked TIGER geometry is OPTIONAL (E2.3/E-4): a results-tracked race (e.g. a safe-seat
      // primary added for results resolution) may have no shape yet — the map + race page skip
      // it (honest-empty), so shape is nullable. When present it must be a valid ring.
      if (d.shape !== null) expect(d.shape.ring.length).toBeGreaterThanOrEqual(3);
    }
    const ids = districts.map((d) => d.id);
    expect([...ids].sort()).toEqual(ids);
  });

  it("derives lean + margin text from the forecast sign", () => {
    for (const d of districts) {
      if (!d.forecast) {
        expect(d.lean).toBeNull();
        expect(d.marginText).toBe("—");
        continue;
      }
      const m = d.forecast.margin;
      if (Math.abs(m) * 100 < 0.05) expect(d.lean).toBeNull();
      else expect(d.lean).toBe(m > 0 ? "D" : "R");
    }
  });
});

describe("houseByState", () => {
  it("groups by state, sorted by name, districts sorted by number", () => {
    const groups = houseByState();
    const names = groups.map((g) => g.name);
    expect([...names].sort()).toEqual(names);
    for (const g of groups) {
      const nums = g.districts.map((d) => d.district);
      expect([...nums].sort((a, b) => a - b)).toEqual(nums);
      for (const d of g.districts) expect(d.state).toBe(g.state);
    }
  });
});

describe("leanFill", () => {
  it("maps lean to party colour + E0.4 overlay; neutral for EVEN/none", () => {
    // R uses the hatch pattern overlay for grayscale legibility
    expect(leanFill("R").fill).toBe(MAP_COLORS.R);
    expect(leanFill("R").overlay).toBe("url(#pf-hatch)");
    // D is solid (no pattern) — overlay undefined
    expect(leanFill("D").fill).toBe(MAP_COLORS.D);
    expect(leanFill("D").overlay).toBeUndefined();
    // EVEN / no forecast => neutral surface fill, no overlay
    expect(leanFill(null).overlay).toBeUndefined();
    expect(leanFill(null).fill).toContain("surface");
  });
});

describe("houseStateFills", () => {
  it("produces a linked, titled fill per state with a competitive race", () => {
    const groups = houseByState();
    const fills = houseStateFills(groups);
    expect(Object.keys(fills).length).toBe(groups.length);
    for (const g of groups) {
      const f = fills[g.state];
      expect(f.href).toBe(`/house#${g.state}`);
      expect(f.title).toContain(g.name);
      expect(f.title).toContain("competitive House");
    }
  });
});
