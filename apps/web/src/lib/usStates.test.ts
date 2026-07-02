import { describe, expect, it } from "vitest";
import {
  MAP_COLORS,
  STATE_CODES,
  describeDelegation,
  seatColor,
  senateMapData,
} from "./usStates";
import type { Member } from "./members";

const sen = (over: Partial<Member>): Member => ({
  bioguide_id: "X000000",
  name: "Test Senator",
  party: "D",
  state: "ZZ",
  chamber: "sen",
  district: null,
  nominate_dim1: null,
  ...over,
});

describe("seatColor", () => {
  it("maps the major parties to their tokens", () => {
    expect(seatColor(sen({ party: "D" }))).toBe(MAP_COLORS.D);
    expect(seatColor(sen({ party: "R" }))).toBe(MAP_COLORS.R);
  });

  it("tints a caucusing independent grey toward its caucus [Q6.3]", () => {
    // Sanders (VT) + King (ME) caucus with the Democrats -> blue-tinted grey.
    expect(seatColor(sen({ party: "I", bioguide_id: "S000033" }))).toBe(MAP_COLORS.indDem);
    expect(seatColor(sen({ party: "I", bioguide_id: "K000383" }))).toBe(MAP_COLORS.indDem);
  });

  it("uses neutral grey for an independent caucusing with neither", () => {
    expect(seatColor(sen({ party: "I", bioguide_id: "UNMAPPED" }))).toBe(MAP_COLORS.indNeutral);
  });
});

describe("describeDelegation", () => {
  it("summarises a same-party delegation", () => {
    expect(describeDelegation([sen({ party: "D" }), sen({ party: "D" })])).toBe("2 Democrat");
  });
  it("orders a split D, R", () => {
    expect(describeDelegation([sen({ party: "R" }), sen({ party: "D" })])).toBe(
      "1 Democrat, 1 Republican",
    );
  });
  it("labels independents", () => {
    expect(describeDelegation([sen({ party: "R" }), sen({ party: "I" })])).toBe(
      "1 Republican, 1 Independent",
    );
  });
  it("handles an empty delegation", () => {
    expect(describeDelegation([])).toBe("No sitting senators");
  });
});

describe("senateMapData", () => {
  const { fills, stripes, rows } = senateMapData();

  it("produces a fill + table row for every state", () => {
    expect(rows).toHaveLength(50);
    for (const code of STATE_CODES) {
      expect(fills[code]).toBeDefined();
      expect(fills[code].title).toContain(":");
    }
  });

  it("fills a solid delegation with the party colour + a texture overlay for non-Dem", () => {
    // WY = 2 Republicans (solid red, hatch overlay); CA = 2 Democrats (solid blue, no overlay).
    expect(fills.WY.fill).toBe(MAP_COLORS.R);
    expect(fills.WY.overlay).toBe("url(#pf-hatch)");
    expect(fills.CA.fill).toBe(MAP_COLORS.D);
    expect(fills.CA.overlay).toBeUndefined(); // Dem = solid = no overlay
  });

  it("stripes a split delegation and registers the pattern [Q6.2]", () => {
    // WI + PA are D/R splits -> a url(#stripe-…) fill, no overlay.
    expect(fills.WI.fill).toMatch(/^url\(#stripe-/);
    expect(fills.WI.overlay).toBeUndefined();
    const drStripe = fills.WI.fill;
    expect(fills.PA.fill).toBe(drStripe); // same colour pair -> deduped to one pattern id
    expect(stripes.some((s) => `url(#${s.id})` === drStripe)).toBe(true);
  });

  it("stripes an independent split (ME = R + independent) [Q6.2/Q6.3]", () => {
    // ME = Collins (R) + King (I, caucus D) -> two different seat colours -> stripes.
    expect(fills.ME.fill).toMatch(/^url\(#stripe-/);
    expect(fills.ME.title).toContain("Maine");
  });

  it("keeps every stripe pattern referenced by at least one state", () => {
    const used = new Set(Object.values(fills).map((f) => f.fill));
    for (const s of stripes) expect(used.has(`url(#${s.id})`)).toBe(true);
  });
});
