// Self-hosts the Pyodide runtime (so the PWA works fully offline, no CDN needed)
// by copying it out of node_modules, plus the one extra wheel the engine uses.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const PYODIDE_PKG = join(here, "..", "node_modules", "pyodide");
const DEST = join(here, "..", "public", "pyodide");

const CORE_FILES = ["pyodide.mjs", "pyodide.mjs.map", "pyodide.asm.js",
                    "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"];

mkdirSync(DEST, { recursive: true });
for (const f of CORE_FILES) {
  copyFileSync(join(PYODIDE_PKG, f), join(DEST, f));
}

// Extra packages engine.js loads at runtime (py.loadPackage(...)) need their
// wheel fetched once from the lock file's own CDN and cached here for offline use.
const lock = JSON.parse(await (await import("node:fs/promises")).readFile(
  join(PYODIDE_PKG, "pyodide-lock.json"), "utf8"));
const EXTRA_PACKAGES = ["pyyaml"];

for (const name of EXTRA_PACKAGES) {
  const info = lock.packages[name];
  const dest = join(DEST, info.file_name);
  if (existsSync(dest)) continue;
  const url = `https://cdn.jsdelivr.net/pyodide/v${lock.info.version}/full/${info.file_name}`;
  console.log(`fetching ${name} <- ${url}`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`failed to fetch ${url}: ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  (await import("node:fs")).writeFileSync(dest, buf);
}

console.log("pyodide runtime + packages synced -> public/pyodide/");
