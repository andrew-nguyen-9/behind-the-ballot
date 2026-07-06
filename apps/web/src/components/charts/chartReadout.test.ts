import { describe, expect, it } from "vitest";
import { clampTooltip, readReadout } from "./chartReadout";

describe("readReadout", () => {
  it("prefers explicit label + value data attributes", () => {
    expect(readReadout({ label: "OH-13", value: "D +2.1" })).toEqual({
      label: "OH-13",
      value: "D +2.1",
    });
  });

  it("uses a bare value with an empty label", () => {
    expect(readReadout({ value: "51 seats" })).toEqual({ label: "", value: "51 seats" });
  });

  it("splits a <title> on the em/en dash into label + value", () => {
    expect(readReadout({}, "PA-08 — forecast D +1.4")).toEqual({
      label: "PA-08",
      value: "forecast D +1.4",
    });
  });

  it("treats an unseparated <title> as the value", () => {
    expect(readReadout({}, "Democratic")).toEqual({ label: "", value: "Democratic" });
  });

  it("returns null when there is nothing to show", () => {
    expect(readReadout({})).toBeNull();
    expect(readReadout({}, "   ")).toBeNull();
  });

  it("falls back to a lone label when no value is given", () => {
    expect(readReadout({ label: "Vacant" })).toEqual({ label: "", value: "Vacant" });
  });
});

describe("clampTooltip", () => {
  const container = { w: 200, h: 100 };
  const tip = { w: 60, h: 20 };

  it("places the tip above-right of the pointer when there is room", () => {
    expect(clampTooltip(container, { x: 40, y: 60 }, tip)).toEqual({ x: 52, y: 28 });
  });

  it("flips left when it would overflow the right edge", () => {
    const { x } = clampTooltip(container, { x: 190, y: 60 }, tip);
    expect(x).toBe(190 - 12 - 60); // 118, pointer.x - gap - tip.w
  });

  it("drops below the pointer when there is no room above", () => {
    const { y } = clampTooltip(container, { x: 40, y: 5 }, tip);
    expect(y).toBe(17); // pointer.y + gap
  });

  it("never lets the tip escape the container box", () => {
    const { x, y } = clampTooltip(container, { x: 199, y: 99 }, tip);
    expect(x).toBeGreaterThanOrEqual(0);
    expect(x).toBeLessThanOrEqual(container.w - tip.w);
    expect(y).toBeGreaterThanOrEqual(0);
    expect(y).toBeLessThanOrEqual(container.h - tip.h);
  });
});
