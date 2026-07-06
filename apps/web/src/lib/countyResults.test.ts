import { describe, expect, it } from "vitest";
import {
  countyCertificationLabel,
  countyMapData,
  countyMargin,
  countyReportingLabel,
  countyResultsForState,
  leadingCandidate,
  marginFill,
  statewideTotals,
  type StateCountyResults,
} from "./countyResults";
// Sample AZ county rollup [E-R9] — the shape aggregate_to_county (E-F2) bakes on election night.
// Lives OUTSIDE src/data/county-results (the production glob) so it proves the map + table path
// end to end WITHOUT committing invented vote totals to a live state (repo honest-empty rule).
import azFixture from "./__fixtures__/countyResults.sample.json";

const az = azFixture as StateCountyResults;
const race = az.races[0];
// County names by FIPS (a slice of az-counties.json), enough to drive the map builder.
const names: Record<string, string> = {
  "04013": "Maricopa",
  "04021": "Pinal",
  "04015": "Mohave",
};

describe("countyResults honest-empty", () => {
  it("returns null when no county rollup is baked for a state (default state of /results)", () => {
    expect(countyResultsForState("ZZ")).toBeNull();
    expect(countyResultsForState("AZ")).toBeNull(); // no committed production file yet
  });
});

describe("countyResults labels (reuse race-page copy)", () => {
  it("labels provisional vs certified identically to the race page", () => {
    expect(countyCertificationLabel(az)).toBe("Unofficial — provisional");
    expect(countyCertificationLabel({ is_certified: true })).toBe("Certified");
  });

  it("is honest about missing precinct reporting", () => {
    expect(countyReportingLabel(36.7)).toBe("36.7% of precincts reporting");
    expect(countyReportingLabel(null)).toBe("Precincts reporting not reported");
  });
});

describe("countyResults leader + margin", () => {
  it("picks the vote-leading candidate, none when a county has zero counted votes", () => {
    expect(leadingCandidate(race.counties[0])!.candidate).toBe("Jane Doe"); // Maricopa
    expect(leadingCandidate(race.counties[1])!.candidate).toBe("John Roe"); // Pinal
    expect(leadingCandidate(race.counties[2])).toBeNull(); // Mohave, 0/0 — no fabricated leader
  });

  it("computes the two-way margin, null when pct is missing", () => {
    expect(countyMargin(race.counties[0])).toBeCloseTo(10.4, 5); // 55.2 - 44.8
    expect(countyMargin(race.counties[1])).toBeCloseTo(16.2, 5); // 58.1 - 41.9
    expect(countyMargin(race.counties[2])).toBeNull();
  });

  it("scales fill alpha by margin and falls back to grey for third parties", () => {
    const strong = marginFill("D", 40);
    const faint = marginFill("D", 0);
    expect(strong).toBe("rgba(44, 111, 179, 0.95)");
    expect(faint).toBe("rgba(44, 111, 179, 0.30)");
    expect(marginFill("L", 10)).toContain("139, 146, 154"); // neutral grey, not a party hue
  });
});

describe("countyMapData (map + accessible twin from real-shaped data)", () => {
  const { fills, rows } = countyMapData(race, names);

  it("fills only counties with a leader — the 0/0 county stays empty (honest)", () => {
    expect(Object.keys(fills).sort()).toEqual(["04013", "04021"]);
    expect(fills["04015"]).toBeUndefined();
    // Leader hue: Maricopa Dem-blue, Pinal Rep-red.
    expect(fills["04013"].fill).toContain("44, 111, 179");
    expect(fills["04021"].fill).toContain("193, 59, 59");
    // Dem leader = solid pattern (no overlay); Rep leader = hatch overlay for grayscale a11y.
    expect(fills["04013"].overlay).toBeUndefined();
    expect(fills["04021"].overlay).toBe("url(#pf-hatch)");
    expect(fills["04013"].title).toContain("Jane Doe leads");
  });

  it("emits one accessible table row per county, alpha-sorted, honest about no-leader", () => {
    expect(rows.map((r) => r.county)).toEqual(["Maricopa", "Mohave", "Pinal"]);
    const mohave = rows.find((r) => r.county === "Mohave")!;
    expect(mohave.leader).toBe("No leader yet");
    expect(mohave.margin).toBe("—");
    expect(mohave.reporting).toBe("Not reported");
    expect(rows.find((r) => r.county === "Maricopa")!.leader).toBe("Jane Doe (Democrat)");
  });
});

describe("statewideTotals", () => {
  it("sums each candidate across reported counties and re-derives the share", () => {
    const totals = statewideTotals(race);
    // Jane 240100+29700+0 = 269800; John 194900+41200+0 = 236100; total 505900.
    expect(totals[0]).toMatchObject({ candidate: "Jane Doe", votes: 269800 });
    expect(totals[1]).toMatchObject({ candidate: "John Roe", votes: 236100 });
    expect(totals[0].pct).toBeCloseTo(53.3, 1);
    expect(totals[0].votes + totals[1].votes).toBe(505900);
  });
});
