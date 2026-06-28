// District geometry for the race page. ponytail: an inline SVG of the district boundary
// (0 JS) renders the shape now; the sanctioned MapLibre + PMTiles interactive map [P8a]
// is the upgrade once R2 hosting is provisioned (it needs tiles in R2). Geometry is
// versioned by `as_of` [L547].
const mods = import.meta.glob("../data/districts/*.json", { eager: true });

export interface DistrictShape {
  geoid: string;
  as_of: string;
  ring: [number, number][]; // [lon, lat] closed ring
}

export function districtShape(raceId: string): DistrictShape | null {
  const m = mods[`../data/districts/${raceId}.json`] as { default: DistrictShape } | undefined;
  return m ? m.default : null;
}

/** Project a lon/lat ring into an SVG path + viewBox of the given pixel size.
 * Equirectangular fit-to-bounds; y flipped (geo lat up -> SVG y down). */
export function ringToSvg(
  ring: [number, number][],
  size = 240,
  pad = 8,
): { d: string; viewBox: string } {
  if (ring.length < 3) throw new Error("ring needs >= 3 points");
  const lons = ring.map((p) => p[0]);
  const lats = ring.map((p) => p[1]);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const w = maxLon - minLon || 1;
  const h = maxLat - minLat || 1;
  const scale = (size - 2 * pad) / Math.max(w, h);
  const project = ([lon, lat]: [number, number]): [number, number] => [
    pad + (lon - minLon) * scale,
    pad + (maxLat - lat) * scale, // flip y
  ];
  const d =
    ring
      .map((p, i) => {
        const [x, y] = project(p);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ") + " Z";
  return { d, viewBox: `0 0 ${size} ${size}` };
}
