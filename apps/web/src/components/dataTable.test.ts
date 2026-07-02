import { describe, expect, it } from "vitest";
import { alignClass, rowCells, type Column } from "./dataTable";

describe("alignClass", () => {
  it("maps align to the text-align utility", () => {
    expect(alignClass("right")).toBe("text-right");
    expect(alignClass("center")).toBe("text-center");
    expect(alignClass("left")).toBe("text-left");
    expect(alignClass()).toBe("text-left");
  });
});

describe("rowCells", () => {
  const cols: Column[] = [
    { key: "state", label: "State" },
    { key: "gap", label: "Gap", align: "right" },
  ];
  it("returns cells in column order", () => {
    expect(rowCells(cols, { state: "MI", gap: 3 })).toEqual(["MI", "3"]);
  });
  it("renders blank for missing / null keys", () => {
    expect(rowCells(cols, { state: "OH" })).toEqual(["OH", ""]);
    expect(rowCells(cols, { state: "OH", gap: null })).toEqual(["OH", ""]);
  });
});
