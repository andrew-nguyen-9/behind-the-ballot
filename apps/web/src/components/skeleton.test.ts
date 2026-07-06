import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { skeletonBars } from "./skeleton";

describe("skeletonBars", () => {
  it("defaults to 3 text lines with a short ragged last line (reads as a paragraph)", () => {
    const bars = skeletonBars();
    expect(bars).toHaveLength(3);
    expect(bars[0].width).toBe("100%");
    expect(bars.at(-1)!.width).toBe("60%");
  });

  it("keeps a single text line full-width (no ragged edge when there's nothing to ragged)", () => {
    const bars = skeletonBars({ lines: 1 });
    expect(bars).toHaveLength(1);
    expect(bars[0].width).toBe("100%");
  });

  it("floors invalid line counts to a single line", () => {
    expect(skeletonBars({ lines: 0 })).toHaveLength(1);
    expect(skeletonBars({ lines: -4 })).toHaveLength(1);
    expect(skeletonBars({ lines: Number.NaN })).toHaveLength(1);
    expect(skeletonBars({ lines: 2.9 })).toHaveLength(2);
  });

  it("block reserves an explicit box (layout reserved → no CLS)", () => {
    const bars = skeletonBars({ variant: "block", width: "12rem", height: "8rem" });
    expect(bars).toEqual([{ width: "12rem", height: "8rem", radius: "var(--radius-md)" }]);
  });

  it("circle is square with a pill radius, sized from width or height", () => {
    expect(skeletonBars({ variant: "circle", width: "3rem" })).toEqual([
      { width: "3rem", height: "3rem", radius: "9999px" },
    ]);
    expect(skeletonBars({ variant: "circle", height: "4rem" })[0].width).toBe("4rem");
  });
});

// The DoD a11y gate: prefers-reduced-motion must be a HARD kill-switch (final state, zero
// motion), not a dimmer. Assert the global stylesheet zeroes animation+transition under it,
// and that the skeleton component parks its shimmer to a static base tint (its final state).
describe("prefers-reduced-motion kill-switch", () => {
  const read = (rel: string) =>
    readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
  const globalCss = read("../styles/global.css");
  const skeleton = read("./Skeleton.astro");

  it("global stylesheet kills all animation + transition under reduced-motion", () => {
    const block = globalCss.match(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*\{([^}]*)\}/,
    );
    expect(block, "reduced-motion block present").not.toBeNull();
    const decls = block![1];
    expect(decls).toMatch(/animation:\s*none\s*!important/);
    expect(decls).toMatch(/transition:\s*none\s*!important/);
  });

  it("skeleton shimmer references motion tokens (retunable) and is not hardcoded ms", () => {
    expect(skeleton).toMatch(/animation:\s*btb-skel-sweep\s+var\(--duration-slow\)/);
    expect(skeleton).toMatch(/var\(--ease-standard\)/);
  });

  it("skeleton parks to a static final state when reduced-motion is on", () => {
    // Local guard: animation none + no moving highlight ⇒ the base surface tint remains.
    expect(skeleton).toMatch(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*animation:\s*none/,
    );
    expect(skeleton).toMatch(/background-color:\s*var\(--color-surface-2\)/);
  });
});
