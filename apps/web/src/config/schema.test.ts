import { describe, expect, it } from "vitest";
import { parseUnit } from "./schema";
import example from "./races/us-senate-2026-OH.json";

describe("UnitConfig", () => {
  it("accepts the seeded example race config", () => {
    expect(parseUnit(example).id).toBe("us-senate-2026-OH");
  });

  it("rejects a house race with no district", () => {
    expect(() =>
      parseUnit({ kind: "race", id: "x", cycle: 2026, title: "x", office: "house", state: "OH" }),
    ).toThrow(/district/);
  });

  it("rejects a senate race with a district", () => {
    expect(() =>
      parseUnit({
        kind: "race", id: "x", cycle: 2026, title: "x",
        office: "senate", state: "OH", senateClass: 3, district: 5,
      }),
    ).toThrow(/district/);
  });

  it("rejects a bad state code", () => {
    expect(() =>
      parseUnit({ kind: "race", id: "x", cycle: 2026, title: "x", office: "governor", state: "ohio" }),
    ).toThrow();
  });
});
