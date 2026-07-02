// Segment math for <PartyBar>. Kept in a plain .ts (not the .astro) so it is unit-testable
// and reusable by any future viz island. Pure — no DOM, no Astro.

export interface BarSegment {
  party: string;
  value: number;
  label?: string;
}

export interface ComputedBarSegment extends BarSegment {
  /** Clamped 0–100 width percentage for the inline `style={width:%}` fill. */
  pct: number;
}

/**
 * Compute each segment's width percentage.
 * - With `max`: each segment is scaled against it (single-fill bars — finance/polling).
 * - Without `max`: segments are normalised against their own sum (stacked bars — chamber).
 * Negative values are floored to 0; result is clamped to [0, 100].
 */
export function computeSegments(segments: BarSegment[], max?: number): ComputedBarSegment[] {
  const total = max ?? segments.reduce((sum, s) => sum + Math.max(0, s.value), 0);
  return segments.map((s) => ({
    ...s,
    pct: total > 0 ? Math.max(0, Math.min(100, (s.value / total) * 100)) : 0,
  }));
}
