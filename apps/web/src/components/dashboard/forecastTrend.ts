// Pure geometry for the forecast win-probability sparkline [E-5]. Kept DOM-free (mirrors
// partyBar.ts / chartReadout.ts) so the point-mapping maths are unit-tested in the node vitest
// env. <ForecastTrend> only *adds* a hover/focus readout over these server-rendered marks; 0-JS
// the sparkline points + their data-readout labels still carry every value. History is the
// DERIVED forecast archived per run in forecast_snapshots (Neon) — never a fabricated point.

export interface TrendPoint {
  as_of: string; // ISO date/timestamp of the forecast run
  win_prob: number; // Dem win probability 0..1
}

export interface SparkPoint {
  x: number; // px within the viewBox
  y: number; // px within the viewBox (higher prob → smaller y)
  pct: number; // rounded win prob 0..100
  date: string; // YYYY-MM-DD
}

export interface Spark {
  width: number;
  height: number;
  points: SparkPoint[];
  line: string; // "x,y x,y …" for a <polyline points>
  area: string; // closed <path d> filling under the line
}

/** Oldest→newest copy. Input may be newest-first (recentSnapshots order) or unsorted. */
export function chronological(history: TrendPoint[]): TrendPoint[] {
  return [...history].sort((a, b) => a.as_of.localeCompare(b.as_of));
}

/**
 * Map a win-probability history to sparkline geometry on a FIXED 0..1 win-prob y-scale (not
 * auto-zoomed), so the slope is comparable across races. Returns null for <2 points — one
 * reading is not a trend, so the caller shows the honest-empty note instead of a fake line.
 */
export function sparkline(history: TrendPoint[], width = 260, height = 56, pad = 6): Spark | null {
  const pts = chronological(history);
  if (pts.length < 2) return null;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;
  const n = pts.length;
  const points: SparkPoint[] = pts.map((p, i) => {
    const t = i / (n - 1);
    const prob = Math.max(0, Math.min(1, p.win_prob));
    return {
      x: Number((pad + t * innerW).toFixed(2)),
      y: Number((pad + (1 - prob) * innerH).toFixed(2)),
      pct: Math.round(prob * 100),
      date: p.as_of.slice(0, 10),
    };
  });
  const line = points.map((p) => `${p.x},${p.y}`).join(" ");
  const first = points[0];
  const last = points[points.length - 1];
  const baseline = height - pad;
  const area =
    `M${first.x},${baseline} ` +
    points.map((p) => `L${p.x},${p.y}`).join(" ") +
    ` L${last.x},${baseline} Z`;
  return { width, height, points, line, area };
}

/** Position (0..100%) of a DW-NOMINATE dim1 score on a −1 (liberal) … +1 (conservative) track. */
export function ideologyPosition(dim1: number): number {
  const clamped = Math.max(-1, Math.min(1, dim1));
  return Number((((clamped + 1) / 2) * 100).toFixed(2));
}
