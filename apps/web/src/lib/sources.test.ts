import { describe, expect, it } from "vitest";
import { SOURCES } from "./sources";

describe("sources contract", () => {
  it("lists every V1 source with required contract fields", () => {
    expect(SOURCES.length).toBeGreaterThanOrEqual(9);
    for (const s of SOURCES) {
      expect(s.label).toBeTruthy();
      expect(s.url).toMatch(/^https:\/\//);
      expect(s.license).toBeTruthy();
      expect(s.freshnessFloor).toBeTruthy();
    }
  });

  it("covers the core providers", () => {
    const providers = SOURCES.map((s) => s.provider).join(" ");
    for (const p of ["OpenFEC", "538", "Census ACS", "TIGER", "Voteview", "congress-legislators"]) {
      expect(providers).toContain(p);
    }
  });
});
