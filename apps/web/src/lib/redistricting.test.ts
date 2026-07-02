import { describe, expect, it } from "vitest";
import {
  REDISTRICTING,
  REDISTRICTING_SOURCE,
  STATUS_META,
  STATUS_ORDER,
  activeCases,
  activeStates,
  redistrictingMapData,
  redistrictingStates,
  statusCounts,
  type RedistrictingStatus,
} from "./redistricting";
import { STATE_CODES, STATE_NAMES } from "./usStates";

const STATUSES: RedistrictingStatus[] = ["settled", "litigation", "redrawn", "at-large"];

describe("redistricting dataset integrity", () => {
  it("carries a freshness stamp and a source binding [R14a,R5a]", () => {
    expect(REDISTRICTING.as_of).toMatch(/^\d{4}-\d{2}-\d{2}/);
    expect(REDISTRICTING.source).toBe(REDISTRICTING_SOURCE);
  });

  it("only uses postal codes and statuses that are known", () => {
    for (const s of REDISTRICTING.states) {
      expect(STATE_CODES).toContain(s.state);
      expect(STATUSES).toContain(s.status);
      expect(s.summary).toBeTruthy();
    }
  });
});

describe("redistrictingStates", () => {
  const states = redistrictingStates();

  it("resolves all 50 states, name-sorted", () => {
    expect(states).toHaveLength(50);
    const names = states.map((s) => s.name);
    expect([...names].sort((a, b) => a.localeCompare(b))).toEqual(names);
  });

  it("defaults an unlisted state to settled", () => {
    // Kansas is intentionally not in the curated dataset.
    const ks = states.find((s) => s.state === "KS");
    expect(ks?.status).toBe("settled");
    expect(ks?.cases).toEqual([]);
  });

  it("marks the six single-district states at-large", () => {
    const atLarge = states.filter((s) => s.status === "at-large").map((s) => s.state).sort();
    expect(atLarge).toEqual(["AK", "DE", "ND", "SD", "VT", "WY"]);
  });
});

describe("statusCounts", () => {
  it("partitions all 50 states across the buckets", () => {
    const counts = statusCounts();
    const total = STATUSES.reduce((n, st) => n + counts[st], 0);
    expect(total).toBe(50);
    expect(counts.redrawn).toBeGreaterThan(0);
    expect(counts.litigation).toBeGreaterThan(0);
  });
});

describe("redistrictingMapData", () => {
  const { fills } = redistrictingMapData();

  it("fills every state with a status colour + descriptive title", () => {
    expect(Object.keys(fills).sort()).toEqual([...STATE_CODES].sort());
    for (const code of STATE_CODES) {
      const f = fills[code];
      expect(f.fill).toBeTruthy();
      expect(f.title).toContain(STATE_NAMES[code]);
    }
  });

  it("gives redrawn/litigation states a grayscale texture overlay", () => {
    for (const s of redistrictingStates()) {
      const f = fills[s.state];
      if (s.status === "redrawn" || s.status === "litigation") {
        expect(f.overlay).toBe(STATUS_META[s.status].overlay);
        expect(f.overlay).toMatch(/^url\(#/);
      } else {
        expect(f.overlay).toBeUndefined();
      }
    }
  });

  it("names the active-case count in the title", () => {
    expect(fills.TX.title).toMatch(/active case/);
  });
});

describe("activeCases", () => {
  it("flattens exactly the curated cases, tagged with the state name", () => {
    const curatedCount = REDISTRICTING.states.reduce((n, s) => n + s.cases.length, 0);
    const cases = activeCases();
    expect(cases).toHaveLength(curatedCount);
    for (const c of cases) {
      expect(Object.values(STATE_NAMES)).toContain(c.state);
      expect(c.name).toBeTruthy();
      expect(c.court).toBeTruthy();
    }
  });
});

describe("activeStates", () => {
  it("lists only redrawn/litigation states, redrawn first", () => {
    const active = activeStates();
    expect(active.every((s) => s.status === "redrawn" || s.status === "litigation")).toBe(true);
    const rank = (st: RedistrictingStatus) => STATUS_ORDER.indexOf(st);
    for (let i = 1; i < active.length; i++) {
      expect(rank(active[i - 1].status)).toBeLessThanOrEqual(rank(active[i].status));
    }
  });
});
