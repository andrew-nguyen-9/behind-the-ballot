import { describe, expect, it } from "vitest";
import {
  certificationLabel,
  fmtAsOf,
  fmtVotes,
  reportingLabel,
  resultsForRace,
  type RaceResults,
} from "./results";

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
