// Hemicycle (semicircle arc) seat layout for the House [Q6.4]. Pure build-time math →
// static SVG <circle>s, 0 JS. Seats sit in concentric semicircle rows within a half-annulus:
// the number of rows is the smallest that fits `seatCount` without overlap, seats are spread
// across rows proportional to each row's arc length, and each row is fanned evenly from the
// left (θ=π) to the right (θ=0) edge. Deterministic — same input, same output every build.

export interface ArcSeat {
  /** 0 = innermost row. */
  row: number;
  /** Angle in radians, π (far left) … 0 (far right). */
  angle: number;
  /** SVG x (origin top-left, padded). */
  x: number;
  /** SVG y (flat side of the arc at the bottom). */
  y: number;
}

export interface ArcLayout {
  /** Ordered left→right (angle desc), then inner→outer — ready for contiguous party fills. */
  seats: ArcSeat[];
  rows: number;
  seatRadius: number;
  width: number;
  height: number;
}

export interface ArcOptions {
  /** Outer radius in SVG units (drives the whole coordinate scale). Default 100. */
  outerRadius?: number;
  /** Inner radius as a fraction of the outer (the empty "well"). Default 0.4. */
  innerRatio?: number;
  /** Seat circle radius as a fraction of the radial row pitch. Default 0.4 (<0.5 ⇒ gaps). */
  seatRatio?: number;
  /** Blank margin around the arc. Default = seatRadius (circles never clip the viewBox). */
  padding?: number;
}

// Seats that fit in each row for a given row count: angular step ≥ pitch ⇒ arc spacing ≥ the
// radial pitch, so packing is uniform in both directions and circles (radius < pitch/2) never
// touch. Row i sits at the mid-radius of its ring.
function rowCapacities(rows: number, innerRadius: number, band: number): number[] {
  const pitch = band / rows;
  const caps: number[] = [];
  for (let i = 0; i < rows; i++) {
    const r = innerRadius + (i + 0.5) * pitch;
    caps.push(Math.max(1, Math.floor(1 + (Math.PI * r) / pitch)));
  }
  return caps;
}

export function houseArcLayout(seatCount: number, options: ArcOptions = {}): ArcLayout {
  const outerRadius = options.outerRadius ?? 100;
  const innerRatio = options.innerRatio ?? 0.4;
  const seatRatio = options.seatRatio ?? 0.4;

  if (seatCount <= 0) {
    return { seats: [], rows: 0, seatRadius: 0, width: 0, height: 0 };
  }

  const innerRadius = outerRadius * innerRatio;
  const band = outerRadius - innerRadius;

  // Smallest row count whose total capacity holds every seat.
  let rows = 1;
  while (rowCapacities(rows, innerRadius, band).reduce((a, b) => a + b, 0) < seatCount) rows++;

  const pitch = band / rows;
  const seatRadius = pitch * seatRatio;
  const caps = rowCapacities(rows, innerRadius, band);
  const totalCap = caps.reduce((a, b) => a + b, 0);

  // Distribute seats proportional to each row's capacity (outer rows hold more), largest-
  // remainder rounding, never exceeding a row's capacity.
  const exact = caps.map((c) => (seatCount * c) / totalCap);
  const alloc = exact.map((e) => Math.floor(e));
  let remaining = seatCount - alloc.reduce((a, b) => a + b, 0);
  const byRemainder = exact
    .map((e, i) => ({ i, frac: e - Math.floor(e) }))
    .sort((a, b) => b.frac - a.frac);
  for (const { i } of byRemainder) {
    if (remaining <= 0) break;
    if (alloc[i] < caps[i]) {
      alloc[i]++;
      remaining--;
    }
  }
  // Rounding can leave a seat unplaced; spill it into any row with headroom (inner→outer).
  for (let i = 0; remaining > 0 && i < rows; i++) {
    while (remaining > 0 && alloc[i] < caps[i]) {
      alloc[i]++;
      remaining--;
    }
  }

  const seats: ArcSeat[] = [];
  for (let row = 0; row < rows; row++) {
    const m = alloc[row];
    if (m === 0) continue;
    const r = innerRadius + (row + 0.5) * pitch;
    for (let j = 0; j < m; j++) {
      const angle = m === 1 ? Math.PI / 2 : Math.PI - (j * Math.PI) / (m - 1);
      seats.push({
        row,
        angle,
        x: outerRadius + r * Math.cos(angle),
        y: outerRadius - r * Math.sin(angle),
      });
    }
  }

  // Left→right for contiguous party wedges (Dems left, Reps right), inner→outer on ties.
  seats.sort((a, b) => b.angle - a.angle || a.row - b.row);

  const padding = options.padding ?? seatRadius;
  for (const s of seats) {
    s.x += padding;
    s.y += padding;
  }

  return {
    seats,
    rows,
    seatRadius,
    width: outerRadius * 2 + padding * 2,
    height: outerRadius + padding * 2,
  };
}

// Zip an ordered seat list onto party seat-counts, in order. With seatCount === Σ counts every
// seat gets a party; any surplus seats fall through as "" (rendered as an uncolored/vacant dot).
export function assignSeatParties(
  seats: ArcSeat[],
  byParty: { party: string; count: number }[],
): (ArcSeat & { party: string })[] {
  const parties: string[] = [];
  for (const { party, count } of byParty) {
    for (let i = 0; i < count; i++) parties.push(party);
  }
  return seats.map((s, i) => ({ ...s, party: parties[i] ?? "" }));
}
