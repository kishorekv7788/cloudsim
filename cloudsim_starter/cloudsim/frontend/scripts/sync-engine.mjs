// Keeps public/engine/*.py (used by src/engine.js + Pyodide) in sync with the
// real backend engine, so the browser runs the exact same simulation code.
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "..", "backend", "app", "engine");
const DEST = join(here, "..", "public", "engine");

const FILES = ["__init__", "models", "network", "routing", "firewall", "iam",
               "compute", "storage", "validator", "topology"];

mkdirSync(DEST, { recursive: true });
for (const f of FILES) {
  copyFileSync(join(SRC, `${f}.py`), join(DEST, `${f}.py`));
}
console.log(`synced ${FILES.length} engine files -> public/engine/`);
