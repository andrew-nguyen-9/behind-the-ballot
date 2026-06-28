// Minimal internal-link checker over a built dist dir [S8a]. Fails CI if any local
// href/src points at a file that isn't in the build. External (http/mailto/#) skipped.
// ponytail: regex scan over dist is enough at this scale; swap for a real crawler
// (linkinator) only if pages start loading links dynamically.
import { readdir, readFile, access } from "node:fs/promises";
import { join, resolve, dirname, extname } from "node:path";

const root = resolve(process.argv[2] ?? "dist");

async function* htmlFiles(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) yield* htmlFiles(p);
    else if (extname(e.name) === ".html") yield p;
  }
}

const isExternal = (u) => /^(https?:|mailto:|tel:|data:|#|\/\/)/.test(u);
const attrRe = /(?:href|src)\s*=\s*["']([^"']+)["']/gi;

let broken = 0;
for await (const file of htmlFiles(root)) {
  const html = await readFile(file, "utf8");
  for (const [, raw] of html.matchAll(attrRe)) {
    const url = raw.split(/[?#]/)[0];
    if (!url || isExternal(url)) continue;
    let target = url.startsWith("/") ? join(root, url) : resolve(dirname(file), url);
    if (extname(target) === "") target = join(target, "index.html");
    try {
      await access(target);
    } catch {
      console.error(`BROKEN: ${url}  (in ${file})`);
      broken++;
    }
  }
}

if (broken) {
  console.error(`\n${broken} broken internal link(s).`);
  process.exit(1);
}
console.log("link check: ok");
