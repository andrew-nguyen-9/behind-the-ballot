// Post-deploy canary [v1.10.2/10.3] — verifies the LIVE Cloudflare preview is healthy:
// every key route serves 200 with NO redirect hop (catches the /races 307 class of regression),
// and the security headers [S8a] are present on the document response. Exits non-zero with a
// summary on any failure → the scheduled GitHub Action goes red → GitHub's native failure
// notification emails the repo owner (no SMTP dependency needed for the basic alert).
//
//   node scripts/canary.mjs [baseUrl]
//
// ponytail: dependency-free (global fetch, redirect:"manual"). Richer SMTP alerts = v1.10.3.

const BASE = (process.argv[2] || "https://behind-the-ballot.hh5zvph54s.workers.dev").replace(/\/$/, "");

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

async function check(path) {
  const url = BASE + path;
  let res;
  try {
    res = await fetch(url, { redirect: "manual" });
  } catch (e) {
    fails.push(`${path}: fetch error ${e.message}`);
    return;
  }
  if (res.status !== 200) {
    fails.push(`${path}: expected 200, got ${res.status}${res.headers.get("location") ? ` -> ${res.headers.get("location")}` : ""}`);
  }
  if (path === "/") {
    for (const h of REQUIRED_HEADERS) {
      if (!res.headers.get(h)) fails.push(`/: missing security header ${h}`);
    }
  }
}

for (const p of ROUTES) await check(p);

if (fails.length) {
  console.error(`CANARY FAIL (${BASE}):\n` + fails.map((f) => "  - " + f).join("\n"));
  process.exit(1);
}
console.log(`canary ok — ${ROUTES.length} routes 200, security headers present (${BASE})`);
