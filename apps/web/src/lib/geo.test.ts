import { describe, expect, it } from "vitest";
import { districtShape, ringToSvg } from "./geo";

describe("geo", () => {
  it("projects a square ring to an SVG path within the viewBox", () => {
    const square: [number, number][] = [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
      [0, 0],
    ];
    const { d, viewBox } = ringToSvg(square, 100, 10);
    expect(viewBox).toBe("0 0 100 100");
    expect(d.startsWith("M")).toBe(true);
    expect(d.endsWith("Z")).toBe(true);
    // first point [0,0] is lon=min, lat=min -> flipped to bottom-left (x=pad, y=size-pad)
    expect(d).toContain("M10.0 90.0");
  });

  it("rejects degenerate rings", () => {
    expect(() => ringToSvg([[0, 0]] as [number, number][])).toThrow();
  });

  // District shapes ship with House key races (TIGER/geo chain — pending). No house race yet →
  // null, and the race page hides the map section.
  it("returns null for an unknown district shape", () => {
    expect(districtShape("no-such-race-9999")).toBeNull();
  });
});
