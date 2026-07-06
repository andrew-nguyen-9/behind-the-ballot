import { describe, expect, it } from "vitest";
import {
  compareCells,
  filterRowIndices,
  nextSort,
  parseNumeric,
  sortIndices,
} from "./tableFilter";

const rows = [
  ["Ohio", "R +2.1"],
  ["Maine", "D +5.4"],
  ["Arizona", "D +0.3"],
];

describe("filterRowIndices", () => {
  it("returns every row for an empty/whitespace query", () => {
    expect(filterRowIndices(rows, "")).toEqual([0, 1, 2]);
    expect(filterRowIndices(rows, "   ")).toEqual([0, 1, 2]);
  });

  it("matches any cell, case-insensitively", () => {
    expect(filterRowIndices(rows, "maine")).toEqual([1]);
    expect(filterRowIndices(rows, "d +")).toEqual([1, 2]);
  });

  it("returns nothing when no cell matches", () => {
    expect(filterRowIndices(rows, "texas")).toEqual([]);
  });
});

describe("parseNumeric", () => {
  it("pulls a signed decimal out of decorated cells", () => {
    expect(parseNumeric("+3.2 pts")).toBe(3.2);
    expect(parseNumeric("R -1.5")).toBe(-1.5);
    expect(parseNumeric("$1,200")).toBe(1200);
  });
  it("returns null for non-numeric cells", () => {
    expect(parseNumeric("Even")).toBeNull();
    expect(parseNumeric("")).toBeNull();
  });
});

describe("compareCells", () => {
  it("orders numeric cells by value", () => {
    expect(compareCells("D +0.3", "D +5.4")).toBeLessThan(0);
  });
  it("sorts blanks last", () => {
    expect(compareCells("", "x")).toBeGreaterThan(0);
    expect(compareCells("x", "")).toBeLessThan(0);
  });
  it("falls back to locale compare for text", () => {
    expect(compareCells("Arizona", "Ohio")).toBeLessThan(0);
  });
});

describe("sortIndices", () => {
  it("sorts ascending by a text column without mutating input", () => {
    const before = structuredClone(rows);
    expect(sortIndices(rows, 0, "asc")).toEqual([2, 1, 0]); // Arizona, Maine, Ohio
    expect(rows).toEqual(before);
  });
  it("sorts descending by a numeric column", () => {
    expect(sortIndices(rows, 1, "desc")).toEqual([1, 0, 2]); // 5.4, 2.1, 0.3
  });
  it("is stable for equal cells", () => {
    const tie = [["a", "1"], ["b", "1"], ["c", "1"]];
    expect(sortIndices(tie, 1, "asc")).toEqual([0, 1, 2]);
  });
});

describe("nextSort", () => {
  it("starts a fresh column ascending", () => {
    expect(nextSort(null, 1)).toEqual({ col: 1, dir: "asc" });
    expect(nextSort({ col: 0, dir: "desc" }, 1)).toEqual({ col: 1, dir: "asc" });
  });
  it("cycles the active column asc → desc → none", () => {
    expect(nextSort({ col: 1, dir: "asc" }, 1)).toEqual({ col: 1, dir: "desc" });
    expect(nextSort({ col: 1, dir: "desc" }, 1)).toBeNull();
  });
});
