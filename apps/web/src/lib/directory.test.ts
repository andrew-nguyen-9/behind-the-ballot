import { describe, expect, it } from "vitest";
import { facetOptions, groupBy, matchesFilters } from "./directory";

interface Row {
  id: string;
  office: string;
  state: string;
  status: string;
}
const rows: Row[] = [
  { id: "a", office: "house", state: "TX", status: "primary" },
  { id: "b", office: "senate", state: "TX", status: "general" },
  { id: "c", office: "house", state: "CA", status: "general" },
  { id: "d", office: "governor", state: "CA", status: "upcoming" },
];

describe("groupBy", () => {
  it("groups by a key and honors the explicit order", () => {
    const groups = groupBy(rows, (r) => r.office, ["senate", "house", "governor"]);
    expect(groups.map((g) => g.key)).toEqual(["senate", "house", "governor"]);
    expect(groups.find((g) => g.key === "house")!.items.map((r) => r.id)).toEqual(["a", "c"]);
  });

  it("places keys not in `order` after the known ones, in first-seen order", () => {
    const groups = groupBy(rows, (r) => r.state, ["CA"]);
    expect(groups.map((g) => g.key)).toEqual(["CA", "TX"]);
  });

  it("omits empty groups (only present keys appear)", () => {
    const groups = groupBy(rows, (r) => r.status, ["called", "general"]);
    expect(groups.map((g) => g.key)).not.toContain("called");
    expect(groups.map((g) => g.key)).toContain("general");
  });
});

describe("facetOptions", () => {
  it("returns unique values sorted alphabetically", () => {
    expect(facetOptions(rows, (r) => r.state)).toEqual(["CA", "TX"]);
    expect(facetOptions(rows, (r) => r.status)).toEqual(["general", "primary", "upcoming"]);
  });

  it("drops empty values", () => {
    expect(facetOptions([{ x: "" }, { x: "y" }], (r) => r.x)).toEqual(["y"]);
  });
});

describe("matchesFilters", () => {
  const row = { search: "jane doe senate", facets: { state: "TX", status: "general" } };

  it("passes with no active filters and no query", () => {
    expect(matchesFilters(row, {}, "")).toBe(true);
    expect(matchesFilters(row, { state: "" }, "")).toBe(true);
  });

  it("requires every active facet to match", () => {
    expect(matchesFilters(row, { state: "TX" }, "")).toBe(true);
    expect(matchesFilters(row, { state: "CA" }, "")).toBe(false);
    expect(matchesFilters(row, { state: "TX", status: "primary" }, "")).toBe(false);
  });

  it("matches the query as a case-insensitive substring of search text", () => {
    expect(matchesFilters(row, {}, "JANE")).toBe(true);
    expect(matchesFilters(row, {}, "  doe ")).toBe(true);
    expect(matchesFilters(row, {}, "smith")).toBe(false);
  });

  it("combines facets and query (both must hold)", () => {
    expect(matchesFilters(row, { state: "TX" }, "senate")).toBe(true);
    expect(matchesFilters(row, { state: "TX" }, "house")).toBe(false);
  });
});
