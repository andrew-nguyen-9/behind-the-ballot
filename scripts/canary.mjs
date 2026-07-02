// Post-deploy canary [v1.10.2/10.3] — verifies the LIVE Cloudflare preview is healthy:
// every key route serves 200 with NO redirect hop (catches the /races 307 class of regression),
// and the security headers [S8a] are present on the document response. Exits non-zero with a
// summary on any failure → the scheduled GitHub Action goes red → GitHub's native failure
// notification emails the repo owner (no SMTP dependency needed for the basic alert).
//
//   node scripts/canary.mjs [baseUrl]
//
// Also writes a machine-readable canary-report.json (checks[] with name/ok/detail/severity) that
// the v1.10.3 regression alerter reads to email + open a deduped GitHub issue with the delta.
// ponytail: dependency-free (global fetch, redirect:"manual").

import { writeFileSync } from "node:fs";

const BASE = (process.argv[2] || "https://ballot.an9.dev").replace(/\/$/, "");

// Slashless paths — the site links to these; drop-trailing-slash must serve them 200, no 307.
const ROUTES = [
  "/", "/races", "/forecast", "/sources", "/members",
  "/gerrymander", "/chamber", "/articles", "/search",
];
const REQUIRED_HEADERS = [
  "content-security-policy",
  "strict-transport-security",
  "x-content-type-options",
];

const fails = [];
const checks = []; // structured, for the regression alerter
const ok = (name) => checks.push({ name, ok: true, detail: "", severity: "critical" });
const bad = (name, detail) => {
  checks.push({ name, ok: false, detail, severity: "critical" });
  fails.push(`${name}: ${detail}`);
};

async function check(path) {
  const url = BASE + path;
  let res;
  try {
    res = await fetch(url, { redirect: "manual" });
  } catch (e) {
    bad(`route ${path}`, `fetch error ${e.message}`);
    return;
  }
  if (res.status !== 200) {
    bad(`route ${path}`, `expected 200, got ${res.status}${res.headers.get("location") ? ` -> ${res.headers.get("location")}` : ""}`);
  } else {
    ok(`route ${path}`);
  }
  if (path === "/") {
    for (const h of REQUIRED_HEADERS) {
      if (!res.headers.get(h)) bad(`header ${h}`, "missing on /");
      else ok(`header ${h}`);
    }
  }
}

for (const p of ROUTES) await check(p);

// Emit the report the regression alerter consumes (run URL from the GH Actions env when present).
const runUrl = process.env.GITHUB_SERVER_URL && process.env.GITHUB_REPOSITORY && process.env.GITHUB_RUN_ID
  ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
  : null;
writeFileSync("canary-report.json", JSON.stringify({ base: BASE, run_url: runUrl, checks }, null, 2));

if (fails.length) {
  console.error(`CANARY FAIL (${BASE}):\n` + fails.map((f) => "  - " + f).join("\n"));
  process.exit(1);
}
console.log(`canary ok — ${ROUTES.length} routes 200, security headers present (${BASE})`);
