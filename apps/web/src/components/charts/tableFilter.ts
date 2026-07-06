// Pure logic behind <TableFilter> [E-3 Tier 1.2]. The island adds instant client-side
// filter + column sort on top of an already-server-rendered <table> (the 0-JS fallback is the
// full, unfiltered table). Rows are modelled as string[] (one cell string per column) so this
// is DOM-free and unit-testable; the .astro script reads live <tr>/<td> text into this shape.

export type SortDir = "asc" | "desc";

/** Row indices whose any cell contains `query` (case-insensitive). Empty query → all rows. */
export function filterRowIndices(rows: string[][], query: string): number[] {
  const q = query.trim().toLowerCase();
  const all = rows.map((_, i) => i);
  if (!q) return all;
  return all.filter((i) => rows[i].some((c) => c.toLowerCase().includes(q)));
}

/**
 * Compare two cell strings, numeric-aware: cells that parse as numbers (tolerating leading
 * +/-, thousands commas, %, $ and surrounding text like "+3.2 pts") sort numerically; anything
 * else falls back to a locale string compare. Blanks sort last.
 */
export function compareCells(a: string, b: string): number {
  const na = parseNumeric(a);
  const nb = parseNumeric(b);
  if (na !== null && nb !== null) return na - nb;
  if (na !== null) return -1;
  if (nb !== null) return 1;
  const ea = a.trim() === "";
  const eb = b.trim() === "";
  if (ea && eb) return 0;
  if (ea) return 1;
  if (eb) return -1;
  return a.localeCompare(b);
}

/** First signed decimal found in the string, ignoring commas/currency/%, else null. */
export function parseNumeric(s: string): number | null {
  const m = s.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  if (!m) return null;
  const n = Number(m[0]);
  return Number.isFinite(n) ? n : null;
}

/** Stable indices of `rows` sorted by column `col` in `dir`. Does not mutate `rows`. */
export function sortIndices(rows: string[][], col: number, dir: SortDir): number[] {
  const idx = rows.map((_, i) => i);
  const sign = dir === "asc" ? 1 : -1;
  return idx.sort((a, b) => {
    const c = compareCells(rows[a][col] ?? "", rows[b][col] ?? "");
    return c !== 0 ? c * sign : a - b; // stable: fall back to original order
  });
}

/**
 * Next sort state when a header is activated. Clicking a new column starts ascending; clicking
 * the active column toggles asc→desc→none (none restores the server order).
 */
export function nextSort(
  current: { col: number; dir: SortDir } | null,
  col: number,
): { col: number; dir: SortDir } | null {
  if (!current || current.col !== col) return { col, dir: "asc" };
  if (current.dir === "asc") return { col, dir: "desc" };
  return null;
}
