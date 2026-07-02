import { describe, expect, it } from "vitest";
import {
  calendarEvents,
  electionDates,
  formatDate,
  generalElectionDate,
  upcomingEvents,
} from "./dates";

describe("election dates [E2.1]", () => {
  it("bakes all 50 states for the default cycle, sorted by name", () => {
    const rows = electionDates();
    expect(rows).toHaveLength(50);
    expect(rows[0].state_name).toBe("Alabama");
    expect(rows[rows.length - 1].state_name).toBe("Wyoming");
    for (const r of rows) {
      expect(r.cycle).toBe(2026);
      expect(r.primary).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(r.general).toBe("2026-11-03");
    }
  });

  it("exposes a single nationwide general election date", () => {
    expect(generalElectionDate()).toBe("2026-11-03");
  });

  it("flattens events chronologically with one general entry", () => {
    const events = calendarEvents();
    for (let i = 1; i < events.length; i++) {
      expect(events[i].date >= events[i - 1].date).toBe(true);
    }
    const generals = events.filter((e) => e.kind === "General");
    expect(generals).toHaveLength(1);
    expect(generals[0].state).toBe("US");
    // Texas has a March primary and a May runoff.
    expect(events.some((e) => e.state === "TX" && e.kind === "Primary")).toBe(true);
    expect(events.some((e) => e.state === "TX" && e.kind === "Runoff")).toBe(true);
  });

  it("returns only upcoming events from a fixed date, capped by limit", () => {
    const up = upcomingEvents(new Date("2026-07-02T00:00:00Z"), 3);
    expect(up).toHaveLength(3);
    for (const e of up) expect(e.date >= "2026-07-02").toBe(true);
    // Arizona's July 21 primary is the next event after July 2.
    expect(up[0]).toMatchObject({ state: "AZ", kind: "Primary", date: "2026-07-21" });
  });

  it("returns nothing upcoming once the cycle is over", () => {
    expect(upcomingEvents(new Date("2027-01-01T00:00:00Z"))).toHaveLength(0);
  });

  it("formats ISO dates without timezone drift", () => {
    expect(formatDate("2026-11-03")).toBe("Nov 3, 2026");
    expect(formatDate("2026-03-03")).toBe("Mar 3, 2026");
  });
});
