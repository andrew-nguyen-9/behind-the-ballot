import { describe, expect, it } from "vitest";
import { districtShape, ringToSvg, ringsToSvg } from "./geo";

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

  it("returns null for an unknown district shape", () => {
    expect(districtShape("no-such-race-9999")).toBeNull();
  });

  // District shapes now ship for the competitive House races [E2.3] (baked from TIGER).
  it("resolves a baked House district shape", () => {
    const s = districtShape("us-house-2026-PA-07");
    expect(s).not.toBeNull();
    expect(s!.geoid).toBe("4207");
    expect(s!.ring.length).toBeGreaterThanOrEqual(3);
  });
});

describe("ringsToSvg", () => {
  const square: [number, number][] = [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
    [0, 0],
  ];
  const tall: [number, number][] = [
    [2, 0],
    [3, 0],
    [3, 2],
    [2, 2],
    [2, 0],
  ];

  it("shares bounds across rings and returns one path per key, in order", () => {
    const { viewBox, paths } = ringsToSvg(
      [
        { key: "a", ring: square },
        { key: "b", ring: tall },
      ],
      100,
      10,
    );
    expect(paths.map((p) => p.key)).toEqual(["a", "b"]);
    // Bounds span lon 0..3, lat 0..2 -> width is the long side => full size; true-aspect height.
    expect(viewBox).toBe("0 0 100.0 73.3");
    for (const p of paths) {
      expect(p.d.startsWith("M")).toBe(true);
      expect(p.d.endsWith("Z")).toBe(true);
    }
  });

  it("skips rings with fewer than 3 points and throws when none remain", () => {
    const { paths } = ringsToSvg([
      { key: "a", ring: square },
      { key: "bad", ring: [[0, 0]] as [number, number][] },
    ]);
    expect(paths.map((p) => p.key)).toEqual(["a"]);
    expect(() => ringsToSvg([{ key: "x", ring: [[0, 0]] as [number, number][] }])).toThrow();
  });
});
