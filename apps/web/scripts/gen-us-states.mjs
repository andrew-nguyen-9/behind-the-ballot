// Build-time geometry bake [E1.1, Q6.1]: us-atlas TopoJSON -> static per-state SVG path `d`
// strings, so pages ship a 0-JS inline choropleth (no runtime topojson/d3). Uses the
// PRE-PROJECTED `states-albers-10m` bundle (albers-usa with AK/HI insets already baked into
// pixel coords on a 975x610 canvas), so geoPath runs with a null projection — the coordinates
// are already screen space. Run once and commit the output; re-run only to refresh geometry:
//   node scripts/gen-us-states.mjs
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { feature } from "topojson-client";
import { geoPath } from "d3-geo";
import topo from "us-atlas/states-albers-10m.json" with { type: "json" };

const here = dirname(fileURLToPath(import.meta.url));

// FIPS state code -> USPS postal code (50 states only; DC/territories dropped — no Senate seats).
const FIPS_TO_POSTAL = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
  "10": "DE", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
  "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA",
  "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV",
  "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
  "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN",
  "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
  "56": "WY",
};

const bbox = topo.bbox; // [x0, y0, x1, y1] in projected pixel space
const viewBox = `0 0 ${Math.round(bbox[2])} ${Math.round(bbox[3])}`;
const path = geoPath(null); // identity: coordinates are already albers-usa pixels

const states = feature(topo, topo.objects.states);
const paths = {};
for (const f of states.features) {
  const postal = FIPS_TO_POSTAL[String(f.id).padStart(2, "0")];
  if (!postal) continue;
  const d = path(f);
  if (d) paths[postal] = d;
}

const missing = Object.values(FIPS_TO_POSTAL).filter((p) => !paths[p]);
if (missing.length) throw new Error(`Missing geometry for: ${missing.join(", ")}`);

const out = { viewBox, paths };
const dest = resolve(here, "../src/data/us-states.json");
writeFileSync(dest, JSON.stringify(out) + "\n");
console.log(`Wrote ${Object.keys(paths).length} states -> ${dest} (viewBox ${viewBox})`);
