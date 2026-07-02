// Build-time geometry bake [E2.3, L6a]: TIGER congressional-district boundaries -> per-race
// `DistrictShape` JSON ({ geoid, as_of, ring }) under src/data/districts/, one file per House
// race. lib/geo.ts `districtShape(raceId)` reads these; the race page and the /house per-state
// district map render them via `ringToSvg` (0-JS static SVG). Run once and commit the output;
// re-run only to refresh geometry:  node scripts/gen-districts.mjs
//
// Source: Census cartographic boundary file, 118th-Congress districts (public domain, keyless) —
// the same asset the pipeline's tiger connector scores for compactness. Districts are keyed by
// STATE + district number (House ids do NOT end in a state postal — see E2.2), so we join each
// race's {state, district} to the TIGER GEOID = STATEFP + zero-padded CD118FP.
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { open } from "shapefile";

const here = dirname(fileURLToPath(import.meta.url));
const CONFIG_DIR = resolve(here, "../src/config/races");
const OUT_DIR = resolve(here, "../src/data/districts");

const SOURCE_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip";
// Geometry version [L547]: cb_2023 = 118th Congress district lines. 2026 races inherit these
// (the sanctioned public asset); states that redrew after 2023 are approximated — noted in .done.
const GEOMETRY_AS_OF = "2023-01-03";
const COORD_DP = 4; // ~11 m; plenty for a 240 px inline SVG, keeps files small.
const SIMPLIFY_EPS = 0.006; // Douglas-Peucker tolerance in degrees (~600 m) — trims dense TIGER
// vertex runs the 240 px inline SVG can't resolve, keeping shapes recognisable but light.

// USPS postal -> state FIPS (50 states; matches the race-config `state` field).
const POSTAL_TO_FIPS = {
  AL: "01", AK: "02", AZ: "04", AR: "05", CA: "06", CO: "08", CT: "09", DE: "10", FL: "12",
  GA: "13", HI: "15", ID: "16", IL: "17", IN: "18", IA: "19", KS: "20", KY: "21", LA: "22",
  ME: "23", MD: "24", MA: "25", MI: "26", MN: "27", MS: "28", MO: "29", MT: "30", NE: "31",
  NV: "32", NH: "33", NJ: "34", NM: "35", NY: "36", NC: "37", ND: "38", OH: "39", OK: "40",
  OR: "41", PA: "42", RI: "44", SC: "45", SD: "46", TN: "47", TX: "48", UT: "49", VT: "50",
  VA: "51", WA: "53", WV: "54", WI: "55", WY: "56",
};

// Collect the House races that need a district shape: raceId -> GEOID.
const targets = new Map();
for (const file of readdirSync(CONFIG_DIR)) {
  if (!file.endsWith(".json")) continue;
  const cfg = JSON.parse(readFileSync(join(CONFIG_DIR, file), "utf8"));
  if (cfg.office !== "house") continue;
  const fips = POSTAL_TO_FIPS[cfg.state];
  if (!fips) throw new Error(`No FIPS for state ${cfg.state} (${cfg.id})`);
  const geoid = fips + String(cfg.district).padStart(2, "0");
  targets.set(cfg.id, geoid);
}
console.log(`${targets.size} House races need district geometry.`);
const geoidToRace = new Map([...targets].map(([id, geoid]) => [geoid, id]));

// Download + unzip the cb shapefile into a temp dir (unzip is a build-time dep of this baker).
const work = mkdtempSync(join(tmpdir(), "btb-cd-"));
try {
  const zip = join(work, "cd.zip");
  console.log("Downloading TIGER cb_2023 CD118…");
  const buf = new Uint8Array(await (await fetch(SOURCE_URL)).arrayBuffer());
  writeFileSync(zip, buf);
  execFileSync("unzip", ["-o", zip, "-d", work], { stdio: "ignore" });
  const stem = readdirSync(work).find((n) => n.endsWith(".shp"))?.slice(0, -4);
  if (!stem) throw new Error("No .shp in the downloaded archive");

  // Douglas-Peucker line simplification on a ring's open point list (perp distance, deg space).
  const perp = (p, a, b) => {
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const len2 = dx * dx + dy * dy;
    if (len2 === 0) return Math.hypot(p[0] - a[0], p[1] - a[1]);
    const t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2;
    const cx = a[0] + t * dx;
    const cy = a[1] + t * dy;
    return Math.hypot(p[0] - cx, p[1] - cy);
  };
  const dp = (pts, eps) => {
    if (pts.length < 3) return pts;
    let maxD = -1;
    let idx = 0;
    for (let i = 1; i < pts.length - 1; i++) {
      const d = perp(pts[i], pts[0], pts[pts.length - 1]);
      if (d > maxD) {
        maxD = d;
        idx = i;
      }
    }
    if (maxD <= eps) return [pts[0], pts[pts.length - 1]];
    return [...dp(pts.slice(0, idx + 1), eps).slice(0, -1), ...dp(pts.slice(idx), eps)];
  };

  // Largest ring of a (Multi)Polygon, as a rounded [lon,lat][] closed ring.
  const round = (v) => Number(v.toFixed(COORD_DP));
  const ringArea = (r) => {
    let a = 0;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) a += r[j][0] * r[i][1] - r[i][0] * r[j][1];
    return Math.abs(a) / 2;
  };
  const biggestRing = (geom) => {
    const polys = geom.type === "MultiPolygon" ? geom.coordinates : [geom.coordinates];
    let best = null;
    let bestA = -1;
    for (const poly of polys) {
      const outer = poly[0]; // exterior ring
      const a = ringArea(outer);
      if (a > bestA) {
        bestA = a;
        best = outer;
      }
    }
    // simplify, then round + drop consecutive duplicates introduced by rounding
    const out = [];
    for (const [lon, lat] of dp(best, SIMPLIFY_EPS)) {
      const p = [round(lon), round(lat)];
      const prev = out[out.length - 1];
      if (!prev || prev[0] !== p[0] || prev[1] !== p[1]) out.push(p);
    }
    return out;
  };

  mkdirSync(OUT_DIR, { recursive: true });
  const src = await open(join(work, stem + ".shp"), join(work, stem + ".dbf"));
  const written = new Set();
  for (;;) {
    const rec = await src.read();
    if (rec.done) break;
    const geoid = rec.value.properties.GEOID;
    const raceId = geoidToRace.get(geoid);
    if (!raceId) continue;
    const ring = biggestRing(rec.value.geometry);
    const shape = { geoid, as_of: GEOMETRY_AS_OF, ring };
    writeFileSync(join(OUT_DIR, `${raceId}.json`), JSON.stringify(shape) + "\n");
    written.add(raceId);
  }

  const missing = [...targets.keys()].filter((id) => !written.has(id));
  if (missing.length) throw new Error(`No TIGER geometry matched: ${missing.join(", ")}`);
  console.log(`Wrote ${written.size} district shapes -> ${OUT_DIR}`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
