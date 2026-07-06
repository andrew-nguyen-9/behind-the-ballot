// Build-time county geometry bake [E-F2] — mirrors gen-us-states.mjs, one state at a time.
// us-atlas counties TopoJSON -> static per-county SVG path `d` strings, committed as JSON so
// E-R9's CountyMap ships a 0-JS inline choropleth (no runtime topojson/d3). Uses the
// PRE-PROJECTED `counties-albers-10m` bundle (albers-usa baked into pixel coords on the same
// 975x610 canvas as the states bundle), so geoPath runs with a null projection. The viewBox is
// cropped to the state's own bounds so the county map fills its frame. Run once and commit the
// output; re-run only to refresh geometry or add a state:
//   node scripts/gen-us-counties.mjs
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { feature } from "topojson-client";
import { geoPath } from "d3-geo";
import topo from "us-atlas/counties-albers-10m.json" with { type: "json" };

const here = dirname(fileURLToPath(import.meta.url));

// Framework-shaped: state postal -> 2-digit state FIPS prefix. AZ is the only entry now; add a
// row (and re-run) to bake another state's counties. County FIPS are 5 digits = state prefix +
// 3-digit county code (e.g. AZ "04" -> Maricopa "04013").
const STATES = {
  AZ: "04",
};

const path = geoPath(null); // identity: coordinates are already albers-usa pixels
const counties = feature(topo, topo.objects.counties);

for (const [postal, prefix] of Object.entries(STATES)) {
  const feats = counties.features.filter((f) =>
    String(f.id).padStart(5, "0").startsWith(prefix),
  );
  if (!feats.length) throw new Error(`No county geometry for state ${postal} (FIPS ${prefix})`);

  // Crop the viewBox to this state's own bounds so the map fills its frame (the path `d`s stay
  // in the shared full-US canvas; viewBox is just the window onto it). geoPath.bounds returns
  // [[x0, y0], [x1, y1]] in projected pixel space.
  const [[x0, y0], [x1, y1]] = path.bounds({ type: "FeatureCollection", features: feats });
  const pad = 4;
  const vx = Math.floor(x0 - pad);
  const vy = Math.floor(y0 - pad);
  const vw = Math.ceil(x1 - x0 + pad * 2);
  const vh = Math.ceil(y1 - y0 + pad * 2);
  const viewBox = `${vx} ${vy} ${vw} ${vh}`;

  const out = { state: postal, viewBox, counties: {} };
  for (const f of feats) {
    const fips = String(f.id).padStart(5, "0");
    const d = path(f);
    if (!d) throw new Error(`Empty geometry for county ${fips} (${postal})`);
    out.counties[fips] = { name: f.properties?.name ?? null, d };
  }

  const dest = resolve(here, `../src/data/geo/${postal.toLowerCase()}-counties.json`);
  writeFileSync(dest, JSON.stringify(out) + "\n");
  console.log(
    `Wrote ${Object.keys(out.counties).length} ${postal} counties -> ${dest} (viewBox ${viewBox})`,
  );
}
