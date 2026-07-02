// Election calendar [E2.1] — per-state primary / runoff / general dates, baked per cycle by
// export_web (`src/data/dates/<cycle>.json`) from the curated NCSL-sourced table. Read at build,
// 0-JS. Dates are plain ISO strings (YYYY-MM-DD); every comparison is string-lexicographic so
// there is no timezone drift.
const mods = import.meta.glob("../data/dates/*.json", { eager: true });

export interface ElectionDate {
  cycle: number;
  state: string; // USPS postal
  state_name: string;
  primary: string; // ISO date
  runoff: string | null;
  general: string; // ISO date
  note: string | null;
}

export const DEFAULT_CYCLE = 2026;

// One state-per-row calendar for a cycle, sorted by state name. Empty if the cycle isn't baked.
export function electionDates(cycle: number = DEFAULT_CYCLE): ElectionDate[] {
  const m = mods[`../data/dates/${cycle}.json`] as { default: ElectionDate[] } | undefined;
  return m ? [...m.default].sort((a, b) => a.state_name.localeCompare(b.state_name)) : [];
}

export type EventKind = "Primary" | "Runoff" | "General";

export interface CalendarEvent {
  date: string; // ISO date
  state: string; // "US" for the nationwide general
  state_name: string;
  kind: EventKind;
}

// Flatten the per-state rows into individual dated events, sorted chronologically. The general
// election is a single nationwide day, so it appears ONCE (not one row per state).
export function calendarEvents(cycle: number = DEFAULT_CYCLE): CalendarEvent[] {
  const rows = electionDates(cycle);
  const out: CalendarEvent[] = [];
  for (const r of rows) {
    out.push({ date: r.primary, state: r.state, state_name: r.state_name, kind: "Primary" });
    if (r.runoff)
      out.push({ date: r.runoff, state: r.state, state_name: r.state_name, kind: "Runoff" });
  }
  const general = rows[0]?.general;
  if (general) out.push({ date: general, state: "US", state_name: "All states", kind: "General" });
  return out.sort((a, b) => a.date.localeCompare(b.date) || a.state_name.localeCompare(b.state_name));
}

// The nationwide general election date for a cycle (uniform across states), or null.
export function generalElectionDate(cycle: number = DEFAULT_CYCLE): string | null {
  return electionDates(cycle)[0]?.general ?? null;
}

// The next `limit` events on or after `from` (default: today). Drives the home teaser.
export function upcomingEvents(
  from: Date = new Date(),
  limit = 5,
  cycle: number = DEFAULT_CYCLE,
): CalendarEvent[] {
  const iso = from.toISOString().slice(0, 10);
  return calendarEvents(cycle)
    .filter((e) => e.date >= iso)
    .slice(0, limit);
}

// ISO date -> "Nov 3, 2026". Parsed as UTC to avoid off-by-one from the local timezone.
export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
