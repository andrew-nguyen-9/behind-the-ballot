import { describe, expect, it } from "vitest";
import { assignSeatParties, houseArcLayout, type ArcSeat } from "./houseArc";

const minPairDistance = (seats: ArcSeat[]): number => {
  let min = Infinity;
  for (let i = 0; i < seats.length; i++) {
    for (let j = i + 1; j < seats.length; j++) {
      const dx = seats[i].x - seats[j].x;
      const dy = seats[i].y - seats[j].y;
      const d = Math.hypot(dx, dy);
      if (d < min) min = d;
    }
  }
  return min;
};

describe("houseArcLayout", () => {
  it("lays out exactly 435 seats", () => {
    expect(houseArcLayout(435).seats.length).toBe(435);
  });

  it("places 435 seats with no overlap (centers ≥ one diameter apart)", () => {
    const layout = houseArcLayout(435);
    // A tiny epsilon guards against floating-point noise at the touching boundary.
    expect(minPairDistance(layout.seats)).toBeGreaterThanOrEqual(2 * layout.seatRadius - 1e-9);
  });

  it("honors arbitrary seat counts (no overlap) — House and Senate sizes", () => {
    for (const n of [1, 2, 10, 100, 218, 435, 437, 538]) {
      const layout = houseArcLayout(n);
      expect(layout.seats.length).toBe(n);
      if (n > 1) {
        expect(minPairDistance(layout.seats)).toBeGreaterThanOrEqual(2 * layout.seatRadius - 1e-9);
      }
    }
  });

  it("keeps every seat (plus its radius) inside the viewBox", () => {
    const layout = houseArcLayout(435);
    for (const s of layout.seats) {
      expect(s.x - layout.seatRadius).toBeGreaterThanOrEqual(-1e-9);
      expect(s.y - layout.seatRadius).toBeGreaterThanOrEqual(-1e-9);
      expect(s.x + layout.seatRadius).toBeLessThanOrEqual(layout.width + 1e-9);
      expect(s.y + layout.seatRadius).toBeLessThanOrEqual(layout.height + 1e-9);
    }
  });

  it("is a hemicycle — seats span the flat bottom half only", () => {
    const layout = houseArcLayout(435);
    for (const s of layout.seats) {
      expect(s.angle).toBeGreaterThanOrEqual(-1e-9);
      expect(s.angle).toBeLessThanOrEqual(Math.PI + 1e-9);
    }
    // Left edge (θ≈π) sits far left, right edge (θ≈0) sits far right.
    const sorted = [...layout.seats];
    expect(sorted[0].x).toBeLessThan(sorted[sorted.length - 1].x);
  });

  it("is deterministic", () => {
    expect(houseArcLayout(435)).toEqual(houseArcLayout(435));
  });

  it("returns an empty layout for zero seats", () => {
    expect(houseArcLayout(0).seats).toEqual([]);
  });
});

describe("assignSeatParties", () => {
  it("assigns parties in order, one per seat, matching the counts", () => {
    const layout = houseArcLayout(435);
    const byParty = [
      { party: "D", count: 213 },
      { party: "R", count: 220 },
      { party: "I", count: 2 },
    ];
    const seats = assignSeatParties(layout.seats, byParty);
    const counts = seats.reduce<Record<string, number>>((acc, s) => {
      acc[s.party] = (acc[s.party] ?? 0) + 1;
      return acc;
    }, {});
    expect(counts).toEqual({ D: 213, R: 220, I: 2 });
    // Leftmost seats are Democrats, rightmost are the independents (fill is left→right).
    expect(seats[0].party).toBe("D");
    expect(seats[seats.length - 1].party).toBe("I");
  });

  it("leaves surplus seats unassigned rather than throwing", () => {
    const layout = houseArcLayout(10);
    const seats = assignSeatParties(layout.seats, [{ party: "D", count: 4 }]);
    expect(seats.filter((s) => s.party === "").length).toBe(6);
  });
});
