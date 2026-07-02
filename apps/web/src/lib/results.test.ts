import { describe, expect, it } from "vitest";
import {
  certificationLabel,
  fmtAsOf,
  fmtVotes,
  reportingLabel,
  resultsForRace,
  type RaceResults,
} from "./results";
// Sample general-election record [E3.3] — the shape a live SoS feed bakes on election night.
// Lives OUTSIDE src/data/results (the production glob) so it proves the display path end to
// end without committing invented vote totals to a real race page (repo honest-empty rule).
import generalFixture from "./__fixtures__/generalResults.sample.json";

const base: RaceResults = {
  race_id: "us-senate-2026-OH",
  election_type: "primary",
  as_of: "2026-08-04T23:30:00+00:00",
  is_certified: false,
  pct_reporting: 62,
  is_called: false,
  called_by: null,
  call_source: null,
  source_url: "https://sos.oh/",
  candidates: [{ candidate: "Jane Doe", party: "D", votes: 1234567, pct: 60 }],
};

describe("results", () => {
  it("formats vote counts with thousands separators", () => {
    expect(fmtVotes(1234567)).toBe("1,234,567");
    expect(fmtVotes(0)).toBe("0");
  });

  it("labels provisional vs certified", () => {
    expect(certificationLabel(base)).toBe("Unofficial — provisional");
    expect(certificationLabel({ ...base, is_certified: true })).toBe("Certified");
  });

  it("is honest about missing precinct reporting", () => {
    expect(reportingLabel(base)).toBe("62% of precincts reporting");
    expect(reportingLabel({ ...base, pct_reporting: null })).toBe(
      "Precincts reporting not reported",
    );
  });

  it("stamps the as-of time in UTC", () => {
    expect(fmtAsOf("2026-08-04T23:30:00+00:00")).toBe("Aug 4, 2026, 11:30 PM UTC");
  });

  it("returns null when no results artifact is baked for a race (honest-empty)", () => {
    expect(resultsForRace("no-such-race-9999")).toBeNull();
  });
});

// E3.3: the display layer is election-type-generic — a general-election fixture renders
// through the same read shape + formatters the race page's Results section consumes.
describe("general-election readiness (fixture end-to-end)", () => {
  const g = generalFixture as RaceResults;

  it("carries a general-election record with candidates sorted by votes desc", () => {
    expect(g.election_type).toBe("general");
    const votes = g.candidates.map((c) => c.votes);
    expect(votes).toEqual([...votes].sort((a, b) => b - a));
    expect(fmtVotes(g.candidates[0].votes)).toBe("1,820,344");
  });

  it("renders provisional-until-certified + reporting + as-of exactly as the page does", () => {
    expect(certificationLabel(g)).toBe("Unofficial — provisional");
    expect(certificationLabel({ ...g, is_certified: true })).toBe("Certified");
    expect(reportingLabel(g)).toBe("78% of precincts reporting");
    expect(fmtAsOf(g.as_of)).toBe("Nov 3, 2026, 11:30 PM UTC");
  });

  it("surfaces the borrowed Wikipedia race call", () => {
    expect(g.is_called).toBe(true);
    expect(g.called_by).toBe("Jane Doe");
    expect(g.call_source).toBe("Wikipedia");
  });
});
