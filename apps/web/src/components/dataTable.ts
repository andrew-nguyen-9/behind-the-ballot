// Column model + cell helpers for <DataTable>. Plain .ts so the mapping logic is
// unit-testable without rendering Astro.

export interface Column {
  key: string;
  label: string;
  align?: "left" | "right" | "center";
}

/** Tailwind text-align utility for a column's `align` (defaults to left). */
export function alignClass(align?: Column["align"]): string {
  if (align === "right") return "text-right";
  if (align === "center") return "text-center";
  return "text-left";
}

/** Ordered cell strings for one row, following the column order. Missing keys render blank. */
export function rowCells(columns: Column[], row: Record<string, unknown>): string[] {
  return columns.map((c) => {
    const v = row[c.key];
    return v == null ? "" : String(v);
  });
}
