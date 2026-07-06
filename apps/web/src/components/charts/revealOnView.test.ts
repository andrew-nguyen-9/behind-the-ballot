import { describe, expect, it } from "vitest";
import { prefersReducedMotion, shouldArm, staggerDelay } from "./revealOnView";

describe("prefersReducedMotion", () => {
  it("reads the media-query match, tolerating a null query", () => {
    expect(prefersReducedMotion({ matches: true })).toBe(true);
    expect(prefersReducedMotion({ matches: false })).toBe(false);
    expect(prefersReducedMotion(null)).toBe(false);
  });
});

describe("shouldArm", () => {
  it("arms only when motion is allowed and the observer is supported", () => {
    expect(shouldArm({ reducedMotion: false, supportsObserver: true })).toBe(true);
  });
  it("stays disarmed under reduced motion (final state instantly)", () => {
    expect(shouldArm({ reducedMotion: true, supportsObserver: true })).toBe(false);
  });
  it("stays disarmed without observer support (final state, no-JS parity)", () => {
    expect(shouldArm({ reducedMotion: false, supportsObserver: false })).toBe(false);
  });
});

describe("staggerDelay", () => {
  it("scales linearly by index", () => {
    expect(staggerDelay(0)).toBe(0);
    expect(staggerDelay(2)).toBe(120);
  });
  it("caps long lists so they never crawl", () => {
    expect(staggerDelay(100)).toBe(360);
  });
  it("floors invalid indices to 0", () => {
    expect(staggerDelay(-3)).toBe(0);
    expect(staggerDelay(Number.NaN)).toBe(0);
  });
});
