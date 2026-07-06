// Skeleton geometry [E-F1] — pure, testable logic behind Skeleton.astro. Kept separate from
// the component (mirrors partyBar.ts / partyBar.astro) so the layout-reservation contract is
// unit-tested in the node vitest env without a DOM. The loading philosophy is skeleton-over-
// spinner: reserve the final layout, show the content's shape, never shift (CLS is a gate).

export type SkeletonVariant = "text" | "block" | "circle";

export interface SkeletonBar {
  /** CSS width (e.g. "100%", "60%", "3rem"). */
  width: string;
  /** CSS height. */
  height: string;
  /** CSS border-radius. */
  radius: string;
}

export interface SkeletonOptions {
  variant?: SkeletonVariant;
  /** text: number of lines (>=1). ignored by block/circle. */
  lines?: number;
  /** block/circle explicit size; text uses a fixed line height. */
  width?: string;
  height?: string;
}

// Last text line is short so the block reads as a paragraph, not a solid box.
const LAST_LINE_WIDTH = "60%";
const TEXT_LINE_HEIGHT = "0.85em";
const TEXT_LINE_RADIUS = "var(--radius-sm)";

/**
 * Resolve a skeleton into the concrete bars to render. One bar per array entry; the count and
 * dimensions are deterministic so the placeholder reserves exactly the same box every render
 * (no layout shift). Invalid `lines` (<1, NaN) floor to a single line.
 */
export function skeletonBars(opts: SkeletonOptions = {}): SkeletonBar[] {
  const variant = opts.variant ?? "text";

  if (variant === "circle") {
    const size = opts.width ?? opts.height ?? "2.5rem";
    return [{ width: size, height: size, radius: "9999px" }];
  }

  if (variant === "block") {
    return [
      {
        width: opts.width ?? "100%",
        height: opts.height ?? "6rem",
        radius: "var(--radius-md)",
      },
    ];
  }

  // text
  const raw = opts.lines ?? 3;
  const count = Number.isFinite(raw) ? Math.max(1, Math.floor(raw)) : 1;
  return Array.from({ length: count }, (_, i) => ({
    width: i === count - 1 && count > 1 ? LAST_LINE_WIDTH : opts.width ?? "100%",
    height: opts.height ?? TEXT_LINE_HEIGHT,
    radius: TEXT_LINE_RADIUS,
  }));
}
