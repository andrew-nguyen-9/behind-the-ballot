import { describe, expect, it } from "vitest";
import { parseUnit } from "./schema";
import example from "./races/us-senate-2026-TX.json";
import houseExample from "./races/us-house-2026-PA-07.json";
import govExample from "./races/us-governor-2026-PA.json";

describe("UnitConfig", () => {
  it("accepts a real generated race config", () => {
    expect(parseUnit(example).id).toBe("us-senate-2026-TX");
  });

  it("accepts a real generated House config (house discriminant + district)", () => {
    const u = parseUnit(houseExample);
    expect(u.kind === "race" && u.office).toBe("house");
    expect(u.kind === "race" && u.district).toBe(7);
  });

  it("accepts a real generated Governor config (governor discriminant, no district/class)", () => {
    const u = parseUnit(govExample);
    expect(u.kind === "race" && u.office).toBe("governor");
    expect(u.kind === "race" && u.district).toBeNull();
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
