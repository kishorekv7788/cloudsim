import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import Canvas from "./Canvas.jsx";
import { registerServiceWorker } from "./registerSW.js";

createRoot(document.getElementById("root")).render(<Canvas labId="az900-lab02" />);

// Cache-first SW is for the built/offline PWA - registering it under `vite dev` makes the
// browser serve a stale cached page forever, so only turn it on in production builds.
if (import.meta.env.PROD) {
  registerServiceWorker();
}
