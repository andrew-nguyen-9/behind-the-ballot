// Coverage report [v1.10.1] — verifies every sanctioned race config has its expected per-race
// data joins, so a broken/empty export (a race that silently lost its finance or demographics
// file) fails CI instead of shipping a half-empty page [F4c,S8a].
//
//   node scripts/coverage.mjs
//
// Invariants (hard-fail): every race resolves DEMOGRAPHICS (state/district rollup always exists),
// and the members roster is non-empty. Reported-but-soft: FINANCE may be legitimately absent for a
// race with no FEC candidates filed yet — counted and printed, never fails the build on its own.
// ponytail: filesystem existence checks over committed src/data; no deps, no network.
import { readdir, readFile, access } from "node:fs/promises";
import { join, resolve } from "node:path";

const SRC = resolve(process.argv[2] ?? "apps/web/src");
const racesDir = join(SRC, "config/races");
const dataDir = join(SRC, "data");

const exists = (p) => access(p).then(() => true, () => false);

const raceFiles = (await readdir(racesDir)).filter((f) => f.endsWith(".json"));
const ids = await Promise.all(
  raceFiles.map(async (f) => JSON.parse(await readFile(join(racesDir, f), "utf8")).id),
);

let hasFinance = 0;
let hasDemographics = 0;
const failures = [];

for (const id of ids) {
  if (await exists(join(dataDir, "finance", `${id}.json`))) hasFinance++;
  if (await exists(join(dataDir, "demographics", `${id}.json`))) hasDemographics++;
  else failures.push(`${id}: missing demographics (every race must resolve a state/district rollup)`);
}

const roster = JSON.parse(await readFile(join(dataDir, "members/roster.json"), "utf8"));
if (!Array.isArray(roster) || roster.length === 0) failures.push("members/roster.json is empty");

const districts = JSON.parse(await readFile(join(dataDir, "gerrymander/districts.json"), "utf8"));

console.log("coverage report");
console.log(`  races:        ${ids.length}`);
console.log(`  finance:      ${hasFinance}/${ids.length}${hasFinance < ids.length ? " (some races have no FEC candidates filed — ok)" : ""}`);
console.log(`  demographics: ${hasDemographics}/${ids.length}`);
console.log(`  members:      ${roster.length}`);
console.log(`  districts:    ${districts.length}`);

if (failures.length) {
  console.error("\ncoverage FAIL:\n" + failures.map((f) => "  - " + f).join("\n"));
  process.exit(1);
}
console.log("coverage ok");
