// Grouping + filtering logic for the /races and /members directory pages [Q6.7]. Pure and
// unit-tested. The pages render the default grouping server-side (the 0-JS fallback) using
// `groupBy`, and the FilterBar island reuses `matchesFilters` shape to progressively
// enhance that same markup — no data fetch, no duplication of the source of truth.

// Stable-ordered grouping. `order` lists known keys first (in that order); any other keys
// follow in first-seen order. Empty groups are naturally omitted (only present keys appear).
export function groupBy<T>(
  items: T[],
  key: (item: T) => string,
  order: string[] = [],
): { key: string; items: T[] }[] {
  const groups = new Map<string, T[]>();
  const insertion: string[] = [];
  for (const item of items) {
    const k = key(item);
    let arr = groups.get(k);
    if (!arr) {
      arr = [];
      groups.set(k, arr);
      insertion.push(k);
    }
    arr.push(item);
  }
  const rankOf = (k: string): number => {
    const i = order.indexOf(k);
    return i === -1 ? order.length + insertion.indexOf(k) : i;
  };
  return insertion
    .slice()
    .sort((a, b) => rankOf(a) - rankOf(b))
    .map((k) => ({ key: k, items: groups.get(k)! }));
}

// Unique facet values present in the data, alphabetically sorted (drops empty values).
export function facetOptions<T>(items: T[], get: (item: T) => string): string[] {
  return [...new Set(items.map(get))].filter(Boolean).sort();
}

// A row matches when every active filter equals the row's value for that key AND the
// (lowercased) query is a substring of the row's search text. An empty filter value or
// empty query imposes no constraint. This mirrors the client island's predicate exactly.
export function matchesFilters(
  row: { search: string; facets: Record<string, string> },
  filters: Record<string, string>,
  query: string,
): boolean {
  for (const [k, v] of Object.entries(filters)) {
    if (v && row.facets[k] !== v) return false;
  }
  const q = query.trim().toLowerCase();
  if (q && !row.search.toLowerCase().includes(q)) return false;
  return true;
}
