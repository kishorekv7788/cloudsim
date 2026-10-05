// Stage 5: run the SAME Python engine inside the browser/APK with Pyodide (no server needed).
import { loadPyodide } from "pyodide";

const ENGINE_FILES = ["__init__", "models", "network", "routing", "firewall", "iam",
                      "compute", "storage", "validator", "topology"];
let py;

export async function initEngine() {
  py = await loadPyodide({ indexURL: "/pyodide/" });   // self-host so it works offline
  await py.loadPackage("pyyaml");
  py.FS.mkdirTree("/home/pyodide/app/engine");
  py.FS.writeFile("/home/pyodide/app/__init__.py", "");
  for (const f of ENGINE_FILES) {
    const src = await (await fetch(`/engine/${f}.py`)).text();   // copy engine/*.py into public/engine/
    py.FS.writeFile(`/home/pyodide/app/engine/${f}.py`, src);
  }
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
}

export function checkCidr(a, b) {
  py.globals.set("cidr_a", a);
  py.globals.set("cidr_b", b);
  return py.runPython(
    "from app.engine.network import check_cidr_overlap\ncheck_cidr_overlap(cidr_a, cidr_b)");
}
